"""
Army81 Tools - arXiv + Wikipedia + Finance
أدوات مجانية لا تحتاج مفاتيح API
"""
import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

logger = logging.getLogger("army81.tools")


# ── arXiv ─────────────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 5) -> str:
    """البحث في أحدث الأبحاث العلمية"""
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            summary = entry.find("atom:summary", ns).text.strip()[:300]
            link = entry.find("atom:id", ns).text.strip()
            published = entry.find("atom:published", ns).text[:10]

            results.append(
                f"**{title}** ({published})\n{summary}...\n🔗 {link}"
            )

        return "\n\n---\n\n".join(results) if results else "لم تُوجد نتائج"

    except Exception as e:
        logger.error(f"arXiv error: {e}")
        return f"خطأ في البحث: {e}"


# ── Wikipedia ─────────────────────────────────────────────

def search_wikipedia(query: str, lang: str = "ar") -> str:
    """البحث في Wikipedia"""
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(query)}"

    try:
        resp = requests.get(url, timeout=15,
                          headers={"User-Agent": "Army81/1.0"})
        if resp.status_code == 404:
            # جرب بالإنجليزية
            url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query)}"
            resp = requests.get(url_en, timeout=15,
                              headers={"User-Agent": "Army81/1.0"})

        resp.raise_for_status()
        data = resp.json()

        return (
            f"**{data.get('title', '')}**\n\n"
            f"{data.get('extract', 'لا معلومات متاحة')}\n\n"
            f"🔗 {data.get('content_urls', {}).get('desktop', {}).get('page', '')}"
        )

    except Exception as e:
        logger.error(f"Wikipedia error: {e}")
        return f"خطأ: {e}"


# ── Yahoo Finance ─────────────────────────────────────────

def get_market_data(symbol: str) -> str:
    """بيانات سوق مالي (سهم، عملة، مؤشر)"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        meta = data["chart"]["result"][0]["meta"]
        return (
            f"**{meta.get('longName', symbol)}** ({symbol})\n"
            f"السعر الحالي: {meta.get('regularMarketPrice', 'N/A')}\n"
            f"التغيير: {meta.get('regularMarketChangePercent', 0):.2f}%\n"
            f"أعلى 52 أسبوع: {meta.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"أدنى 52 أسبوع: {meta.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"العملة: {meta.get('currency', 'USD')}"
        )

    except Exception as e:
        logger.error(f"Finance error [{symbol}]: {e}")
        return f"خطأ في جلب بيانات {symbol}: {e}"


# ── PubMed ─────────────────────────────────────────────────

def search_pubmed(query: str, max_results: int = 5) -> str:
    """البحث في الأبحاث الطبية على PubMed (مجاني)"""
    # أولاً: جلب IDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "date",
    }

    try:
        resp = requests.get(search_url, params=params, timeout=20)
        resp.raise_for_status()
        ids = resp.json()["esearchresult"]["idlist"]

        if not ids:
            return "لم تُوجد نتائج طبية"

        # ثانياً: جلب تفاصيل
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
        }
        resp2 = requests.get(fetch_url, params=fetch_params, timeout=20)
        resp2.raise_for_status()

        root = ET.fromstring(resp2.text)
        results = []

        for article in root.findall(".//PubmedArticle")[:max_results]:
            title_el = article.find(".//ArticleTitle")
            abstract_el = article.find(".//AbstractText")
            pmid_el = article.find(".//PMID")

            title = title_el.text if title_el is not None else "بدون عنوان"
            abstract = abstract_el.text[:300] if abstract_el is not None else "لا ملخص"
            pmid = pmid_el.text if pmid_el is not None else ""

            results.append(
                f"**{title}**\n{abstract}...\n"
                f"🔗 https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            )

        return "\n\n---\n\n".join(results)

    except Exception as e:
        logger.error(f"PubMed error: {e}")
        return f"خطأ في البحث الطبي: {e}"


if __name__ == "__main__":
    print("=== arXiv ===")
    print(search_arxiv("large language models agents 2025", 2))
    print("\n=== Wikipedia ===")
    print(search_wikipedia("ذكاء اصطناعي"))
    print("\n=== Finance ===")
    print(get_market_data("GOOGL"))
