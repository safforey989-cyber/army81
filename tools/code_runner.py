"""
Army81 Tools - Code Runner
تنفيذ كود Python بأمان في بيئة معزولة
"""
import os
import sys
import subprocess
import tempfile
import logging
import time
from typing import Optional

logger = logging.getLogger("army81.tools.code_runner")

# حد زمني للتنفيذ (ثواني)
TIMEOUT_SECONDS = 15

# حجم output أقصى
MAX_OUTPUT_CHARS = 4000

# مكتبات مسموح باستيرادها فقط
ALLOWED_IMPORTS = {
    "math", "random", "json", "re", "datetime", "time",
    "collections", "itertools", "functools", "string",
    "statistics", "decimal", "fractions", "hashlib",
    "base64", "urllib", "os.path", "pathlib",
}

# كلمات محظورة في الكود
BLOCKED_KEYWORDS = [
    "import os", "import sys", "import subprocess",
    "__import__", "exec(", "eval(", "open(",
    "socket", "requests", "urllib.request",
    "shutil", "glob", "os.system", "os.popen",
    "os.remove", "os.unlink", "os.rmdir",
]


def _is_safe_code(code: str) -> tuple[bool, str]:
    """التحقق من أمان الكود قبل تنفيذه"""
    code_lower = code.lower()

    for blocked in BLOCKED_KEYWORDS:
        if blocked.lower() in code_lower:
            return False, f"الكود يحتوي على عملية محظورة: '{blocked}'"

    return True, ""


def run_code_safe(code: str) -> str:
    """
    تنفيذ كود Python بسيط في subprocess معزول
    للحسابات والتحليل البسيط
    """
    is_safe, reason = _is_safe_code(code)
    if not is_safe:
        return f"رُفض تنفيذ الكود: {reason}"

    # اكتب الكود في ملف مؤقت
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        # أضف header آمن
        header = (
            "import math, random, json, re, datetime, time, collections, "
            "itertools, functools, string, statistics\n"
        )
        f.write(header + code)
        tmp_path = f.name

    try:
        start = time.time()

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            # بيئة محدودة
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": "",
            },
        )

        elapsed = round(time.time() - start, 2)
        output = result.stdout + result.stderr

        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + f"\n... (تم اقتطاع الباقي)"

        if result.returncode == 0:
            return f"✅ تم التنفيذ في {elapsed}ث:\n```\n{output.strip()}\n```"
        else:
            return f"❌ خطأ في الكود:\n```\n{output.strip()}\n```"

    except subprocess.TimeoutExpired:
        return f"⏰ انتهت المهلة ({TIMEOUT_SECONDS}ث) — الكود يستغرق وقتاً طويلاً"
    except Exception as e:
        logger.error(f"code_runner error: {e}")
        return f"خطأ في التنفيذ: {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def run_code_e2b(code: str, packages: str = "") -> str:
    """
    تنفيذ كود Python في E2B cloud sandbox (آمن تماماً)
    يتطلب E2B_API_KEY في .env
    """
    api_key = os.getenv("E2B_API_KEY", "")
    if not api_key:
        # fallback لـ safe runner
        logger.info("E2B_API_KEY not set, falling back to safe runner")
        return run_code_safe(code)

    try:
        from e2b_code_interpreter import Sandbox

        with Sandbox(api_key=api_key) as sbx:
            # تثبيت packages إضافية إذا طُلب
            if packages:
                pkg_list = [p.strip() for p in packages.split(",") if p.strip()]
                for pkg in pkg_list:
                    sbx.commands.run(f"pip install {pkg} -q")

            execution = sbx.run_code(code)

            output_parts = []

            if execution.logs.stdout:
                output_parts.append("Output:\n" + "\n".join(execution.logs.stdout))

            if execution.logs.stderr:
                output_parts.append("Errors:\n" + "\n".join(execution.logs.stderr))

            if execution.results:
                for r in execution.results:
                    if hasattr(r, "text"):
                        output_parts.append(str(r.text))

            output = "\n\n".join(output_parts) if output_parts else "لا output"

            if len(output) > MAX_OUTPUT_CHARS:
                output = output[:MAX_OUTPUT_CHARS] + "\n...(مقتطع)"

            return f"✅ E2B تنفيذ:\n```\n{output}\n```"

    except ImportError:
        logger.warning("e2b_code_interpreter not installed, using safe runner")
        return run_code_safe(code)
    except Exception as e:
        logger.error(f"E2B error: {e}")
        return f"خطأ في E2B: {e}\n\nجارٍ التنفيذ المحلي...\n" + run_code_safe(code)


def run_python_snippet(code: str) -> str:
    """دالة مختصرة — تختار التنفيذ الأنسب تلقائياً"""
    if os.getenv("E2B_API_KEY"):
        return run_code_e2b(code)
    return run_code_safe(code)


if __name__ == "__main__":
    print("اختبار code_runner...")
    test_code = """
x = [1, 2, 3, 4, 5]
print("المجموع:", sum(x))
print("المتوسط:", sum(x) / len(x))
import math
print("جذر 144:", math.sqrt(144))
"""
    print(run_code_safe(test_code))
