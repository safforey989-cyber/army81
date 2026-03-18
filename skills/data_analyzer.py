"""Army81 Skill — Data Analyzer"""
import os
import csv
import json
import logging
from typing import List, Dict

logger = logging.getLogger("army81.skill.data_analyzer")


def analyze_csv(file_path: str) -> str:
    """تحليل ملف CSV وإعطاء ملخص"""
    if not os.path.exists(file_path):
        return f"الملف غير موجود: {file_path}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return "الملف فارغ"

        columns = list(rows[0].keys())
        summary = [
            f"الأعمدة: {len(columns)} — {', '.join(columns[:10])}",
            f"الصفوف: {len(rows)}",
        ]

        # تحليل رقمي بسيط
        for col in columns[:5]:
            values = [r.get(col, "") for r in rows if r.get(col)]
            try:
                nums = [float(v) for v in values if v.replace(".", "").replace("-", "").isdigit()]
                if nums:
                    summary.append(
                        f"  {col}: min={min(nums):.2f}, max={max(nums):.2f}, "
                        f"avg={sum(nums)/len(nums):.2f}"
                    )
            except (ValueError, ZeroDivisionError):
                unique = len(set(values))
                summary.append(f"  {col}: {unique} قيمة فريدة")

        return "\n".join(summary)
    except Exception as e:
        return f"خطأ في تحليل CSV: {e}"


def analyze_json(file_path: str) -> str:
    """تحليل ملف JSON"""
    if not os.path.exists(file_path):
        return f"الملف غير موجود: {file_path}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return f"مصفوفة: {len(data)} عنصر\nالمفاتيح: {list(data[0].keys()) if data else 'فارغ'}"
        elif isinstance(data, dict):
            return f"كائن: {len(data)} مفتاح\nالمفاتيح: {list(data.keys())[:15]}"
        else:
            return f"النوع: {type(data).__name__}, القيمة: {str(data)[:200]}"
    except Exception as e:
        return f"خطأ: {e}"


def quick_stats(numbers: List[float]) -> str:
    """إحصائيات سريعة"""
    if not numbers:
        return "لا توجد أرقام"
    n = len(numbers)
    total = sum(numbers)
    avg = total / n
    sorted_nums = sorted(numbers)
    median = sorted_nums[n // 2] if n % 2 else (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
    return (
        f"العدد: {n}\n"
        f"المجموع: {total:.2f}\n"
        f"المتوسط: {avg:.2f}\n"
        f"الوسيط: {median:.2f}\n"
        f"الأدنى: {min(numbers):.2f}\n"
        f"الأعلى: {max(numbers):.2f}"
    )
