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
        description="جلب أخبار حديثة حول موضوع معين من NewsAPI",
        func=_lazy_import("tools.news_fetcher", "fetch_news"),
        parameters={"topic": "الموضوع", "days_back": "عدد الأيام", "num_articles": "عدد المقالات المطلوبة"}
    )

    # LangSearch / Tavily — بحث عميق للوكلاء
    # ملاحظة: نجعله متاحاً دائماً مع fallback إلى web_search
    # حتى لا تفشل تعريفات الوكلاء التي تعتمد عليه عند غياب المفاتيح.
    registry["deep_search"] = Tool(
        name="deep_search",
        description="بحث عميق مع محتوى كامل — يستخدم LangSearch/Tavily عند توفره، وإلا يعود لـ web_search",
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
    # متاح دائماً: بدون GITHUB_TOKEN يعمل بحدود أقل (rate limits).
    registry["github_search"] = Tool(
        name="github_search",
        description="البحث في GitHub عن مستودعات ومشاريع مفتوحة المصدر (بدون token قد تتأثر الحدود)",
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
        parameters={"payload": "المحتوى والمسار بصيغة: path|content"}
    )

    registry["list_files"] = Tool(
        name="list_files",
        description="استعراض الملفات الموجودة في مجلد الأمان Sandbox",
        func=_lazy_import("tools.file_ops", "list_files"),
        parameters={"directory": "المسار (اختياري)"}
    )

    registry["analyze_data"] = Tool(
        name="analyze_data",
        description="تحليل بيانات CSV أو JSON وتلخيصها",
        func=_lazy_import("tools.data_tool", "analyze_data"),
        parameters={"data": "البيانات أو مسار الملف"}
    )

    # ── 3. تنفيذ الكود ───────────────────────────────────

    # Docker Container - Isolation Engine
    registry["run_code"] = Tool(
        name="run_code",
        description="تنفيذ كود Python حقيقي بأمان تام في حاوية دوكر Docker معزولة (Sandbox/Isolation) وتعيد العوائد (stdout/stderr).",
        func=_lazy_import("tools.code_runner", "run_code_docker"),
        parameters={"code": "الكود البرمجي الكامل بلغة Python"}
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

    # ── 6. v6: أدوات متقدمة جديدة ─────────────────────────

    # Brave Search — بحث خاص
    if os.getenv("BRAVE_API_KEY"):
        registry["brave_search"] = Tool(
            name="brave_search",
            description="بحث خاص عبر Brave — خصوصية عالية ونتائج دقيقة",
            func=_lazy_import("core.execution_engine", "_brave_search_wrapper"),
            parameters={"query": "نص البحث"}
        )

    # Polygon.io — بيانات مالية حية
    if os.getenv("POLYGON_API_KEY"):
        registry["stock_data"] = Tool(
            name="stock_data",
            description="بيانات أسهم حية — أسعار، حجم تداول، تغيرات يومية",
            func=_lazy_import("core.execution_engine", "_polygon_ticker_wrapper"),
            parameters={"symbol": "رمز السهم (مثال: AAPL, MSFT)"}
        )
        registry["stock_search"] = Tool(
            name="stock_search",
            description="بحث عن أسهم بالاسم أو الرمز",
            func=_lazy_import("core.execution_engine", "_polygon_search_wrapper"),
            parameters={"query": "اسم أو رمز السهم"}
        )

    # GitHub Enhanced — بحث كود
    if os.getenv("GITHUB_TOKEN"):
        registry["github_code"] = Tool(
            name="github_code",
            description="بحث في كود المصدر على GitHub",
            func=_lazy_import("core.execution_engine", "_github_code_wrapper"),
            parameters={"query": "نص البحث في الكود"}
        )
        registry["github_trending"] = Tool(
            name="github_trending",
            description="المستودعات الرائجة هذا الأسبوع على GitHub",
            func=_lazy_import("core.execution_engine", "_github_trending_wrapper"),
            parameters={"language": "لغة البرمجة (python, javascript...)"}
        )

    # HuggingFace — نماذج متخصصة
    if os.getenv("HF_TOKEN"):
        registry["hf_generate"] = Tool(
            name="hf_generate",
            description="توليد نص عبر نموذج HuggingFace متخصص",
            func=_lazy_import("core.execution_engine", "_hf_generate_wrapper"),
            parameters={"prompt": "النص المطلوب"}
        )
        registry["hf_classify"] = Tool(
            name="hf_classify",
            description="تصنيف نص تلقائياً (موضوع، مشاعر، فئة)",
            func=_lazy_import("core.execution_engine", "_hf_classify_wrapper"),
            parameters={"text": "النص", "labels": "التصنيفات (مفصولة بفاصلة)"}
        )

    # E2B Cloud Execution — تنفيذ سحابي
    if os.getenv("E2B_API_KEY"):
        registry["cloud_execute"] = Tool(
            name="cloud_execute",
            description="تنفيذ كود Python في سحابة E2B المعزولة (أكثر أماناً)",
            func=_lazy_import("core.execution_engine", "_e2b_run_wrapper"),
            parameters={"code": "كود Python"}
        )

    # ── 7. OSS Adapters (Auto-generated) ──────────────────
    # يلتقط أي أدوات مولّدة داخل tools/oss_adapters/*.py ويضيفها كسِجل أدوات.
    # كل ملف يجب أن يعرّف دالة: run(query: str = "") -> str
    enable_oss = os.getenv("OSS_ADAPTERS_ENABLE", "1").strip().lower() not in ("0", "false", "no", "off")
    if enable_oss:
        try:
            adapters_dir = os.path.join(os.path.dirname(__file__), "oss_adapters")
            if os.path.isdir(adapters_dir):
                for fname in sorted(os.listdir(adapters_dir)):
                    if not fname.endswith(".py") or fname.startswith("_"):
                        continue
                    tool_name = fname.replace(".py", "")
                    # تجنّب التضارب مع أسماء أدوات أساسية
                    if tool_name in registry:
                        continue
                    registry[tool_name] = Tool(
                        name=tool_name,
                        description=f"OSS adapter tool (auto): {tool_name}",
                        func=_lazy_import(f"tools.oss_adapters.{tool_name}", "run"),
                        parameters={"query": "اختياري: نص استعلام/سؤال"},
                    )
        except Exception as e:
            logger.warning(f"OSS adapters load failed: {e}")

    logger.info(f"Tools registry v6 built: {len(registry)} tools available")
    return registry


# قائمة الأدوات لكل فئة وكلاء
CATEGORY_TOOLS = {
    "cat1_science": ["web_search", "arxiv_search", "pubmed_search", "research", "run_code"],
    "cat2_society": ["web_search", "fetch_news", "deep_search", "wiki_search", "market_data"],
    "cat3_tools": ["web_search", "fetch_news", "github_search", "arxiv_search", "remember", "recall"],
    "cat4_management": ["web_search", "analyze_data", "read_file", "write_file", "remember"],
    "cat5_behavior": ["web_search", "deep_search", "wiki_search", "research"],
    "cat6_leadership": ["web_search", "deep_search", "research", "market_data", "remember", "recall"],
    "cat7_new":          ["analyze_data", "remember", "recall", "semantic_remember", "semantic_recall", "web_search"],
    "cat8_evolution":    ["analyze_data", "remember", "recall", "semantic_remember", "semantic_recall", "web_search", "run_code"],
    "cat9_execution":    ["run_code", "web_search", "read_file", "write_file", "github_search"],
    "cat10_engineering": ["run_code", "github_search", "read_file", "write_file", "web_search", "deep_search"],
    "cat11_creative":    ["web_search", "deep_search", "remember", "semantic_remember", "wiki_search"],
    "cat12_finance":     ["market_data", "web_search", "analyze_data", "deep_search", "remember"],
    "cat13_osint":       ["web_search", "deep_search", "analyze_data", "remember", "semantic_recall"],
    "cat14_health":      ["pubmed_search", "arxiv_search", "web_search", "deep_search", "remember"],
    "cat15_legal":       ["web_search", "deep_search", "wiki_search", "remember", "semantic_remember"],
    "cat16_education":   ["web_search", "wiki_search", "deep_search", "remember", "semantic_remember"],
    "cat17_cosmic":      ["web_search", "deep_search", "arxiv_search", "remember", "semantic_remember", "analyze_data"],
}


if __name__ == "__main__":
    tools = build_tools_registry()
    print(f"\n✅ {len(tools)} أداة متاحة:")
    for name, tool in tools.items():
        print(f"  - {name}: {tool.description[:60]}...")
