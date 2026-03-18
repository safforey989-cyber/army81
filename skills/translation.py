"""Army81 Skill — Translation"""
import os
import logging
import requests

logger = logging.getLogger("army81.skill.translation")


def translate(text: str, target_lang: str = "en", source_lang: str = "auto") -> str:
    """
    ترجمة نص باستخدام Gemini API
    يحتاج: GOOGLE_API_KEY في .env
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return "خطأ: GOOGLE_API_KEY غير موجود"

    lang_names = {
        "en": "English", "ar": "Arabic", "fr": "French",
        "es": "Spanish", "de": "German", "zh": "Chinese",
        "ja": "Japanese", "ko": "Korean", "ru": "Russian",
        "tr": "Turkish", "pt": "Portuguese", "it": "Italian",
    }
    target_name = lang_names.get(target_lang, target_lang)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Translate the following text to {target_name}. Only output the translation, nothing else:\n\n{text}"}]
            }]
        }

        r = requests.post(url, json=payload, timeout=20)
        if r.status_code == 200:
            result = r.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"خطأ: {r.status_code}"
    except Exception as e:
        return f"خطأ في الترجمة: {e}"


def detect_language(text: str) -> str:
    """كشف لغة النص"""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return "unknown"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"What language is this text written in? Reply with just the ISO 639-1 code (e.g., 'en', 'ar', 'fr'):\n\n{text[:200]}"}]
            }]
        }
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip().lower()[:2]
    except Exception:
        pass
    return "unknown"
