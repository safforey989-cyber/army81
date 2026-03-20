"""
Army81 - Cloud Scheduler Setup
إعداد جدولة المهام اليومية على Google Cloud
المرحلة 3: البنية التحتية

يُنشئ Cloud Scheduler job لتشغيل التحديث اليومي في الساعة 2 صباحاً (Asia/Riyadh)
مع fallback للجدولة المحلية عبر APScheduler
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

logger = logging.getLogger("army81.scheduler")

# ── Cloud Scheduler Setup ──────────────────────────────────────

def setup_cloud_scheduler(service_url: str = "", project_id: str = "",
                          region: str = "us-central1") -> dict:
    """
    إنشاء Cloud Scheduler job على GCP
    يُنفّذ POST /task يومياً في الساعة 2:00 صباحاً (Asia/Riyadh)
    """
    project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        return {"error": "GCP_PROJECT_ID not set"}

    if not service_url:
        service_url = os.getenv("ARMY81_SERVICE_URL", "")
    if not service_url:
        return {"error": "Service URL not provided. Set ARMY81_SERVICE_URL"}

    try:
        from google.cloud import scheduler_v1
        client = scheduler_v1.CloudSchedulerClient()

        parent = f"projects/{project_id}/locations/{region}"

        # ── Job 1: التحديث اليومي (2:00 صباحاً) ──────────────
        daily_job = scheduler_v1.Job(
            name=f"{parent}/jobs/army81-daily-update",
            description="Army81 Daily Knowledge Update — تحديث المعرفة اليومي",
            schedule="0 2 * * *",
            time_zone="Asia/Riyadh",
            http_target=scheduler_v1.HttpTarget(
                uri=f"{service_url}/task",
                http_method=scheduler_v1.HttpMethod.POST,
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "task": "تحديث يومي: اجمع أحدث الأخبار والأبحاث في الذكاء الاصطناعي والتقنية والجيوسياسة",
                    "agent_id": "A04",
                    "context": {"type": "daily_update", "auto": True}
                }).encode("utf-8"),
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=3,
                max_retry_duration={"seconds": 600},
            ),
        )

        # ── Job 2: تقرير الأداء (6:00 صباحاً) ────────────────
        report_job = scheduler_v1.Job(
            name=f"{parent}/jobs/army81-performance-report",
            description="Army81 Performance Report — تقرير الأداء اليومي",
            schedule="0 6 * * *",
            time_zone="Asia/Riyadh",
            http_target=scheduler_v1.HttpTarget(
                uri=f"{service_url}/task",
                http_method=scheduler_v1.HttpMethod.POST,
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "task": "أنتج تقرير أداء يومي لكل الوكلاء مع توصيات التحسين",
                    "agent_id": "A01",
                    "context": {"type": "performance_report", "auto": True}
                }).encode("utf-8"),
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=2,
                max_retry_duration={"seconds": 300},
            ),
        )

        # ── Job 3: تدريب أسبوعي (الجمعة 3:00 صباحاً) ─────────
        training_job = scheduler_v1.Job(
            name=f"{parent}/jobs/army81-weekly-training",
            description="Army81 Weekly Training Cycle — دورة تدريب أسبوعية",
            schedule="0 3 * * 5",
            time_zone="Asia/Riyadh",
            http_target=scheduler_v1.HttpTarget(
                uri=f"{service_url}/training/trigger",
                http_method=scheduler_v1.HttpMethod.POST,
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "cycle_type": "weekly",
                    "auto": True
                }).encode("utf-8"),
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=2,
            ),
        )

        results = []
        for job in [daily_job, report_job, training_job]:
            try:
                created = client.create_job(request={"parent": parent, "job": job})
                results.append({"name": created.name, "status": "created"})
                print(f"  Created: {created.name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    # تحديث بدلاً من إنشاء
                    try:
                        updated = client.update_job(request={"job": job})
                        results.append({"name": updated.name, "status": "updated"})
                        print(f"  Updated: {updated.name}")
                    except Exception as ue:
                        results.append({"name": job.name, "status": f"error: {ue}"})
                else:
                    results.append({"name": job.name, "status": f"error: {e}"})

        return {
            "status": "success",
            "project_id": project_id,
            "jobs": results,
        }

    except ImportError:
        return {
            "error": "google-cloud-scheduler not installed. pip install google-cloud-scheduler"
        }
    except Exception as e:
        return {"error": f"Cloud Scheduler setup failed: {e}"}


# ── Local Scheduler (Fallback) ────────────────────────────────

def setup_local_scheduler():
    """
    جدولة محلية عبر APScheduler
    تعمل بدون Google Cloud
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        print("APScheduler not installed: pip install apscheduler")
        return None

    scheduler = BackgroundScheduler(timezone="Asia/Riyadh")

    # تحديث يومي — 2:00 صباحاً
    def daily_update():
        print(f"[{datetime.now()}] Running daily update...")
        try:
            from scripts.daily_updater import run_daily_update
            run_daily_update()
            print("Daily update completed.")
        except Exception as e:
            print(f"Daily update error: {e}")

    scheduler.add_job(
        daily_update,
        CronTrigger(hour=2, minute=0),
        id="army81_daily_update",
        name="Army81 Daily Knowledge Update",
        replace_existing=True,
    )

    # تقرير أداء — 6:00 صباحاً
    def performance_report():
        print(f"[{datetime.now()}] Generating performance report...")
        try:
            from core.agent_monitor import get_monitor
            monitor = get_monitor()
            report = monitor.generate_improvement_report()
            print(f"Report generated: {len(report)} chars")
        except Exception as e:
            print(f"Performance report error: {e}")

    scheduler.add_job(
        performance_report,
        CronTrigger(hour=6, minute=0),
        id="army81_performance_report",
        name="Army81 Performance Report",
        replace_existing=True,
    )

    # تدريب أسبوعي — الجمعة 3:00 صباحاً
    def weekly_training():
        print(f"[{datetime.now()}] Running weekly training cycle...")
        try:
            from core.prompt_optimizer import get_optimizer
            from core.agent_monitor import get_monitor

            monitor = get_monitor()
            optimizer = get_optimizer()
            overview = monitor.get_system_overview()
            print(f"Training cycle: {overview.get('agents_monitored', 0)} agents")
        except Exception as e:
            print(f"Weekly training error: {e}")

    scheduler.add_job(
        weekly_training,
        CronTrigger(day_of_week="fri", hour=3, minute=0),
        id="army81_weekly_training",
        name="Army81 Weekly Training",
        replace_existing=True,
    )

    return scheduler


# ── Pub/Sub Topics Setup ──────────────────────────────────────

def setup_pubsub_topics(project_id: str = "") -> dict:
    """
    إنشاء Pub/Sub topics المطلوبة
    """
    project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        return {"error": "GCP_PROJECT_ID not set"}

    try:
        from google.cloud import pubsub_v1
        publisher = pubsub_v1.PublisherClient()

        topics = [
            "army81-agent-tasks",
            "army81-agent-results",
            "army81-agent-signals",
            "army81-broadcast",
        ]

        results = []
        for topic_name in topics:
            topic_path = publisher.topic_path(project_id, topic_name)
            try:
                publisher.create_topic(request={"name": topic_path})
                results.append({"topic": topic_name, "status": "created"})
                print(f"  Created topic: {topic_path}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    results.append({"topic": topic_name, "status": "exists"})
                else:
                    results.append({"topic": topic_name, "status": f"error: {e}"})

        return {"status": "success", "topics": results}

    except ImportError:
        return {"error": "google-cloud-pubsub not installed"}
    except Exception as e:
        return {"error": str(e)}


# ── Firestore Setup ──────────────────────────────────────────

def setup_firestore(project_id: str = "") -> dict:
    """تهيئة Firestore collections"""
    project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        return {"error": "GCP_PROJECT_ID not set"}

    try:
        from google.cloud import firestore
        db = firestore.Client(project=project_id)

        collections = [
            "army81_episodes",
            "army81_knowledge",
            "army81_stats",
            "army81_lessons",
        ]

        results = []
        for coll_name in collections:
            # إنشاء مستند تهيئة
            try:
                db.collection(coll_name).document("_init").set({
                    "initialized": True,
                    "created_at": datetime.now().isoformat(),
                    "project": project_id,
                })
                results.append({"collection": coll_name, "status": "ready"})
                print(f"  Collection ready: {coll_name}")
            except Exception as e:
                results.append({"collection": coll_name, "status": f"error: {e}"})

        return {"status": "success", "collections": results}

    except ImportError:
        return {"error": "google-cloud-firestore not installed"}
    except Exception as e:
        return {"error": str(e)}


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Army81 — Cloud Scheduler & Infrastructure Setup")

    parser.add_argument("--cloud", action="store_true",
                        help="Setup Google Cloud Scheduler jobs")
    parser.add_argument("--local", action="store_true",
                        help="Run local APScheduler")
    parser.add_argument("--pubsub", action="store_true",
                        help="Create Pub/Sub topics")
    parser.add_argument("--firestore", action="store_true",
                        help="Initialize Firestore collections")
    parser.add_argument("--all", action="store_true",
                        help="Setup everything on GCP")
    parser.add_argument("--service-url", type=str, default="",
                        help="Cloud Run service URL")
    parser.add_argument("--project", type=str, default="",
                        help="GCP project ID")
    parser.add_argument("--region", type=str, default="us-central1",
                        help="GCP region")

    args = parser.parse_args()

    project_id = args.project or os.getenv("GCP_PROJECT_ID", "")

    if args.all or args.cloud:
        print("\n== Setting up Cloud Scheduler ==")
        result = setup_cloud_scheduler(args.service_url, project_id, args.region)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.all or args.pubsub:
        print("\n== Setting up Pub/Sub Topics ==")
        result = setup_pubsub_topics(project_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.all or args.firestore:
        print("\n== Setting up Firestore ==")
        result = setup_firestore(project_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.local:
        print("\n== Starting Local Scheduler ==")
        scheduler = setup_local_scheduler()
        if scheduler:
            scheduler.start()
            print("Local scheduler running. Press Ctrl+C to stop.")
            try:
                import time
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                scheduler.shutdown()
                print("Scheduler stopped.")
        else:
            print("Failed to start local scheduler")

    if not any([args.cloud, args.local, args.pubsub, args.firestore, args.all]):
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/setup_scheduler.py --all --service-url https://army81.run.app")
        print("  python scripts/setup_scheduler.py --local")
        print("  python scripts/setup_scheduler.py --cloud --service-url https://army81.run.app")


if __name__ == "__main__":
    main()
