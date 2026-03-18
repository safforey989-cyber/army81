"""
Army81 Tools — Perplexity Search
بحث أكاديمي عميق مع استشهادات — للمهام البحثية الجادة
"""
import os
import logging
import requests

logger = logging.getLogger("army81.tools.perplexity")


def research(query: str, detail: str = "detailed") -> str:
    """
    بحث أكاديمي عبر Perplexity API
    يعطي إجابة مع استشهادات ومصادر
    """
    api_key = os.getenv("PERPLEXITY_API_KEY", "")
    if not api_key:
        return "خطأ: PERPLEXITY_API_KEY غير موجود في .env"

    try:
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": "أنت باحث أكاديمي دقيق. أجب بالعربية مع ذكر المصادر والاستشهادات. قدم تحليلاً معمقاً."},
                    {"role": "user", "content": query},
                ],
                "max_tokens": 2000,
                "return_citations": True,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])

        result = content
        if citations:
            result += "\n\n## المصادر:\n"
            for i, cite in enumerate(citations[:10], 1):
                if isinstance(cite, str):
                    result += f"{i}. {cite}\n"
                elif isinstance(cite, dict):
                    result += f"{i}. {cite.get('url', cite.get('title', ''))}\n"

        return result

    except Exception as e:
        logger.error(f"Perplexity error: {e}")
        return f"خطأ Perplexity: {e}"


def quick_answer(query: str) -> str:
    """إجابة سريعة بدون تفاصيل"""
    api_key = os.getenv("PERPLEXITY_API_KEY", "")
    if not api_key:
        return "خطأ: PERPLEXITY_API_KEY غير موجود"

    try:
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [
                    {"role": "user", "content": query},
                ],
                "max_tokens": 500,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("choices", [{}])[0].get("message", {}).get("content", "لا إجابة")
    except Exception as e:
        return f"خطأ: {e}"
