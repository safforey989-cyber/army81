"""
Army81 Tools - News Fetcher
جمع الأخبار من مصادر متعددة: RSS feeds + NewsAPI + Serper
"""
import os
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("army81.tools.news_fetcher")

# ── مصادر RSS ─────────────────────────────────────────────────
RSS_FEEDS = {
    "ai": [
        "https://news.google.com/rss/search?q=artificial+intelligence&hl=en",
        "https://feeds.feedburner.com/oreilly/radar",
    ],
    "tech": [
        "https://news.google.com/rss/search?q=technology&hl=en",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
    ],
    "science": [
        "https://news.google.com/rss/search?q=science+research&hl=en",
    ],
    "security": [
        "https://news.google.com/rss/search?q=cybersecurity&hl=en",
    ],
    "business": [
        "https://news.google.com/rss/search?q=business+economy&hl=en",
    ],
    "arabic": [
        "https://news.google.com/rss/search?q=%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A&hl=ar",
        "https://news.google.com/rss/search?q=%D8%AA%D9%82%D9%86%D9%8A%D8%A9&hl=ar",
    ],
}


def fetch_rss(feed_url: str, max_items: int = 5) -> List[Dict]:
    """جلب أخبار من RSS feed واحد"""
    try:
        resp = requests.get(feed_url, timeout=15, headers={
            "User-Agent": "Army81/1.0 NewsBot"
        })
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = []

        # RSS 2.0 format
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")

            # تنظيف HTML بسيط
            description = _strip_html(description)[:300]

            items.append({
                "title": title,
                "link": link,
                "description": description,
                "published": pub_date,
                "source": "rss",
            })

        # Atom format fallback
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title", "", ns)
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                summary = entry.findtext("atom:summary", "", ns)
                published = entry.findtext("atom:published", "", ns)

                items.append({
                    "title": title,
                    "link": link,
                    "description": _strip_html(summary)[:300],
                    "published": published,
                    "source": "rss",
                })

        return items

    except Exception as e:
        logger.warning(f"RSS fetch error for {feed_url}: {e}")
        return []


def fetch_news_by_topic(topic: str, max_results: int = 5) -> str:
    """
    جمع أخبار حول موضوع معين من كل المصادر المتاحة
    يحاول: NewsAPI → RSS → Serper (بالترتيب)
    """
    results = []

    # 1. حاول NewsAPI
    news_key = os.getenv("NEWSAPI_KEY", "")
    if news_key:
        articles = _fetch_newsapi(topic, news_key, max_results)
        results.extend(articles)

    # 2. أضف من RSS إذا لزم
    if len(results) < max_results:
        rss_results = fetch_rss_by_topic(topic, max_results - len(results))
        results.extend(rss_results)

    # 3. Serper كبديل أخير
    if not results:
        serper_key = os.getenv("SERPER_API_KEY", "")
        if serper_key:
            results = _fetch_serper_news(topic, serper_key, max_results)

    if not results:
        return f"لم تُوجد أخبار حول: {topic}"

    # تنسيق النتائج
    formatted = []
    for i, item in enumerate(results[:max_results], 1):
        formatted.append(
            f"**{i}. {item['title']}**\n"
            f"{item.get('description', '')}\n"
            f"المصدر: {item.get('source_name', item.get('source', 'غير معروف'))} — "
            f"{item.get('published', '')[:16]}\n"
            f"🔗 {item.get('link', '')}"
        )

    return "\n\n---\n\n".join(formatted)


def fetch_rss_by_topic(topic: str, max_results: int = 5) -> List[Dict]:
    """جلب أخبار من RSS feeds حسب الموضوع"""
    topic_lower = topic.lower()

    # تحديد الفئات المناسبة
    feed_urls = []
    topic_map = {
        "ai": ["ذكاء", "ai", "artificial", "machine learning", "llm", "gpt"],
        "tech": ["تقنية", "tech", "software", "hardware", "digital"],
        "science": ["علم", "science", "research", "بحث"],
        "security": ["أمن", "security", "cyber", "hack", "تشفير"],
        "business": ["اقتصاد", "business", "economy", "market", "سوق"],
        "arabic": ["عربي", "arabic"],
    }

    matched = False
    for category, keywords in topic_map.items():
        if any(kw in topic_lower for kw in keywords):
            feed_urls.extend(RSS_FEEDS.get(category, []))
            matched = True

    if not matched:
        # استخدم Google News RSS مباشرة
        from urllib.parse import quote
        feed_urls.append(
            f"https://news.google.com/rss/search?q={quote(topic)}&hl=en"
        )

    all_items = []
    for url in feed_urls:
        items = fetch_rss(url, max_items=max_results)
        all_items.extend(items)
        if len(all_items) >= max_results:
            break

    return all_items[:max_results]


def fetch_daily_briefing(topics: List[str] = None) -> str:
    """
    إعداد تقرير إخباري يومي شامل
    يُستخدم بواسطة daily_updater.py
    """
    if topics is None:
        topics = [
            "artificial intelligence AI",
            "technology breakthroughs",
            "cybersecurity",
            "science research",
            "Middle East",
        ]

    sections = []
    for topic in topics:
        news = fetch_news_by_topic(topic, max_results=3)
        sections.append(f"## {topic}\n\n{news}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    header = f"# التقرير الإخباري اليومي — {date_str}\n\n"
    return header + "\n\n---\n\n".join(sections)


# ── مصادر خارجية ─────────────────────────────────────────────

def _fetch_newsapi(topic: str, api_key: str, max_results: int = 5) -> List[Dict]:
    """جلب أخبار من NewsAPI.org"""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for art in data.get("articles", [])[:max_results]:
            articles.append({
                "title": art.get("title", ""),
                "description": art.get("description", ""),
                "link": art.get("url", ""),
                "published": art.get("publishedAt", ""),
                "source_name": art.get("source", {}).get("name", "NewsAPI"),
                "source": "newsapi",
            })
        return articles

    except Exception as e:
        logger.warning(f"NewsAPI error: {e}")
        return []


def _fetch_serper_news(topic: str, api_key: str, max_results: int = 5) -> List[Dict]:
    """جلب أخبار عبر Serper News API"""
    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": topic, "num": max_results}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("news", [])[:max_results]:
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "link": item.get("link", ""),
                "published": item.get("date", ""),
                "source_name": item.get("source", "Serper"),
                "source": "serper",
            })
        return articles

    except Exception as e:
        logger.warning(f"Serper news error: {e}")
        return []


def _strip_html(text: str) -> str:
    """إزالة HTML tags بسيطة"""
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'")
    return clean.strip()


# ── للاختبار المباشر ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== اختبار جمع الأخبار ===\n")
    print(fetch_news_by_topic("artificial intelligence", max_results=3))
    print("\n\n=== RSS Test ===\n")
    items = fetch_rss_by_topic("ai", max_results=2)
    for item in items:
        print(f"- {item['title']}")
