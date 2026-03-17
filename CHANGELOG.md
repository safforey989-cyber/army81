# CHANGELOG

## [1.2.0] — 2026-03-17 — المرحلة 2: LangGraph + Chroma + 10 وكلاء جدد

### ما تم بناؤه (Claude Code — المرحلة 2)
- `memory/chroma_memory.py` — ذاكرة دلالية بـ ChromaDB (all-MiniLM-L6-v2)
  - remember(), recall() بحث دلالي بالمفاهيم
  - تخزين دائم في workspace/chroma_db/
- `workflows/langgraph_flows.py` — تدفق عمل بـ LangGraph
  - AgentState TypedDict للحالة المشتركة
  - Army81Workflow: يحول قائمة وكلاء إلى graph قابل للتنفيذ
  - Workflows جاهزة: research_pipeline, analysis_pipeline, decision_support
- `tools/registry.py` — أُضيف semantic_remember + semantic_recall (Chroma)
- `requirements.txt` — أُضيف langgraph>=1.1, chromadb>=1.5
- **10 وكلاء جدد (A05-A14):**
  - A05 Code Developer (cat3_tools) — run_code, github_search
  - A06 Data Analyst (cat4_management) — analyze_data, run_code, market_data
  - A07 Medical Research (cat1_science) — pubmed_search, arxiv_search [gemini-pro]
  - A08 Financial Analyst (cat2_society) — market_data, deep_search, fetch_news
  - A09 Security Analyst (cat3_tools) — deep_search, arxiv_search, github_search
  - A10 Knowledge Manager (cat4_management) — remember, recall, wiki_search
  - A11 Translator (cat3_tools) — wiki_search, remember
  - A12 Content Creator (cat2_society) — deep_search, fetch_news, write_file
  - A13 Legal Advisor (cat2_society) — deep_search, wiki_search [gemini-pro]
  - A14 Project Manager (cat4_management) — analyze_data, read_file, write_file
- `tests/test_phase2.py` — 22 اختبار جديد (كلها تنجح ✅)
- الاختبارات الكاملة: 29/29 نجحت (7 phase1 + 22 phase2)

## [1.1.0] — 2026-03-17 — المرحلة 1: الأدوات الحقيقية

### ما تم بناؤه (Claude Code — المرحلة 1)
- `tools/file_ops.py` — قراءة/كتابة ملفات مع sandbox آمن (workspace/)
- `tools/code_runner.py` — تنفيذ Python في subprocess معزول + دعم E2B
- `tools/github_tool.py` — بحث GitHub عن مستودعات (search_repos, get_repo_info)
- `tools/arxiv_tool.py` — wrapper لـ arXiv من science_tools
- `tools/wiki_tool.py` — wrapper لـ Wikipedia
- `tools/finance_tool.py` — wrapper لـ Yahoo Finance
- `tools/pubmed_tool.py` — wrapper لـ PubMed
- `tools/data_tool.py` — تحليل بيانات JSON/CSV
- `memory/memory_ops.py` — ذاكرة محلية (JSON) مع دعم Firestore
- `agents/cat6_leadership/A01_strategic_commander.json` — أُضيفت أدوات: deep_search, arxiv_search, remember, recall
- `agents/cat3_tools/A04_media_intelligence.json` — أُضيفت أدوات: deep_search, arxiv_search
- الاختبارات: 7/7 نجحت ✅

## [1.0.0] — 2026-03-17 — البناء الأساسي

### ما تم بناؤه
- `core/llm_client.py` — نماذج حقيقية: Gemini, Claude, Ollama
- `core/base_agent.py` — الوكيل الأساسي مع أدوات وذاكرة
- `router/smart_router.py` — توجيه ذكي بالكلمات المفتاحية
- `tools/web_search.py` — بحث عبر Serper + Google CSE
- `tools/tavily_search.py` — بحث عميق عبر Tavily
- `tools/science_tools.py` — arXiv, Wikipedia, PubMed, Yahoo Finance
- `tools/registry.py` — سجل موحد لكل الأدوات
- `gateway/app.py` — FastAPI مع كل نقاط API
- `agents/cat6_leadership/A01_strategic_commander.json`
- `agents/cat3_tools/A04_media_intelligence.json`
- `tests/test_core.py` — 7 اختبارات (كلها تنجح)
- `MASTER_PLAN.md` — خطة الـ 3 أشهر الكاملة
- `CLAUDE.md` — دليل كل أدوات AI للعمل على المشروع

### المطلوب في v1.1.0
- [ ] إكمال الـ 79 ملف JSON المتبقية للوكلاء
- [ ] تكامل LangGraph
- [ ] تكامل CrewAI
- [ ] Chroma للذاكرة الدلالية
- [ ] لوحة تحكم Streamlit
