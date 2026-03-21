"""
Army81 - Web Search Tool
أداة للبحث في الإنترنت باستخدام Serper API أو Google Custom Search
"""

import os
import json
import requests
import urllib.parse
import logging
from typing import Dict, Any

from core.base_agent import Tool

logger = logging.getLogger("army81.tools.web_search")

def search_web(query: str, num_results: int = 5) -> str:
    """
    يبحث في الإنترنت عن الكلمات المفتاحية المطلوبة باستخدام Serper API كمفضل،
    أو Google Custom Search كبديل، ويعيد ملخصاً نصياً بالنتائج.
    
    Args:
        query (str): جملة البحث أو الكلمات المفتاحية
        num_results (int): عدد النتائج المطلوبة (الافتراضي 5)
        
    Returns:
        str: نص منسق يحتوي على أهم نتائج البحث ومقتطفاتها (Snippets)
    """
    
    serper_api_key = os.getenv("SERPER_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if serper_api_key:
        return _search_serper(query, serper_api_key, num_results)
    
    if google_api_key and google_cse_id:
        return _search_google(query, google_api_key, google_cse_id, num_results)
        
    return "خطأ: لم يتم العثور على مفاتيح API للبحث (SERPER_API_KEY أو GOOGLE_API_KEY/GOOGLE_CSE_ID) في البيئة."

def _search_serper(query: str, api_key: str, num_results: int) -> str:
    """Implement search using Serper.dev API"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": num_results,
        "hl": "ar"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("organic", [])
        if not results:
            return "لم يتم العثور على نتائج مفيدة لهذا البحث."
            
        formatted_results = [f"نتائج بحث (Serper) لـ '{query}':\n"]
        for idx, res in enumerate(results[:num_results], 1):
            title = res.get("title", "بدون عنوان")
            snippet = res.get("snippet", "لا يوجد وصف متاح للاستعراض")
            link = res.get("link", "#")
            formatted_results.append(f"{idx}. {title}\nالمقتطف: {snippet}\nالرابط: {link}\n")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"فشل البحث عبر Serper: {e}")
        return f"خطأ أثناء جلب نتائج البحث من Serper: {str(e)}"

def _search_google(query: str, api_key: str, cse_id: str, num_results: int) -> str:
    """Implement search using Google Custom Search API"""
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={urllib.parse.quote(query)}&key={api_key}&cx={cse_id}&num={num_results}&hl=ar"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("items", [])
        if not items:
            return "لم يتم العثور على نتائج مفيدة لهذا البحث."
            
        formatted_results = [f"نتائج بحث (Google) لـ '{query}':\n"]
        for idx, item in enumerate(items[:num_results], 1):
            title = item.get("title", "بدون عنوان")
            snippet = item.get("snippet", "لا يوجد وصف متاح للاستعراض")
            link = item.get("link", "#")
            formatted_results.append(f"{idx}. {title}\nالمقتطف: {snippet}\nالرابط: {link}\n")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"فشل البحث عبر Google: {e}")
        return f"خطأ أثناء جلب نتائج البحث من Google: {str(e)}"

# تعريف الأداة لنظام Army81
web_search_tool = Tool(
    name="web_search",
    description="أداة للبحث في الإنترنت عن أحدث المعلومات والمقالات باستخدام كلمات مفتاحية.",
    func=search_web,
    parameters={
        "query": "الكلمات المفتاحية للبحث (نص/String)",
        "num_results": "(اختياري) عدد النتائج المطلوبة كحد أقصى (رقم بحد أقصى 10)"
    }
)
