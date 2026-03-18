"""
Army81 - Tools Registry
سجل كل الأدوات المتاحة للوكلاء
أضف أداة جديدة هنا وستصبح متاحة لكل الوكلاء فوراً
"""
import os
import logging
from typing import Dict
from core.base_agent import Tool

logger = logging.getLogger("army81.tools")


def _lazy_import(module_path: str, func_name: str):
    """تحميل أداة عند الحاجة فقط"""
    def wrapper(*args, **kwargs):
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, func_name)(*args, **kwargs)
    return wrapper


def build_tools_registry() -> Dict[str, Tool]:
    """
    بناء سجل الأدوات الكامل
    كل أداة لها: اسم، وصف، دالة تنفيذ
    """
    registry = {}

    # ── 1. البحث والمعلومات ─────────────────────────────

    registry["web_search"] = Tool(
        name="web_search",
        description="بحث على الإنترنت للحصول على معلومات حديثة ودقيقة",
        func=_lazy_import("tools.web_search", "web_search"),
        parameters={"query": "نص البحث"}
    )

    registry["fetch_news"] = Tool(
        name="fetch_news",
        description="جلب أخبار حديثة حول موضوع معين",
        func=_lazy_import("tools.web_search", "fetch_news"),
        parameters={"topic": "الموضوع", "lang": "اللغة (ar/en)"}
    )

    # LangSearch / Tavily — بحث عميق للوكلاء
    if os.getenv("LANGSEARCH_API_KEY") or os.getenv("TAVILY_API_KEY"):
        registry["deep_search"] = Tool(
            name="deep_search",
            description="بحث عميق مع محتوى كامل — أفضل من web_search للمهام المعقدة (LangSearch/Tavily)",
            func=_lazy_import("tools.web_search", "deep_search"),
            parameters={"query": "سؤال أو موضوع"}
        )

    # Perplexity — بحث أكاديمي
    if os.getenv("PERPLEXITY_API_KEY"):
        registry["research"] = Tool(
            name="research",
            description="بحث أكاديمي عميق مع استشهادات — للمهام البحثية الجادة",
            func=_lazy_import("tools.perplexity_search", "research"),
            parameters={"query": "سؤال بحثي"}
        )

    # arXiv — أبحاث علمية
    registry["arxiv_search"] = Tool(
        name="arxiv_search",
        description="البحث في أحدث الأبحاث العلمية على arXiv",
        func=_lazy_import("tools.arxiv_tool", "search_arxiv"),
        parameters={"query": "موضوع البحث", "max_results": "عدد النتائج"}
    )

    # GitHub — رصد المستودعات
    if os.getenv("GITHUB_TOKEN"):
        registry["github_search"] = Tool(
            name="github_search",
            description="البحث في GitHub عن مستودعات ومشاريع مفتوحة المصدر",
            func=_lazy_import("tools.github_tool", "search_repos"),
            parameters={"query": "نص البحث", "sort": "stars/updated/forks"}
        )

    # ── 2. الملفات والبيانات ─────────────────────────────

    registry["read_file"] = Tool(
        name="read_file",
        description="قراءة محتوى ملف نصي أو JSON",
        func=_lazy_import("tools.file_ops", "read_file"),
        parameters={"path": "مسار الملف"}
    )

    registry["write_file"] = Tool(
        name="write_file",
        description="كتابة أو حفظ محتوى في ملف",
        func=_lazy_import("tools.file_ops", "write_file"),
        parameters={"path": "مسار الملف", "content": "المحتوى"}
    )

    registry["analyze_data"] = Tool(
        name="analyze_data",
        description="تحليل بيانات CSV أو JSON وتلخيصها",
        func=_lazy_import("tools.data_tool", "analyze_data"),
        parameters={"data": "البيانات أو مسار الملف"}
    )

    # ── 3. تنفيذ الكود ───────────────────────────────────

    # E2B — تنفيذ كود آمن في cloud
    if os.getenv("E2B_API_KEY"):
        registry["run_code"] = Tool(
            name="run_code",
            description="تنفيذ كود Python في بيئة آمنة معزولة ومشاهدة النتيجة",
            func=_lazy_import("tools.code_runner", "run_code_e2b"),
            parameters={"code": "كود Python", "packages": "مكتبات إضافية"}
        )
    else:
        registry["run_code"] = Tool(
            name="run_code",
            description="تنفيذ كود Python بسيط وآمن",
            func=_lazy_import("tools.code_runner", "run_code_safe"),
            parameters={"code": "كود Python بسيط"}
        )

    # ── 4. أدوات متخصصة ──────────────────────────────────

    # PubMed — للوكيل الطبي
    registry["pubmed_search"] = Tool(
        name="pubmed_search",
        description="البحث في الأبحاث الطبية على PubMed",
        func=_lazy_import("tools.pubmed_tool", "search_pubmed"),
        parameters={"query": "موضوع طبي", "max_results": "عدد النتائج"}
    )

    # Yahoo Finance — للوكيل الاقتصادي
    registry["market_data"] = Tool(
        name="market_data",
        description="الحصول على بيانات الأسواق المالية والعملات",
        func=_lazy_import("tools.finance_tool", "get_market_data"),
        parameters={"symbol": "رمز السهم أو العملة"}
    )

    # Wikipedia — معلومات عامة
    registry["wiki_search"] = Tool(
        name="wiki_search",
        description="البحث في Wikipedia للحصول على معلومات موثوقة",
        func=_lazy_import("tools.wiki_tool", "search_wikipedia"),
        parameters={"query": "الموضوع", "lang": "اللغة ar/en"}
    )

    # ── 5. الذاكرة والتخزين ──────────────────────────────

    registry["remember"] = Tool(
        name="remember",
        description="حفظ معلومة مهمة في الذاكرة الدائمة للنظام",
        func=_lazy_import("memory.memory_ops", "save_memory"),
        parameters={"key": "مفتاح", "value": "القيمة", "agent_id": "معرف الوكيل"}
    )

    registry["recall"] = Tool(
        name="recall",
        description="استرجاع معلومة محفوظة من الذاكرة",
        func=_lazy_import("memory.memory_ops", "get_memory"),
        parameters={"query": "ما تبحث عنه"}
    )

    # Chroma — ذاكرة دلالية (تذكر المفاهيم لا فقط الكلمات)
    registry["semantic_remember"] = Tool(
        name="semantic_remember",
        description="حفظ معلومة في الذاكرة الدلالية — يمكن استرجاعها لاحقاً بالمفاهيم لا بالكلمات الحرفية",
        func=_lazy_import("memory.chroma_memory", "remember"),
        parameters={"content": "المحتوى", "agent_id": "معرف الوكيل", "tags": "وسوم للتصنيف"}
    )

    registry["semantic_recall"] = Tool(
        name="semantic_recall",
        description="استرجاع المعلومات ذات الصلة من الذاكرة الدلالية — يفهم المعنى لا الكلمات",
        func=_lazy_import("memory.chroma_memory", "recall"),
        parameters={"query": "سؤال أو موضوع", "n_results": "عدد النتائج"}
    )

    logger.info(f"Tools registry built: {len(registry)} tools available")
    return registry


# قائمة الأدوات لكل فئة وكلاء
CATEGORY_TOOLS = {
    "cat1_science": ["web_search", "arxiv_search", "pubmed_search", "research", "run_code"],
    "cat2_society": ["web_search", "fetch_news", "deep_search", "wiki_search", "market_data"],
    "cat3_tools": ["web_search", "fetch_news", "github_search", "arxiv_search", "remember", "recall"],
    "cat4_management": ["web_search", "analyze_data", "read_file", "write_file", "remember"],
    "cat5_behavior": ["web_search", "deep_search", "wiki_search", "research"],
    "cat6_leadership": ["web_search", "deep_search", "research", "market_data", "remember", "recall"],
}


if __name__ == "__main__":
    tools = build_tools_registry()
    print(f"\n✅ {len(tools)} أداة متاحة:")
    for name, tool in tools.items():
        print(f"  - {name}: {tool.description[:60]}...")
