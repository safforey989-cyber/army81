"""
Army81 Data Cleanup — حذف التكرارات وفصل البيانات
"""
import sqlite3
import json
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [cleanup] %(message)s")
log = logging.getLogger()

WORKSPACE = Path(__file__).parent.parent / "workspace"
DB_PATH = WORKSPACE / "episodic_memory.db"
DATA_DIR = Path(__file__).parent.parent / "data"


def cleanup_episodic():
    """حذف التكرارات من episodic_memory.db"""
    log.info("═══ Episodic Memory Cleanup ═══")
    conn = sqlite3.connect(str(DB_PATH))

    before = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    unique = conn.execute("SELECT COUNT(DISTINCT task_summary) FROM episodes").fetchone()[0]
    log.info(f"  Before: {before} rows, {unique} unique tasks, {before - unique} duplicates")

    # احتفظ بأحدث نسخة من كل مهمة فريدة
    conn.execute("""
        DELETE FROM episodes WHERE rowid NOT IN (
            SELECT MAX(rowid) FROM episodes GROUP BY agent_id, task_summary
        )
    """)
    conn.commit()

    after = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    removed = before - after
    log.info(f"  After:  {after} rows — removed {removed} duplicates")

    # VACUUM لتقليص حجم الملف
    conn.execute("VACUUM")
    conn.close()

    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    log.info(f"  DB size: {size_mb:.1f} MB")
    return {"before": before, "after": after, "removed": removed}


def setup_data_dirs():
    """إنشاء هيكل بيانات نظيف"""
    log.info("═══ Setting Up Data Directories ═══")
    dirs = ["insights", "errors", "logs", "metrics"]
    for d in dirs:
        (DATA_DIR / d).mkdir(parents=True, exist_ok=True)
        log.info(f"  ✅ data/{d}/")
    return dirs


def deduplicate_json_file(filepath: str, key: str = "insight"):
    """حذف التكرارات من ملف JSON"""
    p = Path(filepath)
    if not p.exists():
        return 0

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return 0

        before = len(data)
        seen = set()
        unique = []
        for item in data:
            k = str(item.get(key, item.get("text", str(item))))[:200]
            if k not in seen:
                seen.add(k)
                unique.append(item)

        p.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding="utf-8")
        removed = before - len(unique)
        if removed > 0:
            log.info(f"  {p.name}: {before} → {len(unique)} (removed {removed})")
        return removed
    except Exception as e:
        log.warning(f"  Error in {filepath}: {e}")
        return 0


def cleanup_workspace_jsons():
    """تنظيف كل ملفات JSON في workspace"""
    log.info("═══ Workspace JSON Cleanup ═══")
    total_removed = 0

    json_files = [
        "workspace/skillbank/skills.json",
        "workspace/discovery_log.json",
        "workspace/pending_approvals.json",
    ]

    for f in json_files:
        p = Path(f)
        if p.exists():
            total_removed += deduplicate_json_file(str(p))

    # تنظيف agent memories
    mem_dir = WORKSPACE / "agent_memories"
    if mem_dir.exists():
        for f in mem_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                interactions = data.get("interactions", [])
                if len(interactions) > 100:
                    data["interactions"] = interactions[-100:]  # آخر 100 فقط
                    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    total_removed += len(interactions) - 100
            except:
                pass

    log.info(f"  Total removed from JSONs: {total_removed}")
    return total_removed


def apply_retention_policy():
    """سياسة الاحتفاظ — MAX 2000 episode"""
    log.info("═══ Retention Policy ═══")
    MAX_EPISODES = 2000
    conn = sqlite3.connect(str(DB_PATH))
    count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    if count > MAX_EPISODES:
        excess = count - MAX_EPISODES
        conn.execute(f"""
            DELETE FROM episodes WHERE rowid IN (
                SELECT rowid FROM episodes ORDER BY created_at ASC LIMIT {excess}
            )
        """)
        conn.commit()
        log.info(f"  Trimmed {excess} old episodes (kept {MAX_EPISODES})")
    else:
        log.info(f"  OK: {count} episodes (under {MAX_EPISODES} limit)")

    conn.execute("VACUUM")
    conn.close()


if __name__ == "__main__":
    log.info("🧹 Army81 Data Cleanup Starting...")
    log.info(f"  Timestamp: {datetime.now().isoformat()}")

    setup_data_dirs()
    episodic = cleanup_episodic()
    json_removed = cleanup_workspace_jsons()
    apply_retention_policy()

    log.info("═══ CLEANUP COMPLETE ═══")
    log.info(f"  Episodic: {episodic['before']} → {episodic['after']} (-{episodic['removed']})")
    log.info(f"  JSON duplicates removed: {json_removed}")
    log.info("✅ Done!")
