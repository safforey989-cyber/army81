"""
pubmed_loader.py — جلب ملخصات PubMed المجانية
"""
import time
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

CATEGORIES = {
    "pharmacology": "pharmacology drug mechanism receptor",
    "psychiatry": "psychiatry mental health depression anxiety",
    "oncology": "cancer oncology tumor immunotherapy",
    "cardiology": "cardiology heart cardiovascular treatment",
}


def search_pubmed(query: str, max_results: int = 25) -> List[str]:
    """Search PubMed and return list of PMIDs."""
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml",
        "sort": "pub+date",
    })
    url = f"{PUBMED_BASE}/esearch.fcgi?{params}"

    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        return [el.text for el in root.findall(".//Id") if el.text]
    except Exception as e:
        logger.error(f"PubMed search failed: {e}")
        return []


def fetch_abstracts(pmids: List[str]) -> List[Dict]:
    """Fetch abstracts for given PMIDs."""
    if not pmids:
        return []

    params = urllib.parse.urlencode({
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    })
    url = f"{PUBMED_BASE}/efetch.fcgi?{params}"

    articles = []
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)

        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            title_el = article.find(".//ArticleTitle")
            abstract_el = article.find(".//AbstractText")
            year_el = article.find(".//PubDate/Year")

            if title_el is None or abstract_el is None:
                continue

            pmid = pmid_el.text if pmid_el is not None else ""
            articles.append({
                "pmid": pmid,
                "title": (title_el.text or "").strip(),
                "abstract": (abstract_el.text or "").strip(),
                "year": year_el.text if year_el is not None else "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source": "pubmed",
            })
    except Exception as e:
        logger.error(f"PubMed fetch failed: {e}")

    return articles


def load_pubmed_to_chroma(max_per_category: int = 25) -> Dict[str, int]:
    """Load PubMed abstracts into Chroma 'medical_knowledge' collection."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        db_path = Path(__file__).parent.parent.parent / "workspace" / "chroma_db"
        db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(db_path))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(
            name="medical_knowledge",
            embedding_function=ef,
            metadata={"source": "pubmed"},
        )
    except ImportError:
        logger.error("chromadb not installed")
        return {}

    counts = {}
    for category, query in CATEGORIES.items():
        logger.info(f"Fetching PubMed: {category}...")
        pmids = search_pubmed(query, max_per_category)
        time.sleep(1)

        articles = fetch_abstracts(pmids)
        if not articles:
            counts[category] = 0
            continue

        docs = [f"{a['title']}\n\n{a['abstract']}" for a in articles]
        ids = [f"pubmed_{a['pmid']}" for a in articles]
        metas = [{"title": a["title"], "url": a["url"], "year": a["year"], "category": category, "source": "pubmed"} for a in articles]

        try:
            collection.upsert(documents=docs, ids=ids, metadatas=metas)
            counts[category] = len(articles)
            logger.info(f"  ✓ {category}: {len(articles)} abstracts stored")
        except Exception as e:
            logger.error(f"  ✗ {category}: {e}")
            counts[category] = 0

        time.sleep(1)

    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = load_pubmed_to_chroma()
    print(f"Done: {results}")
