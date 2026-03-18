"""Army81 Skill — Image Analyzer"""
import os
import base64
import logging
import requests

logger = logging.getLogger("army81.skill.image_analyzer")


def analyze_image(image_path: str) -> str:
    """
    تحليل صورة باستخدام Gemini Vision API
    يحتاج: GOOGLE_API_KEY في .env
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return "خطأ: GOOGLE_API_KEY غير موجود"

    if not os.path.exists(image_path):
        return f"الصورة غير موجودة: {image_path}"

    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # تحديد نوع الصورة
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
        mime = mime_map.get(ext, "image/jpeg")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "صف هذه الصورة بالتفصيل بالعربية. ما الذي تراه؟"},
                    {"inline_data": {"mime_type": mime, "data": image_data}},
                ]
            }]
        }

        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            result = r.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        else:
            return f"خطأ من Gemini API: {r.status_code}"
    except Exception as e:
        return f"خطأ في تحليل الصورة: {e}"


def image_info(image_path: str) -> str:
    """معلومات أساسية عن الصورة"""
    if not os.path.exists(image_path):
        return f"الصورة غير موجودة: {image_path}"

    size = os.path.getsize(image_path)
    ext = os.path.splitext(image_path)[1]
    return f"الملف: {os.path.basename(image_path)}\nالنوع: {ext}\nالحجم: {size/1024:.1f} KB"
