"""
Army81 Knowledge Loader — يغذي 81 وكيل بمعرفة حقيقية
المصادر: arXiv + PubMed + Wikipedia + GitHub + NewsAPI + WorldBank
"""
import os, json, time, requests
import xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AGENTS_DIR = Path("agents")
WORKSPACE = Path("workspace/knowledge")
WORKSPACE.mkdir(parents=True, exist_ok=True)

CATEGORY_TOPICS = {
    "cat1_science": [
        ("arxiv", "large language models agents autonomous 2025"),
        ("arxiv", "medical AI diagnosis treatment 2025"),
        ("arxiv", "quantum computing algorithms 2025"),
        ("arxiv", "robotics autonomous systems 2025"),
        ("arxiv", "climate change machine learning 2025"),
        ("pubmed", "artificial intelligence clinical diagnosis"),
        ("pubmed", "drug discovery machine learning"),
        ("pubmed", "neuroscience brain computer interface"),
        ("wiki", "Quantum_computing"),
        ("wiki", "Robotics"),
        ("wiki", "Synthetic_biology"),
    ],
    "cat2_society": [
        ("arxiv", "geopolitics international relations AI 2025"),
        ("arxiv", "cryptocurrency blockchain economics 2025"),
        ("wiki", "International_law"),
        ("wiki", "Game_theory"),
        ("wiki", "Propaganda"),
        ("wiki", "Demographics"),
        ("worldbank", "GDP growth inflation"),
        ("news", "global economy trade war 2025"),
        ("news", "cryptocurrency regulation 2025"),
    ],
    "cat3_tools": [
        ("github", "ai-agents python 2025"),
        ("github", "llm tools automation"),
        ("arxiv", "AI agents tools autonomous 2025"),
        ("news", "artificial intelligence tools 2025"),
        ("news", "cybersecurity threats 2025"),
        ("arxiv", "misinformation detection deep learning"),
    ],
    "cat4_management": [
        ("wiki", "Project_management"),
        ("wiki", "Digital_transformation"),
        ("wiki", "Organizational_behavior"),
        ("arxiv", "decision making under uncertainty AI"),
        ("arxiv", "crisis management systems"),
        ("news", "business management strategy 2025"),
    ],
    "cat5_behavior": [
        ("pubmed", "behavioral psychology cognitive bias"),
        ("pubmed", "emotional intelligence social behavior"),
        ("pubmed", "body language nonverbal communication"),
        ("arxiv", "crowd behavior simulation AI"),
        ("wiki", "Behavioral_economics"),
        ("wiki", "Cognitive_bias"),
        ("wiki", "Emotional_intelligence"),
    ],
    "cat6_leadership": [
        ("arxiv", "strategic leadership decision making AI"),
        ("arxiv", "geopolitics conflict analysis 2025"),
        ("wiki", "Military_strategy"),
        ("wiki", "Strategic_management"),
        ("news", "geopolitics military strategy 2025"),
        ("arxiv", "intelligence analysis methods"),
    ],
    "cat7_new": [
        ("arxiv", "AI self-improvement recursive neural 2025"),
        ("arxiv", "multi-agent reinforcement learning"),
        ("arxiv", "AI alignment safety evaluation"),
        ("github", "self-improving agents"),
        ("arxiv", "autonomous agent benchmarks evaluation"),
    ],
}

def fetch_arxiv(query, max_results=5):
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": max_results,
                    "sortBy": "submittedDate", "sortOrder": "descending"},
            timeout=20
        )
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace('\n','')
            summary = entry.find("atom:summary", ns).text.strip()[:600]
            link = entry.find("atom:id", ns).text.strip()
            published = entry.find("atom:published", ns).text[:10]
            results.append(f"[{published}] {title}\n{summary}\nURL: {link}")
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"arXiv error: {e}"

def fetch_pubmed(query, max_results=5):
    try:
        search = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"pubmed","term":query,"retmax":max_results,"retmode":"json"},
            timeout=15
        )
        ids = search.json()["esearchresult"]["idlist"]
        if not ids: return ""

        fetch = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db":"pubmed","id":",".join(ids),"retmode":"xml"},
            timeout=15
        )
        root = ET.fromstring(fetch.text)
        results = []
        for article in root.findall(".//PubmedArticle")[:max_results]:
            title_el = article.find(".//ArticleTitle")
            abstract_el = article.find(".//AbstractText")
            pmid_el = article.find(".//PMID")
            title = title_el.text if title_el is not None else ""
            abstract = abstract_el.text[:500] if abstract_el is not None else ""
            pmid = pmid_el.text if pmid_el is not None else ""
            results.append(f"{title}\n{abstract}\nPubMed: {pmid}")
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"PubMed error: {e}"

def fetch_wiki(topic):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}",
            timeout=10, headers={"User-Agent": "Army81/2.0"}
        )
        if r.status_code == 200:
            data = r.json()
            return f"{data.get('title','')}\n\n{data.get('extract','')[:1000]}"
    except Exception as e:
        return f"Wiki error: {e}"
    return ""

def fetch_github(query, max_results=10):
    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            headers={"Accept": "application/vnd.github.v3+json"},
            params={"q": f"{query} stars:>500", "sort": "stars", "per_page": max_results},
            timeout=15
        )
        repos = r.json().get("items", [])
        results = []
        for repo in repos:
            results.append(f"Stars:{repo['stargazers_count']} {repo['full_name']}: {repo.get('description','')[:200]}")
        return "\n".join(results)
    except Exception as e:
        return f"GitHub error: {e}"

def fetch_news(query):
    key = os.getenv("NEWSAPI_KEY", "")
    if not key: return ""
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "sortBy": "publishedAt", "pageSize": 5, "apiKey": key},
            timeout=15
        )
        articles = r.json().get("articles", [])
        results = []
        for a in articles:
            results.append(f"{a.get('title','')}\n{a.get('description','')}\n{a.get('publishedAt','')[:10]}")
        return "\n\n---\n\n".join(results)
    except:
        return ""

def fetch_worldbank(indicator="NY.GDP.MKTP.CD"):
    try:
        r = requests.get(
            f"https://api.worldbank.org/v2/country/all/indicator/{indicator}",
            params={"format": "json", "mrv": 1, "per_page": 10},
            timeout=15
        )
        data = r.json()
        if len(data) > 1:
            items = data[1][:10]
            results = [f"{item.get('country',{}).get('value','')}: {item.get('value','N/A')}" for item in items if item.get('value')]
            return "\n".join(results)
    except:
        pass
    return ""

def save_knowledge(category, source_type, query, content):
    if not content or len(content) < 50:
        return
    fname = WORKSPACE / f"{category}_{source_type}_{query[:30].replace(' ','_')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"Source: {source_type}\nQuery: {query}\n\n{content}")
    print(f"  saved {fname.name} ({len(content)} chars)")

def run_all():
    print("="*60)
    print("  Army81 Knowledge Loader v2.0")
    print("="*60)

    total = 0
    for category, topics in CATEGORY_TOPICS.items():
        print(f"\n{category} ({len(topics)} topics)...")
        cat_dir = WORKSPACE / category
        cat_dir.mkdir(exist_ok=True)

        for source_type, query in topics:
            print(f"  [{source_type}] {query[:50]}...")

            if source_type == "arxiv":
                content = fetch_arxiv(query)
            elif source_type == "pubmed":
                content = fetch_pubmed(query)
            elif source_type == "wiki":
                content = fetch_wiki(query)
            elif source_type == "github":
                content = fetch_github(query)
            elif source_type == "news":
                content = fetch_news(query)
            elif source_type == "worldbank":
                content = fetch_worldbank()
            else:
                content = ""

            if content and not content.startswith("Error"):
                fname = cat_dir / f"{source_type}_{query[:30].replace(' ','_').replace('/','_')}.txt"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(f"Source: {source_type}\nQuery: {query}\nDate: 2026-03-18\n\n{content}")
                total += 1
                print(f"    OK {len(content)} chars")

            time.sleep(1.5)  # rate limiting

    # Load into Chroma
    try:
        import chromadb
        client = chromadb.PersistentClient(path="workspace/chroma_db")

        for category in CATEGORY_TOPICS.keys():
            cat_dir = WORKSPACE / category
            if not cat_dir.exists():
                continue

            collection = client.get_or_create_collection(
                f"knowledge_{category}",
                metadata={"hnsw:space": "cosine"}
            )

            files = list(cat_dir.glob("*.txt"))
            for i, f in enumerate(files):
                content = f.read_text(encoding="utf-8")
                collection.upsert(
                    ids=[f"{category}_{i}"],
                    documents=[content[:2000]],
                    metadatas=[{"source": f.stem, "category": category}]
                )
            print(f"  {category}: {len(files)} documents -> Chroma")

        print(f"\nChroma updated")
    except Exception as e:
        print(f"  Chroma: {e} -- files saved to workspace/knowledge/")

    print(f"\n{'='*60}")
    print(f"Done: {total} knowledge sources loaded")
    print("="*60)

if __name__ == "__main__":
    run_all()
