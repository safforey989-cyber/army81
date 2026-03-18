"""
Army81 v7 — Continuous Trainer
مدرّب مكثف 24/7 — يدرّب كل الـ 81 وكيل بسيناريوهات حقيقية

الجدول:
  كل 4 ساعات → train_cycle() — دورة تدريب كاملة
  كل 2 ساعة → performance_monitor() — مراقبة أداء
  كل 6 ساعات → multi_agent_drill() — تدريب جماعي

النتائج:
  486 مهمة تدريب/يوم (6 دورات × 81 وكيل)
  + 4 تدريبات جماعية/يوم
  + مراقبة مستمرة مع تدخل فوري
"""
import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.continuous_trainer")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS_FILE = os.path.join(BASE_DIR, "workspace", "agent_levels.json")
TRAINING_LOG = os.path.join(BASE_DIR, "workspace", "training_log.json")

os.makedirs(os.path.join(BASE_DIR, "workspace"), exist_ok=True)


class ContinuousTrainer:
    """
    المدرّب المكثف 24/7
    يرفع مستوى كل وكيل من 1 إلى 10 تدريجياً
    """

    def __init__(self, router=None):
        self.router = router
        self.levels = self._load_levels()
        self.training_log = []
        self._scenario_engine = None
        self._cloud_memory = None
        self._skill_adapter = None

    @property
    def scenario_engine(self):
        if self._scenario_engine is None:
            from core.scenario_engine import get_scenario_engine
            self._scenario_engine = get_scenario_engine()
        return self._scenario_engine

    @property
    def cloud_memory(self):
        if self._cloud_memory is None:
            try:
                from memory.cloud_memory import get_cloud_memory
                self._cloud_memory = get_cloud_memory()
            except Exception:
                pass
        return self._cloud_memory

    @property
    def skill_adapter(self):
        if self._skill_adapter is None:
            try:
                from core.skill_memory_adapter import get_skill_memory_adapter
                self._skill_adapter = get_skill_memory_adapter()
            except Exception:
                pass
        return self._skill_adapter

    # ═══════════════════════════════════════════════
    # دورة التدريب الرئيسية — كل 4 ساعات
    # ═══════════════════════════════════════════════

    def train_cycle(self, max_agents: int = 81) -> Dict:
        """
        دورة تدريب كاملة — يدرّب كل الوكلاء
        يختار سيناريو مناسب لمستوى كل وكيل
        """
        start = datetime.now()
        logger.info(f"=== Training Cycle Started: {start.isoformat()} ===")

        results = {
            "timestamp": start.isoformat(),
            "trained": 0,
            "passed": 0,
            "failed": 0,
            "leveled_up": 0,
            "intensive_triggered": 0,
            "agents": [],
        }

        if not self.router or not self.router.agents:
            logger.warning("No router/agents available for training")
            return results

        agents = list(self.router.agents.values())[:max_agents]

        for agent in agents:
            try:
                agent_result = self._train_single_agent(agent)
                results["trained"] += 1

                if agent_result["passed"]:
                    results["passed"] += 1
                    if agent_result.get("leveled_up"):
                        results["leveled_up"] += 1
                else:
                    results["failed"] += 1
                    if agent_result.get("intensive"):
                        results["intensive_triggered"] += 1

                results["agents"].append({
                    "id": agent.agent_id,
                    "score": agent_result["score"],
                    "grade": agent_result["grade"],
                    "level": self.get_level(agent.agent_id),
                    "passed": agent_result["passed"],
                })

            except Exception as e:
                logger.warning(f"Training error for {agent.agent_id}: {e}")
                results["failed"] += 1

        elapsed = (datetime.now() - start).total_seconds()
        results["elapsed_seconds"] = round(elapsed, 1)

        # حفظ النتائج
        self._log_training(results)
        self._save_levels()

        # إرسال ملخص عبر Telegram
        self._notify_training_complete(results)

        logger.info(
            f"=== Training Cycle Complete: {results['trained']} trained, "
            f"{results['passed']} passed, {results['leveled_up']} leveled up, "
            f"{elapsed:.0f}s ==="
        )
        return results

    def _train_single_agent(self, agent) -> Dict:
        """تدريب وكيل واحد بسيناريو مناسب لمستواه"""
        agent_id = agent.agent_id
        level = self.get_level(agent_id)

        # اختر سيناريو
        scenario = self.scenario_engine.get_scenario_for_agent(agent_id, level)
        if not scenario:
            return {"score": 0, "grade": "F", "passed": False}

        task = scenario["task"]
        min_words = scenario.get("min_words", 50)
        criteria = scenario.get("criteria", [])

        # نفّذ المهمة
        start = time.time()
        try:
            result = agent.run(task)
            response = result.result if hasattr(result, "result") else str(result)
            elapsed = time.time() - start
        except Exception as e:
            return {"score": 0, "grade": "F", "passed": False, "error": str(e)}

        # قيّم
        evaluation = self.scenario_engine.evaluate_response(
            task, response, criteria, min_words
        )

        # سجّل النتيجة
        self.scenario_engine.record_result(
            agent_id, scenario.get("id", "?"), evaluation, elapsed
        )

        # حفظ في cloud memory
        if self.cloud_memory:
            try:
                self.cloud_memory.store_episode(
                    agent_id, f"[TRAINING] {task[:200]}", response[:500],
                    success=evaluation["passed"],
                    rating=int(evaluation["total"]),
                    model=getattr(agent, "model_alias", ""),
                    task_type="training",
                )
            except Exception:
                pass

        # قرار الترقية أو التدريب المكثف
        score = evaluation["total"]
        result_dict = {
            "score": score,
            "grade": evaluation["grade"],
            "passed": evaluation["passed"],
            "leveled_up": False,
            "intensive": False,
        }

        if score >= 8.0 and level < 10:
            self.level_up(agent_id)
            result_dict["leveled_up"] = True
        elif score < 4.0:
            result_dict["intensive"] = True
            # جدول تدريب مكثف لهذا الوكيل
            self._schedule_intensive(agent_id)

        return result_dict

    # ═══════════════════════════════════════════════
    # تدريب مكثف للوكلاء الضعاف
    # ═══════════════════════════════════════════════

    def intensive_training(self, agent_id: str, num_tasks: int = 5) -> Dict:
        """تدريب مكثف — 5 مهام متتالية بمستوى سهل"""
        if not self.router or agent_id not in self.router.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent = self.router.agents[agent_id]
        results = []

        for i in range(num_tasks):
            scenario = self.scenario_engine.get_scenario_for_agent(agent_id, 2)
            if not scenario:
                continue

            try:
                start = time.time()
                result = agent.run(scenario["task"])
                response = result.result if hasattr(result, "result") else str(result)
                elapsed = time.time() - start

                evaluation = self.scenario_engine.evaluate_response(
                    scenario["task"], response,
                    scenario.get("criteria", []),
                    scenario.get("min_words", 50),
                )
                results.append({
                    "task": i + 1,
                    "score": evaluation["total"],
                    "passed": evaluation["passed"],
                })
            except Exception as e:
                results.append({"task": i + 1, "score": 0, "error": str(e)})

        avg = sum(r.get("score", 0) for r in results) / max(len(results), 1)
        return {
            "agent_id": agent_id,
            "tasks": num_tasks,
            "avg_score": round(avg, 1),
            "results": results,
        }

    # ═══════════════════════════════════════════════
    # تدريب جماعي — سيناريوهات متعددة الوكلاء
    # ═══════════════════════════════════════════════

    def multi_agent_drill(self) -> Dict:
        """تدريب جماعي — سيناريو واحد يتعاون فيه عدة وكلاء"""
        scenario = self.scenario_engine.get_multi_agent_scenario()
        if not scenario or not self.router:
            return {"error": "No scenario or router"}

        agent_ids = scenario.get("agents", [])
        task = scenario["task"]
        start = time.time()

        # pipeline: كل وكيل يبني على نتيجة السابق
        if self.router:
            available_ids = [aid for aid in agent_ids if aid in self.router.agents]
            if len(available_ids) >= 2:
                result = self.router.pipeline(task, available_ids)
                elapsed = time.time() - start

                return {
                    "scenario_id": scenario.get("id", "?"),
                    "agents": available_ids,
                    "steps": result.get("steps", 0),
                    "status": result.get("status", "unknown"),
                    "elapsed_seconds": round(elapsed, 1),
                }

        return {"error": "Not enough agents available"}

    # ═══════════════════════════════════════════════
    # مراقبة الأداء — كل 2 ساعة
    # ═══════════════════════════════════════════════

    def performance_monitor(self) -> Dict:
        """
        مراقب حقيقي — يفحص أداء كل وكيل
        إذا تراجع أكثر من 15% → يشغّل تدريب مكثف
        """
        logger.info("=== Performance Monitor Running ===")
        alerts = []
        retrained = []

        if not self.router:
            return {"alerts": [], "retrained": []}

        for agent_id, agent in self.router.agents.items():
            stats = agent.stats
            done = stats.get("tasks_done", 0)
            failed = stats.get("tasks_failed", 0)

            if done < 3:
                continue  # لا بيانات كافية

            fail_rate = failed / (done + failed) if (done + failed) > 0 else 0
            level = self.get_level(agent_id)

            # تنبيه إذا نسبة الفشل عالية
            if fail_rate > 0.3:
                alerts.append({
                    "agent_id": agent_id,
                    "fail_rate": round(fail_rate * 100, 1),
                    "level": level,
                    "action": "intensive_training_scheduled",
                })
                self._schedule_intensive(agent_id)
                retrained.append(agent_id)

        if alerts:
            logger.warning(f"Performance alerts: {len(alerts)} agents need attention")

        return {
            "checked": len(self.router.agents),
            "alerts": alerts,
            "retrained": retrained,
            "timestamp": datetime.now().isoformat(),
        }

    # ═══════════════════════════════════════════════
    # نظام المستويات
    # ═══════════════════════════════════════════════

    def get_level(self, agent_id: str) -> int:
        """مستوى الوكيل الحالي (1-10)"""
        return self.levels.get(agent_id, 3)  # يبدأ من 3

    def level_up(self, agent_id: str):
        """ترقية مستوى"""
        current = self.get_level(agent_id)
        if current < 10:
            self.levels[agent_id] = current + 1
            logger.info(f"⬆️ {agent_id} leveled up: {current} → {current + 1}")

    def level_down(self, agent_id: str):
        """تنزيل مستوى"""
        current = self.get_level(agent_id)
        if current > 1:
            self.levels[agent_id] = current - 1

    def get_all_levels(self) -> Dict[str, int]:
        return dict(self.levels)

    # ═══════════════════════════════════════════════
    # الحالة
    # ═══════════════════════════════════════════════

    def status(self) -> Dict:
        level_dist = {}
        for aid, lvl in self.levels.items():
            level_dist[lvl] = level_dist.get(lvl, 0) + 1

        return {
            "agents_tracked": len(self.levels),
            "avg_level": round(sum(self.levels.values()) / max(len(self.levels), 1), 1),
            "max_level": max(self.levels.values()) if self.levels else 0,
            "min_level": min(self.levels.values()) if self.levels else 0,
            "level_distribution": level_dist,
            "training_log_size": len(self.training_log),
            "scenarios": self.scenario_engine.status(),
            "leaderboard_top5": self.scenario_engine.get_leaderboard()[:5],
        }

    # ═══════════════════════════════════════════════
    # Internal
    # ═══════════════════════════════════════════════

    def _schedule_intensive(self, agent_id: str):
        """يجدول تدريب مكثف"""
        logger.info(f"Scheduled intensive training for {agent_id}")
        # في التشغيل الحقيقي، يمكن إضافته لقائمة انتظار
        # حالياً نسجل فقط
        self.training_log.append({
            "action": "intensive_scheduled",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        })

    def _notify_training_complete(self, results: Dict):
        """إرسال ملخص التدريب عبر Telegram"""
        try:
            from core.human_interface import get_human_interface
            hi = get_human_interface()
            hi.notify(
                "دورة تدريب مكتملة",
                f"تدريب: {results['trained']} وكيل\n"
                f"نجح: {results['passed']} | فشل: {results['failed']}\n"
                f"ترقية: {results['leveled_up']} وكيل\n"
                f"الوقت: {results.get('elapsed_seconds', 0)}s",
                urgency="normal",
            )
        except Exception:
            pass

    def _log_training(self, results: Dict):
        self.training_log.append(results)
        # احتفظ بآخر 50
        self.training_log = self.training_log[-50:]

        # حفظ
        try:
            with open(TRAINING_LOG, "w", encoding="utf-8") as f:
                json.dump(self.training_log, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_levels(self) -> Dict[str, int]:
        if os.path.exists(LEVELS_FILE):
            try:
                with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # مستوى ابتدائي لكل وكيل
        levels = {}
        for i in range(1, 82):
            levels[f"A{str(i).zfill(2)}"] = 3
        return levels

    def _save_levels(self):
        with open(LEVELS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.levels, f, ensure_ascii=False, indent=2)


# Singleton
_trainer: Optional[ContinuousTrainer] = None

def get_continuous_trainer(router=None) -> ContinuousTrainer:
    global _trainer
    if _trainer is None:
        _trainer = ContinuousTrainer(router)
    return _trainer
