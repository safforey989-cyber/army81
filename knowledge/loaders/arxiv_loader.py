"""
arxiv_loader.py — جلب أوراق arXiv وحفظها في Chroma
"""
import time
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

TOPICS = {
    "medicine": "medical diagnosis treatment clinical",
    "quantum_computing": "quantum computing qubit algorithm",
    "climate_science": "climate change global warming carbon",
    "robotics": "robotics autonomous robot manipulation",
    "neuroscience": "neuroscience brain neural cognitive",
    "cryptography": "cryptography encryption security protocol",
    "economics": "economics market financial macroeconomics",
    "military_history": "military history warfare strategy defense",
    "psychology": "psychology behavior cognitive human mental",
    "linguistics": "linguistics language natural processing",
    "AI_agents": "large language model agent autonomous AI",
}

ARXIV_API = "http://export.arxiv.org/api/query"


def fetch_arxiv_papers(topic_query: str, max_results: int = 30) -> List[Dict]:
    """Fetch papers from arXiv API."""
    params = urllib.parse.urlencode({
        "search_query": f"all:{topic_query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"

    papers = []
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            id_el = entry.find("atom:id", ns)

            if title_el is None or summary_el is None:
                continue

            papers.append({
                "title": title_el.text.strip().replace("\n", " "),
                "abstract": summary_el.text.strip().replace("\n", " "),
                "published": published_el.text if published_el is not None else "",
                "url": id_el.text if id_el is not None else "",
                "source": "arxiv",
            })
    except Exception as e:
        logger.error(f"arXiv fetch failed for '{topic_query}': {e}")

    return papers


def load_arxiv_to_chroma(max_results_per_topic: int = 30) -> Dict[str, int]:
    """Load arXiv papers for all topics into Chroma collections."""
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
    for topic, query in TOPICS.items():
        logger.info(f"Fetching arXiv: {topic}...")
        papers = fetch_arxiv_papers(query, max_results_per_topic)

        if not papers:
            counts[topic] = 0
            continue

        collection = client.get_or_create_collection(
            name=f"arxiv_{topic}",
            embedding_function=ef,
            metadata={"topic": topic, "source": "arxiv"},
        )

        docs = [f"{p['title']}\n\n{p['abstract']}" for p in papers]
        ids = [f"arxiv_{topic}_{i}" for i in range(len(papers))]
        metas = [{"title": p["title"], "url": p["url"], "published": p["published"], "source": "arxiv", "topic": topic} for p in papers]

        # Add in batches, skip existing
        try:
            collection.upsert(documents=docs, ids=ids, metadatas=metas)
            counts[topic] = len(papers)
            logger.info(f"  ✓ {topic}: {len(papers)} papers stored")
        except Exception as e:
            logger.error(f"  ✗ {topic}: {e}")
            counts[topic] = 0

        time.sleep(3)  # Rate limit

    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = load_arxiv_to_chroma(max_results_per_topic=30)
    print(f"Done: {results}")
