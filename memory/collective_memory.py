"""
CollectiveMemory — 81 وكيل يشاركون المعرفة
مستوحى من openai/swarm
"""
import logging
from typing import Optional

logger = logging.getLogger("army81.collective_memory")


class CollectiveMemory:
    """
    ذاكرة جماعية مشتركة بين جميع الوكلاء
    collection واحدة في Chroma: army81_collective
    """
    COLLECTION = "army81_collective"

    def contribute(self, agent_id: str, insight: str,
                   topic: str, confidence: float = 0.8):
        """
        وكيل يشارك ما تعلمه مع البقية
        يُحفظ في Chroma بـ collection المشتركة
        """
        try:
            from memory.chroma_memory import _get_collection
            collection = _get_collection(self.COLLECTION)

            import hashlib
            from datetime import datetime
            doc_id = hashlib.md5(
                (agent_id + insight[:100] + datetime.now().isoformat()).encode()
            ).hexdigest()

            metadata = {
                "agent_id": agent_id,
                "topic": topic,
                "confidence": str(confidence),
                "timestamp": datetime.now().isoformat(),
            }
            collection.add(
                ids=[doc_id],
                documents=[insight],
                metadatas=[metadata],
            )
            logger.info(f"[CollectiveMem] {agent_id} contributed insight on '{topic}'")

        except Exception as e:
            logger.warning(f"[CollectiveMem] contribute error: {e}")

    def query(self, topic: str, requesting_agent_id: str, k: int = 3) -> str:
        """
        وكيل يسأل البقية عن موضوع
        يعيد أفضل k نتائج من المعرفة الجماعية
        """
        try:
            from memory.chroma_memory import _get_collection
            collection = _get_collection(self.COLLECTION)

            if collection.count() == 0:
                return ""

            results = collection.query(
                query_texts=[topic],
                n_results=min(k, collection.count()),
            )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            if not docs:
                return ""

            lines = []
            for doc, meta, dist in zip(docs, metas, distances):
                relevance = round((1 - dist) * 100, 1)
                contributor = meta.get("agent_id", "?")
                # لا تُظهر مساهمات الوكيل نفسه
                if contributor == requesting_agent_id:
                    continue
                lines.append(
                    f"[{contributor} | {relevance}% صلة]: {doc[:200]}"
                )

            return "\n".join(lines) if lines else ""

        except Exception as e:
            logger.warning(f"[CollectiveMem] query error: {e}")
            return ""

    def get_expert_on(self, topic: str) -> Optional[str]:
        """
        من هو أكثر وكيل خبرة في هذا الموضوع؟
        يعيد agent_id للوكيل الأكثر مساهمةً في هذا الموضوع
        """
        try:
            from memory.chroma_memory import _get_collection
            collection = _get_collection(self.COLLECTION)

            if collection.count() == 0:
                return None

            results = collection.query(
                query_texts=[topic],
                n_results=min(10, collection.count()),
            )

            metas = results.get("metadatas", [[]])[0]
            if not metas:
                return None

            # احسب عدد المساهمات لكل وكيل
            counts = {}
            for meta in metas:
                agent = meta.get("agent_id", "unknown")
                counts[agent] = counts.get(agent, 0) + 1

            expert = max(counts, key=counts.get)
            logger.info(f"[CollectiveMem] Expert on '{topic}': {expert} ({counts[expert]} contributions)")
            return expert

        except Exception as e:
            logger.warning(f"[CollectiveMem] get_expert_on error: {e}")
            return None
