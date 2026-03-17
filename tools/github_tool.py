"""
Army81 Tools - GitHub Tool
رصد المستودعات والمشاريع مفتوحة المصدر
"""
import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("army81.tools.github")

GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    token = os.getenv("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def search_repos(query: str, sort: str = "stars", max_results: int = 5) -> str:
    """
    البحث في GitHub عن مستودعات
    sort: stars | updated | forks
    """
    valid_sorts = {"stars", "updated", "forks"}
    if sort not in valid_sorts:
        sort = "stars"

    url = f"{GITHUB_API}/search/repositories"
    params = {
        "q": query,
        "sort": sort,
        "order": "desc",
        "per_page": min(max_results, 10),
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=15)

        if resp.status_code == 403:
            return "خطأ: تجاوزت حد الطلبات. أضف GITHUB_TOKEN في .env لزيادة الحد."

        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return f"لم تُوجد مستودعات لـ: {query}"

        results = []
        for repo in items:
            lang = repo.get("language") or "غير محدد"
            results.append(
                f"**{repo['full_name']}** ⭐ {repo['stargazers_count']:,}\n"
                f"{repo.get('description') or 'بدون وصف'}\n"
                f"اللغة: {lang} | آخر تحديث: {repo['updated_at'][:10]}\n"
                f"🔗 {repo['html_url']}"
            )

        total = data.get("total_count", 0)
        header = f"نتائج البحث عن '{query}' (إجمالي {total:,} مستودع):\n\n"
        return header + "\n\n---\n\n".join(results)

    except Exception as e:
        logger.error(f"GitHub search error: {e}")
        return f"خطأ في البحث على GitHub: {e}"


def get_repo_info(owner: str, repo: str) -> str:
    """معلومات تفصيلية عن مستودع معين"""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
        r = resp.json()

        return (
            f"**{r['full_name']}**\n"
            f"{r.get('description') or 'بدون وصف'}\n\n"
            f"⭐ النجوم: {r['stargazers_count']:,}\n"
            f"🍴 Forks: {r['forks_count']:,}\n"
            f"🐛 Issues مفتوحة: {r['open_issues_count']}\n"
            f"اللغة: {r.get('language') or 'غير محدد'}\n"
            f"الرخصة: {r.get('license', {}).get('name', 'غير محدد') if r.get('license') else 'غير محدد'}\n"
            f"آخر تحديث: {r['updated_at'][:10]}\n"
            f"🔗 {r['html_url']}"
        )

    except Exception as e:
        logger.error(f"GitHub repo info error: {e}")
        return f"خطأ في جلب معلومات {owner}/{repo}: {e}"


def get_trending(language: str = "", period: str = "daily") -> str:
    """
    الحصول على المستودعات الرائجة
    (يستخدم البحث كبديل لـ trending API غير الرسمي)
    """
    query = "stars:>100"
    if language:
        query += f" language:{language}"

    return search_repos(query, sort="stars", max_results=5)


def search_code(query: str, language: str = "") -> str:
    """البحث في كود GitHub"""
    q = query
    if language:
        q += f" language:{language}"

    url = f"{GITHUB_API}/search/code"
    params = {"q": q, "per_page": 5}

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=15)

        if resp.status_code == 403:
            return "خطأ: البحث في الكود يتطلب GITHUB_TOKEN. أضفه في .env"

        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return f"لم يُوجد كود لـ: {query}"

        results = []
        for item in items:
            results.append(
                f"**{item['name']}** في {item['repository']['full_name']}\n"
                f"🔗 {item['html_url']}"
            )

        return "\n\n".join(results)

    except Exception as e:
        logger.error(f"GitHub code search error: {e}")
        return f"خطأ في البحث: {e}"


if __name__ == "__main__":
    print("اختبار github_tool...")
    print(search_repos("AI agent framework python", max_results=3))
