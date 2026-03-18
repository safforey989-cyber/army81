"""
Army81 - Agents Registry
ربط كل وكيل بأدواته المناسبة
يُستخدم عند تحميل الوكلاء لتحديد أدواتهم تلقائياً
"""
import logging
from typing import Dict, List

logger = logging.getLogger("army81.agents.registry")

# ── خريطة الأدوات لكل وكيل ────────────────────────────────────
# كل وكيل مربوط بأدوات تناسب تخصصه

AGENT_TOOLS: Dict[str, List[str]] = {
    # ══════════════════════════════════════════════════════════════
    # cat6_leadership — القيادة العليا
    # ══════════════════════════════════════════════════════════════
    "A01": ["web_search", "deep_search", "arxiv_search", "remember", "recall", "fetch_news"],
    "A28": ["web_search", "deep_search", "wiki_search", "remember"],       # استراتيجي عسكري
    "A29": ["web_search", "fetch_news", "deep_search", "remember"],         # إدارة أزمات
    "A30": ["web_search", "arxiv_search", "github_search", "deep_search"],  # ابتكار
    "A31": ["web_search", "deep_search", "wiki_search", "remember"],        # استخبارات
    "A32": ["web_search", "deep_search", "wiki_search", "market_data"],     # جيوسياسة
    "A33": ["web_search", "deep_search", "arxiv_search", "fetch_news"],     # استشراف
    "A34": ["web_search", "deep_search", "market_data", "remember"],        # مخاطر
    "A35": ["web_search", "deep_search", "wiki_search", "remember"],        # تغيير
    "A36": ["web_search", "deep_search", "market_data", "remember"],        # منظمات
    "A37": ["web_search", "deep_search", "remember", "recall"],             # قرارات
    "A67": ["web_search", "deep_search", "wiki_search"],                    # تواصل إنساني
    "A68": ["web_search", "market_data", "remember", "recall"],             # توزيع موارد
    "A69": ["web_search", "deep_search", "remember", "recall"],             # تقييم شامل
    "A70": ["web_search", "arxiv_search", "deep_search", "github_search"],  # ابتكار جذري
    "A71": ["web_search", "deep_search", "fetch_news", "remember"],         # أمن داخلي

    # ══════════════════════════════════════════════════════════════
    # cat1_science — العلوم
    # ══════════════════════════════════════════════════════════════
    "A02": ["arxiv_search", "pubmed_search", "web_search", "deep_search", "run_code"],  # بحث علمي
    "A07": ["pubmed_search", "arxiv_search", "web_search", "deep_search"],               # طب
    "A38": ["arxiv_search", "web_search", "deep_search", "run_code"],                    # فيزياء/كم
    "A39": ["arxiv_search", "web_search", "deep_search", "fetch_news"],                  # مناخ
    "A40": ["arxiv_search", "github_search", "web_search", "deep_search"],               # تقنيات
    "A52": ["pubmed_search", "arxiv_search", "web_search", "deep_search"],               # طب سريري
    "A53": ["arxiv_search", "web_search", "deep_search", "run_code"],                    # تصنيع
    "A54": ["arxiv_search", "github_search", "web_search", "run_code"],                  # روبوتات
    "A55": ["arxiv_search", "web_search", "deep_search", "fetch_news"],                  # فضاء/دفاع

    # ══════════════════════════════════════════════════════════════
    # cat2_society — المجتمع
    # ══════════════════════════════════════════════════════════════
    "A03": ["web_search", "deep_search", "wiki_search", "fetch_news"],      # سياسات
    "A08": ["market_data", "web_search", "deep_search", "fetch_news"],      # مالي
    "A12": ["web_search", "deep_search", "fetch_news", "write_file"],       # محتوى
    "A13": ["web_search", "deep_search", "wiki_search"],                    # قانون
    "A41": ["market_data", "web_search", "fetch_news", "deep_search"],      # اقتصاد عالمي
    "A42": ["market_data", "web_search", "fetch_news", "deep_search"],      # عملات رقمية
    "A43": ["wiki_search", "web_search", "deep_search"],                    # تاريخ
    "A44": ["web_search", "fetch_news", "deep_search"],                     # إعلام
    "A45": ["web_search", "deep_search", "wiki_search"],                    # قانون دولي
    "A46": ["web_search", "deep_search", "wiki_search"],                    # فنون
    "A47": ["web_search", "wiki_search", "deep_search"],                    # لغويات
    "A48": ["run_code", "web_search", "arxiv_search"],                      # رياضيات
    "A49": ["web_search", "deep_search", "wiki_search", "fetch_news"],      # اجتماع
    "A50": ["web_search", "deep_search", "wiki_search", "fetch_news"],      # تعليم
    "A51": ["web_search", "github_search", "deep_search", "run_code"],      # هندسة عكسية

    # ══════════════════════════════════════════════════════════════
    # cat3_tools — الأدوات
    # ══════════════════════════════════════════════════════════════
    "A04": ["web_search", "fetch_news", "deep_search", "remember"],             # إعلام ذكي
    "A05": ["run_code", "github_search", "web_search", "read_file", "write_file"],  # مطور
    "A09": ["web_search", "deep_search", "arxiv_search", "github_search"],      # أمن
    "A11": ["web_search", "wiki_search", "remember"],                           # ترجمة
    "A56": ["web_search", "fetch_news", "deep_search", "remember"],             # استخبارات وسائط
    "A57": ["web_search", "github_search", "run_code", "read_file"],            # تكامل أنظمة
    "A58": ["web_search", "fetch_news", "deep_search", "remember"],             # إنذار مبكر
    "A59": ["web_search", "arxiv_search", "github_search", "deep_search"],      # ابتكار مفتوح
    "A60": ["web_search", "fetch_news", "deep_search", "remember"],             # مكافحة تضليل
    "A61": ["arxiv_search", "pubmed_search", "run_code", "web_search"],         # بيولوجيا حسابية

    # ══════════════════════════════════════════════════════════════
    # cat4_management — الإدارة
    # ══════════════════════════════════════════════════════════════
    "A06": ["analyze_data", "run_code", "market_data", "web_search"],       # تحليل بيانات
    "A10": ["remember", "recall", "semantic_remember", "semantic_recall", "wiki_search"],  # معرفة
    "A14": ["analyze_data", "read_file", "write_file", "web_search"],       # مشاريع
    "A62": ["web_search", "deep_search", "remember", "recall"],             # حوكمة
    "A63": ["web_search", "deep_search", "market_data", "remember"],        # منظمات كبرى
    "A64": ["web_search", "analyze_data", "read_file", "write_file"],       # مشاريع ضخمة
    "A65": ["web_search", "deep_search", "github_search", "remember"],      # تحول رقمي
    "A66": ["analyze_data", "web_search", "remember", "recall"],            # أداء

    # ══════════════════════════════════════════════════════════════
    # cat5_behavior — السلوك
    # ══════════════════════════════════════════════════════════════
    "A15": ["web_search", "deep_search", "wiki_search", "pubmed_search"],   # علم نفس
    "A16": ["web_search", "deep_search", "wiki_search"],                    # تفاوض
    "A17": ["web_search", "deep_search", "wiki_search"],                    # لغة جسد
    "A18": ["web_search", "deep_search", "wiki_search"],                    # إقناع
    "A19": ["web_search", "deep_search", "wiki_search"],                    # ذكاء عاطفي
    "A20": ["web_search", "deep_search", "wiki_search"],                    # ديناميكيات اجتماعية
    "A21": ["web_search", "fetch_news", "deep_search"],                     # جماهير
    "A22": ["web_search", "deep_search", "market_data"],                    # اقتصاد سلوكي
    "A23": ["web_search", "deep_search", "wiki_search"],                    # نزاعات
    "A24": ["web_search", "deep_search", "wiki_search"],                    # قيادة
    "A25": ["web_search", "deep_search", "wiki_search"],                    # تواصل
    "A26": ["web_search", "deep_search", "wiki_search"],                    # قرار
    "A27": ["web_search", "deep_search", "wiki_search"],                    # ثقافي

    # ══════════════════════════════════════════════════════════════
    # cat7_new — التطور الذاتي
    # ══════════════════════════════════════════════════════════════
    "A72": ["web_search", "remember", "recall", "analyze_data"],            # مراقبة تطور
    "A73": ["web_search", "remember", "recall"],                            # تنسيق وكلاء
    "A74": ["web_search", "remember", "recall", "analyze_data"],            # ضبط جودة
    "A75": ["web_search", "arxiv_search", "github_search", "remember"],     # تحسين نظام
    "A76": ["remember", "recall", "semantic_remember", "semantic_recall"],   # تجميع تعلم
    "A77": ["web_search", "remember", "recall"],                            # سير عمل
    "A78": ["analyze_data", "remember", "recall", "market_data"],           # تخصيص موارد
    "A79": ["web_search", "remember", "recall"],                            # تغذية راجعة
    "A80": ["web_search", "remember", "recall", "analyze_data"],            # أنماط
    "A81": ["web_search", "deep_search", "remember", "recall", "arxiv_search"],  # ميتا استخباراتي
}


def get_tools_for_agent(agent_id: str) -> List[str]:
    """إرجاع قائمة أسماء الأدوات لوكيل معين"""
    return AGENT_TOOLS.get(agent_id, ["web_search"])


def get_agents_with_tool(tool_name: str) -> List[str]:
    """إرجاع قائمة الوكلاء الذين يملكون أداة معينة"""
    return [aid for aid, tools in AGENT_TOOLS.items() if tool_name in tools]


def get_category_agents(category: str) -> Dict[str, List[str]]:
    """إرجاع خريطة الأدوات لوكلاء فئة معينة"""
    # خريطة الفئات
    cat_prefixes = {
        "cat1_science": ["A02", "A07", "A38", "A39", "A40", "A52", "A53", "A54", "A55"],
        "cat2_society": ["A03", "A08", "A12", "A13", "A41", "A42", "A43", "A44", "A45",
                         "A46", "A47", "A48", "A49", "A50", "A51"],
        "cat3_tools": ["A04", "A05", "A09", "A11", "A56", "A57", "A58", "A59", "A60", "A61"],
        "cat4_management": ["A06", "A10", "A14", "A62", "A63", "A64", "A65", "A66"],
        "cat5_behavior": [f"A{i}" for i in range(15, 28)],
        "cat6_leadership": ["A01", "A28", "A29", "A30", "A31", "A32", "A33", "A34",
                            "A35", "A36", "A37", "A67", "A68", "A69", "A70", "A71"],
        "cat7_new": [f"A{i}" for i in range(72, 82)],
    }

    agents = cat_prefixes.get(category, [])
    return {aid: AGENT_TOOLS.get(aid, []) for aid in agents}


def validate_registry() -> Dict:
    """التحقق من صحة السجل"""
    issues = []
    total_agents = len(AGENT_TOOLS)
    all_tools = set()

    for agent_id, tools in AGENT_TOOLS.items():
        all_tools.update(tools)
        if not tools:
            issues.append(f"{agent_id}: لا أدوات مُعرّفة")

    return {
        "total_agents": total_agents,
        "unique_tools": len(all_tools),
        "tools_list": sorted(all_tools),
        "issues": issues,
        "valid": len(issues) == 0,
    }


if __name__ == "__main__":
    report = validate_registry()
    print(f"\n{'='*50}")
    print(f"  سجل الوكلاء — التقرير")
    print(f"{'='*50}")
    print(f"  الوكلاء: {report['total_agents']}")
    print(f"  الأدوات الفريدة: {report['unique_tools']}")
    print(f"  الأدوات: {', '.join(report['tools_list'])}")
    if report['issues']:
        print(f"\n  مشاكل:")
        for issue in report['issues']:
            print(f"    ⚠ {issue}")
    else:
        print(f"\n  ✅ كل شيء سليم!")
    print(f"{'='*50}\n")
