# CHANGELOG

## [2.0.0] — 2026-03-17 — المرحلة 4: 41 وكيل جديد + CrewAI + Streamlit Dashboard

### ما تم بناؤه (Claude Code — المرحلة 4)
- **41 وكيل جديد (A41-A81) — إجمالي: 81 وكيل ✅**
  - **cat2_society (A41-A51):** الاقتصاد العالمي، العملات الرقمية، التاريخ، الإعلام، القانون الدولي، الفنون، اللغويات، الرياضيات، علم الاجتماع، التعليم، الهندسة العكسية
  - **cat1_science (A52-A55):** الطب السريري، التصنيع المتقدم، الروبوتات، الفضاء والدفاع
  - **cat3_tools (A56-A61):** استخبارات الوسائط، تكامل الأنظمة، الإنذار المبكر، الابتكار المفتوح، مكافحة التضليل، البيولوجيا الحسابية
  - **cat4_management (A62-A66):** الحوكمة، المنظمات الكبرى، المشاريع الضخمة، التحول الرقمي، إدارة الأداء
  - **cat6_leadership (A67-A71):** التواصل الإنساني، توزيع الموارد، التقييم الشامل، الابتكار الجذري، الأمن الداخلي
  - **cat7_new (A72-A81):** مراقبة التطور الذاتي، تنسيق متعدد الوكلاء، ضبط الجودة، تحسين النظام، تجميع التعلم، تنسيق سير العمل، التخصيص الديناميكي للموارد، معالجة التغذية الراجعة، التعرف على الأنماط، الميتا الاستخباراتي (A81)
- **`crews/army81_crews.py`** — CrewAI فرق عمل متخصصة:
  - فريق التحليل الاستراتيجي (A01, A31, A32, A33) — Sequential Process
  - فريق البحث العلمي (A07, A38, A39, A40) — Sequential Process
  - فريق إدارة الأزمات (A29, A34, A35, A23) — Sequential Process
  - وضع Fallback تلقائي عند غياب API keys
  - `run_team(key, task)` — واجهة موحدة
- **`dashboard/app.py`** — لوحة تحكم Streamlit كاملة:
  - الرئيسية: إحصائيات الـ 81 وكيل
  - الوكلاء: قائمة قابلة للفلترة والبحث
  - إرسال مهمة: لوكيل محدد أو workflow
  - فرق CrewAI: تشغيل الفرق الثلاثة من الواجهة
  - الإحصائيات: رسوم بيانية + تقرير يومي
- **`tests/test_phase4.py`** — 37 اختباراً ✅ جميعها ناجحة
- **`requirements.txt`** — أضيف crewai>=1.10.0 و streamlit>=1.55.0

### كيفية التشغيل
```bash
# لوحة التحكم
streamlit run dashboard/app.py

# فريق CrewAI من سطر الأوامر
python crews/army81_crews.py strategic "ما أهم التحديات الاستراتيجية؟"

# الاختبارات
python tests/test_phase4.py
```

## [1.3.0] — 2026-03-17 — المرحلة 3: 28 وكيل جديد + Daily Updater + /workflow

### ما تم بناؤه (Claude Code — المرحلة 3)
- **28 وكيل جديد (A02-A03 + A15-A40) — إجمالي: 40 وكيل**
  - **cat5_behavior (A15-A27):** علم النفس، التفاوض، لغة الجسد، الإقناع، الذكاء العاطفي، الديناميكيات الاجتماعية، سلوك الجماهير، الاقتصاد السلوكي، حل النزاعات، سيكولوجية القيادة، التواصل، سيكولوجية القرار، الذكاء الثقافي
  - **cat6_leadership (A28-A37):** الاستراتيجية العسكرية، إدارة الأزمات، الابتكار، الاستخبارات، الجيوسياسة، استشراف المستقبل، تقييم المخاطر، إدارة التغيير، استراتيجي المنظمات، مهندس القرارات
  - **cat1_science (A02, A38-A40):** البحث العلمي، الفيزياء والكم، المناخ، كاشف التقنيات
  - **cat2_society (A03):** تحليل السياسات
- **`scripts/daily_updater.py`** — تحديث ذكاء يومي:
  - يجمع من arXiv (5 موضوعات AI) + GitHub Trending (3 استعلامات) + NewsAPI (3 موضوعات)
  - يحفظ كل شيء في Chroma تلقائياً
  - يُنتج تقرير Markdown يومي في workspace/reports/
  - APScheduler: يُجدول عند 2:00 صباحاً (Asia/Riyadh)
  - تشغيل يدوي: `python scripts/daily_updater.py`
  - تشغيل مجدول: `python scripts/daily_updater.py --schedule`
- **`gateway/app.py`** تحديثات:
  - v1.3.0 — يستخدم build_tools_registry() الكامل (16 أداة)
  - `POST /workflow` — ينفذ مهمة عبر LangGraph workflow
  - `GET /workflows` — يعرض الـ workflows المتاحة وجاهزيتها
  - WorkflowRequest: workflow / task / agent_ids (custom) / context
- `tests/test_phase3.py` — 37 اختبار جديد
- **الاختبارات الكاملة: 66/66 نجحت** ✅ (7+22+37)

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
