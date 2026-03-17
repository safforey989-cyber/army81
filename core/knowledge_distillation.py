"""
KnowledgeDistillation — DeepSeek approach
Flash يتعلم من Pro → نفس الأداء بتكلفة أقل 10x
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("army81.knowledge_distillation")


class KnowledgeDistillation:
    """
    تقطير المعرفة: النموذج الكبير يعلّم النموذج الصغير
    Teacher: gemini-pro / claude-sonnet
    Student: gemini-flash / claude-haiku
    """

    TEACHER_STUDENT = [
        ("gemini-pro",    "gemini-flash"),
        ("claude-sonnet", "claude-haiku"),
    ]

    # خريطة alias → model_name (للمطابقة مع EpisodicMemory)
    _ALIAS_TO_MODEL = {
        "gemini-pro":     "gemini-1.5-pro",
        "gemini-flash":   "gemini-2.0-flash",
        "claude-sonnet":  "claude-sonnet-4-6",
        "claude-haiku":   "claude-haiku-4-5-20251001",
    }

    def record_teacher_solution(self, task_type: str, task: str,
                                 solution: str, model: str):
        """
        احفظ حل teacher في EpisodicMemory بـ tag teacher_example=True
        يُستدعى عند استخدام pro/sonnet
        """
        try:
            from memory.hierarchical_memory import _EpisodicMemory
            em = _EpisodicMemory()
            em.record(
                agent_id=f"teacher_{model}",
                task_summary=task[:200],
                result_summary=solution[:500],
                success=True,
                rating=9,
                model_used=model,
                tokens=0,
                task_type=task_type,
                teacher_example=True,
            )
            logger.info(f"[Distillation] Teacher solution recorded: {model} → {task_type}")
        except Exception as e:
            logger.warning(f"[Distillation] record_teacher_solution error: {e}")

    def get_examples_for_student(self, task_type: str, student_model: str,
                                  k: int = 5) -> str:
        """
        اجلب أفضل k حلول من teacher لنفس النوع
        أعطها للـ student في context قبل المهمة
        """
        try:
            # حدد teacher المناسب للـ student
            teacher_model = self._get_teacher_for(student_model)
            if not teacher_model:
                return ""

            from memory.hierarchical_memory import _EpisodicMemory
            em = _EpisodicMemory()
            examples = em.get_teacher_examples(task_type, teacher_model, limit=k)

            if not examples:
                return ""

            lines = [f"## أمثلة حلول خبيرة ({task_type}):\n"]
            for i, ex in enumerate(examples, 1):
                lines.append(
                    f"### مثال {i}:\n"
                    f"**المهمة:** {ex.get('task_summary', '')}\n"
                    f"**الحل:** {ex.get('result_summary', '')[:300]}\n"
                )

            return "\n".join(lines)

        except Exception as e:
            logger.warning(f"[Distillation] get_examples_for_student error: {e}")
            return ""

    def measure_gap(self, agent_id: str, task_type: str) -> float:
        """
        هل Flash يحتاج Pro لهذا النوع؟
        إذا gap < 10% → استخدم Flash دائماً (وفّر المال)
        يعيد gap كنسبة مئوية (0-100)
        """
        try:
            from memory.hierarchical_memory import _EpisodicMemory
            em = _EpisodicMemory()

            # جلب تقييمات Flash
            import sqlite3
            from memory.hierarchical_memory import _DB_PATH
            with sqlite3.connect(_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                flash_rows = conn.execute("""
                    SELECT AVG(rating) as avg_rating FROM episodes
                    WHERE agent_id = ? AND task_type = ? AND success = 1
                    AND model_used LIKE '%flash%'
                    LIMIT 10
                """, (agent_id, task_type)).fetchone()

                pro_rows = conn.execute("""
                    SELECT AVG(rating) as avg_rating FROM episodes
                    WHERE task_type = ? AND success = 1
                    AND (model_used LIKE '%pro%' OR model_used LIKE '%sonnet%')
                    AND teacher_example = 1
                    LIMIT 10
                """, (task_type,)).fetchone()

            flash_avg = flash_rows["avg_rating"] if flash_rows["avg_rating"] else 7.0
            pro_avg = pro_rows["avg_rating"] if pro_rows["avg_rating"] else 9.0

            gap = ((pro_avg - flash_avg) / pro_avg) * 100 if pro_avg > 0 else 0
            logger.info(
                f"[Distillation] Gap for {agent_id}/{task_type}: "
                f"flash={flash_avg:.1f}, pro={pro_avg:.1f}, gap={gap:.1f}%"
            )
            return round(gap, 1)

        except Exception as e:
            logger.warning(f"[Distillation] measure_gap error: {e}")
            return 0.0

    def daily_distillation(self):
        """
        الساعة 2 صباحاً: لكل حل teacher → سجّل مثالاً للـ student
        يمر على كل episodes ذات teacher_example=False ويسجّلها
        """
        try:
            from memory.hierarchical_memory import _DB_PATH
            import sqlite3

            with sqlite3.connect(_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                # خذ آخر 50 حل ناجح لم يُسجّل بعد كـ teacher examples
                rows = conn.execute("""
                    SELECT agent_id, task_summary, result_summary,
                           model_used, task_type, rating
                    FROM episodes
                    WHERE success = 1 AND teacher_example = 0
                    AND (model_used LIKE '%pro%' OR model_used LIKE '%sonnet%')
                    ORDER BY created_at DESC
                    LIMIT 50
                """).fetchall()

            recorded = 0
            for row in rows:
                self.record_teacher_solution(
                    task_type=row["task_type"],
                    task=row["task_summary"],
                    solution=row["result_summary"],
                    model=row["model_used"],
                )
                recorded += 1

            logger.info(f"[Distillation] Daily distillation: {recorded} examples recorded")
            return {"recorded": recorded}

        except Exception as e:
            logger.error(f"[Distillation] daily_distillation error: {e}")
            return {"recorded": 0, "error": str(e)}

    def _get_teacher_for(self, student_model: str) -> Optional[str]:
        """ابحث عن teacher النموذج المعطى"""
        # normalize
        student_norm = student_model.lower()
        for teacher, student in self.TEACHER_STUDENT:
            if student in student_norm or student_norm in student:
                return self._ALIAS_TO_MODEL.get(teacher, teacher)
        # fallback
        if "flash" in student_norm or "haiku" in student_norm:
            return self._ALIAS_TO_MODEL.get("gemini-pro", "gemini-1.5-pro")
        return None
