# CHANGELOG

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
