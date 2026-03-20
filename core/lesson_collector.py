"""
Army81 - Lesson Collector
جمع الدروس المستفادة من كل مهمة
المرحلة 4: التطور الذاتي
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger("army81.lessons")


class LessonCollector:
    """
    يجمع ويحلل الدروس المستفادة من كل مهمة
    ويوفرها للوكلاء للتعلم المستمر

    أنواع الدروس:
    - success_pattern: نمط نجاح يُكرّر
    - failure_lesson: درس من فشل
    - tool_insight: اكتشاف عن أداة
    - collaboration: درس من تعاون بين وكلاء
    - model_insight: اكتشاف عن نموذج AI
    """

    LESSON_TYPES = [
        "success_pattern",
        "failure_lesson",
        "tool_insight",
        "collaboration",
        "model_insight",
        "general",
    ]

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "workspace", "lessons"
        )
        os.makedirs(self.data_dir, exist_ok=True)

        # الدروس في الذاكرة
        self._lessons: List[Dict] = []
        self._agent_lessons: Dict[str, List[Dict]] = defaultdict(list)
        self._topic_lessons: Dict[str, List[Dict]] = defaultdict(list)

        # إحصائيات
        self.stats = {
            "total_lessons": 0,
            "by_type": defaultdict(int),
            "by_agent": defaultdict(int),
            "started_at": datetime.now().isoformat(),
        }

        self._load_lessons()

    def collect(self, agent_id: str, task: str, result: str,
                success: bool, lesson_type: str = "",
                importance: int = 5, tags: List[str] = None) -> str:
        """
        جمع درس من مهمة منفذة
        يُستخرج الدرس تلقائياً إذا لم يُحدد النوع
        """
        # تحديد نوع الدرس تلقائياً
        if not lesson_type:
            lesson_type = self._classify_lesson(task, result, success)

        # استخراج الدرس
        lesson_text = self._extract_lesson(task, result, success, lesson_type)

        lesson = {
            "id": f"L{len(self._lessons)+1:05d}",
            "agent_id": agent_id,
            "task_preview": task[:200],
            "result_preview": result[:200],
            "success": success,
            "lesson_type": lesson_type,
            "lesson": lesson_text,
            "importance": importance,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
            "applied_count": 0,
        }

        self._lessons.append(lesson)
        self._agent_lessons[agent_id].append(lesson)

        # تصنيف حسب الموضوع
        for tag in (tags or []):
            self._topic_lessons[tag].append(lesson)

        # تحديث الإحصائيات
        self.stats["total_lessons"] += 1
        self.stats["by_type"][lesson_type] += 1
        self.stats["by_agent"][agent_id] += 1

        # حفظ دوري
        if len(self._lessons) % 10 == 0:
            self._save_lessons()

        return lesson["id"]

    def get_lessons_for_agent(self, agent_id: str, limit: int = 10,
                              lesson_type: str = "") -> List[Dict]:
        """استرجاع دروس مفيدة لوكيل"""
        # دروس الوكيل نفسه
        own = self._agent_lessons.get(agent_id, [])

        # دروس عامة مهمة
        important = [l for l in self._lessons if l["importance"] >= 7]

        combined = own + important
        if lesson_type:
            combined = [l for l in combined if l["lesson_type"] == lesson_type]

        # ترتيب: الأهم أولاً، ثم الأحدث
        combined.sort(key=lambda x: (-x["importance"], x["timestamp"]), reverse=False)

        # إزالة التكرار
        seen = set()
        unique = []
        for l in combined:
            if l["id"] not in seen:
                seen.add(l["id"])
                unique.append(l)

        return unique[:limit]

    def get_lessons_for_task(self, task: str, limit: int = 5) -> List[Dict]:
        """استرجاع دروس مرتبطة بنوع المهمة"""
        task_lower = task.lower()

        scored = []
        for lesson in self._lessons:
            score = 0
            # تطابق الكلمات
            lesson_words = set(lesson["task_preview"].lower().split())
            task_words = set(task_lower.split())
            common = lesson_words & task_words
            score += len(common) * 2

            # مكافأة الأهمية
            score += lesson["importance"]

            # مكافأة الدروس الناجحة
            if lesson["success"]:
                score += 3

            if score > 2:
                scored.append((score, lesson))

        scored.sort(key=lambda x: -x[0])
        return [l for _, l in scored[:limit]]

    def inject_lessons_context(self, agent_id: str, task: str,
                                max_lessons: int = 3) -> str:
        """
        توليد سياق دروس لحقنه في system prompt
        يُستخدم قبل تنفيذ مهمة
        """
        # دروس مرتبطة بالمهمة
        task_lessons = self.get_lessons_for_task(task, limit=max_lessons)

        # دروس الوكيل
        agent_lessons = self.get_lessons_for_agent(agent_id, limit=2)

        all_lessons = task_lessons + agent_lessons
        if not all_lessons:
            return ""

        # إزالة التكرار
        seen = set()
        unique = []
        for l in all_lessons:
            if l["id"] not in seen:
                seen.add(l["id"])
                unique.append(l)

        lines = ["## دروس مستفادة من مهام سابقة:"]
        for l in unique[:max_lessons]:
            icon = "+" if l["success"] else "-"
            lines.append(f"{icon} {l['lesson']}")

        return "\n".join(lines)

    def get_summary(self) -> Dict:
        """ملخص النظام"""
        return {
            "total_lessons": self.stats["total_lessons"],
            "by_type": dict(self.stats["by_type"]),
            "by_agent": dict(self.stats["by_agent"]),
            "recent_lessons": self._lessons[-5:] if self._lessons else [],
            "most_important": sorted(
                self._lessons, key=lambda x: -x["importance"]
            )[:5] if self._lessons else [],
        }

    def get_all_lessons(self, limit: int = 50, lesson_type: str = "") -> List[Dict]:
        """كل الدروس"""
        lessons = self._lessons
        if lesson_type:
            lessons = [l for l in lessons if l["lesson_type"] == lesson_type]
        return lessons[-limit:]

    # ── Private Methods ──────────────────────────────────────────

    def _classify_lesson(self, task: str, result: str, success: bool) -> str:
        """تصنيف نوع الدرس تلقائياً"""
        task_lower = task.lower()
        result_lower = result.lower()

        if not success:
            return "failure_lesson"

        if any(w in task_lower for w in ["أداة", "tool", "use_tool"]):
            return "tool_insight"

        if any(w in task_lower for w in ["تعاون", "تفويض", "delegate", "chain"]):
            return "collaboration"

        if any(w in result_lower for w in ["نموذج", "model", "gemini", "claude"]):
            return "model_insight"

        return "success_pattern"

    def _extract_lesson(self, task: str, result: str, success: bool,
                        lesson_type: str) -> str:
        """استخراج نص الدرس"""
        if lesson_type == "failure_lesson":
            # استخراج سبب الفشل
            if "خطأ" in result:
                error_part = result[result.index("خطأ"):result.index("خطأ")+100]
                return f"فشل في مهمة '{task[:50]}': {error_part}"
            return f"فشل في مهمة '{task[:50]}': تحقق من الـ prompt والأدوات"

        if lesson_type == "tool_insight":
            return f"استخدام الأدوات في '{task[:50]}' نجح — تأكد من وجود المفاتيح"

        if lesson_type == "collaboration":
            return f"التعاون في '{task[:50]}' كان فعالاً — استمر بهذا النمط"

        if lesson_type == "success_pattern":
            # استخراج نمط النجاح
            result_len = len(result)
            if result_len > 500:
                return f"الإجابات التفصيلية نجحت في '{task[:50]}'"
            return f"المهمة '{task[:50]}' نُفذت بنجاح — نمط يُكرّر"

        return f"درس عام من '{task[:50]}'"

    def _save_lessons(self) -> None:
        """حفظ الدروس على القرص"""
        filepath = os.path.join(self.data_dir, "lessons.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "lessons": self._lessons,
                    "stats": {
                        "total_lessons": self.stats["total_lessons"],
                        "by_type": dict(self.stats["by_type"]),
                        "by_agent": dict(self.stats["by_agent"]),
                        "started_at": self.stats["started_at"],
                    },
                    "saved_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save lessons error: {e}")

    def _load_lessons(self) -> None:
        """تحميل الدروس المحفوظة"""
        filepath = os.path.join(self.data_dir, "lessons.json")
        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._lessons = data.get("lessons", [])
            stats = data.get("stats", {})
            self.stats["total_lessons"] = stats.get("total_lessons", len(self._lessons))
            self.stats["by_type"] = defaultdict(int, stats.get("by_type", {}))
            self.stats["by_agent"] = defaultdict(int, stats.get("by_agent", {}))

            # إعادة بناء الفهارس
            for lesson in self._lessons:
                agent_id = lesson.get("agent_id", "")
                if agent_id:
                    self._agent_lessons[agent_id].append(lesson)
                for tag in lesson.get("tags", []):
                    self._topic_lessons[tag].append(lesson)

            logger.info(f"Loaded {len(self._lessons)} lessons")
        except Exception as e:
            logger.error(f"Load lessons error: {e}")


# ── Singleton ──────────────────────────────────────────────────
_instance = None


def get_lesson_collector() -> LessonCollector:
    """الحصول على instance واحد"""
    global _instance
    if _instance is None:
        _instance = LessonCollector()
    return _instance
