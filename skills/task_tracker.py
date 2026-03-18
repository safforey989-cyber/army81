"""Army81 Skill — Task Tracker"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("army81.skill.task_tracker")

TASKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workspace", "tasks.json"
)


def _load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_tasks(tasks):
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def add_task(title: str, priority: str = "normal", assignee: str = "") -> str:
    """إضافة مهمة"""
    tasks = _load_tasks()
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "priority": priority,
        "assignee": assignee,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    tasks.append(task)
    _save_tasks(tasks)
    return f"تمت إضافة المهمة #{task['id']}: {title}"


def complete_task(task_id: int) -> str:
    """إكمال مهمة"""
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            t["completed_at"] = datetime.now().isoformat()
            _save_tasks(tasks)
            return f"تم إكمال المهمة #{task_id}: {t['title']}"
    return f"المهمة #{task_id} غير موجودة"


def list_tasks(status: str = "all") -> str:
    """عرض المهام"""
    tasks = _load_tasks()
    if status != "all":
        tasks = [t for t in tasks if t.get("status") == status]

    if not tasks:
        return "لا توجد مهام" if status == "all" else f"لا توجد مهام بحالة: {status}"

    lines = [f"المهام ({len(tasks)}):"]
    for t in tasks:
        icon = "✅" if t["status"] == "done" else "⏳"
        lines.append(f"  {icon} #{t['id']} [{t['priority']}] {t['title']}")
    return "\n".join(lines)


def task_stats() -> str:
    """إحصائيات المهام"""
    tasks = _load_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "done")
    pending = total - done
    return f"إجمالي: {total} | منجز: {done} | قيد الانتظار: {pending}"
