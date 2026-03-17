"""
Army81 Tools - Tavily Deep Search
بحث عميق مع تلخيص تلقائي - مُحسَّن للوكلاء
"""
import os
import requests
import logging

logger = logging.getLogger("army81.tools.tavily")


def deep_search(query: str, search_depth: str = "basic") -> str:
    """
    بحث عميق عبر Tavily API
    search_depth: "basic" (سريع) أو "advanced" (معمّق)
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return "خطأ: TAVILY_API_KEY غير موجود في .env"

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": False,
        "max_results": 5,
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        output = []

        # الإجابة المباشرة إذا وُجدت
        if data.get("answer"):
            output.append(f"## الإجابة المباشرة:\n{data['answer']}\n")

        # النتائج التفصيلية
        output.append("## المصادر:")
        for r in data.get("results", []):
            output.append(
                f"**{r.get('title', '')}**\n"
                f"{r.get('content', '')[:300]}...\n"
                f"المصدر: {r.get('url', '')}"
            )

        return "\n\n---\n\n".join(output)

    except Exception as e:
        logger.error(f"Tavily error: {e}")
        return f"خطأ في البحث العميق: {e}"


if __name__ == "__main__":
    result = deep_search("latest AI agent frameworks 2026")
    print(result)
