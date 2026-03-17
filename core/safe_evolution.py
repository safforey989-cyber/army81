"""
SafeEvolution — مستوحى من aden-hive/hive
مع constitutional_guardrails لمنع الانحراف
نتيجة Monte Carlo: هذا الفرق بين 8% و 90% نجاة
"""
import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger("army81.safe_evolution")

_WORKSPACE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
)
_BACKUPS_DIR = os.path.join(_WORKSPACE, "backups")
_EVOLUTION_LOG = os.path.join(_WORKSPACE, "evolution_log.json")
_BENCHMARK_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tests", "benchmark_tasks.json")
)


class SafeEvolution:
    """دورة التطور الذاتي الأسبوعية للوكلاء"""

    def evaluate(self, agent_id: str) -> float:
        """
        يشغّل 5 مهام من tests/benchmark_tasks.json
        يحسب: avg_quality + speed + cost_efficiency
        يعيد score 0-100
        """
        try:
            if not os.path.exists(_BENCHMARK_FILE):
                logger.warning(f"[SafeEvolution] benchmark_tasks.json not found")
                return 50.0

            with open(_BENCHMARK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            tasks = data.get("tasks", [])[:5]
            if not tasks:
                return 50.0

            # تحميل الوكيل
            agent = self._load_agent(agent_id)
            if not agent:
                return 0.0

            scores = []
            for task_def in tasks:
                try:
                    import time
                    start = time.time()
                    result = agent.run(task_def["task"])
                    elapsed = time.time() - start

                    # تقييم الجودة
                    quality = self._score_result(result.result, task_def)
                    speed_score = max(0, 100 - elapsed * 10)  # سريع = جيد
                    cost_score = max(0, 100 - (result.tokens_used / 100))

                    task_score = (quality * 0.6) + (speed_score * 0.2) + (cost_score * 0.2)
                    scores.append(task_score)
                except Exception as e:
                    logger.warning(f"[SafeEvolution] benchmark task failed: {e}")
                    scores.append(0.0)

            avg = sum(scores) / len(scores) if scores else 0.0
            logger.info(f"[SafeEvolution] {agent_id} score: {avg:.1f}")
            return round(avg, 1)

        except Exception as e:
            logger.error(f"[SafeEvolution] evaluate error: {e}")
            return 50.0

    def _score_result(self, result: str, task_def: Dict) -> float:
        """تقييم جودة النتيجة بناءً على معايير المهمة"""
        score = 50.0  # baseline

        # معيار min_words
        min_words = task_def.get("min_words", 0)
        if min_words > 0:
            word_count = len(result.split())
            if word_count >= min_words:
                score += 30
            else:
                score += (word_count / min_words) * 30

        # معيار must_contain
        must_contain = task_def.get("must_contain", [])
        if must_contain:
            found = sum(1 for kw in must_contain if kw.lower() in result.lower())
            score += (found / len(must_contain)) * 20

        # لم يحدث خطأ
        if "خطأ" not in result and "ERROR" not in result:
            score += 10

        return min(100.0, score)

    def propose_improvement(self, agent_id: str) -> Optional[Dict]:
        """
        يقرأ آخر 10 episodes فاشلة من EpisodicMemory
        يقترح تعديل على system_prompt
        يعيد: {prompt, reasoning, expected_gain}
        """
        try:
            from memory.hierarchical_memory import HierarchicalMemory
            hm = HierarchicalMemory()
            failures = hm.L2.get_failures(agent_id, limit=10)

            if not failures:
                return None

            # بناء تحليل الفشل
            failure_summary = "\n".join([
                f"- {f.get('task_summary', '')[:100]}: {f.get('result_summary', '')[:100]}"
                for f in failures[:5]
            ])

            # الحصول على system_prompt الحالي
            current_prompt = self._get_current_prompt(agent_id)

            try:
                from core.llm_client import LLMClient
                client = LLMClient("gemini-flash")
                response = client.chat([
                    {
                        "role": "system",
                        "content": "أنت خبير تحسين أداء وكلاء الذكاء الاصطناعي."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"الـ system_prompt الحالي:\n{current_prompt[:500]}\n\n"
                            f"أبرز الإخفاقات:\n{failure_summary}\n\n"
                            f"اقترح تحسيناً مختصراً على system_prompt يعالج هذه الإخفاقات. "
                            f"أجب بصيغة JSON: {{\"prompt\": \"...\", \"reasoning\": \"...\", \"expected_gain\": 0-100}}"
                        ),
                    },
                ])
                content = response.get("content", "")
                # حاول استخراج JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"[SafeEvolution] propose_improvement LLM error: {e}")

            # fallback: اقتراح بسيط
            return {
                "prompt": current_prompt + "\n\n## تعليمات إضافية:\n- كن أكثر دقة وتفصيلاً في إجاباتك",
                "reasoning": f"بناءً على {len(failures)} إخفاق أخير",
                "expected_gain": 10,
            }

        except Exception as e:
            logger.error(f"[SafeEvolution] propose_improvement error: {e}")
            return None

    def test_improvement(self, agent_id: str, proposed_prompt: str) -> bool:
        """
        يشغّل 3 مهام قياسية بالـ prompt الجديد
        يقبل فقط إذا تحسّن > 10%
        """
        try:
            # قياس الأداء الحالي
            current_score = self.evaluate(agent_id)

            # تطبيق الـ prompt مؤقتاً
            agent = self._load_agent(agent_id)
            if not agent:
                return False

            old_prompt = agent.system_prompt
            agent.system_prompt = proposed_prompt

            # قياس الأداء الجديد (3 مهام فقط)
            if not os.path.exists(_BENCHMARK_FILE):
                return False

            with open(_BENCHMARK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            tasks = data.get("tasks", [])[:3]
            scores = []
            for task_def in tasks:
                try:
                    result = agent.run(task_def["task"])
                    score = self._score_result(result.result, task_def)
                    scores.append(score)
                except Exception:
                    scores.append(0.0)

            new_score = sum(scores) / len(scores) if scores else 0.0

            # استرجع الـ prompt القديم
            agent.system_prompt = old_prompt

            improvement = new_score - current_score
            logger.info(
                f"[SafeEvolution] {agent_id}: current={current_score:.1f}, "
                f"new={new_score:.1f}, improvement={improvement:.1f}"
            )
            return improvement > 10.0

        except Exception as e:
            logger.error(f"[SafeEvolution] test_improvement error: {e}")
            return False

    def apply_improvement(self, agent_id: str, new_prompt: str):
        """
        1. تحقق من ConstitutionalGuardrails
        2. احفظ النسخة القديمة في workspace/backups/
        3. طبّق التغيير على ملف JSON
        4. سجّل في workspace/evolution_log.json
        """
        from core.constitutional_guardrails import ConstitutionalGuardrails
        guardrails = ConstitutionalGuardrails()

        # 1. تحقق من القواعد
        allowed, reason = guardrails.check(
            "update_system_prompt",
            {"agent_id": agent_id, "tests_passed": 3}
        )
        if not allowed:
            logger.warning(f"[SafeEvolution] Blocked by guardrails: {reason}")
            return

        # 2. احفظ النسخة القديمة
        agent_json = self._find_agent_json(agent_id)
        if agent_json and os.path.exists(agent_json):
            os.makedirs(_BACKUPS_DIR, exist_ok=True)
            backup_name = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(_BACKUPS_DIR, backup_name)
            shutil.copy2(agent_json, backup_path)
            logger.info(f"[SafeEvolution] Backup saved: {backup_path}")

            # 3. طبّق التغيير
            with open(agent_json, "r", encoding="utf-8") as f:
                agent_data = json.load(f)
            agent_data["system_prompt"] = new_prompt
            with open(agent_json, "w", encoding="utf-8") as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)

        # 4. سجّل
        self._log_evolution(agent_id, new_prompt)

    def rollback(self, agent_id: str):
        """استعد النسخة الأخيرة من workspace/backups/"""
        try:
            if not os.path.exists(_BACKUPS_DIR):
                logger.warning(f"[SafeEvolution] No backups directory")
                return

            # ابحث عن أحدث backup
            backups = sorted([
                f for f in os.listdir(_BACKUPS_DIR)
                if f.startswith(agent_id) and f.endswith(".json")
            ], reverse=True)

            if not backups:
                logger.warning(f"[SafeEvolution] No backup found for {agent_id}")
                return

            backup_path = os.path.join(_BACKUPS_DIR, backups[0])
            agent_json = self._find_agent_json(agent_id)

            if agent_json:
                shutil.copy2(backup_path, agent_json)
                logger.info(f"[SafeEvolution] Rolled back {agent_id} from {backups[0]}")
            else:
                logger.warning(f"[SafeEvolution] Cannot find agent JSON for {agent_id}")

        except Exception as e:
            logger.error(f"[SafeEvolution] rollback error: {e}")

    def weekly_cycle(self):
        """
        يُشغَّل كل أحد الساعة 5 صباحاً:
        1. evaluate كل الوكلاء
        2. حدد أضعف 10 وكلاء
        3. improve كل واحد
        4. git commit + push إذا تغيّر > 3 وكلاء
        """
        import subprocess

        logger.info("[SafeEvolution] === بدء دورة التطور الأسبوعي ===")
        changed_agents = []

        # 1. تحميل كل الوكلاء
        agents_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "agents")
        )
        all_agent_ids = self._discover_agents(agents_dir)

        # 2. تقييم وترتيب
        scores = {}
        for agent_id in all_agent_ids:
            score = self.evaluate(agent_id)
            scores[agent_id] = score

        # أضعف 10
        weakest = sorted(scores.items(), key=lambda x: x[1])[:10]
        logger.info(f"[SafeEvolution] أضعف 10 وكلاء: {[a[0] for a in weakest]}")

        # 3. تحسين
        for agent_id, score in weakest:
            try:
                proposal = self.propose_improvement(agent_id)
                if not proposal:
                    continue

                if self.test_improvement(agent_id, proposal["prompt"]):
                    self.apply_improvement(agent_id, proposal["prompt"])
                    changed_agents.append(agent_id)
                    logger.info(f"[SafeEvolution] ✅ Improved: {agent_id}")
                else:
                    logger.info(f"[SafeEvolution] ⏭ No improvement for {agent_id}")
            except Exception as e:
                logger.error(f"[SafeEvolution] Error improving {agent_id}: {e}")

        # 4. git commit إذا تغيّر > 3 وكلاء
        if len(changed_agents) > 3:
            try:
                agents_str = ", ".join(changed_agents[:5])
                subprocess.run(["git", "add", "agents/"], check=True)
                subprocess.run([
                    "git", "commit", "-m",
                    f"feat(evolution): auto-improve {len(changed_agents)} agents\n"
                    f"Improved: {agents_str}..."
                ], check=True)
                subprocess.run(["git", "push"], check=True)
                logger.info(f"[SafeEvolution] Committed and pushed {len(changed_agents)} improvements")
            except Exception as e:
                logger.warning(f"[SafeEvolution] Git commit error: {e}")

        logger.info(f"[SafeEvolution] === انتهت الدورة: {len(changed_agents)} تحسين ===")
        return {"changed": changed_agents, "scores": scores}

    # ── دوال مساعدة ──────────────────────────────────

    def _load_agent(self, agent_id: str):
        """تحميل وكيل بـ ID"""
        try:
            json_path = self._find_agent_json(agent_id)
            if not json_path:
                return None
            from core.base_agent import load_agent_from_json
            return load_agent_from_json(json_path)
        except Exception as e:
            logger.warning(f"[SafeEvolution] Cannot load agent {agent_id}: {e}")
            return None

    def _find_agent_json(self, agent_id: str) -> Optional[str]:
        """ابحث عن ملف JSON للوكيل"""
        agents_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "agents")
        )
        for root, _, files in os.walk(agents_dir):
            for f in files:
                if f.endswith(".json") and agent_id.lower() in f.lower():
                    return os.path.join(root, f)
        return None

    def _get_current_prompt(self, agent_id: str) -> str:
        """اقرأ system_prompt الحالي"""
        json_path = self._find_agent_json(agent_id)
        if not json_path or not os.path.exists(json_path):
            return ""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("system_prompt", "")
        except Exception:
            return ""

    def _log_evolution(self, agent_id: str, new_prompt: str):
        """سجّل التطور في evolution_log.json"""
        os.makedirs(_WORKSPACE, exist_ok=True)
        log = []
        if os.path.exists(_EVOLUTION_LOG):
            try:
                with open(_EVOLUTION_LOG, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except Exception:
                log = []

        log.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "prompt_preview": new_prompt[:200],
        })

        with open(_EVOLUTION_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    def _discover_agents(self, agents_dir: str):
        """اكتشف كل IDs الوكلاء"""
        ids = []
        if not os.path.exists(agents_dir):
            return ids
        for root, _, files in os.walk(agents_dir):
            for f in files:
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                            data = json.load(fp)
                        if "agent_id" in data:
                            ids.append(data["agent_id"])
                    except Exception:
                        pass
        return ids
