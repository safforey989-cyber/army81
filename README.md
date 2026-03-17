# Army81 - نظام 81 وكيل ذكاء اصطناعي متكامل

> نظام بيئي متكامل من 81 وكيلاً متخصصاً يعملون معاً كفريق واحد، مع قدرة على التطور الذاتي.

## البنية

| الفئة | العدد | الوصف |
|-------|-------|-------|
| cat1_leadership | 12 | القيادة والإدارة الاستراتيجية |
| cat2_engineering | 15 | التطوير والهندسة البرمجية |
| cat3_research | 12 | البحث والتحليل |
| cat4_creative | 10 | المحتوى والإبداع |
| cat5_operations | 12 | العمليات والأتمتة |
| cat6_security | 10 | الأمن والجودة |
| cat7_evolution | 10 | التحسين الذاتي والتطور |

## التثبيت السريع

### Windows
```cmd
setup.bat
```

### Linux / Mac
```bash
chmod +x setup.sh && ./setup.sh
```

### Docker
```bash
docker-compose up -d
```

## الاستخدام

### سطر الأوامر
```bash
# حالة النظام
python cli.py status

# قائمة الوكلاء
python cli.py list

# تنفيذ مهمة (توجيه تلقائي)
python cli.py task "اكتب تقريراً عن أحدث تطورات الذكاء الاصطناعي"

# تنفيذ مهمة لوكيل محدد
python cli.py task "اكتب كود Python لتحليل CSV" --agent A13

# سلسلة وكلاء (pipeline)
python cli.py pipeline "حلل هذا المشروع وحسنه" --agents A28 A13 A14

# وضع الدردشة التفاعلي
python cli.py chat

# تشغيل خادم API
python cli.py serve --port 8181
```

### API (FastAPI)
```bash
# تشغيل الخادم
python cli.py serve

# تنفيذ مهمة
curl -X POST http://localhost:8181/task \
  -H "Content-Type: application/json" \
  -d '{"task": "اكتب مقالاً عن الذكاء الاصطناعي"}'

# قائمة الوكلاء
curl http://localhost:8181/agents

# حالة النظام
curl http://localhost:8181/status
```

## المكونات الأساسية

- **Smart Router**: بوابة ذكية توجه المهام للوكيل المناسب
- **Memory System**: ذاكرة 4 مستويات (قصيرة، عاملة، طويلة، عرضية)
- **A2A Protocol**: بروتوكول تواصل مباشر بين الوكلاء
- **Daily Updater**: تحديث يومي تلقائي من GitHub وHuggingFace
- **Self Improver**: محرك تحسين ذاتي مستوحى من Hermes Agent

## النماذج المدعومة

| المزود | النماذج | الاستخدام |
|--------|---------|-----------|
| Ollama (محلي) | qwen3:8b, qwen2.5-coder:14b | المهام الروتينية |
| OpenAI | gpt-4o, gpt-5 | المهام الحرجة |
| Anthropic | claude-3.5-sonnet | التحليل العميق |
| Perplexity | sonar-pro | البحث المباشر |

## الترخيص

MIT License
