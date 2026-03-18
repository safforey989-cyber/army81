"""
Army81 — Autonomy Loop (24/7)

هدفه: إنتاجية ذاتية للنظام نفسه:
- اكتشاف OSS + معرفة جديدة
- تقطير معرفي (teacher→student)
- تدريب مستمر + مراقبة أداء
- تحسين آمن (اختياري) للـ system_prompts

مبادئ:
- يعمل حتى بدون مفاتيح API (مع fallbacks)
- يحافظ على حدود السلامة (no git auto-push, تغييرات محدودة)
- يكتب حالة تشغيل في workspace/autonomy_state.json
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.llm_client import LLMClient

logger = logging.getLogger("army81.autonomy")


WORKSPACE = Path("workspace")
STATE_FILE = WORKSPACE / "autonomy_state.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state() -> Dict[str, Any]:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "started_at": _now_iso(),
        "ticks": 0,
        "last": {},
        "counters": {
            "discoveries": 0,
            "knowledge_layers_added": 0,
            "distill_examples": 0,
            "train_cycles": 0,
            "performance_checks": 0,
            "prompt_proposals": 0,
            "prompt_applied": 0,
        },
        "errors": [],
    }


def _save_state(state: Dict[str, Any]) -> None:
    WORKSPACE.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _due(last_ts: str | None, seconds: int) -> bool:
    if not last_ts:
        return True
    try:
        t = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).total_seconds() >= seconds
    except Exception:
        return True


@dataclass
class AutonomyConfig:
    # تكرارات (بالثواني)
    discovery_every_s: int = 60 * 60          # كل ساعة
    distill_every_s: int = 24 * 60 * 60       # يومياً
    micro_train_every_s: int = 30 * 60        # كل 30 دقيقة
    perf_check_every_s: int = 60 * 60         # كل ساعة
    prompt_opt_every_s: int = 6 * 60 * 60     # كل 6 ساعات

    # أحجام
    micro_train_max_agents: int = 10

    # مفاتيح تشغيل/حماية
    enable_discovery: bool = True
    enable_distillation: bool = True
    # micro-train داخل tick قد يكون مكلفاً جداً (LLM لكل وكيل).
    # نعطّله افتراضياً، ويمكن تفعيله عبر AUTONOMY_ENABLE_MICRO_TRAIN=1
    enable_micro_train: bool = False
    enable_perf_monitor: bool = True
    auto_apply_knowledge_layers: bool = True    # يضيف معرفة تلقائياً بدل pending
    auto_evolve_prompts: bool = True            # يطبق تحسين prompts تلقائياً

    # تقطير أسرع لتجنب تعليق الـ tick
    distill_max_pairs: int = 1

    # استغلال OSS إلى أدوات/مقترحات
    enable_oss_exploit: bool = True

    @staticmethod
    def from_env() -> "AutonomyConfig":
        def _b(name: str, default: bool) -> bool:
            v = os.getenv(name, "")
            if not v:
                return default
            return v.strip().lower() in ("1", "true", "yes", "on")

        def _i(name: str, default: int) -> int:
            v = os.getenv(name, "")
            try:
                return int(v) if v else default
            except Exception:
                return default

        return AutonomyConfig(
            discovery_every_s=_i("AUTONOMY_DISCOVERY_EVERY_S", 60 * 60),
            distill_every_s=_i("AUTONOMY_DISTILL_EVERY_S", 24 * 60 * 60),
            micro_train_every_s=_i("AUTONOMY_MICRO_TRAIN_EVERY_S", 30 * 60),
            perf_check_every_s=_i("AUTONOMY_PERF_CHECK_EVERY_S", 60 * 60),
            prompt_opt_every_s=_i("AUTONOMY_PROMPT_OPT_EVERY_S", 6 * 60 * 60),
            micro_train_max_agents=_i("AUTONOMY_TRAIN_MAX_AGENTS", 10),
            enable_discovery=_b("AUTONOMY_ENABLE_DISCOVERY", True),
            enable_distillation=_b("AUTONOMY_ENABLE_DISTILLATION", True),
            enable_micro_train=_b("AUTONOMY_ENABLE_MICRO_TRAIN", False),
            enable_perf_monitor=_b("AUTONOMY_ENABLE_PERF_MONITOR", True),
            auto_apply_knowledge_layers=_b("AUTO_APPLY_KNOWLEDGE_LAYERS", True),
            auto_evolve_prompts=_b("AUTO_EVOLVE_PROMPTS", True),
            distill_max_pairs=_i("AUTONOMY_DISTILL_MAX_PAIRS", 1),
            enable_oss_exploit=_b("AUTONOMY_ENABLE_OSS_EXPLOIT", True),
        )


class AutonomyLoop:
    def __init__(self, router=None, config: Optional[AutonomyConfig] = None):
        self.router = router
        self.cfg = config or AutonomyConfig.from_env()
        self.state = _load_state()

    def attach_router(self, router) -> None:
        self.router = router

    def tick(self) -> Dict[str, Any]:
        """
        Tick واحد: ينفّذ ما هو مستحق الآن فقط.
        Designed ليُستدعى كل 5-15 دقيقة من scheduler.
        """
        self.state["ticks"] = int(self.state.get("ticks", 0)) + 1
        started = time.time()
        ran = []
        errors = []

        last = self.state.setdefault("last", {})
        counters = self.state.setdefault("counters", {})

        # 0) sanity
        if not self.router or not getattr(self.router, "agents", None):
            msg = "router/agents not available (autonomy tick skipped)"
            logger.warning(msg)
            result = {"status": "skipped", "reason": msg, "ticks": self.state["ticks"]}
            self._finalize(ran, errors, started)
            return result

        # 1) Discovery (SelfBuilder)
        if self.cfg.enable_discovery and _due(last.get("discovery"), self.cfg.discovery_every_s):
            try:
                from core.self_builder import SelfBuilder
                b = SelfBuilder()
                discoveries = b.discover_and_add_knowledge()
                counters["discoveries"] = int(counters.get("discoveries", 0)) + 1
                last["discovery"] = _now_iso()
                ran.append({"step": "discovery", "github": len(discoveries.get("github", []))})
                _save_state(self.state)

                # auto-apply أفضل عنصر واحد كطبقة معرفة (اختياري)
                if self.cfg.auto_apply_knowledge_layers:
                    top = (discoveries.get("github", []) or [])[:1]
                    for repo in top:
                        try:
                            r = b.add_knowledge_layer("github", repo.get("full_name") or repo.get("name", ""), agent_id="A10")
                            counters["knowledge_layers_added"] = int(counters.get("knowledge_layers_added", 0)) + 1
                            ran.append({"step": "knowledge_layer", "repo": repo.get("full_name", repo.get("name", "")), "result": r})
                            _save_state(self.state)
                        except Exception as e:
                            errors.append(f"knowledge_layer_error: {e}")
            except Exception as e:
                errors.append(f"discovery_error: {e}")

        # 1.5) OSS exploit — توليد adapters ومقترحات دمج
        if self.cfg.enable_oss_exploit and _due(last.get("oss_exploit"), 60 * 60):
            try:
                from core.oss_exploiter import OSSExploiter
                ex = OSSExploiter()
                exr = ex.exploit_latest()
                last["oss_exploit"] = _now_iso()
                ran.append({"step": "oss_exploit", "repos": len(exr.get("repos", []))})
                _save_state(self.state)
            except Exception as e:
                errors.append(f"oss_exploit_error: {e}")

        # 2) Distillation (engine الجديد) — يعمل حتى بدون Router API keys (قد يسجل ERROR إن لم يوجد مفتاح)
        if self.cfg.enable_distillation and _due(last.get("distillation"), self.cfg.distill_every_s):
            try:
                from core.distillation_engine import DistillationEngine

                def get_agent_fn(task: str, model: str = "gemini-flash") -> Dict[str, str]:
                    client = LLMClient(model)
                    resp = client.chat([
                        {"role": "system", "content": "أنت نموذج خبير. أجب بإيجاز مفيد ومنظم."},
                        {"role": "user", "content": task},
                    ], temperature=0.4)
                    return {
                        "result": resp.get("content", ""),
                        "reasoning": "",
                        "model": model,
                    }

                de = DistillationEngine()
                dres = de.daily_distillation(
                    get_agent_fn=get_agent_fn,
                    max_pairs=self.cfg.distill_max_pairs,
                    sleep_s=0.1,
                )
                counters["distill_examples"] = int(counters.get("distill_examples", 0)) + int(dres.get("examples_added", 0))
                last["distillation"] = _now_iso()
                ran.append({"step": "distillation", "result": dres})
                _save_state(self.state)
            except Exception as e:
                errors.append(f"distillation_error: {e}")

        # 3) Micro Training (جزء من الوكلاء، بتكرار أعلى)
        if self.cfg.enable_micro_train and _due(last.get("micro_train"), self.cfg.micro_train_every_s):
            try:
                from core.continuous_trainer import get_continuous_trainer
                trainer = get_continuous_trainer(self.router)
                res = trainer.train_cycle(max_agents=self.cfg.micro_train_max_agents)
                counters["train_cycles"] = int(counters.get("train_cycles", 0)) + 1
                last["micro_train"] = _now_iso()
                ran.append({"step": "micro_train", "trained": res.get("trained", 0), "passed": res.get("passed", 0)})
                _save_state(self.state)
            except Exception as e:
                errors.append(f"micro_train_error: {e}")

        # 4) Performance monitor
        if self.cfg.enable_perf_monitor and _due(last.get("perf_check"), self.cfg.perf_check_every_s):
            try:
                from core.continuous_trainer import get_continuous_trainer
                trainer = get_continuous_trainer(self.router)
                pres = trainer.performance_monitor()
                counters["performance_checks"] = int(counters.get("performance_checks", 0)) + 1
                last["perf_check"] = _now_iso()
                ran.append({"step": "performance_monitor", "alerts": len(pres.get("alerts", []))})
                _save_state(self.state)
            except Exception as e:
                errors.append(f"perf_check_error: {e}")

        # 5) Prompt evolution (SafeEvolution) — مقيد ومغلق افتراضياً
        if self.cfg.auto_evolve_prompts and _due(last.get("prompt_opt"), self.cfg.prompt_opt_every_s):
            try:
                from core.safe_evolution import SafeEvolution
                se = SafeEvolution()

                # اختار وكيل واحد فقط لتقليل المخاطر
                agent_id = "A01"
                counters["prompt_proposals"] = int(counters.get("prompt_proposals", 0)) + 1
                proposal = se.propose_improvement(agent_id)
                if proposal and isinstance(proposal, dict) and proposal.get("prompt"):
                    if se.test_improvement(agent_id, proposal["prompt"]):
                        se.apply_improvement(agent_id, proposal["prompt"])
                        counters["prompt_applied"] = int(counters.get("prompt_applied", 0)) + 1
                        ran.append({"step": "prompt_evolve", "agent": agent_id, "applied": True})
                    else:
                        ran.append({"step": "prompt_evolve", "agent": agent_id, "applied": False})
                last["prompt_opt"] = _now_iso()
                _save_state(self.state)
            except Exception as e:
                errors.append(f"prompt_opt_error: {e}")

        self._finalize(ran, errors, started)
        return {
            "status": "ok",
            "ran": ran,
            "errors": errors,
            "ticks": self.state["ticks"],
            "ts": _now_iso(),
        }

    def _finalize(self, ran: list, errors: list, started: float) -> None:
        if errors:
            self.state.setdefault("errors", [])
            # احتفظ بآخر 50 خطأ
            for e in errors[-10:]:
                self.state["errors"].append({"ts": _now_iso(), "error": str(e)[:400]})
            self.state["errors"] = self.state["errors"][-50:]

        self.state["last_tick"] = _now_iso()
        self.state["last_tick_elapsed_s"] = round(time.time() - started, 2)
        self.state["last_tick_ran"] = ran
        _save_state(self.state)

