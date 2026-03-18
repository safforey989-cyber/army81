"""
Army81 — Consciousness Node (عقدة الوعي)
يُحقن ديناميكياً قبل كل مهمة — يجعل الوكيل يدرك:
  1. من هو في الشبكة
  2. ما حالة النظام الآن (حقيقي وليس ثابت)
  3. من نفّذ مهام مشابهة مؤخراً
  4. ما المعرفة الجماعية المتاحة
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger("army81.consciousness")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConsciousnessNode:
    """
    عقدة الوعي — تُولّد سياقاً ديناميكياً لكل وكيل قبل كل مهمة
    """

    def __init__(self):
        self._agents_cache = None
        self._last_cache_time = None

    def generate(self, agent_id: str, task: str, router=None) -> str:
        """
        يولّد نص الوعي الديناميكي لوكيل محدد
        يُحقن في بداية system_prompt قبل كل مهمة
        """
        parts = []

        # 1. الهوية في الشبكة
        parts.append(self._identity_block(agent_id, router))

        # 2. حالة النظام الحية
        parts.append(self._system_state(router))

        # 3. تجارب مشابهة سابقة
        parts.append(self._relevant_history(agent_id, task))

        # 4. معرفة جماعية متاحة
        parts.append(self._collective_knowledge(agent_id, task))

        # 5. توصيات التعاون
        parts.append(self._collaboration_hints(agent_id, task, router))

        # دمج + تقليم
        consciousness = "\n".join(p for p in parts if p)
        # لا تتجاوز 1500 حرف لتوفير مساحة context
        if len(consciousness) > 1500:
            consciousness = consciousness[:1500] + "\n..."

        return consciousness

    def _identity_block(self, agent_id: str, router=None) -> str:
        """هوية الوكيل في الشبكة"""
        info = ""
        if router and agent_id in router.agents:
            agent = router.agents[agent_id]
            total = len(router.agents)
            done = agent.stats.get("tasks_done", 0)
            info = (
                f"[أنت {agent_id} — {agent.name_ar} | "
                f"نموذج: {agent.model_alias} | "
                f"مهام منجزة: {done} | "
                f"جزء من شبكة {total} وكيل]"
            )
        else:
            info = f"[أنت {agent_id} — جزء من شبكة Army81 (81 وكيل)]"
        return info

    def _system_state(self, router=None) -> str:
        """حالة النظام الحية"""
        if not router:
            return ""

        total = len(router.agents)
        active = sum(1 for a in router.agents.values()
                     if a.stats.get("tasks_done", 0) > 0)
        total_tasks = sum(a.stats.get("tasks_done", 0)
                         for a in router.agents.values())

        now = datetime.now().strftime("%H:%M")
        return f"[النظام: {active}/{total} نشط | {total_tasks} مهمة اليوم | {now}]"

    def _relevant_history(self, agent_id: str, task: str) -> str:
        """تجارب مشابهة من الذاكرة"""
        try:
            from memory.hierarchical_memory import HierarchicalMemory
            hm = HierarchicalMemory(agent_id)
            lessons = hm.L2.get_lessons(agent_id, limit=2)
            if lessons:
                return f"[دروس سابقة: {lessons[:300]}]"
        except Exception:
            pass
        return ""

    def _collective_knowledge(self, agent_id: str, task: str) -> str:
        """معرفة جماعية من وكلاء آخرين"""
        try:
            from memory.collective_memory import CollectiveMemory
            cm = CollectiveMemory()
            result = cm.query(task[:50], agent_id, k=2)
            if result and len(result) > 10:
                return f"[معرفة جماعية: {result[:300]}]"
        except Exception:
            pass
        return ""

    def _collaboration_hints(self, agent_id: str, task: str,
                              router=None) -> str:
        """توصيات تعاون ذكية بناءً على المهمة"""
        if not router:
            return ""

        task_lower = task.lower()
        hints = []

        # خريطة: كلمة مفتاحية → وكيل مقترح
        suggestions = {
            "طب": ("A07", "البحث الطبي"),
            "medical": ("A07", "البحث الطبي"),
            "مال": ("A08", "التحليل المالي"),
            "سوق": ("A08", "التحليل المالي"),
            "finance": ("A08", "التحليل المالي"),
            "كود": ("A05", "البرمجة"),
            "code": ("A05", "البرمجة"),
            "قانون": ("A13", "القانون"),
            "legal": ("A13", "القانون"),
            "أمن": ("A09", "الأمن السيبراني"),
            "security": ("A09", "الأمن السيبراني"),
            "استراتيج": ("A01", "القيادة الاستراتيجية"),
            "strategy": ("A01", "القيادة الاستراتيجية"),
            "أزم": ("A29", "إدارة الأزمات"),
            "crisis": ("A29", "إدارة الأزمات"),
            "ترجم": ("A11", "الترجمة"),
            "translate": ("A11", "الترجمة"),
            "بيانات": ("A06", "تحليل البيانات"),
            "data": ("A06", "تحليل البيانات"),
            "نفس": ("A15", "علم النفس"),
            "بحث": ("A02", "البحث العلمي"),
            "research": ("A02", "البحث العلمي"),
        }

        for keyword, (aid, name) in suggestions.items():
            if keyword in task_lower and aid != agent_id:
                hints.append(f"{aid}({name})")

        if hints:
            return f"[وكلاء مقترحون للتعاون: {', '.join(hints[:3])}]"
        return ""


# ═══ Singleton ═══
_node: Optional[ConsciousnessNode] = None

def get_consciousness() -> ConsciousnessNode:
    global _node
    if _node is None:
        _node = ConsciousnessNode()
    return _node
