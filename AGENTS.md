# AGENTS.md — دليل Codex وكل أدوات الذكاء الاصطناعي

## ما هذا المشروع؟

Army81 هو نظام من 81 وكيل ذكاء اصطناعي متخصص يعملون معاً.
المالك: غير تقني — يحتاج كل كود أن يعمل فعلاً بدون تعقيد.
البيئة: Google Cloud Platform + نماذج Gemini + Ollama محلياً.

## قواعد صارمة لكل أداة AI تعمل على هذا المشروع

1. **لا تكتب كوداً وهمياً** — كل دالة تكتبها يجب أن تعمل فعلاً
2. **لا نماذج وهمية** — استخدم فقط: gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash, Codex-3-5-haiku, llama3.2 (ollama)
3. **اختبر كل شيء** — بعد كل تغيير شغّل: `python tests/test_core.py`
4. **وثّق كل تغيير** في CHANGELOG.md
5. **لا تحذف كوداً موجوداً** — أضف فقط أو عدّل مع الإبقاء على الوظيفة القديمة

## هيكل المشروع

```
army81_v2/
├── AGENTS.md              ← أنت هنا
├── CHANGELOG.md           ← سجّل كل تغيير
├── .env.example           ← متغيرات البيئة المطلوبة
├── requirements.txt       ← المكتبات
├── docker-compose.yml     ← للتشغيل المحلي
│
├── core/
│   ├── base_agent.py      ← الوكيل الأساسي (لا تغيّر الواجهة)
│   └── llm_client.py      ← عميل النماذج الموحّد
│
├── tools/                 ← أدوات الوكلاء (أضف هنا)
│   ├── web_search.py      ← البحث على الإنترنت
│   ├── file_ops.py        ← قراءة/كتابة الملفات
│   ├── code_runner.py     ← تنفيذ الكود بأمان
│   └── news_fetcher.py    ← جمع الأخبار
│
├── memory/
│   └── memory_system.py   ← 4 مستويات ذاكرة
│
├── router/
│   └── smart_router.py    ← توجيه المهام للوكلاء
│
├── protocols/
│   └── a2a.py             ← تواصل بين الوكلاء
│
├── agents/                ← تعريفات الوكلاء JSON
│   ├── cat1_leadership/   ← 10 وكلاء قيادة
│   ├── cat2_science/      ← 9 وكلاء علوم
│   ├── cat3_society/      ← 15 وكيل مجتمع
│   ├── cat4_tools/        ← 10 وكلاء أدوات
│   ├── cat5_management/   ← 8 وكلاء إدارة
│   ├── cat6_behavior/     ← 13 وكيل سلوك
│   └── cat7_leadership/   ← 16 وكيل قيادة عليا
│
├── gateway/
│   └── app.py             ← FastAPI - نقطة الدخول الوحيدة
│
├── scripts/
│   ├── setup_gcp.sh       ← إعداد Google Cloud
│   ├── deploy.sh          ← النشر
│   └── add_agent.py       ← إضافة وكيل جديد
│
└── tests/
    ├── test_core.py       ← اختبارات أساسية
    └── test_agents.py     ← اختبار الوكلاء
```

## المهام القادمة — بالترتيب (Codex: ابدأ من هنا)

### المرحلة 1 — الأدوات الحقيقية (الأولوية القصوى)
- [ ] `tools/web_search.py` — استخدم Google Custom Search API أو Serper API
- [ ] `tools/news_fetcher.py` — RSS feeds + NewsAPI
- [ ] `tools/file_ops.py` — قراءة/كتابة آمنة مع sandbox
- [ ] `tools/code_runner.py` — تنفيذ Python في Docker container معزول

### المرحلة 2 — تخصيص الوكلاء
- [ ] ربط كل وكيل بأدواته المناسبة في `agents/registry.py`
- [ ] تحسين system prompts لكل وكيل
- [ ] اختبار كل وكيل بمهمة حقيقية

### المرحلة 3 — البنية التحتية
- [ ] نشر على Google Cloud Run
- [ ] Firestore للذاكرة الدائمة
- [ ] Cloud Scheduler للتحديث اليومي (2 صباحاً)
- [ ] Pub/Sub للتواصل بين الوكلاء

### المرحلة 4 — التطور الذاتي
- [ ] وكيل يراقب أداء الوكلاء الآخرين
- [ ] آلية تحسين system prompts تلقائياً
- [ ] جمع دروس من كل مهمة

## متغيرات البيئة المطلوبة

```bash
GOOGLE_API_KEY=          # Gemini API
GOOGLE_CSE_ID=           # Custom Search Engine
ANTHROPIC_API_KEY=       # Codex API
SERPER_API_KEY=          # للبحث على الإنترنت
GCP_PROJECT_ID=          # Google Cloud Project
```

## كيفية إضافة وكيل جديد

```bash
python scripts/add_agent.py \
  --id A82 \
  --name "Agent Name" \
  --category cat2_science \
  --model gemini-1.5-flash \
  --tools web_search,file_ops
```

## للتشغيل المحلي

```bash
cp .env.example .env
# عبئ .env بمفاتيحك
pip install -r requirements.txt
python gateway/app.py
# افتح http://localhost:8181
```
