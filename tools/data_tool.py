"""
Army81 Tools - Data Analyzer
تحليل بيانات CSV وJSON وتلخيصها
"""
import json
import logging
from typing import Union

logger = logging.getLogger("army81.tools.data")


def analyze_data(data: str) -> str:
    """
    تحليل بيانات JSON أو CSV وتلخيصها
    data: نص JSON/CSV أو مسار ملف
    """
    import os

    # إذا كان مساراً لملف
    if os.path.exists(data):
        try:
            with open(data, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"خطأ في قراءة الملف: {e}"
    else:
        content = data

    # جرب JSON أولاً
    try:
        parsed = json.loads(content)
        return _analyze_json(parsed)
    except json.JSONDecodeError:
        pass

    # جرب CSV
    if "," in content or "\t" in content:
        return _analyze_csv(content)

    # نص عادي
    lines = content.strip().splitlines()
    words = content.split()
    return (
        f"**تحليل النص:**\n"
        f"- الأسطر: {len(lines)}\n"
        f"- الكلمات: {len(words)}\n"
        f"- الأحرف: {len(content)}\n"
        f"- عينة: {content[:200]}..."
    )


def _analyze_json(data) -> str:
    """تحليل بيانات JSON"""
    if isinstance(data, list):
        total = len(data)
        sample = data[:3] if total > 3 else data
        keys = list(sample[0].keys()) if sample and isinstance(sample[0], dict) else []
        return (
            f"**تحليل JSON (قائمة):**\n"
            f"- عدد السجلات: {total}\n"
            f"- الحقول: {', '.join(keys) if keys else 'غير محدد'}\n"
            f"- عينة (أول 3):\n```json\n{json.dumps(sample, ensure_ascii=False, indent=2)}\n```"
        )
    elif isinstance(data, dict):
        return (
            f"**تحليل JSON (كائن):**\n"
            f"- عدد المفاتيح: {len(data)}\n"
            f"- المفاتيح: {', '.join(list(data.keys())[:10])}\n"
            f"- البيانات:\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:500]}\n```"
        )
    return f"بيانات JSON: {str(data)[:200]}"


def _analyze_csv(content: str) -> str:
    """تحليل بيانات CSV"""
    lines = [l.strip() for l in content.strip().splitlines() if l.strip()]
    if not lines:
        return "ملف CSV فارغ"

    # تحديد الفاصل
    sep = "\t" if "\t" in lines[0] else ","
    headers = [h.strip() for h in lines[0].split(sep)]
    rows = lines[1:]

    # إحصائيات بسيطة
    result = [
        f"**تحليل CSV:**",
        f"- الأعمدة ({len(headers)}): {', '.join(headers[:10])}",
        f"- عدد الصفوف: {len(rows)}",
    ]

    # عينة
    if rows:
        result.append(f"\n**أول 3 صفوف:**")
        for row in rows[:3]:
            cells = row.split(sep)
            result.append("  " + " | ".join(cells[:10]))

    return "\n".join(result)


if __name__ == "__main__":
    test_json = '[{"name": "A01", "category": "leadership"}, {"name": "A02", "category": "science"}]'
    print(analyze_data(test_json))
