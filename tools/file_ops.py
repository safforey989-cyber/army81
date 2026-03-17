"""
Army81 Tools - File Operations
قراءة وكتابة الملفات بأمان مع sandbox
"""
import os
import json
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger("army81.tools.file_ops")

# المجلد الآمن المسموح به (sandbox)
_SANDBOX_ROOT = os.path.abspath(
    os.getenv("SANDBOX_DIR", os.path.join(os.path.dirname(__file__), "..", "workspace"))
)


def _safe_path(path: str) -> str:
    """التأكد من أن المسار داخل sandbox"""
    # إذا كان المسار نسبياً، اجعله داخل sandbox
    if not os.path.isabs(path):
        full = os.path.abspath(os.path.join(_SANDBOX_ROOT, path))
    else:
        full = os.path.abspath(path)

    # تأكد أنه داخل sandbox
    if not full.startswith(_SANDBOX_ROOT):
        raise PermissionError(
            f"المسار '{path}' خارج نطاق الـ sandbox المسموح به: {_SANDBOX_ROOT}"
        )

    return full


def _ensure_sandbox():
    """إنشاء مجلد workspace إذا لم يكن موجوداً"""
    os.makedirs(_SANDBOX_ROOT, exist_ok=True)


def read_file(path: str) -> str:
    """
    قراءة ملف نصي أو JSON بأمان
    يدعم: .txt, .md, .json, .csv, .py, .yaml
    """
    try:
        _ensure_sandbox()
        safe = _safe_path(path)

        if not os.path.exists(safe):
            return f"خطأ: الملف '{path}' غير موجود"

        if os.path.getsize(safe) > 5 * 1024 * 1024:  # 5MB limit
            return f"خطأ: الملف كبير جداً (أكثر من 5MB)"

        with open(safe, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # إذا كان JSON، نعيده منسّقاً
        if safe.endswith(".json"):
            try:
                data = json.loads(content)
                return json.dumps(data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass

        return content

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        return f"خطأ في الصلاحيات: {e}"
    except Exception as e:
        logger.error(f"read_file error: {e}")
        return f"خطأ في قراءة الملف: {e}"


def write_file(path: str, content: str) -> str:
    """
    كتابة محتوى في ملف بأمان
    يُنشئ المجلدات الوسيطة تلقائياً
    """
    try:
        _ensure_sandbox()
        safe = _safe_path(path)

        # إنشاء المجلدات الوسيطة
        os.makedirs(os.path.dirname(safe), exist_ok=True)

        with open(safe, "w", encoding="utf-8") as f:
            f.write(content)

        size = os.path.getsize(safe)
        logger.info(f"Wrote {size} bytes to {safe}")
        return f"تم الحفظ بنجاح: {path} ({size} بايت)"

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        return f"خطأ في الصلاحيات: {e}"
    except Exception as e:
        logger.error(f"write_file error: {e}")
        return f"خطأ في الكتابة: {e}"


def append_file(path: str, content: str) -> str:
    """إضافة محتوى لملف موجود"""
    try:
        _ensure_sandbox()
        safe = _safe_path(path)
        os.makedirs(os.path.dirname(safe), exist_ok=True)

        with open(safe, "a", encoding="utf-8") as f:
            f.write(content)

        return f"تمت الإضافة إلى: {path}"

    except PermissionError as e:
        return f"خطأ في الصلاحيات: {e}"
    except Exception as e:
        return f"خطأ: {e}"


def list_files(directory: str = ".") -> str:
    """عرض قائمة الملفات في مجلد"""
    try:
        _ensure_sandbox()
        safe = _safe_path(directory)

        if not os.path.isdir(safe):
            return f"خطأ: '{directory}' ليس مجلداً"

        files = []
        for item in sorted(Path(safe).iterdir()):
            size = item.stat().st_size if item.is_file() else 0
            kind = "📁" if item.is_dir() else "📄"
            files.append(f"{kind} {item.name} ({size} بايت)" if item.is_file() else f"{kind} {item.name}/")

        return "\n".join(files) if files else "المجلد فارغ"

    except PermissionError as e:
        return f"خطأ في الصلاحيات: {e}"
    except Exception as e:
        return f"خطأ: {e}"


def delete_file(path: str) -> str:
    """حذف ملف من workspace"""
    try:
        _ensure_sandbox()
        safe = _safe_path(path)

        if not os.path.exists(safe):
            return f"الملف '{path}' غير موجود"

        os.remove(safe)
        return f"تم حذف: {path}"

    except PermissionError as e:
        return f"خطأ في الصلاحيات: {e}"
    except Exception as e:
        return f"خطأ: {e}"


if __name__ == "__main__":
    print("اختبار file_ops...")
    print(write_file("test.txt", "مرحباً من Army81!\n"))
    print(read_file("test.txt"))
    print(list_files("."))
    print(delete_file("test.txt"))
