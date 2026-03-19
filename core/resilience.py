"""
Army81 Resilience Layer — حماية النظام من الأعطال والتضخم
"""
import os
import json
import time
import logging
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger("army81.resilience")

WORKSPACE = Path(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
))

# ═══════════════════════════════════════
# 1. Safe Request — retry + timeout
# ═══════════════════════════════════════

def safe_request(url: str, method: str = "GET", json_data: dict = None,
                 retries: int = 3, timeout: int = 10) -> dict:
    """طلب HTTP آمن مع retry و timeout"""
    import requests
    for i in range(retries):
        try:
            if method == "POST":
                r = requests.post(url, json=json_data, timeout=timeout)
            else:
                r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == retries - 1:
                logger.warning(f"Request failed after {retries} attempts: {url} — {e}")
                return {"error": str(e), "url": url, "attempts": retries}
            wait = min(2 ** i, 10)
            time.sleep(wait)
    return {"error": "max retries", "url": url}


# ═══════════════════════════════════════
# 2. Health Check System
# ═══════════════════════════════════════

class HealthChecker:
    """فحص صحة كل مكونات النظام"""

    SERVICES = {
        "gateway": "http://localhost:8181/health",
        "ollama": "http://localhost:11434/api/tags",
    }

    def check_all(self) -> Dict[str, bool]:
        results = {}
        for name, url in self.SERVICES.items():
            results[name] = self._check(url)
        # Check files
        results["episodic_db"] = (WORKSPACE / "episodic_memory.db").exists()
        results["chroma_db"] = (WORKSPACE / "chroma_db").exists()
        results["agent_memories"] = len(list((WORKSPACE / "agent_memories").glob("*.json"))) >= 80
        return results

    def _check(self, url: str) -> bool:
        import requests
        try:
            r = requests.get(url, timeout=3)
            return r.status_code == 200
        except:
            return False


# ═══════════════════════════════════════
# 3. Data Lifecycle Manager
# ═══════════════════════════════════════

class DataLifecycle:
    """إدارة دورة حياة البيانات — منع التضخم"""

    MAX_EPISODES = 5000       # حد أقصى
    MAX_INSIGHTS_PER_AGENT = 50
    MAX_LOG_LINES = 10000
    DEDUP_THRESHOLD = 0.9     # تشابه 90% = تكرار

    def cleanup_episodic(self) -> Dict:
        """تنظيف الذاكرة من التكرارات"""
        db_path = WORKSPACE / "episodic_memory.db"
        if not db_path.exists():
            return {"status": "no_db"}

        conn = sqlite3.connect(str(db_path))

        # عدد قبل التنظيف
        before = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

        # حذف التكرارات — احتفظ بالأحدث لكل مهمة
        conn.execute("""
            DELETE FROM episodes WHERE rowid NOT IN (
                SELECT MAX(rowid) FROM episodes
                GROUP BY agent_id, task_summary
            )
        """)

        # احتفظ بآخر MAX_EPISODES فقط
        conn.execute(f"""
            DELETE FROM episodes WHERE rowid NOT IN (
                SELECT rowid FROM episodes
                ORDER BY created_at DESC
                LIMIT {self.MAX_EPISODES}
            )
        """)

        conn.commit()
        conn.execute("VACUUM")
        conn.commit()

        after = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        conn.close()

        removed = before - after
        logger.info(f"🧹 Episodic cleanup: {before} → {after} ({removed} removed)")
        return {"before": before, "after": after, "removed": removed}

    def cleanup_agent_memories(self) -> Dict:
        """تنظيف ذاكرة الوكلاء من التكرارات"""
        mdir = WORKSPACE / "agent_memories"
        if not mdir.exists():
            return {"status": "no_dir"}

        cleaned = 0
        for f in mdir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))

                # إزالة التكرار من interactions
                if "interactions" in data:
                    seen = set()
                    unique = []
                    for item in data["interactions"]:
                        key = str(item.get("with", "")) + str(item.get("topic", ""))[:50]
                        if key not in seen:
                            seen.add(key)
                            unique.append(item)
                    data["interactions"] = unique[-self.MAX_INSIGHTS_PER_AGENT:]

                f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                cleaned += 1
            except:
                pass

        logger.info(f"🧹 Agent memories cleaned: {cleaned} files")
        return {"files_cleaned": cleaned}

    def cleanup_logs(self) -> Dict:
        """تقليم ملفات السجل"""
        log_dir = Path(os.path.join(os.path.dirname(__file__), "..", "logs"))
        trimmed = 0

        for f in log_dir.glob("*.log"):
            try:
                lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
                if len(lines) > self.MAX_LOG_LINES:
                    # احتفظ بآخر MAX_LOG_LINES سطر
                    f.write_text("\n".join(lines[-self.MAX_LOG_LINES:]), encoding="utf-8")
                    trimmed += len(lines) - self.MAX_LOG_LINES
            except:
                pass

        logger.info(f"🧹 Logs trimmed: {trimmed} lines removed")
        return {"lines_trimmed": trimmed}

    def full_cleanup(self) -> Dict:
        """تنظيف شامل"""
        results = {
            "episodic": self.cleanup_episodic(),
            "agent_memories": self.cleanup_agent_memories(),
            "logs": self.cleanup_logs(),
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"🧹 Full cleanup complete")
        return results


# ═══════════════════════════════════════
# 4. Structured Event System
# ═══════════════════════════════════════

class EventLogger:
    """نظام أحداث منظم — فصل insights عن errors عن logs"""

    def __init__(self):
        self.data_dir = WORKSPACE / "structured_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.insights_file = self.data_dir / "insights.json"
        self.errors_file = self.data_dir / "errors.json"
        self.metrics_file = self.data_dir / "metrics.json"

        # تهيئة الملفات
        for f in [self.insights_file, self.errors_file, self.metrics_file]:
            if not f.exists():
                f.write_text("[]", encoding="utf-8")

    def add_insight(self, agent_id: str, insight: str, topic: str, confidence: float = 0.8):
        """إضافة معرفة جديدة — مع فحص التكرار"""
        data = json.loads(self.insights_file.read_text(encoding="utf-8"))

        # فحص التكرار
        key = hashlib.md5((agent_id + insight[:100]).encode()).hexdigest()
        if any(d.get("key") == key for d in data[-100:]):
            return  # تكرار

        data.append({
            "key": key,
            "agent_id": agent_id,
            "insight": insight[:500],
            "topic": topic,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })

        # حد أقصى 1000
        if len(data) > 1000:
            data = data[-1000:]

        self.insights_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_error(self, agent_id: str, error: str, context: str = ""):
        """تسجيل خطأ — في ملف منفصل"""
        data = json.loads(self.errors_file.read_text(encoding="utf-8"))
        data.append({
            "agent_id": agent_id,
            "error": str(error)[:300],
            "context": context[:200],
            "timestamp": datetime.now().isoformat()
        })
        if len(data) > 500:
            data = data[-500:]
        self.errors_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_metric(self, name: str, value: float, agent_id: str = ""):
        """تسجيل مقياس أداء"""
        data = json.loads(self.metrics_file.read_text(encoding="utf-8"))
        data.append({
            "name": name,
            "value": value,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        })
        if len(data) > 2000:
            data = data[-2000:]
        self.metrics_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_stats(self) -> Dict:
        """إحصائيات الأحداث"""
        insights = json.loads(self.insights_file.read_text(encoding="utf-8"))
        errors = json.loads(self.errors_file.read_text(encoding="utf-8"))
        metrics = json.loads(self.metrics_file.read_text(encoding="utf-8"))
        return {
            "insights": len(insights),
            "errors": len(errors),
            "metrics": len(metrics)
        }


# ═══════════════════════════════════════
# 5. Register endpoints
# ═══════════════════════════════════════

def register_resilience_endpoints(app):
    """إضافة endpoints للـ resilience"""

    health = HealthChecker()
    lifecycle = DataLifecycle()
    events = EventLogger()

    @app.get("/system/health-check")
    async def health_check():
        return health.check_all()

    @app.post("/system/cleanup")
    async def cleanup():
        return lifecycle.full_cleanup()

    @app.get("/system/data-stats")
    async def data_stats():
        import os
        db_size = os.path.getsize(WORKSPACE / "episodic_memory.db") / 1024 / 1024
        return {
            "episodic_db_mb": round(db_size, 1),
            "structured_events": events.get_stats(),
            "workspace_files": sum(1 for _ in WORKSPACE.rglob("*") if _.is_file()),
        }

    @app.post("/system/cleanup/episodic")
    async def cleanup_episodic():
        return lifecycle.cleanup_episodic()

    logger.info("🛡️ Resilience endpoints registered")
    return health, lifecycle, events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🛡️ Army81 Resilience Layer")
    print("=" * 40)

    # Health check
    h = HealthChecker()
    print("\n📊 Health Check:")
    for k, v in h.check_all().items():
        print(f"  {'✅' if v else '❌'} {k}")

    # Cleanup
    lc = DataLifecycle()
    print("\n🧹 Running cleanup...")
    results = lc.full_cleanup()
    print(json.dumps(results, indent=2, ensure_ascii=False))
