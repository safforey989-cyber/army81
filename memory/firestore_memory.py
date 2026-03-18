"""
Army81 Memory - Firestore Integration
ذاكرة دائمة على Google Cloud Firestore
تعمل كبديل/مكمّل للذاكرة المحلية
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.memory.firestore")

# ── Firestore Client (lazy loading) ──────────────────────────
_firestore_client = None


def _get_client():
    """الحصول على Firestore client (lazy)"""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    project_id = os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        return None

    try:
        from google.cloud import firestore
        _firestore_client = firestore.Client(project=project_id)
        logger.info(f"Firestore connected: project={project_id}")
        return _firestore_client
    except ImportError:
        logger.warning("google-cloud-firestore not installed")
        return None
    except Exception as e:
        logger.error(f"Firestore connection error: {e}")
        return None


# ── Agent Memory Collection ──────────────────────────────────

def save_agent_memory(agent_id: str, key: str, value: str,
                      metadata: Dict = None) -> bool:
    """حفظ ذاكرة وكيل في Firestore"""
    db = _get_client()
    if not db:
        return False

    try:
        doc_ref = db.collection("army81_agent_memory").document(f"{agent_id}_{key}")
        doc_ref.set({
            "agent_id": agent_id,
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "updated_at": datetime.now().isoformat(),
        })
        return True
    except Exception as e:
        logger.error(f"Firestore save_agent_memory error: {e}")
        return False


def get_agent_memory(agent_id: str, key: str) -> Optional[str]:
    """استرجاع ذاكرة وكيل من Firestore"""
    db = _get_client()
    if not db:
        return None

    try:
        doc = db.collection("army81_agent_memory").document(f"{agent_id}_{key}").get()
        if doc.exists:
            return doc.to_dict().get("value")
        return None
    except Exception as e:
        logger.error(f"Firestore get_agent_memory error: {e}")
        return None


def list_agent_memories(agent_id: str, limit: int = 50) -> List[Dict]:
    """عرض كل ذكريات وكيل"""
    db = _get_client()
    if not db:
        return []

    try:
        docs = (db.collection("army81_agent_memory")
                .where("agent_id", "==", agent_id)
                .order_by("updated_at", direction="DESCENDING")
                .limit(limit)
                .stream())
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Firestore list error: {e}")
        return []


# ── Task History Collection ──────────────────────────────────

def save_task_result(agent_id: str, task: str, result: str,
                     status: str, model_used: str,
                     elapsed: float, tokens: int) -> bool:
    """حفظ نتيجة مهمة في Firestore"""
    db = _get_client()
    if not db:
        return False

    try:
        db.collection("army81_tasks").add({
            "agent_id": agent_id,
            "task": task[:500],
            "result": result[:2000],
            "status": status,
            "model_used": model_used,
            "elapsed_seconds": elapsed,
            "tokens_used": tokens,
            "created_at": datetime.now().isoformat(),
        })
        return True
    except Exception as e:
        logger.error(f"Firestore save_task error: {e}")
        return False


def get_task_history(agent_id: str = None, limit: int = 20) -> List[Dict]:
    """عرض تاريخ المهام"""
    db = _get_client()
    if not db:
        return []

    try:
        query = db.collection("army81_tasks")
        if agent_id:
            query = query.where("agent_id", "==", agent_id)
        docs = (query.order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream())
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Firestore task_history error: {e}")
        return []


# ── System Config Collection ─────────────────────────────────

def save_config(key: str, value: Dict) -> bool:
    """حفظ إعداد نظام"""
    db = _get_client()
    if not db:
        return False

    try:
        db.collection("army81_config").document(key).set({
            **value,
            "updated_at": datetime.now().isoformat(),
        })
        return True
    except Exception as e:
        logger.error(f"Firestore save_config error: {e}")
        return False


def get_config(key: str) -> Optional[Dict]:
    """استرجاع إعداد نظام"""
    db = _get_client()
    if not db:
        return None

    try:
        doc = db.collection("army81_config").document(key).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        logger.error(f"Firestore get_config error: {e}")
        return None


# ── Collective Knowledge ─────────────────────────────────────

def save_collective_insight(agent_id: str, topic: str,
                            content: str, confidence: float = 0.7) -> bool:
    """حفظ معرفة جماعية"""
    db = _get_client()
    if not db:
        return False

    try:
        db.collection("army81_collective").add({
            "agent_id": agent_id,
            "topic": topic,
            "content": content[:1000],
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
        })
        return True
    except Exception as e:
        logger.error(f"Firestore collective error: {e}")
        return False


def query_collective(topic: str, limit: int = 10) -> List[Dict]:
    """البحث في المعرفة الجماعية"""
    db = _get_client()
    if not db:
        return []

    try:
        docs = (db.collection("army81_collective")
                .where("topic", "==", topic)
                .order_by("confidence", direction="DESCENDING")
                .limit(limit)
                .stream())
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.error(f"Firestore query_collective error: {e}")
        return []


# ── Health Check ─────────────────────────────────────────────

def check_firestore_health() -> Dict:
    """فحص اتصال Firestore"""
    db = _get_client()
    if not db:
        return {
            "connected": False,
            "reason": "No GCP_PROJECT_ID or google-cloud-firestore not installed",
        }

    try:
        # محاولة قراءة بسيطة
        db.collection("army81_config").document("_health").get()
        return {"connected": True, "project": os.getenv("GCP_PROJECT_ID", "")}
    except Exception as e:
        return {"connected": False, "reason": str(e)}


if __name__ == "__main__":
    health = check_firestore_health()
    print(f"Firestore health: {health}")
