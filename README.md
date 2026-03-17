# Army81 — نظام 81 وكيل ذكاء اصطناعي

نظام متكامل من 81 وكيلاً متخصصاً يعملون معاً كفريق واحد.

## التشغيل السريع

```bash
# 1. استنسخ المشروع
git clone https://github.com/YOUR_USERNAME/army81.git
cd army81

# 2. إعداد البيئة
cp .env.example .env
# عبّئ .env بمفاتيحك (GOOGLE_API_KEY مطلوب للبدء)

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. تشغيل الاختبارات
python tests/test_core.py

# 5. تشغيل النظام
python gateway/app.py
# افتح: http://localhost:8181
```

## الهيكل

| الفئة | العدد | التخصص |
|-------|-------|--------|
| cat1_science | 9 | العلوم والتقنية |
| cat2_society | 15 | المجتمع والاستراتيجية |
| cat3_tools | 10 | الأدوات والتمكين |
| cat4_management | 8 | الإدارة |
| cat5_behavior | 13 | السلوك البشري |
| cat6_leadership | 16 | القيادة |
| **المجموع** | **81** | |

## API

```bash
# تنفيذ مهمة (توجيه تلقائي)
POST /task
{"task": "لخص أهم أخبار الذكاء الاصطناعي اليوم"}

# تنفيذ لوكيل محدد
POST /task
{"task": "...", "agent_id": "A04"}

# سلسلة وكلاء
POST /pipeline
{"task": "...", "agent_ids": ["A01", "A04", "A07"]}

# حالة النظام
GET /status
```

## للمطورين والأدوات AI

اقرأ [CLAUDE.md](CLAUDE.md) أولاً — يحتوي على كل التعليمات والمهام القادمة.

## CHANGELOG

### v1.0.0 — 2026-03-17
- البنية الأساسية: BaseAgent, LLMClient, SmartRouter
- نماذج حقيقية: Gemini, Claude, Ollama
- أدوات: web_search, fetch_news
- وكيلان نموذجيان: A01, A04
- FastAPI Gateway
- اختبارات أساسية
- GitHub Actions CI
