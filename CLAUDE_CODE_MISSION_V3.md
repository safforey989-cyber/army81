# CLAUDE_CODE_MISSION_V3.md
## Army81 v3 — إعادة المعمارية الكاملة

اقرأ أولاً بالترتيب: CLAUDE.md ثم MASTER_PLAN.md ثم core/base_agent.py

ستبني Army81 v3 — إعادة المعمارية من الداخل.
لا تكسر أي API موجودة. كل الـ endpoints تبقى تعمل.
ابنِ بالترتيب الدقيق التالي:

---

## المرحلة A — الأساس المحمي (ابدأ هنا)

### 1. core/smart_queue.py
```python
"""
SmartQueue — حل مشكلة rate limiting و API failures
نتيجة Monte Carlo: بدون هذا → 0% نجاة بعد 90 يوم
"""
class SmartQueue:
    # أولويات المهام
    CRITICAL = 1   # A81, A01
    HIGH = 2       # مهام مع deadline
    NORMAL = 3     # مهام عادية
    LOW = 4        # daily_updater, distillation

    # حدود النماذج
    MODEL_LIMITS = {
        "gemini-flash": {"rpm": 15, "fallback": "gemini-pro"},
        "gemini-pro": {"rpm": 2, "fallback": "claude-haiku"},
        "claude-haiku": {"rpm": 50, "fallback": "gemini-flash"},
        "claude-sonnet": {"rpm": 50, "fallback": "claude-haiku"},
        "ollama-local": {"rpm": 999, "fallback": None},
    }

    def submit(self, agent_id, task, priority=3, model="gemini-flash"):
        # ضع في queue بالأولوية
        # إذا انتظر > 60 ثانية → انزل للـ fallback تلقائياً
        # إذا فشل الـ fallback → ollama-local
        pass

    def stats(self):
        # pending, processed, fallbacks_used, by_model
        pass
```

### 2. core/army81_adapter.py
```python
"""
Army81Adapter — طبقة عزل واحدة فوق كل الأطر
Army81 لا يستدعي LangGraph أو CrewAI مباشرة أبداً
كل شيء يمر من هنا
نتيجة Loop 4: أولوية 6.0 — تأثير عالي، جهد منخفض
"""
class Army81Adapter:
    def run_native(self, agent, task, context):
        # الأسرع والأرخص — للمهام البسيطة
        pass

    def run_langgraph(self, workflow, task, agents):
        # للـ pipelines المتسلسلة
        pass

    def run_crewai(self, crew_name, task):
        # للفرق المتعاونة
        pass

    def run_openai_agents(self, agent, task):
        # للقرارات الحرجة فقط
        pass

    def complexity_score(self, task) -> int:
        # 1-10 بناءً على طول المهمة وكلماتها
        # < 3 → native
        # 3-6 → langgraph
        # 7-8 → crewai
        # 9-10 → openai_agents
        pass

    def auto_select(self, task, messages):
        score = self.complexity_score(task)
        if score < 3: return self.run_native(...)
        elif score < 7: return self.run_langgraph(...)
        elif score < 9: return self.run_crewai(...)
        else: return self.run_openai_agents(...)
```

### 3. core/constitutional_guardrails.py
```python
"""
ConstitutionalGuardrails — يمنع التطور الخاطئ
نتيجة Monte Carlo: بدون هذا → drift يدمر النظام
"""
class ConstitutionalGuardrails:
    RULES = [
        "لا تعديل على ملفات core/ بدون موافقة",
        "لا تغيير يرفع التكلفة أكثر من 20%",
        "كل تغيير في system_prompt يحتاج اختبار 3 مهام أولاً",
        "rollback تلقائي إذا تراجع الأداء أكثر من 15%",
        "لا حذف من الذاكرة الطويلة بدون موافقة بشرية",
    ]

    def check(self, action_type, params) -> tuple[bool, str]:
        # (allowed, reason)
        pass

    def log_violation(self, rule, action, agent_id):
        # يكتب في workspace/audit_trail.jsonl
        pass

    def get_audit_trail(self):
        pass
```

---

## المرحلة B — الذاكرة الهرمية الحقيقية

### 4. memory/hierarchical_memory.py
```python
"""
HierarchicalMemory — مستوحى من mem0 (50k stars)
مبني فوق Chroma الموجودة بالفعل في المشروع
نتيجة Loop 2: أعلى تأثير بأقل جهد (6.7 أولوية)
"""

class HierarchicalMemory:
    """
    4 مستويات:
    
    L1 — WorkingMemory (dict في RAM):
        المحادثة الجارية فقط
        تُمسح عند انتهاء كل run()
    
    L2 — EpisodicMemory (SQLite):
        كل مهمة: task + result + success + rating
        "المرة السابقة طُلب مني X، فعلت Y ونجح"
        
        CREATE TABLE episodes (
            id INTEGER PRIMARY KEY,
            agent_id TEXT,
            task_summary TEXT,
            result_summary TEXT,
            success BOOLEAN,
            rating INTEGER,
            model_used TEXT,
            tokens INTEGER,
            created_at TIMESTAMP
        )
    
    L3 — SemanticMemory (Chroma الموجودة):
        بحث دلالي — يفهم المفاهيم لا الكلمات
        namespace منفصل لكل agent_id
    
    L4 — CompressedMemory (ملف مضغوط):
        كل أحد: يلخص L2+L3 في 500 كلمة
        يُحقن في system_prompt تلقائياً
        يقلص الذاكرة 80% بدون فقدان المعنى
    """

    def inject_context(self, agent_id: str, task: str) -> str:
        """
        يُستدعى قبل كل run() — يجمع أفضل context
        مثال للناتج:
        ## دروسي السابقة:
        - المرة السابقة طُلب مني تحليل سهم، استخدمت Yahoo Finance وكانت النتيجة دقيقة
        
        ## معرفتي المرتبطة:
        - [نتائج بحث دلالي من Chroma]
        
        ## ملخص خبرتي:
        - [ملخص مضغوط من L4]
        """
        context = ""
        lessons = self.L2.get_lessons(agent_id)  # أهم 3 دروس مشابهة
        if lessons: context += f"## دروسي السابقة:\n{lessons}\n\n"
        relevant = self.L3.search(agent_id, task, k=3)
        if relevant: context += f"## معرفتي المرتبطة:\n{relevant}\n\n"
        summary = self.L4.get_summary(agent_id)
        if summary: context += f"## ملخص خبرتي:\n{summary}\n"
        return context[:2000]  # لا تتجاوز 2000 حرف

    def store(self, agent_id, task, result, success, rating=7):
        """يُستدعى بعد كل run() ناجح"""
        self.L2.record(agent_id, task[:200], result[:500], success, rating)

    def compress_weekly(self, agent_id):
        """يُشغَّل كل أحد الساعة 4 صباحاً"""
        # اجمع كل L2 + L3 للوكيل
        # استخدم gemini-flash لتلخيصها في 500 كلمة
        # احفظ في workspace/compressed/{agent_id}_summary.md
        pass

    def transfer(self, from_agent, to_agent, topic):
        """نقل معرفة بين وكيلين"""
        pass
```

### 5. memory/collective_memory.py
```python
"""
CollectiveMemory — 81 وكيل يشاركون المعرفة
مستوحى من openai/swarm
"""
class CollectiveMemory:
    # collection واحدة مشتركة في Chroma
    COLLECTION = "army81_collective"

    def contribute(self, agent_id, insight, topic, confidence=0.8):
        """وكيل يشارك ما تعلمه مع البقية"""
        pass

    def query(self, topic, requesting_agent_id, k=3):
        """وكيل يسأل البقية عن موضوع"""
        pass

    def get_expert_on(self, topic) -> str:
        """من هو أكثر وكيل خبرة في هذا الموضوع؟"""
        pass
```

---

## المرحلة C — التطور الذاتي الآمن

### 6. core/safe_evolution.py
```python
"""
SafeEvolution — مستوحى من aden-hive/hive
مع constitutional_guardrails لمنع الانحراف
نتيجة Monte Carlo: هذا الفرق بين 8% و 90% نجاة
"""
class SafeEvolution:

    def evaluate(self, agent_id) -> float:
        """
        يشغّل 5 مهام من tests/benchmark_tasks.json
        يحسب: avg_quality + speed + cost_efficiency
        يعيد score 0-100
        """
        pass

    def propose_improvement(self, agent_id) -> dict:
        """
        يقرأ آخر 10 episodes فاشلة من EpisodicMemory
        يقترح تعديل على system_prompt
        يعيد: {prompt, reasoning, expected_gain}
        """
        pass

    def test_improvement(self, agent_id, proposed_prompt) -> bool:
        """
        يشغّل 3 مهام قياسية بالـ prompt الجديد
        يقبل فقط إذا تحسّن > 10%
        """
        pass

    def apply_improvement(self, agent_id, new_prompt):
        """
        1. تحقق من ConstitutionalGuardrails
        2. احفظ النسخة القديمة في workspace/backups/
        3. طبّق التغيير على ملف JSON
        4. سجّل في workspace/evolution_log.json
        """
        pass

    def rollback(self, agent_id):
        """استعد النسخة من workspace/backups/"""
        pass

    def weekly_cycle(self):
        """
        يُشغَّل كل أحد الساعة 5 صباحاً:
        1. evaluate كل الوكلاء
        2. حدد أضعف 10 وكلاء
        3. improve كل واحد
        4. git commit + push إذا تغيّر > 3 وكلاء
        """
        pass
```

### 7. core/knowledge_distillation.py
```python
"""
KnowledgeDistillation — DeepSeek approach
Flash يتعلم من Pro → نفس الأداء بتكلفة أقل 10x
"""
class KnowledgeDistillation:
    TEACHER_STUDENT = [
        ("gemini-pro", "gemini-flash"),
        ("claude-sonnet", "claude-haiku"),
    ]

    def record_teacher_solution(self, task_type, task, solution, model):
        """احفظ في EpisodicMemory مع tag teacher_example"""
        pass

    def get_examples_for_student(self, task_type, student_model, k=5):
        """
        اجلب أفضل 5 حلول من teacher لنفس النوع
        أعطها للـ student في context قبل المهمة
        """
        pass

    def measure_gap(self, agent_id, task_type) -> float:
        """
        هل Flash يحتاج Pro لهذا النوع؟
        إذا gap < 10% → استخدم Flash دائماً (وفّر المال)
        """
        pass

    def daily_distillation(self):
        """الساعة 2 صباحاً: لكل حل teacher → سجّل مثالاً للـ student"""
        pass
```

---

## المرحلة D — ربط كل شيء بـ BaseAgent

### 8. عدّل core/base_agent.py — أضف فقط، لا تحذف

```python
# في __init__ أضف:
from memory.hierarchical_memory import HierarchicalMemory
from memory.collective_memory import CollectiveMemory
from core.smart_queue import SmartQueue
from core.constitutional_guardrails import ConstitutionalGuardrails
from core.knowledge_distillation import KnowledgeDistillation
from core.army81_adapter import Army81Adapter

self.memory = HierarchicalMemory(self.agent_id)
self.collective = CollectiveMemory()
self.queue = SmartQueue.get_instance()   # singleton
self.guardrails = ConstitutionalGuardrails()
self.distillation = KnowledgeDistillation()
self.adapter = Army81Adapter()

# عدّل run(task, context) ليصبح:
def run(self, task: str, context: dict = None):
    context = context or {}
    start = time.time()

    try:
        # A: احصل على context من الذاكرة
        memory_ctx = self.memory.inject_context(self.agent_id, task)
        collective_ctx = self.collective.query(task[:50], self.agent_id)
        examples = self.distillation.get_examples_for_student(
            self._classify_task(task), self.model_alias, k=3)

        # B: أثرِ الـ system prompt
        enriched_system = self.system_prompt
        if memory_ctx:
            enriched_system += f"\n\n{memory_ctx}"
        if examples:
            enriched_system += f"\n\n## أمثلة ناجحة مشابهة:\n{examples}"

        # C: ابنِ الرسائل
        messages = self._build_messages(task, context)
        messages[0]["content"] = enriched_system

        # D: نفّذ عبر LLM مباشرة (native أسرع وأرخص)
        response = self.llm.chat(messages)
        result_text = response["content"]

        # E: سجّل في الذاكرة
        self.memory.store(self.agent_id, task, result_text, success=True, rating=7)

        # F: ساهم في الذاكرة الجماعية
        if len(result_text) > 100:
            self.collective.contribute(
                self.agent_id, result_text[:500],
                topic=self._classify_task(task))

        elapsed = round(time.time() - start, 2)
        self.stats["tasks_done"] += 1
        self.stats["last_active"] = datetime.now().isoformat()

        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name_ar,
            task=task,
            result=result_text,
            status="success",
            model_used=self.model_alias,
            elapsed_seconds=elapsed,
            tokens_used=response.get("tokens", 0),
        )

    except Exception as e:
        self.stats["tasks_failed"] += 1
        self.memory.store(self.agent_id, task, str(e), success=False, rating=1)
        logger.error(f"Agent {self.agent_id} failed: {e}")
        return AgentResult(
            agent_id=self.agent_id, agent_name=self.name_ar,
            task=task, result=f"خطأ: {e}", status="error",
            model_used=self.model_alias,
            elapsed_seconds=round(time.time() - start, 2), tokens_used=0)

# أضف:
def _classify_task(self, task: str) -> str:
    keywords = {
        "medical": ["طب","دواء","مرض","علاج","سريري","pubmed"],
        "financial": ["سوق","سهم","اقتصاد","مالي","عملة","nasdaq"],
        "code": ["كود","برمج","python","api","debug","function","class"],
        "research": ["بحث","ورقة","دراسة","أثبت","نظرية","arxiv"],
        "strategy": ["استراتيج","خطة","قرار","تحليل","رؤية"],
        "news": ["خبر","أخبار","حدث","تقرير","مستجد"],
    }
    task_lower = task.lower()
    for topic, kws in keywords.items():
        if any(k in task_lower for k in kws):
            return topic
    return "general"
```

---

## المرحلة E — الجدولة التلقائية

### 9. عدّل scripts/daily_updater.py — أضف الجدولة الكاملة

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="Asia/Jerusalem")

# 2:00 صباحاً — تحديث خارجي (arXiv + GitHub + أخبار)
scheduler.add_job(run_daily_update, 'cron', hour=2, minute=0)

# 3:00 صباحاً — تقطير المعرفة (DeepSeek style)
scheduler.add_job(daily_distillation, 'cron', hour=3, minute=0)

# كل أحد 4:00 صباحاً — ضغط ذاكرة كل الوكلاء
scheduler.add_job(compress_all_agents, 'cron', day_of_week='sun', hour=4)

# كل أحد 5:00 صباحاً — دورة التطور الذاتي
scheduler.add_job(weekly_evolution_cycle, 'cron', day_of_week='sun', hour=5)

scheduler.start()
```

---

## المرحلة F — الملفات المساعدة

### 10. ابنِ tests/benchmark_tasks.json
```json
{
  "version": "1.0",
  "tasks": [
    {"id": "B001", "type": "research", "task": "لخص آخر تطورات LLMs في 2026 في 5 نقاط", "min_words": 80},
    {"id": "B002", "type": "code", "task": "اكتب دالة Python تحسب Fibonacci بـ memoization", "must_contain": ["def", "return"]},
    {"id": "B003", "type": "strategy", "task": "ضع خطة تسويقية مختصرة لمنتج AI جديد", "min_words": 100},
    {"id": "B004", "type": "medical", "task": "اشرح آلية عمل الأنسولين في الجسم", "min_words": 80},
    {"id": "B005", "type": "financial", "task": "حلل 3 مخاطر رئيسية للاستثمار في العملات الرقمية", "min_words": 80}
  ]
}
```

### 11. ابنِ tests/test_v3_architecture.py
اختبر:
- `test_smart_queue_fallback` — API يفشل → fallback يعمل
- `test_memory_l1_to_l4` — احفظ واسترجع من كل مستوى
- `test_episodic_inject` — الدرس يظهر في context قبل المهمة
- `test_constitutional_block` — قاعدة تمنع تغييراً خاطئاً
- `test_collective_sharing` — وكيل A يشارك → وكيل B يجد المعلومة
- `test_distillation_examples` — Flash يحصل على أمثلة Pro
- `test_safe_evolution_rollback` — تحسين سيء → rollback تلقائي
- `test_weekly_cycle_dry_run` — دورة التطور بدون API calls حقيقية

---

## الخاتمة — الترتيب النهائي

```bash
# 1. شغّل الاختبارات القديمة أولاً (يجب أن تبقى خضراء)
python tests/test_core.py

# 2. شغّل اختبارات v3
python tests/test_v3_architecture.py

# 3. ارفع
git add .
git commit -m "feat: Army81 v3 - hierarchical memory + safe evolution + distillation

- SmartQueue: rate limiting + fallback chain
- Army81Adapter: unified layer over all frameworks  
- ConstitutionalGuardrails: safe evolution rules
- HierarchicalMemory L1-L4: episodic + semantic + compressed
- CollectiveMemory: 81 agents share knowledge
- SafeEvolution: weekly improvement cycle + rollback
- KnowledgeDistillation: Flash learns from Pro (DeepSeek approach)
- APScheduler: fully automated daily/weekly cycles
- Monte Carlo validated: 0% → 100% survival rate"

git push origin main
```

---

## ملاحظة مهمة
- لا تكسر أي endpoint موجود في gateway/app.py
- كل الـ endpoints القديمة تبقى تعمل بدون تغيير
- إذا فشل أي جزء، سجّل الخطأ وأكمل البقية
- النظام يعمل جزئياً أفضل من لا يعمل أبداً
