"""
Army81 Memory - Chroma Semantic Memory
ذاكرة دلالية باستخدام ChromaDB — تذكر المفاهيم لا فقط الكلمات
"""
import os
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("army81.memory.chroma")

# مسار قاعدة بيانات Chroma المحلية
_CHROMA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace", "chroma_db")
)

_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        import chromadb
        os.makedirs(_CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_DIR)
        logger.info(f"Chroma client initialized at {_CHROMA_DIR}")
    return _client


def _get_collection(name: str = "army81_memory"):
    """الحصول على collection أو إنشاؤها"""
    client = _get_client()
    try:
        return client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:
        logger.error(f"Chroma collection error: {e}")
        raise


def _make_id(text: str) -> str:
    """إنشاء ID فريد من النص"""
    return hashlib.md5(text.encode()).hexdigest()


def remember(content: str, agent_id: str = "system", tags: List[str] = None) -> str:
    """
    حفظ معلومة في الذاكرة الدلالية
    content: المحتوى المراد حفظه
    agent_id: الوكيل الذي يحفظ
    tags: وسوم للتصنيف
    """
    try:
        collection = _get_collection()
        doc_id = _make_id(content + agent_id + datetime.now().isoformat())

        metadata = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "tags": ",".join(tags or []),
            "content_preview": content[:100],
        }

        collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )

        logger.info(f"Stored memory [{doc_id[:8]}] by {agent_id}")
        return f"تم الحفظ في الذاكرة الدلالية (ID: {doc_id[:8]})"

    except Exception as e:
        logger.error(f"Chroma remember error: {e}")
        return f"خطأ في الحفظ: {e}"


def recall(query: str, n_results: int = 5, agent_id: str = None) -> str:
    """
    استرجاع المعلومات ذات الصلة من الذاكرة
    يبحث دلالياً — يجد المفاهيم المتشابهة حتى لو الكلمات مختلفة
    """
    try:
        collection = _get_collection()

        # بناء فلتر اختياري للوكيل
        where = {"agent_id": agent_id} if agent_id else None

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, max(1, collection.count())),
            where=where,
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not docs:
            return f"لا توجد ذكريات متعلقة بـ: {query}"

        output = [f"**ذكريات متعلقة بـ '{query}':**\n"]
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
            relevance = round((1 - dist) * 100, 1)
            output.append(
                f"**{i}.** [{relevance}% صلة] (بواسطة {meta.get('agent_id', '?')} | {meta.get('timestamp', '')[:10]})\n"
                f"{doc[:300]}{'...' if len(doc) > 300 else ''}"
            )

        return "\n\n".join(output)

    except Exception as e:
        logger.error(f"Chroma recall error: {e}")
        return f"خطأ في الاسترجاع: {e}"


def search_by_agent(agent_id: str, limit: int = 10) -> str:
    """استرجاع كل ذكريات وكيل معين"""
    try:
        collection = _get_collection()

        if collection.count() == 0:
            return "لا توجد ذكريات محفوظة بعد"

        results = collection.get(
            where={"agent_id": agent_id},
            limit=limit,
        )

        docs = results.get("documents", [])
        metas = results.get("metadatas", [])

        if not docs:
            return f"لا ذكريات للوكيل {agent_id}"

        output = [f"**ذكريات {agent_id} ({len(docs)} عنصر):**\n"]
        for doc, meta in zip(docs, metas):
            output.append(
                f"- [{meta.get('timestamp', '')[:10]}] {doc[:150]}..."
            )

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Chroma agent search error: {e}")
        return f"خطأ: {e}"


def get_stats() -> Dict:
    """إحصائيات الذاكرة"""
    try:
        collection = _get_collection()
        count = collection.count()
        return {
            "total_memories": count,
            "db_path": _CHROMA_DIR,
            "status": "active",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def clear_agent_memory(agent_id: str) -> str:
    """مسح ذاكرة وكيل محدد"""
    try:
        collection = _get_collection()
        results = collection.get(where={"agent_id": agent_id})
        ids = results.get("ids", [])

        if not ids:
            return f"لا توجد ذكريات للوكيل {agent_id}"

        collection.delete(ids=ids)
        return f"تم مسح {len(ids)} ذاكرة للوكيل {agent_id}"

    except Exception as e:
        return f"خطأ في المسح: {e}"


if __name__ == "__main__":
    print("اختبار Chroma Memory...")
    print(remember("الذكاء الاصطناعي يتطور بسرعة كبيرة في 2026", "A01", ["ai", "tech"]))
    print(remember("نماذج اللغة الكبيرة تحقق نتائج رائعة في التحليل", "A01", ["llm"]))
    print(recall("تطور الذكاء الاصطناعي"))
    print(get_stats())
