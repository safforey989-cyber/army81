#!/usr/bin/env python3
"""
Army81 - إضافة وكيل جديد
الاستخدام:
  python scripts/add_agent.py --id A82 --name "Agent Name" --name_ar "اسم عربي" \
    --category cat2_science --model gemini-1.5-flash --tools web_search,file_ops \
    --description "وصف الوكيل"
"""
import argparse
import json
import os
import sys

# مسار المشروع
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(PROJECT_DIR, "agents")

# القوالب الافتراضية للـ system prompt حسب الفئة
CATEGORY_PROMPTS = {
    "cat1_science": "أنت وكيل متخصص في العلوم والبحث العلمي ضمن منظومة Army81. مهمتك تحليل الأبحاث العلمية وتقديم إجابات دقيقة مبنية على الأدلة.",
    "cat2_society": "أنت وكيل متخصص في شؤون المجتمع والسياسات ضمن منظومة Army81. مهمتك تحليل القضايا الاجتماعية والسياسية والاقتصادية.",
    "cat3_tools": "أنت وكيل أدوات تقنية ضمن منظومة Army81. مهمتك تقديم حلول تقنية ومعالجة البيانات والبرمجة.",
    "cat4_management": "أنت وكيل إداري ضمن منظومة Army81. مهمتك إدارة المشاريع واتخاذ القرارات وتحليل الأداء.",
    "cat5_behavior": "أنت وكيل سلوكي ضمن منظومة Army81. مهمتك تحليل السلوك البشري والنفسي والاجتماعي.",
    "cat6_leadership": "أنت وكيل قيادي ضمن منظومة Army81. مهمتك التخطيط الاستراتيجي واتخاذ القرارات الكبرى.",
    "cat7_new": "أنت وكيل متطور ضمن منظومة Army81. مهمتك مراقبة النظام وتحسينه باستمرار.",
}

VALID_MODELS = [
    "gemini-flash", "gemini-fast", "gemini-pro", "gemini-think",
    "claude-haiku", "claude-sonnet", "local-coder", "local-fast",
]


def create_agent(args):
    """إنشاء ملف JSON لوكيل جديد"""

    # تحقق من الفئة
    cat_dir = os.path.join(AGENTS_DIR, args.category)
    if not os.path.isdir(cat_dir):
        os.makedirs(cat_dir, exist_ok=True)
        print(f"📁 أُنشئ مجلد الفئة: {args.category}")

    # تحقق من عدم التكرار
    existing_files = [f for f in os.listdir(cat_dir) if f.endswith(".json")]
    for f in existing_files:
        with open(os.path.join(cat_dir, f), "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if data.get("agent_id") == args.id:
                print(f"❌ الوكيل {args.id} موجود بالفعل في {f}")
                sys.exit(1)

    # بناء system prompt
    base_prompt = CATEGORY_PROMPTS.get(args.category, CATEGORY_PROMPTS["cat3_tools"])
    system_prompt = args.system_prompt or f"{base_prompt}\n\nاسمك: {args.name_ar}\nمعرّفك: {args.id}\n\nأجب دائماً بدقة ووضوح. إذا لم تكن متأكداً قل ذلك."

    # بناء الوكيل
    agent_data = {
        "agent_id": args.id,
        "name": args.name,
        "name_ar": args.name_ar,
        "category": args.category,
        "description": args.description or f"وكيل {args.name_ar}",
        "model": args.model,
        "tools": [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools else ["web_search"],
        "system_prompt": system_prompt,
    }

    # اسم الملف
    safe_name = args.name.lower().replace(" ", "_").replace("-", "_")
    filename = f"{args.id}_{safe_name}.json"
    filepath = os.path.join(cat_dir, filename)

    # الحفظ
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(agent_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ تم إنشاء الوكيل بنجاح!")
    print(f"   📄 الملف: {filepath}")
    print(f"   🆔 المعرّف: {args.id}")
    print(f"   📛 الاسم: {args.name_ar} ({args.name})")
    print(f"   📂 الفئة: {args.category}")
    print(f"   🤖 النموذج: {args.model}")
    print(f"   🔧 الأدوات: {agent_data['tools']}")

    return filepath


def main():
    parser = argparse.ArgumentParser(description="إضافة وكيل جديد لـ Army81")
    parser.add_argument("--id", required=True, help="معرّف الوكيل (مثل A82)")
    parser.add_argument("--name", required=True, help="اسم الوكيل بالإنجليزية")
    parser.add_argument("--name_ar", default=None, help="اسم الوكيل بالعربية")
    parser.add_argument("--category", required=True, choices=[
        "cat1_science", "cat2_society", "cat3_tools",
        "cat4_management", "cat5_behavior", "cat6_leadership", "cat7_new"
    ], help="فئة الوكيل")
    parser.add_argument("--model", default="gemini-flash", choices=VALID_MODELS,
                       help="النموذج (افتراضي: gemini-flash)")
    parser.add_argument("--tools", default="web_search",
                       help="الأدوات مفصولة بفواصل (مثل: web_search,file_ops)")
    parser.add_argument("--description", default=None, help="وصف الوكيل")
    parser.add_argument("--system_prompt", default=None, help="system prompt مخصص")

    args = parser.parse_args()

    # اسم عربي افتراضي
    if not args.name_ar:
        args.name_ar = f"وكيل {args.name}"

    create_agent(args)


if __name__ == "__main__":
    main()
