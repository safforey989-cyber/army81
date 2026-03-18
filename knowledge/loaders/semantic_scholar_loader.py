"""
semantic_scholar_loader.py — أكثر الأوراق اقتباساً من Semantic Scholar (مجاني)
"""
import time
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

SS_API = "https://api.semanticscholar.org/graph/v1"

SPECIALTIES = {
    "artificial_intelligence": "artificial intelligence machine learning deep learning",
    "medicine": "clinical medicine evidence-based treatment diagnosis",
    "economics": "macroeconomics monetary policy trade finance",
    "psychology": "cognitive psychology behavior therapy mental health",
    "security": "cybersecurity cryptography network security",
    "physics": "quantum computing condensed matter physics",
    "climate": "climate change global warming carbon emissions",
    "robotics": "robotics autonomous systems control",
    "neuroscience": "neuroscience brain neural cognition",
    "linguistics": "natural language processing computational linguistics",
}


def search_top_cited(query: str, limit: int = 20) -> List[Dict]:
    """Search Semantic Scholar for highly cited papers."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,citationCount,url,authors",
        "sort": "citationCount:desc",
    })
    url = f"{SS_API}/paper/search?{params}"

    papers = []
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Army81/2.0 (educational research project)",
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())

        for paper in data.get("data", []):
            abstract = paper.get("abstract") or ""
            if not abstract:
                continue
            papers.append({
                "title": paper.get("title", ""),
                "abstract": abstract,
                "year": paper.get("year", ""),
                "citations": paper.get("citationCount", 0),
                "url": paper.get("url", ""),
                "source": "semantic_scholar",
                "specialty": query[:50],
            })
    except Exception as e:
        logger.error(f"Semantic Scholar search failed for '{query}': {e}")

    return papers


def load_semantic_scholar_to_chroma() -> Dict[str, int]:
    """Load top cited papers for all specialties into Chroma."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        db_path = Path(__file__).parent.parent.parent / "workspace" / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(db_path))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
    except ImportError:
        logger.error("chromadb not installed")
        return {}

    counts = {}
    for specialty, query in SPECIALTIES.items():
        logger.info(f"Semantic Scholar: {specialty}...")
        papers = search_top_cited(query, limit=20)

        if not papers:
            counts[specialty] = 0
            time.sleep(5)
            continue

        collection = client.get_or_create_collection(
            name=f"ss_{specialty}",
            embedding_function=ef,
            metadata={"source": "semantic_scholar", "specialty": specialty},
        )

        docs = [f"{p['title']}\n\n{p['abstract']}" for p in papers]
        ids = [f"ss_{specialty}_{i}" for i in range(len(papers))]
        metas = [{
            "title": p["title"],
            "year": str(p.get("year", "")),
            "citations": p.get("citations", 0),
            "url": p.get("url", ""),
            "source": "semantic_scholar",
            "specialty": specialty,
        } for p in papers]

        try:
            collection.upsert(documents=docs, ids=ids, metadatas=metas)
            counts[specialty] = len(papers)
            logger.info(f"  ✓ {specialty}: {len(papers)} papers")
        except Exception as e:
            logger.error(f"  ✗ {specialty}: {e}")
            counts[specialty] = 0

        time.sleep(3)  # Rate limit: ~100 req/5min

    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = load_semantic_scholar_to_chroma()
    print(f"Done: {results}")
