"""
Army81 v5 - Human Interface
طبقة التواصل مع المستخدم البشري
- تجمع كل الإشعارات والطلبات في مكان واحد
- ترسل عبر Telegram تلقائياً
- تنتظر الموافقات وتنفذها
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.human_interface")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
PENDING_FILE = os.path.join(WORKSPACE_DIR, "pending_approvals.json")
NOTIFICATIONS_FILE = os.path.join(WORKSPACE_DIR, "notifications.json")

os.makedirs(WORKSPACE_DIR, exist_ok=True)


class HumanInterface:
    """
    واجهة التواصل مع المستخدم البشري
    كل مكون في النظام يستخدم هذه الواجهة للتواصل معك
    """

    def __init__(self, telegram_enabled: bool = True):
        self.telegram_enabled = telegram_enabled
        self._telegram_bot = None
        self._load_state()

    @property
    def telegram(self):
        """تحميل Telegram Bot كسول"""
        if self._telegram_bot is None and self.telegram_enabled:
            try:
                from integrations.telegram_bot import get_bot
                self._telegram_bot = get_bot()
            except Exception as e:
                logger.warning(f"Telegram bot not available: {e}")
                self._telegram_bot = None
        return self._telegram_bot

    # ══════════════════════════════════════
    # طلبات الموافقة
    # ══════════════════════════════════════

    def create_request(self, title: str, description: str,
                       action_type: str = "general",
                       action_data: Dict = None,
                       urgency: str = "normal") -> Dict:
        """
        إنشاء طلب موافقة جديد
        يُحفظ محلياً + يُرسل عبر Telegram
        """
        request = {
            "id": f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.pending)}",
            "title": title,
            "description": description,
            "action_type": action_type,
            "action_data": action_data or {},
            "urgency": urgency,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        self.pending.append(request)
        self._save_pending()

        # أرسل عبر Telegram
        if self.telegram:
            try:
                self.telegram.send_approval_request(request)
            except Exception as e:
                logger.warning(f"Failed to send Telegram approval: {e}")

        logger.info(f"Created request: {request['id']} — {title}")
        return request

    def get_pending(self) -> List[Dict]:
        """الحصول على الطلبات المعلقة"""
        return [r for r in self.pending if r["status"] == "pending"]

    def approve(self, request_id: str) -> Dict:
        """الموافقة على طلب"""
        for req in self.pending:
            if req["id"] == request_id:
                req["status"] = "approved"
                req["responded_at"] = datetime.now().isoformat()
                self._save_pending()
                return req
        return {"error": "not found"}

    def reject(self, request_id: str) -> Dict:
        """رفض طلب"""
        for req in self.pending:
            if req["id"] == request_id:
                req["status"] = "rejected"
                req["responded_at"] = datetime.now().isoformat()
                self._save_pending()
                return req
        return {"error": "not found"}

    # ══════════════════════════════════════
    # الإشعارات
    # ══════════════════════════════════════

    def notify(self, title: str, message: str,
               urgency: str = "normal") -> bool:
        """إرسال إشعار"""
        notification = {
            "title": title,
            "message": message,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat(),
        }

        self.notifications.append(notification)
        self._save_notifications()

        # أرسل عبر Telegram
        if self.telegram:
            try:
                return self.telegram.send_alert(title, message, urgency)
            except Exception as e:
                logger.warning(f"Telegram notify failed: {e}")

        return True

    def send_daily_report(self, report: Dict) -> bool:
        """إرسال التقرير اليومي"""
        # حفظ محلياً
        self.notifications.append({
            "title": "تقرير يومي",
            "message": json.dumps(report, ensure_ascii=False),
            "urgency": "normal",
            "timestamp": datetime.now().isoformat(),
        })
        self._save_notifications()

        # أرسل عبر Telegram
        if self.telegram:
            try:
                return self.telegram.send_daily_report(report)
            except Exception as e:
                logger.warning(f"Telegram report failed: {e}")

        return True

    # ══════════════════════════════════════
    # حالة الواجهة
    # ══════════════════════════════════════

    def status(self) -> Dict:
        """حالة الواجهة"""
        return {
            "pending_requests": len(self.get_pending()),
            "total_notifications": len(self.notifications),
            "telegram_connected": self.telegram is not None,
            "telegram_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        }

    # ══════════════════════════════════════
    # تخزين داخلي
    # ══════════════════════════════════════

    def _load_state(self):
        """تحميل الحالة من الملفات"""
        if os.path.exists(PENDING_FILE):
            try:
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    self.pending = json.load(f)
            except Exception:
                self.pending = []
        else:
            self.pending = []

        if os.path.exists(NOTIFICATIONS_FILE):
            try:
                with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
                    self.notifications = json.load(f)
            except Exception:
                self.notifications = []
        else:
            self.notifications = []

    def _save_pending(self):
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(self.pending, f, ensure_ascii=False, indent=2)

    def _save_notifications(self):
        # احتفظ بآخر 200 فقط
        self.notifications = self.notifications[-200:]
        with open(NOTIFICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notifications, f, ensure_ascii=False, indent=2)


# ── Singleton ────────────────────────────────────
_instance: Optional[HumanInterface] = None


def get_human_interface() -> HumanInterface:
    global _instance
    if _instance is None:
        _instance = HumanInterface()
    return _instance
