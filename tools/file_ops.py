"""
Army81 Tools - File Operations
أدوات قراءة وكتابة الملفات والتحكم بها مع حماية Sandbox صارمة جداً
"""

import os
import json
import logging
from pathlib import Path
from typing import Union

from core.base_agent import Tool

logger = logging.getLogger("army81.tools.file_ops")

# المجلد الآمن المسموح به (sandbox)
_SANDBOX_ROOT = os.path.abspath(
    os.getenv("SANDBOX_DIR", os.path.join(os.path.dirname(__file__), "..", "sandbox"))
)


def _safe_path(path: str) -> str:
    """التأكد من أن المسار داخل sandbox بشكل قطعي"""
    # تنظيف اسم الملف والمسار
    clean_path = path.lstrip("/\\")
    full = os.path.abspath(os.path.join(_SANDBOX_ROOT, clean_path))

    # تأكد أنه داخل sandbox
    if not full.startswith(_SANDBOX_ROOT):
        raise PermissionError(
            f"ممنوع: المسار '{path}' يحاول الخروج من الـ Sandbox المسموح به وهو {_SANDBOX_ROOT}"
        )

    return full


def _ensure_sandbox():
    """إنشاء مجلد sandbox إذا لم يكن موجوداً"""
    os.makedirs(_SANDBOX_ROOT, exist_ok=True)


def read_file(path: str) -> str:
    """
    قراءة ملف نصي أو JSON بأمان من داخل الـ Sandbox
    """
    try:
        _ensure_sandbox()
        safe = _safe_path(path)

        if not os.path.exists(safe):
            return f"خطأ: الملف '{path}' غير موجود في الـ Sandbox."

        if os.path.getsize(safe) > 10 * 1024 * 1024:  # 10MB limit
            return f"خطأ: الملف كبير جداً (أكثر من 10MB) ولا يمكن قراءته دفعة واحدة."

        with open(safe, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return content

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        return f"خطأ في الصلاحيات: {e}"
    except Exception as e:
        logger.error(f"read_file error: {e}")
        return f"خطأ غير متوقع في قراءة الملف: {e}"


def write_file(payload: str) -> str:
    """
    كتابة محتوى في ملف بأمان داخل الـ Sandbox.
    توقع أن المدخل يكون بتنسيق: path|content
    """
    try:
        parts = payload.split("|", 1)
        if len(parts) < 2:
            return "خطأ: المعاملات غير صحيحة. يجب أن تكون: path|content"
            
        path, content = parts[0].strip(), parts[1]
        
        _ensure_sandbox()
        safe = _safe_path(path)

        # إنشاء المجلدات الوسيطة في الـ Sandbox بشكل آمن
        os.makedirs(os.path.dirname(safe), exist_ok=True)

        with open(safe, "w", encoding="utf-8") as f:
            f.write(content)

        size = os.path.getsize(safe)
        logger.info(f"Wrote {size} bytes to {safe}")
        return f"تم الحفظ بنجاح: {path} ({size} بايت) داخل بيئة Sandbox."

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        return f"خطأ أمني: {e}"
    except Exception as e:
        logger.error(f"write_file error: {e}")
        return f"خطأ في عملية الكتابة: {e}"


def list_files(directory: str = ".") -> str:
    """عرض قائمة الملفات في مجلد محدد داخل الـ Sandbox"""
    try:
        _ensure_sandbox()
        safe = _safe_path(directory)

        if not os.path.exists(safe) or not os.path.isdir(safe):
            return f"خطأ: '{directory}' ليس مجلداً صحيحاً في الـ Sandbox."

        files = []
        for item in sorted(Path(safe).iterdir()):
            size = item.stat().st_size if item.is_file() else 0
            kind = "📁 Directory:" if item.is_dir() else "📄 File:"
            files.append(f"{kind} {item.name} ({size} بايت)" if item.is_file() else f"{kind} {item.name}/")

        return "\n".join(files) if files else f"المجلد '{directory}' فارغ."

    except PermissionError as e:
        return f"خطأ أمني: {e}"
    except Exception as e:
        return f"خطأ أثناء استعراض الملفات: {e}"


# التسجيل المباشر كأدوات (Tools) لوكلاء Army81
file_read_tool = Tool(
    name="read_file",
    description="تُقرأ محتويات ملف بنص كامل. (المسار داخل Sandbox)",
    func=read_file,
    parameters={"path": "مسار الملف المراد قراءته (نص)"}
)

file_write_tool = Tool(
    name="write_file",
    description="تقوم بكتابة محتوى إلى ملف. استخدم معامل التجزئة: path|content",
    func=write_file,
    parameters={"payload": "سلسلة نصية تحتوي مسار الملف والمحتوى يفصل بينهما | (مثل file.txt|hello world)"}
)

file_list_tool = Tool(
    name="list_files",
    description="استعراض وعرض الملفات الموجودة في الـ Sandbox.",
    func=list_files,
    parameters={"directory": "المسار (اختياري، الافتراضي هو المجلد الجذري)"}
)

# قائمة شاملة لجميع أدوات الملفات
ALL_FILE_TOOLS = [file_read_tool, file_write_tool, file_list_tool]
