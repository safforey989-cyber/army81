"""
Army81 Tools - News Fetcher
جمع الأخبار من RSS feeds + NewsAPI
المرحلة 1: أداة حقيقية لجمع الأخبار من مصادر متعددة
"""
import os
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger("army81.tools.news_fetcher")

# ── RSS Feeds المدعومة ──────────────────────────────────────
RSS_FEEDS = {
    # أخبار عامة
    "bbc_arabic": "https://feeds.bbci.co.uk/arabic/rss.xml",
    "aljazeera": "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9",
    "reuters": "https://feeds.reuters.com/reuters/topNews",
    "bbc_tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    # تقنية وذكاء اصطناعي
    "techcrunch": "https://techcrunch.com/feed/",
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/index",
    "hacker_news": "https://hnrss.org/frontpage",
    "mit_tech": "https://www.technologyreview.com/feed/",
    # علوم
    "nature": "https://www.nature.com/nature.rss",
    "science_daily": "https://www.sciencedaily.com/rss/all.xml",
    "arxiv_ai": "https://rss.arxiv.org/rss/cs.AI",
    "arxiv_ml": "https://rss.arxiv.org/rss/cs.LG",
    # اقتصاد
    "cnbc": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "ft": "https://www.ft.com/rss/home",
    "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
}

# تصنيف المواضيع إلى feeds
TOPIC_FEEDS = {
    "ai": ["techcrunch", "ars_technica", "hacker_news", "mit_tech", "arxiv_ai", "arxiv_ml"],
    "tech": ["techcrunch", "ars_technica", "hacker_news", "bbc_tech", "mit_tech"],
    "science": ["nature", "science_daily", "arxiv_ai", "arxiv_ml"],
    "economy": ["cnbc", "ft", "bloomberg", "reuters"],
    "world": ["bbc_arabic", "aljazeera", "reuters"],
    "arabic": ["bbc_arabic", "aljazeera"],
}


def fetch_rss(feed_url: str, max_items: int = 5, timeout: int = 15) -> List[Dict]:
    """
    جلب أخبار من RSS feed واحد
    يُرجع قائمة من العناصر: title, link, description, pubDate
    """
    try:
        headers = {
            "User-Agent": "Army81-NewsBot/1.0 (AI Research Agent)"
        }
        resp = requests.get(feed_url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = []

        # RSS 2.0 format
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub_date = item.findtext("pubDate", "").strip()

            if title:
                # تنظيف HTML tags من الوصف
                desc = _strip_html(desc)
                if len(desc) > 300:
                    desc = desc[:300] + "..."

                items.append({
                    "title": title,
                    "link": link,
                    "description": desc,
                    "pub_date": pub_date,
                })

            if len(items) >= max_items:
                break

        # Atom format fallback
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                title = entry.findtext("atom:title", "", ns).strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                desc = entry.findtext("atom:summary", "", ns).strip()
                pub_date = entry.findtext("atom:published", "", ns).strip()

                if title:
                    desc = _strip_html(desc)
                    if len(desc) > 300:
                        desc = desc[:300] + "..."
                    items.append({
                        "title": title,
                        "link": link,
                        "description": desc,
                        "pub_date": pub_date,
                    })

                if len(items) >= max_items:
                    break

        return items

    except ET.ParseError as e:
        logger.warning(f"RSS parse error for {feed_url}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.warning(f"RSS fetch error for {feed_url}: {e}")
        return []
    except Exception as e:
        logger.warning(f"RSS unexpected error for {feed_url}: {e}")
        return []


def fetch_news_rss(topic: str = "tech", max_items: int = 10) -> str:
    """
    جلب أخبار من RSS feeds حسب الموضوع
    المواضيع المدعومة: ai, tech, science, economy, world, arabic
    """
    topic_lower = topic.lower().strip()

    # تحديد الـ feeds المناسبة
    feed_keys = TOPIC_FEEDS.get(topic_lower, [])

    # إذا لم يطابق موضوعاً محدداً، جرّب البحث بالكلمات
    if not feed_keys:
        for key, feeds in TOPIC_FEEDS.items():
            if key in topic_lower or topic_lower in key:
                feed_keys = feeds
                break

    # fallback: استخدم أخبار التقنية والعالم
    if not feed_keys:
        feed_keys = ["techcrunch", "reuters", "bbc_tech"]

    all_items = []
    for key in feed_keys:
        if key in RSS_FEEDS:
            items = fetch_rss(RSS_FEEDS[key], max_items=3)
            for item in items:
                item["source"] = key
            all_items.extend(items)

        if len(all_items) >= max_items:
            break

    if not all_items:
        return f"لم يتم العثور على أخبار حول: {topic}"

    # تنسيق النتائج
    results = []
    for item in all_items[:max_items]:
        source = item.get("source", "unknown")
        date = item.get("pub_date", "")[:25] if item.get("pub_date") else ""
        results.append(
            f"**{item['title']}**\n"
            f"{item['description']}\n"
            f"المصدر: {source} — {date}\n"
            f"الرابط: {item['link']}"
        )

    return "\n\n---\n\n".join(results)


def fetch_news_api(topic: str = "artificial intelligence", lang: str = "en",
                   max_items: int = 5) -> str:
    """
    جلب أخبار عبر NewsAPI.org
    يتطلب NEWSAPI_KEY في متغيرات البيئة
    """
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        return ""

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "language": lang,
        "sortBy": "publishedAt",
        "pageSize": max_items,
        "apiKey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("articles", [])
        if not articles:
            return ""

        results = []
        for art in articles[:max_items]:
            source_name = art.get("source", {}).get("name", "")
            pub_date = art.get("publishedAt", "")[:10]
            results.append(
                f"**{art.get('title', '')}**\n"
                f"{art.get('description', '')}\n"
                f"المصدر: {source_name} — {pub_date}\n"
                f"الرابط: {art.get('url', '')}"
            )

        return "\n\n---\n\n".join(results)

    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return ""


def fetch_news_headlines(country: str = "us", category: str = "technology",
                         max_items: int = 5) -> str:
    """
    جلب عناوين الأخبار الرئيسية عبر NewsAPI
    يتطلب NEWSAPI_KEY
    """
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        return fetch_news_rss("tech", max_items)

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": country,
        "category": category,
        "pageSize": max_items,
        "apiKey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("articles", [])
        if not articles:
            return f"لا توجد عناوين رئيسية لـ {category} في {country}"

        results = []
        for art in articles[:max_items]:
            source_name = art.get("source", {}).get("name", "")
            results.append(
                f"**{art.get('title', '')}**\n"
                f"{art.get('description', '')}\n"
                f"المصدر: {source_name}"
            )

        return "\n\n---\n\n".join(results)

    except Exception as e:
        logger.error(f"NewsAPI headlines error: {e}")
        return fetch_news_rss("tech", max_items)


def fetch_news(topic: str = "artificial intelligence", lang: str = "ar",
               max_items: int = 10) -> str:
    """
    الدالة الرئيسية — جمع أخبار من كل المصادر المتاحة
    ترتيب الأولوية:
    1. NewsAPI (إذا كان المفتاح متاحاً)
    2. RSS feeds (دائماً متاح)
    3. دمج النتائج
    """
    all_results = []

    # 1. NewsAPI
    api_result = fetch_news_api(topic, lang, max_items=max_items // 2)
    if api_result:
        all_results.append("## أخبار من NewsAPI:\n" + api_result)

    # 2. RSS feeds — تحديد الموضوع
    rss_topic = _map_topic_to_rss(topic)
    rss_result = fetch_news_rss(rss_topic, max_items=max_items // 2)
    if rss_result and "لم يتم العثور" not in rss_result:
        all_results.append("## أخبار من RSS:\n" + rss_result)

    if not all_results:
        return f"لا توجد أخبار حول: {topic}"

    return "\n\n" + "\n\n".join(all_results)


def list_available_feeds() -> str:
    """عرض قائمة RSS feeds المتاحة"""
    lines = ["## مصادر الأخبار المتاحة (RSS):\n"]
    for key, url in RSS_FEEDS.items():
        lines.append(f"- **{key}**: {url[:60]}...")
    lines.append(f"\n## المواضيع المدعومة:")
    for topic, feeds in TOPIC_FEEDS.items():
        lines.append(f"- **{topic}**: {', '.join(feeds)}")
    return "\n".join(lines)


# ── دوال مساعدة ──────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """إزالة HTML tags من النص"""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"&[a-z]+;", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _map_topic_to_rss(topic: str) -> str:
    """تحويل موضوع حر إلى تصنيف RSS"""
    topic_lower = topic.lower()
    mappings = {
        "ai": ["ai", "artificial intelligence", "ذكاء اصطناعي", "machine learning", "deep learning", "تعلم آلي"],
        "tech": ["tech", "technology", "تقنية", "تكنولوجيا", "software", "برمجة", "حاسوب"],
        "science": ["science", "علوم", "فيزياء", "كيمياء", "أحياء", "research", "بحث"],
        "economy": ["economy", "اقتصاد", "finance", "مالي", "سوق", "أسهم", "market", "trade"],
        "world": ["world", "عالم", "politics", "سياسة", "حرب", "war", "conflict"],
        "arabic": ["arabic", "عربي", "شرق أوسط", "middle east"],
    }
    for rss_topic, keywords in mappings.items():
        if any(kw in topic_lower for kw in keywords):
            return rss_topic
    return "tech"


# ── للاختبار المباشر ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("اختبار news_fetcher.py")
    print("=" * 60)

    print("\n--- اختبار RSS (تقنية) ---")
    result = fetch_news_rss("tech", max_items=3)
    print(result[:500] if result else "لا نتائج")

    print("\n--- اختبار RSS (علوم) ---")
    result = fetch_news_rss("science", max_items=3)
    print(result[:500] if result else "لا نتائج")

    print("\n--- اختبار fetch_news الشامل ---")
    result = fetch_news("artificial intelligence", max_items=5)
    print(result[:500] if result else "لا نتائج")

    print("\n--- المصادر المتاحة ---")
    print(list_available_feeds())
