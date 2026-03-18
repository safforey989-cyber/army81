"""Army81 Skill — Web Scraper"""
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("army81.skill.web_scraper")


def scrape_url(url: str, max_chars: int = 3000) -> str:
    """يجلب محتوى صفحة ويب ويستخرج النص"""
    try:
        headers = {"User-Agent": "Army81-Bot/1.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # أزل العناصر غير المفيدة
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # نظّف الأسطر الفارغة
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        clean = "\n".join(lines)
        return clean[:max_chars]
    except Exception as e:
        return f"خطأ في جلب الصفحة: {e}"


def scrape_links(url: str) -> str:
    """يستخرج كل الروابط من صفحة"""
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)[:50]
            if href.startswith("http"):
                links.append(f"- [{text}]({href})")
        return "\n".join(links[:30]) or "لا توجد روابط"
    except Exception as e:
        return f"خطأ: {e}"
