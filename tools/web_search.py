"""
Army81 Tools - Web Search
بحث حقيقي على الإنترنت
"""
import os
import logging
import requests
from typing import List, Dict

logger = logging.getLogger("army81.tools.search")


def web_search(query: str, num_results: int = 5) -> str:
    """
    بحث على الإنترنت — ترتيب الأولوية:
    1. LangSearch (أعمق — يعطي محتوى كامل)
    2. Serper (أسرع — Google results)
    3. Google CSE (بديل)
    """
    # 1. LangSearch أولاً (بحث عميق مع محتوى)
    langsearch_key = os.getenv("LANGSEARCH_API_KEY", "")
    if langsearch_key:
        result = _search_langsearch(query, num_results, langsearch_key)
        if result and "خطأ" not in result:
            return result

    # 2. Serper (أسرع)
    serper_key = os.getenv("SERPER_API_KEY", "")
    if serper_key:
        return _search_serper(query, num_results, serper_key)

    # 3. Google Custom Search
    google_key = os.getenv("GOOGLE_API_KEY", "")
    cse_id = os.getenv("GOOGLE_CSE_ID", "")
    if google_key and cse_id:
        return _search_google_cse(query, num_results, google_key, cse_id)

    return "خطأ: لا يوجد مفتاح API للبحث. أضف LANGSEARCH_API_KEY أو SERPER_API_KEY في .env"


def _search_langsearch(query: str, num: int, api_key: str) -> str:
    """
    بحث عبر LangSearch API — يعطي محتوى كامل للصفحات
    أفضل للوكلاء لأنه يوفر سياقاً أعمق
    """
    url = "https://api.langsearch.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "count": min(num, 10),
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        results = []
        # LangSearch response: data.webPages.value[]
        web_pages = data.get("data", {})
        if isinstance(web_pages, dict):
            items = web_pages.get("webPages", {}).get("value", [])
        else:
            items = data.get("results", [])

        for item in items[:num]:
            title = item.get("name", item.get("title", ""))
            snippet = item.get("snippet", item.get("summary", ""))
            link = item.get("url", item.get("link", ""))
            # LangSearch يعطي محتوى أطول — اقتطع بذكاء
            if len(snippet) > 500:
                snippet = snippet[:500] + "..."
            results.append(
                f"**{title}**\n"
                f"{snippet}\n"
                f"المصدر: {link}"
            )

        if not results:
            return "لم تُوجد نتائج من LangSearch"

        return "\n\n---\n\n".join(results)

    except requests.exceptions.HTTPError as e:
        logger.warning(f"LangSearch HTTP error: {e}")
        return f"خطأ LangSearch: {e}"
    except Exception as e:
        logger.warning(f"LangSearch error: {e}")
        return f"خطأ في LangSearch: {e}"


def deep_search(query: str, num_results: int = 5) -> str:
    """
    بحث عميق — يستخدم LangSearch للحصول على محتوى كامل
    مخصص للوكلاء الذين يحتاجون سياقاً غنياً (A04, A60, A01)
    """
    langsearch_key = os.getenv("LANGSEARCH_API_KEY", "")
    if langsearch_key:
        return _search_langsearch(query, num_results, langsearch_key)
    # fallback
    return web_search(query, num_results)


def _search_serper(query: str, num: int, api_key: str) -> str:
    """بحث عبر Serper.dev"""
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": num, "gl": "us", "hl": "ar"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic", [])[:num]:
            results.append(
                f"**{item.get('title', '')}**\n"
                f"{item.get('snippet', '')}\n"
                f"المصدر: {item.get('link', '')}"
            )

        if not results:
            return "لم تُوجد نتائج"

        return "\n\n---\n\n".join(results)

    except Exception as e:
        logger.error(f"Serper search error: {e}")
        return f"خطأ في البحث: {e}"


def _search_google_cse(query: str, num: int, api_key: str, cse_id: str) -> str:
    """بحث عبر Google Custom Search Engine"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": min(num, 10),
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("items", []):
            results.append(
                f"**{item.get('title', '')}**\n"
                f"{item.get('snippet', '')}\n"
                f"المصدر: {item.get('link', '')}"
            )

        return "\n\n---\n\n".join(results) if results else "لم تُوجد نتائج"

    except Exception as e:
        logger.error(f"Google CSE error: {e}")
        return f"خطأ في البحث: {e}"


def fetch_news(topic: str = "artificial intelligence", lang: str = "ar") -> str:
    """
    جمع أخبار حديثة حول موضوع معين
    يستخدم NewsAPI إذا كان مفتاحه متاحاً، وإلا يبحث عبر Serper
    """
    news_key = os.getenv("NEWSAPI_KEY", "")

    if news_key:
        return _fetch_newsapi(topic, lang, news_key)
    else:
        # استخدم البحث العادي كبديل
        return web_search(f"أخبار {topic} اليوم", num_results=5)


def _fetch_newsapi(topic: str, lang: str, api_key: str) -> str:
    """جمع أخبار عبر NewsAPI.org"""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "language": lang,
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("articles", [])
        if not articles:
            return f"لا توجد أخبار حول: {topic}"

        results = []
        for art in articles[:5]:
            results.append(
                f"**{art.get('title', '')}**\n"
                f"{art.get('description', '')}\n"
                f"المصدر: {art.get('source', {}).get('name', '')} — {art.get('publishedAt', '')[:10]}"
            )

        return "\n\n---\n\n".join(results)

    except Exception as e:
        return f"خطأ في جلب الأخبار: {e}"


# للاختبار المباشر
if __name__ == "__main__":
    print("اختبار البحث...")
    result = web_search("أحدث تطورات الذكاء الاصطناعي 2026")
    print(result)
