"""
Army81 - Smart Router
يستقبل المهام ويوجهها للوكيل الأنسب
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("army81.router")

# خريطة الكلمات المفتاحية → الفئات (عربي وإنجليزي)
ROUTING_MAP = {
    "cat1_science": [
        "طب", "دواء", "مرض", "جين", "دنا", "روبوت", "فضاء", "كمومي",
        "ليزر", "فوتون", "اتصالات", "نجم", "مجرة", "فيزياء", "كيمياء",
        "medical", "robot", "space", "quantum", "laser", "physics"
    ],
    "cat2_society": [
        "اقتصاد", "تاريخ", "قانون", "إعلام", "دعاية", "حرب", "سياسة",
        "عملة", "بلوكشين", "مناخ", "سكان", "هجرة", "ثقافة", "قبيلة",
        "economy", "history", "law", "war", "politics", "climate"
    ],
    "cat3_tools": [
        "ذكاء اصطناعي", "أخبار", "برمجة", "كود", "تشفير", "أمن",
        "إنذار", "ابتكار", "تضليل", "أزمة", "مستقبل",
        "ai", "news", "code", "security", "crisis", "future"
    ],
    "cat4_management": [
        "إدارة", "حوكمة", "مشروع", "تحول رقمي", "قرار", "أداء", "كارثة",
        "management", "project", "digital", "decision", "governance"
    ],
    "cat5_behavior": [
        "سلوك", "نفس", "مشاعر", "لغة جسد", "صوت", "وجه", "حشود",
        "behavior", "psychology", "emotion", "body language", "crowd"
    ],
    "cat6_leadership": [
        "استراتيجية", "رؤية", "تنسيق", "أولويات", "نزاع", "تقييم شامل",
        "strategy", "vision", "coordination", "priority", "evaluation"
    ],
}


class SmartRouter:
    """الموزّع الذكي للمهام"""

    def __init__(self):
        self.agents: Dict[str, object] = {}
        self.history: List[Dict] = []
        self.stats = {"total": 0, "by_category": {}, "by_agent": {}}

    def register(self, agent):
        """تسجيل وكيل"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered: {agent.agent_id} ({agent.name_ar})")

    def register_all(self, agents: List):
        for agent in agents:
            self.register(agent)
        logger.info(f"Total agents registered: {len(self.agents)}")

    def route(self, task: str, agent_id: str = None, category: str = None,
              context: Dict = None) -> Dict:
        """
        توجيه مهمة:
        1. وكيل محدد → مباشرة
        2. فئة محددة → أفضل وكيل فيها
        3. تلقائي → تحليل المهمة
        """
        start = time.time()
        context = context or {}

        # 1. وكيل محدد
        if agent_id:
            if agent_id in self.agents:
                result = self.agents[agent_id].run(task, context)
            else:
                return {"status": "error", "result": f"الوكيل {agent_id} غير موجود"}

        # 2. فئة محددة
        elif category:
            agent = self._best_in_category(category)
            if not agent:
                return {"status": "error", "result": f"لا وكلاء في الفئة {category}"}
            result = agent.run(task, context)

        # 3. توجيه تلقائي
        else:
            agent = self._auto_select(task)
            result = agent.run(task, context)

        # تسجيل
        self._log(task, result, time.time() - start)
        return result.to_dict() if hasattr(result, "to_dict") else result

    def pipeline(self, task: str, agent_ids: List[str], context: Dict = None) -> Dict:
        """
        تسلسل وكلاء: نتيجة كل وكيل تدخل للتالي
        """
        context = context or {}
        current = task
        results = []

        for aid in agent_ids:
            if aid not in self.agents:
                logger.warning(f"Pipeline: agent {aid} not found, skipping")
                continue

            r = self.agents[aid].run(current, context)
            results.append(r.to_dict() if hasattr(r, "to_dict") else r)

            if getattr(r, "status", "") == "error":
                return {"status": "pipeline_error", "failed_at": aid, "steps": results}

            result_text = getattr(r, "result", str(r))
            current = f"نتيجة {self.agents[aid].name_ar}:\n{result_text}\n\nالمهمة الأصلية: {task}"

        return {
            "status": "success",
            "steps": len(results),
            "final": results[-1] if results else None,
            "all_results": results,
        }

    def broadcast(self, task: str, category: str = None, context: Dict = None) -> List[Dict]:
        """إرسال مهمة لكل وكلاء فئة"""
        targets = list(self.agents.values())
        if category:
            targets = [a for a in targets if a.category == category]

        results = []
        for agent in targets:
            r = agent.run(task, context or {})
            results.append(r.to_dict() if hasattr(r, "to_dict") else r)

        return results

    def _auto_select(self, task: str):
        """اختيار الوكيل تلقائياً بناءً على محتوى المهمة"""
        task_lower = task.lower()

        # حدد الفئة بناءً على الكلمات المفتاحية
        scores = {cat: 0 for cat in ROUTING_MAP}
        for cat, keywords in ROUTING_MAP.items():
            for kw in keywords:
                if kw in task_lower:
                    scores[cat] += 1

        best_category = max(scores, key=scores.get)

        if scores[best_category] > 0:
            agent = self._best_in_category(best_category)
            if agent:
                logger.info(f"Auto-routed to {agent.agent_id} (category: {best_category})")
                return agent

        # افتراضي: أول وكيل متاح
        return list(self.agents.values())[0]

    def _best_in_category(self, category: str):
        """أفضل وكيل في فئة (الأقل انشغالاً)"""
        candidates = [a for a in self.agents.values() if a.category == category]
        if not candidates:
            return None
        # اختر الأقل مهاماً
        candidates.sort(key=lambda a: a.stats.get("tasks_done", 0))
        return candidates[0]

    def _log(self, task: str, result, elapsed: float):
        self.stats["total"] += 1
        agent_id = getattr(result, "agent_id", "unknown")
        self.stats["by_agent"][agent_id] = self.stats["by_agent"].get(agent_id, 0) + 1
        self.history.append({
            "ts": datetime.now().isoformat(),
            "task": task[:100],
            "agent": agent_id,
            "status": getattr(result, "status", "unknown"),
            "elapsed": round(elapsed, 2),
        })
        # احتفظ بآخر 1000 سجل
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

    def status(self) -> Dict:
        """حالة النظام الكاملة"""
        return {
            "agents_count": len(self.agents),
            "by_category": self._count_by_category(),
            "stats": self.stats,
            "agents": [a.info() for a in self.agents.values()],
        }

    def _count_by_category(self) -> Dict:
        counts = {}
        for a in self.agents.values():
            counts[a.category] = counts.get(a.category, 0) + 1
        return counts
