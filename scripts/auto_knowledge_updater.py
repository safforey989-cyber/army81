"""
Army81 — Auto Knowledge Updater (24/7)
يجلب معرفة جديدة كل 6 ساعات تلقائياً من:
- arXiv (أبحاث AI)
- GitHub trending (أدوات جديدة)
- NewsAPI (أخبار تقنية)
- Wikipedia (مواضيع متخصصة)
- PubMed (أبحاث طبية)
"""
import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

# تحميل .env دائماً
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [army81.knowledge] %(levelname)s: %(message)s')
logger = logging.getLogger("army81.knowledge")

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")
KNOWLEDGE_DIR = Path("workspace/knowledge")
UPDATE_INTERVAL_HOURS = 6


def wait_for_gateway(timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{GATEWAY}/health", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def fetch_arxiv(query: str, max_results: int = 5) -> list:
    """جلب أبحاث من arXiv"""
    results = []
    try:
        import urllib.parse
        q = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                summary = entry.find("atom:summary", ns)
                if title is not None and summary is not None:
                    results.append({
                        "title": title.text.strip(),
                        "summary": summary.text.strip()[:500],
                        "source": "arXiv",
                    })
    except Exception as e:
        logger.warning(f"arXiv fetch failed for '{query}': {e}")
    return results


def fetch_news(query: str, max_results: int = 5) -> list:
    """جلب أخبار من NewsAPI"""
    results = []
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        return results
    try:
        r = requests.get("https://newsapi.org/v2/everything",
                        params={"q": query, "sortBy": "publishedAt", "pageSize": max_results,
                                "language": "en", "apiKey": api_key}, timeout=15)
        if r.status_code == 200:
            for art in r.json().get("articles", []):
                results.append({
                    "title": art.get("title", ""),
                    "summary": art.get("description", "")[:300],
                    "source": "NewsAPI",
                })
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed: {e}")
    return results


def fetch_github_trending() -> list:
    """جلب أشهر repos من GitHub"""
    results = []
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}"} if token else {}
    try:
        r = requests.get("https://api.github.com/search/repositories",
                        params={"q": "AI agent created:>2026-01-01", "sort": "stars", "per_page": 5},
                        headers=headers, timeout=15)
        if r.status_code == 200:
            for repo in r.json().get("items", []):
                results.append({
                    "title": repo.get("full_name", ""),
                    "summary": repo.get("description", "")[:300],
                    "source": "GitHub",
                    "stars": repo.get("stargazers_count", 0),
                })
    except Exception as e:
        logger.warning(f"GitHub fetch failed: {e}")
    return results


def save_knowledge(items: list, category: str):
    """حفظ المعرفة في ملفات"""
    cat_dir = KNOWLEDGE_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    for item in items:
        try:
            title = item["title"][:60].replace("/", "_").replace("\\", "_").replace(":", "_")
            filename = f"{item['source']}_{title}.txt"
            filepath = cat_dir / filename

            if not filepath.exists():
                content = f"Title: {item['title']}\nSource: {item['source']}\nDate: {datetime.now().isoformat()}\n\n{item['summary']}"
                filepath.write_text(content, encoding="utf-8")
                saved += 1
        except Exception:
            pass

    return saved


def store_in_chroma(items: list, category: str):
    """حفظ في Chroma للبحث الدلالي"""
    try:
        from memory.collective_memory import CollectiveMemory
        cm = CollectiveMemory()
        for item in items:
            cm.contribute("KNOWLEDGE_HUNTER", item["summary"][:500],
                         f"{category}:{item.get('source', 'unknown')}", 0.85)
    except Exception as e:
        logger.warning(f"Chroma store failed: {e}")


def run_knowledge_update():
    """دورة تحديث المعرفة الكاملة"""
    logger.info("📚 Starting knowledge update cycle...")
    total_fetched = 0
    total_saved = 0

    # ─── أبحاث AI ───
    topics = {
        "cat1_science": [
            "large language models agents 2026",
            "AI self-improvement recursive",
            "knowledge distillation efficient",
            "medical AI diagnosis",
            "quantum computing algorithms",
        ],
        "cat2_society": [
            "AI regulation policy 2026",
            "cryptocurrency blockchain economics",
            "geopolitics artificial intelligence",
        ],
        "cat3_tools": [
            "AI agent tools frameworks 2026",
            "prompt engineering automation",
            "RAG retrieval augmented generation",
        ],
        "cat7_new": [
            "multi-agent reinforcement learning",
            "model merging evolutionary",
            "synthetic data generation training",
            "AI alignment safety",
        ],
    }

    for category, queries in topics.items():
        for query in queries:
            items = fetch_arxiv(query, 3)
            total_fetched += len(items)
            total_saved += save_knowledge(items, category)
            store_in_chroma(items, category)
            time.sleep(2)

    # ─── أخبار تقنية ───
    news_queries = ["artificial intelligence", "machine learning", "AI agents"]
    for query in news_queries:
        items = fetch_news(query, 3)
        total_fetched += len(items)
        total_saved += save_knowledge(items, "news")
        store_in_chroma(items, "news")
        time.sleep(1)

    # ─── GitHub Trending ───
    items = fetch_github_trending()
    total_fetched += len(items)
    total_saved += save_knowledge(items, "cat3_tools")
    store_in_chroma(items, "github_trending")

    logger.info(f"✅ Knowledge update done: {total_fetched} fetched, {total_saved} new saved")

    # أرسل تقرير على Telegram
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            msg = f"📚 *تحديث المعرفة*\n⏰ {datetime.now().strftime('%H:%M')}\n📥 جلبت: {total_fetched}\n💾 حفظت: {total_saved} جديد"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                         json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except Exception:
        pass

    return total_fetched, total_saved


def main():
    logger.info("🕷️ Army81 Knowledge Hunter starting...")

    if not wait_for_gateway():
        logger.warning("Gateway not available — running standalone")

    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n🔄 Knowledge Cycle {cycle}")

        try:
            fetched, saved = run_knowledge_update()
            logger.info(f"✅ Cycle {cycle} done: {fetched} fetched, {saved} saved")
        except Exception as e:
            logger.error(f"❌ Knowledge cycle error: {e}")

        logger.info(f"😴 Sleeping {UPDATE_INTERVAL_HOURS}h until next update...")
        time.sleep(UPDATE_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()
