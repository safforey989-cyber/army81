"""
Army81 - Prompt Optimizer
تحسين system prompts تلقائياً بناءً على أداء الوكلاء
المرحلة 4: التطور الذاتي
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.prompt_optimizer")

_WORKSPACE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
)
_BACKUPS_DIR = os.path.join(_WORKSPACE, "prompt_backups")
_LESSONS_DIR = os.path.join(_WORKSPACE, "lessons")


class PromptOptimizer:
    """
    يحسّن system prompts تلقائياً:
    1. يجمع دروس من كل مهمة
    2. يحلل أنماط النجاح والفشل
    3. يقترح تحسينات على الـ prompt
    4. يحفظ نسخة احتياطية قبل التعديل
    """

    def __init__(self):
        self._llm = None
        os.makedirs(_BACKUPS_DIR, exist_ok=True)
        os.makedirs(_LESSONS_DIR, exist_ok=True)

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import LLMClient
            self._llm = LLMClient("gemini-flash")
        return self._llm

    # ── جمع الدروس ──────────────────────────────────────────

    def collect_lesson(self, agent_id: str, task: str, result: str,
                       success: bool, rating: int = 7,
                       feedback: str = "") -> Dict:
        """
        جمع درس من مهمة — يُستدعى بعد كل تنفيذ
        """
        lesson = {
            "agent_id": agent_id,
            "task": task[:300],
            "result_preview": result[:500],
            "success": success,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
        }

        # حفظ الدرس
        lessons_file = os.path.join(_LESSONS_DIR, f"{agent_id}_lessons.jsonl")
        try:
            with open(lessons_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(lesson, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Save lesson error: {e}")

        return lesson

    def get_lessons(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """قراءة دروس وكيل"""
        lessons_file = os.path.join(_LESSONS_DIR, f"{agent_id}_lessons.jsonl")
        if not os.path.exists(lessons_file):
            return []

        lessons = []
        try:
            with open(lessons_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        lessons.append(json.loads(line))
        except Exception as e:
            logger.error(f"Read lessons error: {e}")

        return lessons[-limit:]

    # ── تحليل الأنماط ────────────────────────────────────────

    def analyze_patterns(self, agent_id: str) -> Dict:
        """تحليل أنماط النجاح والفشل لوكيل"""
        lessons = self.get_lessons(agent_id)
        if not lessons:
            return {"agent_id": agent_id, "message": "لا دروس كافية"}

        successful = [l for l in lessons if l.get("success")]
        failed = [l for l in lessons if not l.get("success")]

        # تحليل الكلمات المتكررة في المهام الناجحة vs الفاشلة
        success_words = self._extract_keywords([l["task"] for l in successful])
        fail_words = self._extract_keywords([l["task"] for l in failed])

        # متوسط التقييم
        avg_rating = (
            sum(l.get("rating", 5) for l in lessons) / len(lessons)
            if lessons else 0
        )

        return {
            "agent_id": agent_id,
            "total_lessons": len(lessons),
            "success_count": len(successful),
            "fail_count": len(failed),
            "success_rate": round(len(successful) / len(lessons), 3) if lessons else 0,
            "avg_rating": round(avg_rating, 1),
            "success_patterns": success_words[:10],
            "fail_patterns": fail_words[:10],
            "recent_failures": [
                {"task": l["task"][:100], "timestamp": l["timestamp"]}
                for l in failed[-5:]
            ],
        }

    def _extract_keywords(self, texts: List[str]) -> List[str]:
        """استخراج الكلمات المتكررة"""
        word_count = {}
        stop_words = {"في", "من", "على", "إلى", "و", "أن", "ما", "هل",
                      "the", "is", "a", "an", "to", "of", "and", "in"}

        for text in texts:
            words = text.lower().split()
            for word in words:
                if len(word) > 2 and word not in stop_words:
                    word_count[word] = word_count.get(word, 0) + 1

        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words]

    # ── تحسين الـ Prompt ─────────────────────────────────────

    def suggest_improvement(self, agent_id: str, current_prompt: str) -> Optional[str]:
        """
        اقتراح تحسين لـ system prompt بناءً على الدروس
        يُرجع الـ prompt المُحسَّن أو None
        """
        patterns = self.analyze_patterns(agent_id)

        if patterns.get("total_lessons", 0) < 5:
            logger.info(f"[{agent_id}] Not enough lessons for optimization")
            return None

        if patterns.get("success_rate", 0) > 0.85:
            logger.info(f"[{agent_id}] Already performing well ({patterns['success_rate']:.0%})")
            return None

        # بناء رسالة التحسين
        improvement_prompt = f"""أنت خبير في تحسين system prompts لوكلاء الذكاء الاصطناعي.

## الوكيل الحالي: {agent_id}
## System Prompt الحالي:
{current_prompt[:2000]}

## تحليل الأداء:
- إجمالي المهام: {patterns['total_lessons']}
- معدل النجاح: {patterns['success_rate']:.0%}
- متوسط التقييم: {patterns['avg_rating']}/10

## أنماط الفشل:
{json.dumps(patterns.get('recent_failures', []), ensure_ascii=False, indent=2)}

## المطلوب:
حسّن الـ system prompt ليكون أكثر فعالية. أبقِ على:
1. نفس الهوية والتخصص
2. نفس الأسلوب (عربي/إنجليزي)
3. لا تحذف معلومات مهمة

أضف أو عدّل:
1. توجيهات أوضح للمهام التي فشل فيها
2. أمثلة إذا كانت مفيدة
3. قيود لتجنب الأخطاء المتكررة

أعد الـ prompt المُحسَّن فقط، بدون شرح."""

        try:
            response = self.llm.chat([
                {"role": "system", "content": "أنت خبير تحسين prompts. أعد النص المحسّن فقط."},
                {"role": "user", "content": improvement_prompt},
            ])
            improved = response.get("content", "")

            if len(improved) > 100:
                return improved
            return None

        except Exception as e:
            logger.error(f"Prompt improvement error for {agent_id}: {e}")
            return None

    def apply_improvement(self, agent_id: str, agent, new_prompt: str) -> bool:
        """
        تطبيق تحسين مع حفظ نسخة احتياطية
        يحتاج موافقة (ConstitutionalGuardrails)
        """
        # 1. حفظ النسخة الاحتياطية
        self._backup_prompt(agent_id, agent.system_prompt)

        # 2. تطبيق
        agent.system_prompt = new_prompt
        logger.info(f"[{agent_id}] Prompt updated ({len(new_prompt)} chars)")

        # 3. تحديث ملف JSON
        self._update_json_file(agent_id, new_prompt)

        return True

    def rollback_prompt(self, agent_id: str, agent) -> bool:
        """استعادة الـ prompt السابق"""
        backup = self._get_latest_backup(agent_id)
        if not backup:
            logger.warning(f"[{agent_id}] No backup found")
            return False

        agent.system_prompt = backup["prompt"]
        logger.info(f"[{agent_id}] Prompt rolled back to {backup['timestamp']}")
        return True

    def _backup_prompt(self, agent_id: str, prompt: str):
        """حفظ نسخة احتياطية"""
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(_BACKUPS_DIR, f"{agent_id}_{date_str}.json")
        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump({
                    "agent_id": agent_id,
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Backup error: {e}")

    def _get_latest_backup(self, agent_id: str) -> Optional[Dict]:
        """قراءة آخر نسخة احتياطية"""
        backup_dir = Path(_BACKUPS_DIR)
        backups = sorted(backup_dir.glob(f"{agent_id}_*.json"), reverse=True)
        if not backups:
            return None
        try:
            with open(backups[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _update_json_file(self, agent_id: str, new_prompt: str):
        """تحديث ملف JSON للوكيل"""
        agents_dir = os.path.join(os.path.dirname(__file__), "..", "agents")
        for cat_dir in os.listdir(agents_dir):
            cat_path = os.path.join(agents_dir, cat_dir)
            if not os.path.isdir(cat_path):
                continue
            for fname in os.listdir(cat_path):
                if fname.startswith(agent_id) and fname.endswith(".json"):
                    fpath = os.path.join(cat_path, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["system_prompt"] = new_prompt
                        with open(fpath, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Updated JSON: {fpath}")
                        return
                    except Exception as e:
                        logger.error(f"Update JSON error: {e}")

    # ── تحسين جماعي ──────────────────────────────────────────

    def optimize_weakest(self, router, count: int = 10) -> List[Dict]:
        """
        تحسين أضعف N وكيل
        يُستدعى أسبوعياً بواسطة Cloud Scheduler
        """
        from core.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor(router)
        report = monitor.generate_report()

        weakest = report.get("weakest_agents", [])[:count]
        results = []

        for agent_eval in weakest:
            agent_id = agent_eval["agent_id"]
            if agent_id not in router.agents:
                continue

            agent = router.agents[agent_id]
            improved = self.suggest_improvement(agent_id, agent.system_prompt)

            if improved:
                self.apply_improvement(agent_id, agent, improved)
                results.append({
                    "agent_id": agent_id,
                    "name": agent_eval["name"],
                    "old_score": agent_eval["score"],
                    "action": "prompt_updated",
                })
            else:
                results.append({
                    "agent_id": agent_id,
                    "name": agent_eval["name"],
                    "old_score": agent_eval["score"],
                    "action": "no_change",
                })

        logger.info(f"Optimized {len([r for r in results if r['action'] == 'prompt_updated'])} agents")
        return results


if __name__ == "__main__":
    optimizer = PromptOptimizer()
    print("Prompt Optimizer ready.")
    print("Use: optimizer.collect_lesson(agent_id, task, result, success)")
    print("     optimizer.suggest_improvement(agent_id, current_prompt)")
