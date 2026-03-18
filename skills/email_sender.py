"""Army81 Skill — Email Sender (SMTP)"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("army81.skill.email_sender")


def send_email(to: str, subject: str, body: str, html: bool = False) -> str:
    """
    إرسال بريد إلكتروني عبر SMTP
    يحتاج: EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD في .env
    """
    smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    user = os.getenv("EMAIL_USER", "")
    password = os.getenv("EMAIL_PASSWORD", "")

    if not user or not password:
        return "خطأ: EMAIL_USER و EMAIL_PASSWORD غير موجودين في .env"

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = user
        msg["To"] = to
        msg["Subject"] = subject

        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        logger.info(f"Email sent to {to}: {subject}")
        return f"تم إرسال البريد إلى {to}"
    except Exception as e:
        return f"خطأ في إرسال البريد: {e}"


def check_email_config() -> str:
    """تحقق من إعدادات البريد"""
    user = os.getenv("EMAIL_USER", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    if user and password:
        return f"البريد جاهز: {user}"
    return "البريد غير مُعد. أضف EMAIL_USER و EMAIL_PASSWORD في .env"
