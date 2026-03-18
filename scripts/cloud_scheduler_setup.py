"""
Army81 - Cloud Scheduler Setup
إعداد Google Cloud Scheduler للتحديث اليومي الساعة 2 صباحاً
"""
import os
import json
import logging
import argparse
from datetime import datetime

logger = logging.getLogger("army81.scheduler")

# ── إعدادات Cloud Scheduler ─────────────────────────────────

SCHEDULER_JOBS = [
    {
        "name": "army81-daily-update",
        "description": "التحديث اليومي للمعرفة — arXiv + GitHub + NewsAPI",
        "schedule": "0 2 * * *",  # كل يوم الساعة 2 صباحاً
        "timezone": "Asia/Riyadh",
        "target_type": "http",
        "uri": "/task",
        "method": "POST",
        "body": {
            "task": "تحديث يومي: اجمع أحدث المعلومات من arXiv وGitHub وNewsAPI",
            "agent_id": "A75",  # وكيل تحسين النظام
        },
    },
    {
        "name": "army81-weekly-compress",
        "description": "الضغط الأسبوعي للذاكرة — كل أحد الساعة 4 صباحاً",
        "schedule": "0 4 * * 0",  # كل أحد الساعة 4 صباحاً
        "timezone": "Asia/Riyadh",
        "target_type": "http",
        "uri": "/task",
        "method": "POST",
        "body": {
            "task": "ضغط أسبوعي للذاكرة: لخّص أداء الأسبوع الماضي لكل الوكلاء",
            "agent_id": "A76",  # وكيل تجميع التعلم
        },
    },
    {
        "name": "army81-performance-check",
        "description": "فحص أداء الوكلاء — كل يوم الساعة 6 صباحاً",
        "schedule": "0 6 * * *",
        "timezone": "Asia/Riyadh",
        "target_type": "http",
        "uri": "/task",
        "method": "POST",
        "body": {
            "task": "فحص أداء: راجع إحصائيات كل الوكلاء وحدد من يحتاج تحسين",
            "agent_id": "A72",  # وكيل مراقبة التطور
        },
    },
    {
        "name": "army81-self-evolution",
        "description": "التطور الذاتي الأسبوعي — كل سبت الساعة 3 صباحاً",
        "schedule": "0 3 * * 6",  # كل سبت الساعة 3 صباحاً
        "timezone": "Asia/Riyadh",
        "target_type": "http",
        "uri": "/task",
        "method": "POST",
        "body": {
            "task": "تطور أسبوعي: حسّن أضعف 10 وكلاء بناءً على أدائهم",
            "agent_id": "A74",  # وكيل ضبط الجودة
        },
    },
]


def setup_cloud_scheduler():
    """إعداد Cloud Scheduler jobs عبر gcloud CLI"""
    project_id = os.getenv("GCP_PROJECT_ID", "")
    region = os.getenv("GCP_REGION", "me-central1")
    service_url = os.getenv("CLOUD_RUN_URL", "")

    if not project_id:
        print("خطأ: GCP_PROJECT_ID غير مُعرَّف في .env")
        return False

    if not service_url:
        print("خطأ: CLOUD_RUN_URL غير مُعرَّف (URL الخاص بـ Cloud Run)")
        return False

    print(f"\n{'='*60}")
    print(f"  إعداد Cloud Scheduler — {project_id}")
    print(f"{'='*60}\n")

    commands = []
    for job in SCHEDULER_JOBS:
        body_json = json.dumps(job["body"])
        cmd = (
            f"gcloud scheduler jobs create http {job['name']} "
            f"--project={project_id} "
            f"--location={region} "
            f'--schedule="{job["schedule"]}" '
            f"--time-zone={job['timezone']} "
            f"--uri={service_url}{job['uri']} "
            f"--http-method={job['method']} "
            f"--headers='Content-Type=application/json' "
            f"--body='{body_json}' "
            f'--description="{job["description"]}" '
            f"--attempt-deadline=300s"
        )
        commands.append(cmd)
        print(f"📅 {job['name']}: {job['schedule']} ({job['timezone']})")
        print(f"   {job['description']}")
        print()

    # إنشاء سكربت shell
    script_path = os.path.join(os.path.dirname(__file__), "setup_scheduler.sh")
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Army81 Cloud Scheduler Setup\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"PROJECT_ID={project_id}\n")
        f.write(f"REGION={region}\n")
        f.write(f"SERVICE_URL={service_url}\n\n")

        f.write("echo '=== Army81 Cloud Scheduler Setup ==='\n\n")

        for cmd in commands:
            f.write(f"{cmd}\n\n")

        f.write("echo '=== Done! ==='\n")
        f.write("gcloud scheduler jobs list --project=$PROJECT_ID --location=$REGION\n")

    os.chmod(script_path, 0o755)
    print(f"✅ سكربت الإعداد محفوظ: {script_path}")
    print(f"   شغّل: bash {script_path}")

    return True


def setup_local_scheduler():
    """
    بديل محلي: APScheduler للتشغيل بدون Google Cloud
    يُستخدم في التطوير المحلي و Docker
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        print("خطأ: APScheduler غير مثبت — pip install apscheduler")
        return None

    scheduler = BackgroundScheduler()

    # التحديث اليومي
    def daily_update():
        logger.info("Running daily update...")
        try:
            from scripts.daily_updater import run_daily_update
            run_daily_update()
        except Exception as e:
            logger.error(f"Daily update error: {e}")

    # الضغط الأسبوعي
    def weekly_compress():
        logger.info("Running weekly compression...")
        try:
            from memory.hierarchical_memory import HierarchicalMemory
            hm = HierarchicalMemory()
            # ضغط لأهم 20 وكيل
            for i in range(1, 82):
                agent_id = f"A{i:02d}" if i < 10 else f"A{i}"
                hm.compress_weekly(agent_id)
        except Exception as e:
            logger.error(f"Weekly compress error: {e}")

    # فحص الأداء
    def performance_check():
        logger.info("Running performance check...")
        try:
            from core.performance_monitor import PerformanceMonitor
            monitor = PerformanceMonitor()
            report = monitor.generate_report()
            logger.info(f"Performance report: {len(report)} agents analyzed")
        except Exception as e:
            logger.error(f"Performance check error: {e}")

    scheduler.add_job(
        daily_update,
        CronTrigger(hour=2, minute=0, timezone="Asia/Riyadh"),
        id="daily_update",
        name="التحديث اليومي",
    )

    scheduler.add_job(
        weekly_compress,
        CronTrigger(day_of_week="sun", hour=4, minute=0, timezone="Asia/Riyadh"),
        id="weekly_compress",
        name="الضغط الأسبوعي",
    )

    scheduler.add_job(
        performance_check,
        CronTrigger(hour=6, minute=0, timezone="Asia/Riyadh"),
        id="performance_check",
        name="فحص الأداء",
    )

    return scheduler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Army81 Cloud Scheduler Setup")
    parser.add_argument("--cloud", action="store_true", help="إعداد Cloud Scheduler")
    parser.add_argument("--local", action="store_true", help="تشغيل APScheduler محلياً")
    args = parser.parse_args()

    if args.cloud:
        setup_cloud_scheduler()
    elif args.local:
        scheduler = setup_local_scheduler()
        if scheduler:
            scheduler.start()
            print("✅ APScheduler running locally. Press Ctrl+C to stop.")
            try:
                import time
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                scheduler.shutdown()
                print("\nStopped.")
    else:
        print("Army81 Cloud Scheduler Setup")
        print("  --cloud  إعداد Google Cloud Scheduler")
        print("  --local  تشغيل APScheduler محلياً")
