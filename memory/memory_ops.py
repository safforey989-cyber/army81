"""
Army81 Memory - Memory Operations
حفظ واسترجاع المعلومات من الذاكرة الدائمة
يستخدم ملفات JSON محلية كـ fallback عند غياب Firestore
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("army81.memory")

# مسار الذاكرة المحلية
_MEMORY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace", "memory")
)


def _ensure_memory_dir():
    os.makedirs(_MEMORY_DIR, exist_ok=True)


def _memory_file(key: str) -> str:
    # تنظيف المفتاح ليكون اسم ملف آمن
    safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
    return os.path.join(_MEMORY_DIR, f"{safe_key}.json")


def save_memory(key: str, value: str, agent_id: str = "system") -> str:
    """حفظ معلومة في الذاكرة"""
    try:
        _ensure_memory_dir()

        # حاول Firestore أولاً
        firestore_result = _try_firestore_save(key, value, agent_id)
        if firestore_result:
            return firestore_result

        # fallback: ملف محلي
        data = {
            "key": key,
            "value": value,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        }

        with open(_memory_file(key), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Memory saved: {key} by {agent_id}")
        return f"تم الحفظ: {key}"

    except Exception as e:
        logger.error(f"save_memory error: {e}")
        return f"خطأ في الحفظ: {e}"


def get_memory(query: str) -> str:
    """
    استرجاع معلومة من الذاكرة
    query: المفتاح المحدد أو جزء منه للبحث
    """
    try:
        _ensure_memory_dir()

        # حاول Firestore أولاً
        firestore_result = _try_firestore_get(query)
        if firestore_result:
            return firestore_result

        # fallback: بحث محلي
        memory_path = Path(_MEMORY_DIR)
        if not memory_path.exists():
            return f"لا توجد ذاكرة محفوظة بعد"

        # بحث مباشر بالمفتاح
        exact_file = _memory_file(query)
        if os.path.exists(exact_file):
            with open(exact_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return f"**{data['key']}** (محفوظ بواسطة {data['agent_id']} في {data['timestamp'][:10]}):\n{data['value']}"

        # بحث بالمحتوى
        results = []
        for file in memory_path.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if query.lower() in data["key"].lower() or query.lower() in str(data["value"]).lower():
                    results.append(
                        f"**{data['key']}**: {str(data['value'])[:100]}..."
                    )
            except Exception:
                continue

        if results:
            return f"نتائج البحث عن '{query}':\n\n" + "\n\n".join(results[:5])

        return f"لم تُوجد ذاكرة تتعلق بـ: {query}"

    except Exception as e:
        logger.error(f"get_memory error: {e}")
        return f"خطأ في الاسترجاع: {e}"


def _try_firestore_save(key: str, value: str, agent_id: str) -> str:
    """محاولة الحفظ في Firestore (إذا كان متاحاً)"""
    project_id = os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        return ""

    try:
        from google.cloud import firestore
        db = firestore.Client(project=project_id)
        db.collection("army81_memory").document(key).set({
            "value": value,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        })
        return f"تم الحفظ في Firestore: {key}"
    except ImportError:
        return ""
    except Exception as e:
        logger.warning(f"Firestore save failed, using local: {e}")
        return ""


def _try_firestore_get(query: str) -> str:
    """محاولة الاسترجاع من Firestore"""
    project_id = os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        return ""

    try:
        from google.cloud import firestore
        db = firestore.Client(project=project_id)
        doc = db.collection("army81_memory").document(query).get()
        if doc.exists:
            data = doc.to_dict()
            return f"**{query}** (من Firestore):\n{data.get('value', '')}"
        return ""
    except ImportError:
        return ""
    except Exception as e:
        logger.warning(f"Firestore get failed, using local: {e}")
        return ""


def list_memories(agent_id: str = None) -> str:
    """عرض قائمة الذكريات المحفوظة"""
    try:
        _ensure_memory_dir()
        memory_path = Path(_MEMORY_DIR)
        files = list(memory_path.glob("*.json"))

        if not files:
            return "لا توجد ذاكرة محفوظة"

        results = []
        for file in sorted(files)[:20]:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if agent_id and data.get("agent_id") != agent_id:
                    continue
                results.append(f"- **{data['key']}** ({data['timestamp'][:10]})")
            except Exception:
                continue

        return f"الذاكرة المحفوظة ({len(results)} عنصر):\n" + "\n".join(results)

    except Exception as e:
        return f"خطأ: {e}"
