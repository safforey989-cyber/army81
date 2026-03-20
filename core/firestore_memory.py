"""
Army81 - Firestore Persistent Memory
ذاكرة دائمة على Google Firestore
المرحلة 3: البنية التحتية السحابية
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("army81.firestore_memory")

# Firestore client (lazy)
_firestore_client = None
_FIRESTORE_AVAILABLE = False


def _get_firestore():
    """تحميل Firestore client عند الحاجة فقط"""
    global _firestore_client, _FIRESTORE_AVAILABLE

    if _firestore_client is not None:
        return _firestore_client

    project_id = os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        logger.info("GCP_PROJECT_ID not set — Firestore disabled, using local fallback")
        return None

    try:
        from google.cloud import firestore
        _firestore_client = firestore.Client(project=project_id)
        _FIRESTORE_AVAILABLE = True
        logger.info(f"Firestore connected to project: {project_id}")
        return _firestore_client
    except ImportError:
        logger.warning("google-cloud-firestore not installed. pip install google-cloud-firestore")
        return None
    except Exception as e:
        logger.error(f"Firestore connection failed: {e}")
        return None


class FirestoreMemory:
    """
    ذاكرة دائمة على Firestore مع fallback محلي
    Collections:
    - army81_episodes: سجل المهام (agent_id, task, result, timestamp)
    - army81_knowledge: المعرفة المشتركة (topic, content, source)
    - army81_stats: إحصائيات الوكلاء
    - army81_lessons: الدروس المستفادة
    """

    COLLECTION_EPISODES = "army81_episodes"
    COLLECTION_KNOWLEDGE = "army81_knowledge"
    COLLECTION_STATS = "army81_stats"
    COLLECTION_LESSONS = "army81_lessons"

    def __init__(self):
        self.db = _get_firestore()
        self._local_fallback_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "workspace", "firestore_local"
        )
        if not self.db:
            os.makedirs(self._local_fallback_dir, exist_ok=True)

    @property
    def is_cloud(self) -> bool:
        return self.db is not None

    # ── Episodes (سجل المهام) ──────────────────────────────────

    def store_episode(self, agent_id: str, task: str, result: str,
                      success: bool = True, rating: int = 5,
                      model: str = "", tokens: int = 0,
                      task_type: str = "general") -> str:
        """حفظ نتيجة مهمة"""
        doc = {
            "agent_id": agent_id,
            "task": task[:500],
            "result": result[:2000],
            "success": success,
            "rating": rating,
            "model": model,
            "tokens": tokens,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
        }

        if self.db:
            try:
                ref = self.db.collection(self.COLLECTION_EPISODES).add(doc)
                return f"stored:{ref[1].id}"
            except Exception as e:
                logger.error(f"Firestore store_episode error: {e}")

        # Local fallback
        return self._store_local(self.COLLECTION_EPISODES, doc)

    def get_agent_episodes(self, agent_id: str, limit: int = 20) -> List[Dict]:
        """استرجاع سجل مهام وكيل"""
        if self.db:
            try:
                docs = (self.db.collection(self.COLLECTION_EPISODES)
                        .where("agent_id", "==", agent_id)
                        .order_by("timestamp", direction="DESCENDING")
                        .limit(limit)
                        .stream())
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Firestore get_episodes error: {e}")

        return self._get_local(self.COLLECTION_EPISODES, agent_id=agent_id, limit=limit)

    def get_recent_episodes(self, limit: int = 50) -> List[Dict]:
        """آخر المهام المنفذة عبر النظام"""
        if self.db:
            try:
                docs = (self.db.collection(self.COLLECTION_EPISODES)
                        .order_by("timestamp", direction="DESCENDING")
                        .limit(limit)
                        .stream())
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Firestore get_recent error: {e}")

        return self._get_local(self.COLLECTION_EPISODES, limit=limit)

    # ── Knowledge (المعرفة المشتركة) ────────────────────────────

    def store_knowledge(self, topic: str, content: str, source: str = "",
                        agent_id: str = "") -> str:
        """حفظ معرفة مشتركة"""
        doc = {
            "topic": topic,
            "content": content[:3000],
            "source": source,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        }

        if self.db:
            try:
                ref = self.db.collection(self.COLLECTION_KNOWLEDGE).add(doc)
                return f"stored:{ref[1].id}"
            except Exception as e:
                logger.error(f"Firestore store_knowledge error: {e}")

        return self._store_local(self.COLLECTION_KNOWLEDGE, doc)

    def search_knowledge(self, topic: str, limit: int = 10) -> List[Dict]:
        """البحث في المعرفة المشتركة"""
        if self.db:
            try:
                docs = (self.db.collection(self.COLLECTION_KNOWLEDGE)
                        .where("topic", "==", topic)
                        .order_by("timestamp", direction="DESCENDING")
                        .limit(limit)
                        .stream())
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Firestore search_knowledge error: {e}")

        return self._get_local(self.COLLECTION_KNOWLEDGE, topic=topic, limit=limit)

    # ── Stats (إحصائيات الوكلاء) ──────────────────────────────

    def update_agent_stats(self, agent_id: str, stats: Dict) -> str:
        """تحديث إحصائيات وكيل"""
        doc = {
            "agent_id": agent_id,
            "stats": stats,
            "updated_at": datetime.now().isoformat(),
        }

        if self.db:
            try:
                self.db.collection(self.COLLECTION_STATS).document(agent_id).set(doc, merge=True)
                return f"updated:{agent_id}"
            except Exception as e:
                logger.error(f"Firestore update_stats error: {e}")

        return self._store_local(self.COLLECTION_STATS, doc)

    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        """استرجاع إحصائيات وكيل"""
        if self.db:
            try:
                doc = self.db.collection(self.COLLECTION_STATS).document(agent_id).get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as e:
                logger.error(f"Firestore get_stats error: {e}")

        results = self._get_local(self.COLLECTION_STATS, agent_id=agent_id, limit=1)
        return results[0] if results else None

    def get_all_stats(self) -> List[Dict]:
        """إحصائيات كل الوكلاء"""
        if self.db:
            try:
                docs = self.db.collection(self.COLLECTION_STATS).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Firestore get_all_stats error: {e}")

        return self._get_local(self.COLLECTION_STATS, limit=100)

    # ── Lessons (الدروس المستفادة) ─────────────────────────────

    def store_lesson(self, agent_id: str, task_type: str, lesson: str,
                     importance: int = 5) -> str:
        """حفظ درس مستفاد"""
        doc = {
            "agent_id": agent_id,
            "task_type": task_type,
            "lesson": lesson[:1000],
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
        }

        if self.db:
            try:
                ref = self.db.collection(self.COLLECTION_LESSONS).add(doc)
                return f"stored:{ref[1].id}"
            except Exception as e:
                logger.error(f"Firestore store_lesson error: {e}")

        return self._store_local(self.COLLECTION_LESSONS, doc)

    def get_lessons(self, agent_id: str = "", task_type: str = "",
                    limit: int = 20) -> List[Dict]:
        """استرجاع الدروس المستفادة"""
        if self.db:
            try:
                query = self.db.collection(self.COLLECTION_LESSONS)
                if agent_id:
                    query = query.where("agent_id", "==", agent_id)
                if task_type:
                    query = query.where("task_type", "==", task_type)
                docs = query.order_by("timestamp", direction="DESCENDING").limit(limit).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Firestore get_lessons error: {e}")

        return self._get_local(self.COLLECTION_LESSONS,
                               agent_id=agent_id if agent_id else None,
                               limit=limit)

    # ── Status ──────────────────────────────────────────────────

    def status(self) -> Dict:
        """حالة نظام الذاكرة"""
        return {
            "backend": "firestore" if self.is_cloud else "local_json",
            "project_id": os.getenv("GCP_PROJECT_ID", "not_set"),
            "available": self.is_cloud or True,
            "collections": [
                self.COLLECTION_EPISODES,
                self.COLLECTION_KNOWLEDGE,
                self.COLLECTION_STATS,
                self.COLLECTION_LESSONS,
            ],
        }

    # ── Local Fallback ──────────────────────────────────────────

    def _store_local(self, collection: str, doc: Dict) -> str:
        """حفظ محلي كـ JSON"""
        coll_dir = os.path.join(self._local_fallback_dir, collection)
        os.makedirs(coll_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        agent_id = doc.get("agent_id", "system")
        filename = f"{agent_id}_{timestamp}.json"
        filepath = os.path.join(coll_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

        return f"local:{filepath}"

    def _get_local(self, collection: str, agent_id: str = None,
                   topic: str = None, limit: int = 20) -> List[Dict]:
        """استرجاع من التخزين المحلي"""
        coll_dir = os.path.join(self._local_fallback_dir, collection)
        if not os.path.isdir(coll_dir):
            return []

        results = []
        files = sorted(os.listdir(coll_dir), reverse=True)

        for fname in files:
            if not fname.endswith(".json"):
                continue

            filepath = os.path.join(coll_dir, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)

                # فلترة
                if agent_id and doc.get("agent_id") != agent_id:
                    continue
                if topic and doc.get("topic") != topic:
                    continue

                results.append(doc)

                if len(results) >= limit:
                    break
            except Exception:
                continue

        return results


# ── Singleton ──────────────────────────────────────────────────
_instance = None


def get_firestore_memory() -> FirestoreMemory:
    """الحصول على instance واحد"""
    global _instance
    if _instance is None:
        _instance = FirestoreMemory()
    return _instance
