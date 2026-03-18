"""
Army81 — 24/7 Evolution Launcher
يشغل النظام بالكامل مع جدولة التطور الذاتي
"""
import sys
import os
import logging
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("army81.evolution_launcher")


def main():
    """إطلاق محرك التطور 24/7"""
    logger.info("🚀 إطلاق Army81 Evolution Engine 24/7")

    try:
        from core.awakening_protocol import MasterEvolutionEngine
        engine = MasterEvolutionEngine()
        logger.info(f"✅ محرك التطور جاهز — {len(engine.components)} مكون")

        # عرض المكونات
        for name in engine.components:
            logger.info(f"  🔧 {name}")

        # تشغيل دورة واحدة فوراً
        logger.info("🔄 تشغيل الدورة اليومية الأولى...")
        results = engine.run_daily_cycle()

        phases_done = len([p for p in results.get("phases", {}).values()
                          if isinstance(p, dict) and p.get("status") != "error"
                          or isinstance(p, dict) and "error" not in p])

        logger.info(f"✅ اكتملت الدورة الأولى — {phases_done} مراحل ناجحة")

        # عرض الإحصائيات
        stats = engine.get_full_stats()
        for comp, data in stats.get("components", {}).items():
            logger.info(f"  📊 {comp}: {data}")

        logger.info("🎯 النظام يعمل. للجدولة التلقائية شغّل: python scripts/daily_updater.py --schedule")

    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
