"""
HierarchicalMemory — مستوحى من mem0 (50k stars)
مبني فوق Chroma الموجودة بالفعل في المشروع
نتيجة Loop 2: أعلى تأثير بأقل جهد (6.7 أولوية)

4 مستويات:
  L1 — WorkingMemory (dict في RAM): المحادثة الجارية
  L2 — EpisodicMemory (SQLite): كل مهمة وتقييمها
  L3 — SemanticMemory (Chroma): بحث دلالي
  L4 — CompressedMemory (ملف): ملخص أسبوعي مضغوط
"""
import os
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.hierarchical_memory")

_WORKSPACE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
)
_DB_PATH = os.path.join(_WORKSPACE, "episodic_memory.db")
_COMPRESSED_DIR = os.path.join(_WORKSPACE, "compressed")


# ────────────────────────────────────────────────────
# L1 — WorkingMemory
# ────────────────────────────────────────────────────
class _WorkingMemory:
    """RAM فقط — تُمسح بعد كل run()"""

    def __init__(self):
        self._data: Dict[str, Dict] = {}

    def set(self, agent_id: str, key: str, value):
        if agent_id not in self._data:
            self._data[agent_id] = {}
        self._data[agent_id][key] = value

    def get(self, agent_id: str, key: str, default=None):
        return self._data.get(agent_id, {}).get(key, default)

    def clear(self, agent_id: str):
        self._data.pop(agent_id, None)

    def get_all(self, agent_id: str) -> Dict:
        return dict(self._data.get(agent_id, {}))


# ────────────────────────────────────────────────────
# L2 — EpisodicMemory (SQLite)
# ────────────────────────────────────────────────────
class _EpisodicMemory:
    _lock = threading.Lock()

    def __init__(self):
        os.makedirs(_WORKSPACE, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id    TEXT    NOT NULL,
                    task_summary    TEXT,
                    result_summary  TEXT,
                    success     BOOLEAN,
                    rating      INTEGER DEFAULT 7,
                    model_used  TEXT,
                    tokens      INTEGER DEFAULT 0,
                    task_type   TEXT    DEFAULT 'general',
                    teacher_example BOOLEAN DEFAULT 0,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record(self, agent_id: str, task_summary: str, result_summary: str,
               success: bool, rating: int = 7, model_used: str = "",
               tokens: int = 0, task_type: str = "general",
               teacher_example: bool = False):
        with self._lock:
            with sqlite3.connect(_DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO episodes
                        (agent_id, task_summary, result_summary, success, rating,
                         model_used, tokens, task_type, teacher_example, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (agent_id, task_summary[:200], result_summary[:500],
                      success, rating, model_used, tokens, task_type,
                      teacher_example, datetime.now().isoformat()))
                conn.commit()

    def get_lessons(self, agent_id: str, limit: int = 3) -> str:
        """أهم الدروس الناجحة للوكيل"""
        with sqlite3.connect(_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT task_summary, result_summary, rating, created_at
                FROM episodes
                WHERE agent_id = ? AND success = 1
                ORDER BY rating DESC, created_at DESC
                LIMIT ?
            """, (agent_id, limit)).fetchall()

        if not rows:
            return ""

        lessons = []
        for row in rows:
            lessons.append(
                f"- المهمة: {row['task_summary']}\n"
                f"  النتيجة: {row['result_summary'][:150]}"
            )
        return "\n".join(lessons)

    def get_failures(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """آخر الإخفاقات للوكيل (للتطور الذاتي)"""
        with sqlite3.connect(_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT task_summary, result_summary, model_used, created_at
                FROM episodes
                WHERE agent_id = ? AND success = 0
                ORDER BY created_at DESC
                LIMIT ?
            """, (agent_id, limit)).fetchall()
        return [dict(row) for row in rows]

    def get_all_for_agent(self, agent_id: str) -> List[Dict]:
        """كل episodes للوكيل"""
        with sqlite3.connect(_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM episodes WHERE agent_id = ?
                ORDER BY created_at DESC
            """, (agent_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_teacher_examples(self, task_type: str, model: str, limit: int = 5) -> List[Dict]:
        """أمثلة teacher لنوع مهمة معين"""
        with sqlite3.connect(_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT task_summary, result_summary, rating
                FROM episodes
                WHERE task_type = ? AND teacher_example = 1 AND model_used = ?
                ORDER BY rating DESC, created_at DESC
                LIMIT ?
            """, (task_type, model, limit)).fetchall()
        return [dict(row) for row in rows]


# ────────────────────────────────────────────────────
# L3 — SemanticMemory (Chroma موجودة)
# ────────────────────────────────────────────────────
class _SemanticMemory:
    def store(self, agent_id: str, content: str, tags: List[str] = None):
        """حفظ في Chroma بـ namespace خاص بالوكيل"""
        try:
            from memory.chroma_memory import remember
            agent_tags = [agent_id] + (tags or [])
            remember(content, agent_id=agent_id, tags=agent_tags)
        except Exception as e:
            logger.warning(f"[L3] Chroma store error: {e}")

    def search(self, agent_id: str, query: str, k: int = 3) -> str:
        """بحث دلالي في ذاكرة الوكيل"""
        try:
            from memory.chroma_memory import recall
            results = recall(query, n_results=k, agent_id=agent_id)
            if "لا توجد ذكريات" in results or "خطأ" in results:
                return ""
            return results
        except Exception as e:
            logger.warning(f"[L3] Chroma search error: {e}")
            return ""


# ────────────────────────────────────────────────────
# L4 — CompressedMemory (ملف مضغوط)
# ────────────────────────────────────────────────────
class _CompressedMemory:
    def get_summary(self, agent_id: str) -> str:
        """اقرأ الملخص المضغوط للوكيل"""
        path = os.path.join(_COMPRESSED_DIR, f"{agent_id}_summary.md")
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"[L4] Read summary error: {e}")
            return ""

    def save_summary(self, agent_id: str, summary: str):
        """احفظ الملخص المضغوط"""
        os.makedirs(_COMPRESSED_DIR, exist_ok=True)
        path = os.path.join(_COMPRESSED_DIR, f"{agent_id}_summary.md")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(summary)
            logger.info(f"[L4] Compressed summary saved for {agent_id}")
        except Exception as e:
            logger.error(f"[L4] Save summary error: {e}")


# ────────────────────────────────────────────────────
# HierarchicalMemory — الواجهة الموحّدة
# ────────────────────────────────────────────────────
class HierarchicalMemory:
    """
    4 مستويات ذاكرة متكاملة:
    L1 (RAM) + L2 (SQLite) + L3 (Chroma) + L4 (ملف مضغوط)
    """

    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id
        self.L1 = _WorkingMemory()
        self.L2 = _EpisodicMemory()
        self.L3 = _SemanticMemory()
        self.L4 = _CompressedMemory()

    def inject_context(self, agent_id: str, task: str) -> str:
        """
        يُستدعى قبل كل run() — يجمع أفضل context من الذاكرة
        الناتج: نص منسّق يُحقن في system_prompt
        """
        context = ""

        # L2: الدروس السابقة
        lessons = self.L2.get_lessons(agent_id)
        if lessons:
            context += f"## دروسي السابقة:\n{lessons}\n\n"

        # L3: البحث الدلالي
        relevant = self.L3.search(agent_id, task, k=3)
        if relevant:
            context += f"## معرفتي المرتبطة:\n{relevant}\n\n"

        # L4: الملخص المضغوط
        summary = self.L4.get_summary(agent_id)
        if summary:
            context += f"## ملخص خبرتي:\n{summary}\n"

        return context[:2000]  # لا تتجاوز 2000 حرف

    def store(self, agent_id: str, task: str, result: str,
              success: bool, rating: int = 7, model_used: str = "",
              tokens: int = 0, task_type: str = "general"):
        """يُستدعى بعد كل run() — يحفظ في L2 و L3"""
        # L2: تسجيل عرضي
        self.L2.record(
            agent_id=agent_id,
            task_summary=task[:200],
            result_summary=result[:500],
            success=success,
            rating=rating,
            model_used=model_used,
            tokens=tokens,
            task_type=task_type,
        )

        # L3: حفظ دلالي إذا كانت النتيجة ذات قيمة
        if success and len(result) > 50:
            content = f"[{task_type}] مهمة: {task[:100]}\nنتيجة: {result[:400]}"
            self.L3.store(agent_id, content, tags=[task_type])

    def compress_weekly(self, agent_id: str):
        """يُشغَّل كل أحد الساعة 4 صباحاً — يلخص L2+L3 في 500 كلمة"""
        try:
            # اجمع episodes
            episodes = self.L2.get_all_for_agent(agent_id)
            if not episodes:
                return

            # بناء نص للتلخيص
            text_parts = [f"# ملخص خبرة {agent_id}\n"]
            successful = [e for e in episodes if e.get("success")]
            failed = [e for e in episodes if not e.get("success")]

            text_parts.append(f"## الإحصائيات: {len(successful)} نجاح، {len(failed)} فشل\n")

            text_parts.append("## أبرز الإنجازات:\n")
            for ep in successful[:5]:
                text_parts.append(f"- {ep.get('task_summary', '')[:100]}\n")

            text_parts.append("\n## الدروس المستفادة من الإخفاقات:\n")
            for ep in failed[:3]:
                text_parts.append(f"- {ep.get('task_summary', '')[:100]}\n")

            full_text = "".join(text_parts)

            # حاول استخدام gemini-flash للتلخيص
            try:
                from core.llm_client import LLMClient
                client = LLMClient("gemini-flash")
                response = client.chat([
                    {"role": "system", "content": "أنت خبير تلخيص. لخّص في 500 كلمة بالعربية."},
                    {"role": "user", "content": full_text[:3000]},
                ])
                summary = response.get("content", full_text[:2000])
            except Exception:
                summary = full_text[:2000]

            self.L4.save_summary(agent_id, summary)
            logger.info(f"[HM] Weekly compression done for {agent_id}")

        except Exception as e:
            logger.error(f"[HM] compress_weekly error for {agent_id}: {e}")

    def transfer(self, from_agent: str, to_agent: str, topic: str):
        """نقل معرفة بين وكيلين عبر L3"""
        try:
            # ابحث عن معرفة المصدر
            content = self.L3.search(from_agent, topic, k=5)
            if content:
                # احفظها باسم الوكيل الهدف
                self.L3.store(to_agent, content, tags=["transferred", topic])
                logger.info(f"[HM] Knowledge transferred: {from_agent} → {to_agent} (topic: {topic})")
        except Exception as e:
            logger.error(f"[HM] transfer error: {e}")
