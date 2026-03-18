"""Army81 Skill — Calendar Manager"""
import os
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("army81.skill.calendar_manager")

CALENDAR_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workspace", "calendar.json"
)


def _load_events():
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_events(events):
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def add_event(title: str, date: str, time: str = "", description: str = "") -> str:
    """إضافة حدث"""
    events = _load_events()
    event = {
        "id": len(events) + 1,
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "created_at": datetime.now().isoformat(),
    }
    events.append(event)
    _save_events(events)
    return f"تمت إضافة الحدث: {title} في {date} {time}"


def get_today_events() -> str:
    """أحداث اليوم"""
    today = datetime.now().strftime("%Y-%m-%d")
    events = _load_events()
    today_events = [e for e in events if e.get("date") == today]
    if not today_events:
        return "لا توجد أحداث اليوم"
    lines = [f"أحداث اليوم ({today}):"]
    for e in today_events:
        lines.append(f"  - {e.get('time', '')} {e['title']}")
    return "\n".join(lines)


def get_upcoming(days: int = 7) -> str:
    """الأحداث القادمة"""
    now = datetime.now()
    end = now + timedelta(days=days)
    events = _load_events()

    upcoming = []
    for e in events:
        try:
            event_date = datetime.strptime(e["date"], "%Y-%m-%d")
            if now.date() <= event_date.date() <= end.date():
                upcoming.append(e)
        except (ValueError, KeyError):
            pass

    if not upcoming:
        return f"لا أحداث في الـ {days} أيام القادمة"

    upcoming.sort(key=lambda x: x["date"])
    lines = [f"الأحداث القادمة ({days} أيام):"]
    for e in upcoming:
        lines.append(f"  - {e['date']} {e.get('time','')} — {e['title']}")
    return "\n".join(lines)
