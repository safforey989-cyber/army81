"""
Army81 — Evolution Runner (24/7)
يشغّل التطور الأُسّي المستمر — كل 6 ساعات دورة جديدة
"""
import os
import sys
import time
import logging
import requests
from datetime import datetime

# تحميل .env دائماً
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [army81.evolver] %(levelname)s: %(message)s')
logger = logging.getLogger("army81.evolver")

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")
CYCLE_HOURS = 2  # كل دورة ساعتين
PAUSE_HOURS = 4  # استراحة 4 ساعات بين الدورات


def wait_for_gateway(timeout=300):
    """انتظر حتى يعمل Gateway"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{GATEWAY}/health", timeout=5)
            if r.status_code == 200:
                logger.info("✅ Gateway ready")
                return True
        except Exception:
            pass
        time.sleep(5)
    logger.error("❌ Gateway not available")
    return False


def run_evolution_cycle():
    """شغّل دورة تطور أُسّي"""
    logger.info(f"🚀 Starting evolution cycle — {CYCLE_HOURS}h")
    try:
        r = requests.post(f"{GATEWAY}/evolution/exponential/start",
                         json={"duration_hours": CYCLE_HOURS}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            logger.info(f"✅ Evolution started: {data}")
            return True
        else:
            logger.warning(f"⚠️ Evolution start failed: {r.status_code} {r.text[:200]}")
            # Fallback: try hyper swarm
            r2 = requests.post(f"{GATEWAY}/hyper/start",
                              json={"duration_hours": CYCLE_HOURS}, timeout=30)
            if r2.status_code == 200:
                logger.info(f"✅ Hyper swarm started as fallback: {r2.json()}")
                return True
    except Exception as e:
        logger.error(f"❌ Evolution error: {e}")
    return False


def send_telegram_report():
    """أرسل تقرير التطور على Telegram"""
    try:
        # Get stats
        r = requests.get(f"{GATEWAY}/evolution/exponential/stats", timeout=10)
        if r.status_code == 200:
            stats = r.json()
            token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
            if token and chat_id:
                msg = f"""📊 *تقرير التطور الذاتي*
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔄 الدورات: {stats.get('cycle_count', 0)}
📈 المضاعف: {stats.get('multiplier', 1)}x
🧪 التجارب: {stats.get('total_experiments', 0)}
📚 المعرفة: {stats.get('total_knowledge', 0)}
🛠️ المهارات: {stats.get('total_skills', 0)}
🎓 التقطير: {stats.get('total_distillations', 0)}
⚔️ المعارك: {stats.get('total_battles', 0)}
💡 الاختراعات: {stats.get('total_inventions', 0)}"""
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                             json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
                logger.info("📱 Telegram report sent")
    except Exception as e:
        logger.warning(f"Telegram report failed: {e}")


def run_adversarial_test():
    """Layer 3: اختبار عدائي — A74 ينقد آخر 10 إجابات"""
    import json
    from pathlib import Path
    logger.info("⚔️ Running adversarial quality test...")

    try:
        # جلب آخر 10 حلقات من الذاكرة
        import sqlite3
        db = Path("workspace/episodic_memory.db")
        if not db.exists():
            return

        conn = sqlite3.connect(str(db))
        rows = conn.execute(
            "SELECT agent_id, task_summary, result_summary FROM episodes "
            "ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        conn.close()

        if not rows:
            return

        # A74 (ضبط الجودة) ينقد كل إجابة
        critiques = []
        for agent_id, task, result in rows:
            if not result or len(result) < 50:
                continue
            critique_task = f"""كناقد جودة، حلّل هذه الإجابة:

السؤال: {task[:200]}
الإجابة: {result[:500]}

اكتب نقداً موجزاً (3 أسطر):
1. ما الصحيح؟
2. ما الخطأ المحتمل؟
3. كيف تُحسَّن؟"""

            try:
                r = requests.post(f"{GATEWAY}/task", json={
                    "task": critique_task,
                    "preferred_agent": "A74"
                }, timeout=60)
                if r.ok:
                    critique = r.json().get("result", "")
                    critiques.append({
                        "agent": agent_id,
                        "task": task[:100],
                        "critique": critique[:500],
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception:
                pass

        # حفظ النقد
        if critiques:
            log_dir = Path("workspace/adversarial_log")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"adversarial_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            log_file.write_text(json.dumps(critiques, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"📝 Adversarial test: {len(critiques)} critiques saved")

    except Exception as e:
        logger.warning(f"Adversarial test failed: {e}")


def main():
    logger.info("🧬 Army81 Evolution Runner starting...")

    if not wait_for_gateway():
        logger.error("Cannot start without gateway")
        sys.exit(1)

    cycle = 0
    while True:
        cycle += 1
        logger.info(f"\n{'='*50}")
        logger.info(f"🔄 Evolution Cycle {cycle}")
        logger.info(f"{'='*50}")

        # شغّل دورة التطور
        success = run_evolution_cycle()

        if success:
            # انتظر حتى تنتهي الدورة
            logger.info(f"⏳ Waiting {CYCLE_HOURS}h for cycle to complete...")
            time.sleep(CYCLE_HOURS * 3600 + 60)  # +1 min buffer

            # أرسل تقرير
            send_telegram_report()

            # Layer 3: اختبار عدائي كل 3 دورات
            if cycle % 3 == 0:
                run_adversarial_test()

        # استراحة أقصر لمضاعفة السرعة (ساعة بدل 4)
        rest = max(1, PAUSE_HOURS - cycle)  # تتناقص مع كل دورة
        logger.info(f"😴 Resting {rest}h before next cycle...")
        time.sleep(rest * 3600)


if __name__ == "__main__":
    main()
