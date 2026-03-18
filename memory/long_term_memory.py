"""
long_term_memory.py — الذاكرة الطويلة الأمد لكل وكيل
فوق Chroma مع أهمية متغيرة ونسيان تدريجي
"""
import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available — long-term memory disabled")


class LongTermMemory:
    """
    الذاكرة الطويلة الأمد لكل وكيل.
    - store: يحفظ بأهمية 1-10
    - recall: يسترجع أهم المعلومات
    - forget: ينسى القديم أو الأقل أهمية
    - summarize: يلخص الذاكرة الزائدة
    - share: ينقل معرفة بين وكيلين
    - importance_decay: تتراجع الأهمية مع الوقت
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "workspace" / "chroma_db")

        Path(db_path).mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._client = None
        self._ef = None
        self._collections: Dict[str, Any] = {}

    def _get_client(self):
        if not CHROMA_AVAILABLE:
            return None
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self._db_path)
            self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        return self._client

    def _get_collection(self, agent_id: str):
        if agent_id in self._collections:
            return self._collections[agent_id]
        client = self._get_client()
        if client is None:
            return None
        col = client.get_or_create_collection(
            name=f"ltm_{agent_id}",
            embedding_function=self._ef,
            metadata={"agent_id": agent_id, "type": "long_term_memory"},
        )
        self._collections[agent_id] = col
        return col

    def _make_id(self, agent_id: str, content: str) -> str:
        h = hashlib.md5(content[:200].encode()).hexdigest()[:12]
        ts = str(int(time.time()))[-6:]
        return f"ltm_{agent_id}_{ts}_{h}"

    def store(
        self,
        agent_id: str,
        content: str,
        metadata: Dict = None,
        importance: int = 5,
    ) -> str:
        """
        حفظ محتوى في الذاكرة الطويلة.
        importance: 1 (عادي) → 10 (حرج جداً)
        """
        col = self._get_collection(agent_id)
        if col is None:
            return ""

        importance = max(1, min(10, importance))
        meta = {
            "agent_id": agent_id,
            "importance": importance,
            "stored_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
            "decay_score": float(importance),  # يتراجع مع الوقت
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        doc_id = self._make_id(agent_id, content)
        try:
            col.upsert(documents=[content], ids=[doc_id], metadatas=[meta])
            logger.debug(f"LTM stored: {agent_id} | importance={importance} | id={doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"LTM store failed: {e}")
            return ""

    def recall(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
        min_importance: int = 1,
    ) -> List[Dict]:
        """
        استرجاع أهم المعلومات ذات الصلة بالسؤال.
        يُحدّث access_count و last_accessed لكل نتيجة.
        """
        col = self._get_collection(agent_id)
        if col is None:
            return []

        try:
            where = {"importance": {"$gte": min_importance}} if min_importance > 1 else None
            kwargs = {
                "query_texts": [query],
                "n_results": min(top_k, max(1, col.count())),
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where

            results = col.query(**kwargs)
            memories = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for doc, meta, dist in zip(docs, metas, dists):
                relevance = round(1 - float(dist), 3) if dist else 0
                memories.append({
                    "content": doc,
                    "importance": int(meta.get("importance", 5)),
                    "stored_at": meta.get("stored_at", ""),
                    "relevance_score": relevance,
                    "access_count": int(meta.get("access_count", 0)),
                })

            # Update access stats
            self._update_access_stats(col, agent_id, memories)
            return memories

        except Exception as e:
            logger.error(f"LTM recall failed: {e}")
            return []

    def _update_access_stats(self, col, agent_id: str, memories: List[Dict]):
        """تحديث إحصاءات الوصول."""
        try:
            all_items = col.get(include=["metadatas", "documents"])
            ids = all_items.get("ids", [])
            metas = all_items.get("metadatas", [])

            for i, meta in enumerate(metas):
                for mem in memories:
                    if meta.get("stored_at") == mem.get("stored_at"):
                        updated_meta = dict(meta)
                        updated_meta["access_count"] = int(meta.get("access_count", 0)) + 1
                        updated_meta["last_accessed"] = datetime.now().isoformat()
                        try:
                            col.update(ids=[ids[i]], metadatas=[updated_meta])
                        except Exception:
                            pass
                        break
        except Exception:
            pass

    def forget(self, agent_id: str, older_than_days: int = 90, min_importance_to_keep: int = 7) -> int:
        """
        ينسى المحتوى القديم ذو الأهمية المنخفضة.
        يحافظ على المحتوى ذو الأهمية العالية حتى لو كان قديماً.
        """
        col = self._get_collection(agent_id)
        if col is None:
            return 0

        cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
        try:
            all_items = col.get(include=["metadatas"])
            ids = all_items.get("ids", [])
            metas = all_items.get("metadatas", [])

            to_delete = []
            for doc_id, meta in zip(ids, metas):
                stored_at = meta.get("stored_at", "")
                importance = int(meta.get("importance", 5))
                if stored_at < cutoff and importance < min_importance_to_keep:
                    to_delete.append(doc_id)

            if to_delete:
                col.delete(ids=to_delete)
                logger.info(f"LTM forget: {agent_id} deleted {len(to_delete)} old memories")
            return len(to_delete)
        except Exception as e:
            logger.error(f"LTM forget failed: {e}")
            return 0

    def summarize(self, agent_id: str) -> str:
        """
        يلخص ذاكرة الوكيل إذا كانت كبيرة.
        يُرجع ملخصاً نصياً لأهم 20 ذكرى.
        """
        col = self._get_collection(agent_id)
        if col is None:
            return ""

        try:
            count = col.count()
            if count == 0:
                return f"لا توجد ذكريات محفوظة للوكيل {agent_id}"

            all_items = col.get(include=["documents", "metadatas"])
            docs = all_items.get("documents", [])
            metas = all_items.get("metadatas", [])

            # ترتيب حسب الأهمية
            pairs = sorted(
                zip(docs, metas),
                key=lambda x: int(x[1].get("importance", 5)),
                reverse=True,
            )[:20]

            lines = [f"ملخص ذاكرة الوكيل {agent_id} ({count} ذكرى):"]
            for doc, meta in pairs:
                imp = meta.get("importance", 5)
                date = meta.get("stored_at", "")[:10]
                lines.append(f"[أهمية {imp}] [{date}] {doc[:200]}")

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"LTM summarize failed: {e}")
            return ""

    def share(self, from_agent: str, to_agent: str, topic: str, top_k: int = 3) -> int:
        """
        نقل معرفة ذات صلة من وكيل لآخر.
        يبحث في ذاكرة from_agent ويحفظ النتائج في to_agent.
        """
        memories = self.recall(from_agent, topic, top_k=top_k)
        if not memories:
            return 0

        shared = 0
        for mem in memories:
            new_content = f"[مُشارَك من {from_agent}] {mem['content']}"
            doc_id = self.store(
                to_agent,
                new_content,
                metadata={"shared_from": from_agent, "topic": topic},
                importance=max(3, mem["importance"] - 1),  # أهمية أقل قليلاً
            )
            if doc_id:
                shared += 1

        logger.info(f"LTM share: {from_agent} → {to_agent} | {shared} memories on '{topic}'")
        return shared

    def importance_decay(self, agent_id: str, decay_rate: float = 0.05) -> int:
        """
        تُخفِّض أهمية الذكريات القديمة تدريجياً.
        decay_rate: نسبة التراجع اليومية (0.05 = 5% يومياً)
        """
        col = self._get_collection(agent_id)
        if col is None:
            return 0

        try:
            all_items = col.get(include=["metadatas"])
            ids = all_items.get("ids", [])
            metas = all_items.get("metadatas", [])

            updated = 0
            now = datetime.now()
            for doc_id, meta in zip(ids, metas):
                stored_at_str = meta.get("stored_at", "")
                if not stored_at_str:
                    continue
                try:
                    stored_at = datetime.fromisoformat(stored_at_str)
                    days_old = (now - stored_at).days
                    original_imp = int(meta.get("importance", 5))
                    # لا تُخفِّض الأهمية العالية جداً (9-10)
                    if original_imp >= 9:
                        continue
                    decay = decay_rate * days_old
                    new_decay_score = float(meta.get("decay_score", original_imp)) * (1 - decay)
                    new_decay_score = max(1.0, new_decay_score)

                    updated_meta = dict(meta)
                    updated_meta["decay_score"] = new_decay_score
                    col.update(ids=[doc_id], metadatas=[updated_meta])
                    updated += 1
                except Exception:
                    continue

            logger.info(f"LTM decay: {agent_id} | {updated} memories updated")
            return updated
        except Exception as e:
            logger.error(f"LTM decay failed: {e}")
            return 0

    def stats(self, agent_id: str) -> Dict:
        """إحصائيات ذاكرة الوكيل."""
        col = self._get_collection(agent_id)
        if col is None:
            return {"error": "ChromaDB not available"}
        try:
            count = col.count()
            all_items = col.get(include=["metadatas"])
            metas = all_items.get("metadatas", [])
            importance_dist = {}
            for meta in metas:
                imp = str(meta.get("importance", "?"))
                importance_dist[imp] = importance_dist.get(imp, 0) + 1
            return {
                "agent_id": agent_id,
                "total_memories": count,
                "importance_distribution": importance_dist,
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton
_ltm_instance: Optional[LongTermMemory] = None

def get_long_term_memory() -> LongTermMemory:
    global _ltm_instance
    if _ltm_instance is None:
        _ltm_instance = LongTermMemory()
    return _ltm_instance
