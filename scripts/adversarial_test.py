"""
Army81 Adversarial Test — A74 يراجع إجابات الوكلاء ويكتشف الأخطاء
يُشغّل أسبوعياً أو يدوياً
"""
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [adversarial] %(message)s")
log = logging.getLogger()

WORKSPACE = Path(__file__).parent.parent / "workspace"
DB_PATH = WORKSPACE / "episodic_memory.db"
LOG_DIR = WORKSPACE / "adversarial_log"


def get_recent_episodes(limit: int = 10):
    """جلب آخر 10 إجابات ناجحة"""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("""
        SELECT agent_id, task_summary, result_summary, rating, created_at
        FROM episodes WHERE success=1
        ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [{"agent": r[0], "task": r[1], "result": r[2][:500], "rating": r[3], "time": r[4]} for r in rows]


def adversarial_review(episodes: list) -> list:
    """A74 يراجع كل إجابة ويحدد الأخطاء المحتملة"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from core.llm_client import LLMClient

        client = LLMClient("gemini-flash")
        reviews = []

        for ep in episodes:
            prompt = f"""أنت مراجع جودة صارم. راجع هذه الإجابة وحدد:
1. هل تحتوي على معلومات خاطئة؟
2. هل هناك افتراضات غير مبررة؟
3. هل الإجابة كاملة أم ناقصة؟
4. تقييمك: ممتاز / جيد / يحتاج تحسين / ضعيف

المهمة: {ep['task'][:200]}
الإجابة: {ep['result'][:400]}

اكتب مراجعتك في 3 أسطر فقط."""

            result = client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=300)
            review_text = result.get("content", "فشل المراجعة")

            reviews.append({
                "agent": ep["agent"],
                "task": ep["task"][:100],
                "rating_before": ep["rating"],
                "review": review_text,
                "timestamp": datetime.now().isoformat()
            })
            log.info(f"  Reviewed {ep['agent']}: {review_text[:80]}...")

        return reviews
    except Exception as e:
        log.error(f"Review failed: {e}")
        return []


def save_reviews(reviews: list):
    """حفظ المراجعات"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    filename = LOG_DIR / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filename.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"✅ Saved {len(reviews)} reviews to {filename.name}")
    return str(filename)


if __name__ == "__main__":
    log.info("⚔️ Army81 Adversarial Review Starting...")

    episodes = get_recent_episodes(10)
    log.info(f"Found {len(episodes)} recent episodes to review")

    if episodes:
        reviews = adversarial_review(episodes)
        if reviews:
            save_reviews(reviews)
    else:
        log.info("No episodes to review")

    log.info("✅ Adversarial review complete")
