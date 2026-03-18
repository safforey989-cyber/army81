"""
Army81 v5 - Telegram Bot
بوت Telegram — تواصل مباشر مع Army81
- ترسل مهمة -> الوكيل المناسب يجيب
- النظام يرسل لك التنبيهات والتقارير
- توافق على الطلبات من هاتفك
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("army81.telegram")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [telegram] %(levelname)s: %(message)s",
)


class TelegramBot:
    """
    بوت Telegram يربطك بـ Army81 مباشرة
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8181")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    # ══════════════════════════════════════
    # إرسال رسائل للمستخدم
    # ══════════════════════════════════════

    def send_message(self, text: str, reply_markup: Dict = None,
                     chat_id: str = None) -> bool:
        """إرسال رسالة نصية"""
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set")
            return False

        target_chat = chat_id or self.chat_id
        if not target_chat:
            logger.warning("TELEGRAM_CHAT_ID not set")
            return False

        # Telegram حد 4096 حرف
        if len(text) > 4000:
            text = text[:4000] + "\n\n... (تم اقتطاع الرسالة)"

        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": "Markdown",
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)

        try:
            r = requests.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=10,
            )
            if r.status_code != 200:
                # جرب بدون Markdown لو فشل
                payload["parse_mode"] = "HTML"
                payload["text"] = text.replace("*", "").replace("_", "")
                r = requests.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=10,
                )
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_approval_request(self, request: Dict) -> bool:
        """إرسال طلب موافقة مع أزرار"""
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ وافق", "callback_data": f"approve_{request['id']}"},
                {"text": "❌ ارفض", "callback_data": f"reject_{request['id']}"},
            ]]
        }

        text = (
            f"🔔 *طلب موافقة*\n\n"
            f"*{request.get('title', 'بدون عنوان')}*\n\n"
            f"{request.get('description', '')[:1500]}\n\n"
            f"⏰ ينتهي خلال: 24 ساعة"
        )

        return self.send_message(text, keyboard)

    def send_daily_report(self, report: Dict) -> bool:
        """إرسال التقرير اليومي"""
        completed = report.get("completed", "لا شيء")
        improvements = report.get("improvements", "لا شيء")
        pending_count = report.get("pending_count", 0)
        key_finding = report.get("key_finding", "لا شيء")

        text = (
            f"📊 *تقرير Army81 اليومي*\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"✅ *ما تم اليوم:*\n{completed}\n\n"
            f"📈 *التحسينات:*\n{improvements}\n\n"
            f"⏳ *ينتظر موافقتك:* {pending_count} طلب\n\n"
            f"💡 *اكتشاف مهم:*\n{key_finding}"
        )

        return self.send_message(text)

    def send_alert(self, title: str, message: str,
                   urgency: str = "normal") -> bool:
        """إرسال تنبيه"""
        emoji_map = {"critical": "🚨", "high": "⚠️", "normal": "ℹ️", "low": "📝"}
        emoji = emoji_map.get(urgency, "ℹ️")
        return self.send_message(f"{emoji} *{title}*\n\n{message}")

    # ══════════════════════════════════════
    # استقبال الرسائل من المستخدم
    # ══════════════════════════════════════

    def process_message(self, message: Dict):
        """معالجة رسالة واردة"""
        text = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))

        # تحديث chat_id تلقائياً لو لم يُحدد
        if not self.chat_id and chat_id:
            self.chat_id = chat_id
            logger.info(f"Auto-set CHAT_ID: {chat_id}")

        if not text:
            return

        # أوامر خاصة
        commands = {
            "/start": self._cmd_start,
            "/status": self._cmd_status,
            "/pending": self._cmd_pending,
            "/report": self._cmd_report,
            "/agents": self._cmd_agents,
            "/help": self._cmd_help,
        }

        if text in commands:
            commands[text]()
        elif text.startswith("/agent_"):
            self._cmd_agent_direct(text)
        else:
            self.route_to_agent(text)

    def process_callback(self, callback: Dict):
        """معالجة ضغطة زر (موافقة/رفض)"""
        data = callback.get("data", "")
        callback_id = callback.get("id", "")

        # أجب على الـ callback فوراً
        try:
            requests.post(
                f"{self.base_url}/answerCallbackQuery",
                json={"callback_query_id": callback_id},
                timeout=5,
            )
        except Exception:
            pass

        if data.startswith("approve_"):
            request_id = data.replace("approve_", "")
            self._handle_approval(request_id, True)
        elif data.startswith("reject_"):
            request_id = data.replace("reject_", "")
            self._handle_approval(request_id, False)

    # ══════════════════════════════════════
    # أوامر البوت
    # ══════════════════════════════════════

    def _cmd_start(self):
        self.send_message(
            "🎖️ *مرحباً بك في Army81*\n\n"
            "81 وكيل ذكاء اصطناعي تحت أمرك.\n\n"
            "*الأوامر المتاحة:*\n"
            "/status — حالة النظام\n"
            "/pending — الطلبات المنتظرة\n"
            "/report — آخر تقرير\n"
            "/agents — قائمة الوكلاء\n"
            "/help — المساعدة\n\n"
            "أو أرسل أي سؤال مباشرة وسيجيبك الوكيل المناسب."
        )

    def _cmd_status(self):
        try:
            r = requests.get(f"{self.gateway_url}/status", timeout=10)
            data = r.json()
            agents_count = data.get("router", {}).get("total_agents", 0)
            self.send_message(
                f"📊 *حالة Army81*\n\n"
                f"🤖 الوكلاء: {agents_count}/81\n"
                f"🟢 الحالة: يعمل\n"
                f"⏰ {datetime.now().strftime('%H:%M')}"
            )
        except Exception as e:
            self.send_message(f"❌ السيرفر غير متاح\n{e}")

    def _cmd_pending(self):
        try:
            pending_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "workspace", "pending_approvals.json"
            )
            if os.path.exists(pending_file):
                with open(pending_file, "r", encoding="utf-8") as f:
                    pending = json.load(f)
                pending_items = [p for p in pending if p.get("status") == "pending"]
                if not pending_items:
                    self.send_message("✅ لا توجد طلبات منتظرة")
                    return
                for req_item in pending_items[:5]:
                    self.send_approval_request(req_item)
            else:
                self.send_message("✅ لا توجد طلبات منتظرة")
        except Exception as e:
            self.send_message(f"خطأ: {e}")

    def _cmd_report(self):
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "workspace", "reports"
        )
        if not os.path.exists(reports_dir):
            self.send_message("لا توجد تقارير بعد")
            return

        reports = sorted(
            [f for f in os.listdir(reports_dir) if f.endswith(".md")],
            reverse=True,
        )
        if not reports:
            self.send_message("لا توجد تقارير بعد")
            return

        latest = os.path.join(reports_dir, reports[0])
        with open(latest, "r", encoding="utf-8") as f:
            content = f.read()

        self.send_message(f"📄 *آخر تقرير:* {reports[0]}\n\n{content[:3000]}")

    def _cmd_agents(self):
        try:
            r = requests.get(f"{self.gateway_url}/agents", timeout=10)
            data = r.json()
            agents = data.get("agents", [])
            total = data.get("total", 0)

            text = f"🤖 *قائمة الوكلاء* ({total})\n\n"
            for a in agents[:20]:  # أول 20 فقط
                text += f"• `{a['id']}` {a.get('name_ar', a.get('name', ''))}\n"

            if total > 20:
                text += f"\n... و{total - 20} وكيل آخر"

            self.send_message(text)
        except Exception as e:
            self.send_message(f"❌ خطأ: {e}")

    def _cmd_help(self):
        self.send_message(
            "📖 *مساعدة Army81 Bot*\n\n"
            "*أوامر:*\n"
            "/start — رسالة ترحيب\n"
            "/status — حالة النظام\n"
            "/pending — طلبات تنتظر موافقتك\n"
            "/report — آخر تقرير يومي\n"
            "/agents — قائمة الوكلاء\n\n"
            "*محادثة مع وكيل محدد:*\n"
            "`/agent_A04 ما أخبار الذكاء الاصطناعي؟`\n\n"
            "*محادثة عامة:*\n"
            "أرسل أي سؤال وسيوجّه للوكيل المناسب تلقائياً"
        )

    def _cmd_agent_direct(self, text: str):
        """محادثة مع وكيل محدد: /agent_A04 السؤال"""
        parts = text.split(" ", 1)
        agent_id = parts[0].replace("/agent_", "")
        task = parts[1] if len(parts) > 1 else "مرحبا"

        self.send_message(f"⏳ جاري المعالجة بواسطة {agent_id}...")

        try:
            r = requests.post(
                f"{self.gateway_url}/task",
                json={"task": task, "agent_id": agent_id},
                timeout=90,
            )
            result = r.json()
            agent_name = result.get("agent_name", agent_id)
            response = result.get("result", "لا يوجد رد")
            elapsed = result.get("elapsed_seconds", 0)

            self.send_message(
                f"🤖 *{agent_name}* ({agent_id})\n"
                f"⏱️ {elapsed}s\n\n"
                f"{response[:3000]}"
            )
        except Exception as e:
            self.send_message(f"❌ خطأ: {e}")

    def route_to_agent(self, task: str):
        """يرسل المهمة للوكيل المناسب تلقائياً"""
        self.send_message("⏳ جاري المعالجة...")

        try:
            r = requests.post(
                f"{self.gateway_url}/task",
                json={"task": task},
                timeout=90,
            )
            result = r.json()
            agent_name = result.get("agent_name", "وكيل")
            response = result.get("result", "لا يوجد رد")
            elapsed = result.get("elapsed_seconds", 0)
            model = result.get("model_used", "")

            self.send_message(
                f"🤖 *{agent_name}*\n"
                f"⏱️ {elapsed}s | 🧠 {model}\n\n"
                f"{response[:3000]}"
            )
        except Exception as e:
            self.send_message(f"❌ خطأ في الاتصال بالبوابة: {e}")

    # ══════════════════════════════════════
    # معالجة الموافقات
    # ══════════════════════════════════════

    def _handle_approval(self, request_id: str, approved: bool):
        """معالجة الموافقة/الرفض"""
        try:
            from core.self_builder import SelfBuilder
            builder = SelfBuilder()

            if approved:
                result = builder.approve_request(request_id)
                self.send_message(f"✅ تمت الموافقة وتنفيذ: {request_id}")
            else:
                result = builder.reject_request(request_id)
                self.send_message(f"❌ تم رفض الطلب: {request_id}")
        except Exception as e:
            self.send_message(f"خطأ في معالجة الطلب: {e}")

    # ══════════════════════════════════════
    # تشغيل البوت
    # ══════════════════════════════════════

    def run(self):
        """تشغيل البوت — long polling"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not set in .env")
            print("❌ TELEGRAM_BOT_TOKEN غير موجود في .env")
            print("📖 اقرأ TELEGRAM_SETUP.md لمعرفة كيف تحصل عليه")
            return

        logger.info("Army81 Telegram Bot starting...")
        print("🤖 Army81 Telegram Bot يعمل...")

        # رسالة بدء
        if self.chat_id:
            self.send_message("🟢 Army81 أصبح متصلاً على Telegram")

        while True:
            try:
                r = requests.get(
                    f"{self.base_url}/getUpdates",
                    params={"offset": self.offset, "timeout": 30},
                    timeout=35,
                )

                if r.status_code != 200:
                    logger.warning(f"Telegram API returned {r.status_code}")
                    time.sleep(5)
                    continue

                updates = r.json().get("result", [])

                for update in updates:
                    self.offset = update["update_id"] + 1

                    if "message" in update:
                        msg = update["message"]
                        # تحقق من أن الرسالة من المالك
                        sender_id = str(msg.get("chat", {}).get("id", ""))
                        if self.chat_id and sender_id != self.chat_id:
                            logger.warning(
                                f"Unauthorized message from {sender_id}")
                            continue
                        self.process_message(msg)

                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        sender_id = str(
                            cb.get("from", {}).get("id", ""))
                        if self.chat_id and sender_id != self.chat_id:
                            continue
                        self.process_callback(cb)

            except requests.exceptions.Timeout:
                continue  # طبيعي مع long polling
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                self.send_message("🔴 Army81 Bot متوقف")
                break
            except Exception as e:
                logger.error(f"Bot error: {e}")
                time.sleep(5)


# ══════════════════════════════════════
# Singleton للاستخدام من أجزاء أخرى
# ══════════════════════════════════════

_bot_instance: Optional[TelegramBot] = None


def get_bot() -> TelegramBot:
    """الحصول على instance واحد من البوت"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot()
    return _bot_instance


def notify(text: str, urgency: str = "normal") -> bool:
    """دالة سريعة لإرسال تنبيه"""
    bot = get_bot()
    return bot.send_alert("Army81", text, urgency)


# ── Entry Point ───────────────────────────────────
if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
