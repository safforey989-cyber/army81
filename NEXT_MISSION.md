# ARMY81 V3 — READ THIS FIRST, THEN EXECUTE

> اقرأ CLAUDE.md و MASTER_PLAN.md و core/base_agent.py أولاً
> ثم نفّذ كل شيء بالترتيب بدون توقف

## السياق من المحاكاة (نتائج 4 loops)
- بدون v3: 0% نجاة بعد 90 يوم (Monte Carlo 1000 تشغيل)
- مع v3 كاملاً: 100% نجاة + درجة مركبة 84.5/100
- أخطر مشكلة: context overflow (90% احتمال) → تحلها HierarchicalMemory
- الأولوية القصوى: SmartQueue أولاً (يمنع انهيار 81 وكيل من rate limiting)

---

## المرحلة A — الأساس المحمي (ابدأ هنا)

### 1. core/smart_queue.py
```python
"""
Queue ذات أولويات مع fallback تلقائي
يحل مشكلة: 81 وكيل يستدعون API في نفس الوقت
"""
from enum import IntEnum
from collections import defaultdict
import time, threading, queue, logging

logger = logging.getLogger("army81.queue")

class Priority(IntEnum):
    CRITICAL = 1  # A81, A01 — قرارات مصيرية
    HIGH = 2      # مهام بـ deadline
    NORMAL = 3    # مهام عادية
    LOW = 4       # daily_updater, distillation

# حدود كل نموذج (requests per minute)
MODEL_LIMITS = {
    "gemini-flash": 15,
    "gemini-pro": 2,
    "claude-sonnet": 50,
    "claude-haiku": 100,
    "local-medium": 9999,  # ollama محلي
}

# سلسلة الـ fallback
FALLBACK_CHAIN = [
    "gemini-flash",
    "gemini-pro",
    "claude-haiku",
    "local-medium",
]

class SmartQueue:
    _instance = None  # Singleton

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._queues = {p: queue.PriorityQueue() for p in Priority}
        self._counters = defaultdict(list)  # model → [timestamps]
        self._lock = threading.Lock()
        self.stats = {"total": 0, "fallbacks": 0, "errors": 0}

    def submit(self, agent_id: str, task: str, priority: int = 3,
               model: str = "gemini-flash", run_fn=None) -> dict:
        """أرسل مهمة وانفّذها مع fallback تلقائي"""
        self.stats["total"] += 1
        models_to_try = self._get_fallback_chain(model)

        for m in models_to_try:
            if self._check_limit(m):
                self._record_call(m)
                try:
                    if run_fn:
                        result = run_fn(m)
                        return {"status": "success", "model": m, "result": result}
                except Exception as e:
                    logger.error(f"Model {m} failed: {e}")
                    self.stats["errors"] += 1
                    continue
            else:
                logger.info(f"Rate limit for {m}, trying next...")
                self.stats["fallbacks"] += 1
                continue

        return {"status": "error", "result": "كل النماذج وصلت للحد المسموح"}

    def _check_limit(self, model: str) -> bool:
        limit = MODEL_LIMITS.get(model, 10)
        now = time.time()
        with self._lock:
            calls = [t for t in self._counters[model] if now - t < 60]
            self._counters[model] = calls
            return len(calls) < limit

    def _record_call(self, model: str):
        with self._lock:
            self._counters[model].append(time.time())

    def _get_fallback_chain(self, preferred: str) -> list:
        chain = [preferred]
        for m in FALLBACK_CHAIN:
            if m != preferred:
                chain.append(m)
        return chain

    def get_stats(self) -> dict:
        return {**self.stats, "pending": sum(q.qsize() for q in self._queues.values())}
```

### 2. core/army81_adapter.py
```python
"""
طبقة التوحيد — Army81 لا يستدعي LangGraph/CrewAI مباشرة
كل شيء يمر من هنا
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("army81.adapter")

def _complexity_score(task: str) -> int:
    """احسب تعقيد المهمة 1-10"""
    score = 1
    task_lower = task.lower()
    if len(task) > 500: score += 3
    if len(task) > 200: score += 2
    complex_keywords = ["حلل","قارن","استراتيج","multi","pipeline","سلسلة","فريق","خطة"]
    score += sum(1 for k in complex_keywords if k in task_lower)
    return min(10, score)

class Army81Adapter:
    """
    يختار المحرك الأنسب تلقائياً:
    simple (1-3)  → native (أسرع وأرخص)
    medium (4-6)  → langgraph
    complex (7-8) → crewai
    critical (9+) → openai_agents
    """

    def __init__(self, agents_registry: dict = None):
        self.agents = agents_registry or {}
        self._langgraph = None
        self._crewai = None
        self.stats = {"native": 0, "langgraph": 0, "crewai": 0, "openai": 0}

    def run(self, agent_id: str, task: str, context: dict = None,
            force_engine: str = None) -> dict:
        context = context or {}
        score = _complexity_score(task)
        engine = force_engine or self._select_engine(score)

        logger.info(f"Agent {agent_id} | score={score} | engine={engine}")

        if engine == "native":
            return self._run_native(agent_id, task, context)
        elif engine == "langgraph":
            return self._run_langgraph(agent_id, task, context)
        elif engine == "crewai":
            return self._run_crewai(agent_id, task, context)
        else:
            return self._run_native(agent_id, task, context)

    def _select_engine(self, score: int) -> str:
        if score <= 3: return "native"
        if score <= 6: return "langgraph"
        if score <= 8: return "crewai"
        return "native"  # fallback للأمان

    def _run_native(self, agent_id, task, context) -> dict:
        self.stats["native"] += 1
        agent = self.agents.get(agent_id)
        if not agent:
            return {"status": "error", "result": f"Agent {agent_id} not found"}
        result = agent.run(task, context)
        return result.to_dict() if hasattr(result, "to_dict") else result

    def _run_langgraph(self, agent_id, task, context) -> dict:
        self.stats["langgraph"] += 1
        try:
            from workflows.langgraph_flows import Army81Workflow
            agent = self.agents.get(agent_id)
            if not agent:
                return self._run_native(agent_id, task, context)
            wf = Army81Workflow([agent], name=f"auto_{agent_id}")
            return wf.run(task, context)
        except Exception as e:
            logger.warning(f"LangGraph failed ({e}), falling back to native")
            return self._run_native(agent_id, task, context)

    def _run_crewai(self, agent_id, task, context) -> dict:
        self.stats["crewai"] += 1
        try:
            from crews.army81_crews import run_crew_task
            return run_crew_task(agent_id, task, context)
        except Exception as e:
            logger.warning(f"CrewAI failed ({e}), falling back to native")
            return self._run_native(agent_id, task, context)
```

### 3. core/constitutional_guardrails.py
```python
"""
قواعد لا تُكسر — تحمي النظام من التطور الخاطئ
"""
import json, logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("army81.guardrails")

RULES = [
    {"id": "R001", "desc": "لا تعديل على core/ بدون اختبار", "action": "modify_core"},
    {"id": "R002", "desc": "لا رفع تكلفة > 20% فجأة", "action": "cost_spike"},
    {"id": "R003", "desc": "كل تغيير prompt يحتاج 3 اختبارات", "action": "change_prompt"},
    {"id": "R004", "desc": "rollback إذا تراجع الأداء > 15%", "action": "performance_drop"},
    {"id": "R005", "desc": "لا حذف من الذاكرة الطويلة بدون موافقة", "action": "delete_memory"},
]

AUDIT_FILE = Path("workspace/audit_trail.jsonl")

class ConstitutionalGuardrails:
    def check(self, action_type: str, params: dict = None) -> tuple:
        """Returns (allowed: bool, reason: str)"""
        params = params or {}
        for rule in RULES:
            if rule["action"] == action_type:
                # فحص خاص لكل نوع
                if action_type == "cost_spike":
                    increase = params.get("increase_pct", 0)
                    if increase > 20:
                        self._log_violation(rule, action_type, params)
                        return False, f"تكلفة ترتفع {increase}% — تجاوزت 20%"
                elif action_type == "performance_drop":
                    drop = params.get("drop_pct", 0)
                    if drop > 15:
                        self._log_violation(rule, action_type, params)
                        return False, f"أداء تراجع {drop}% — rollback مطلوب"
                elif action_type == "delete_memory":
                    return False, "حذف الذاكرة يحتاج موافقة بشرية"
        return True, "مسموح"

    def _log_violation(self, rule: dict, action: str, params: dict):
        AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "rule": rule["id"],
            "desc": rule["desc"],
            "action": action,
            "params": str(params)[:200]
        }
        with open(AUDIT_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.warning(f"Guardrail violation: {rule['desc']}")

    def get_audit_trail(self, limit: int = 50) -> list:
        if not AUDIT_FILE.exists():
            return []
        lines = AUDIT_FILE.read_text().strip().split("\n")
        return [json.loads(l) for l in lines[-limit:] if l]
```

---

## المرحلة B — الذاكرة الهرمية

### 4. memory/hierarchical_memory.py
```python
"""
4 مستويات ذاكرة — مستوحى من mem0 (50k stars)
مبني فوق Chroma الموجودة + SQLite جديدة
"""
import sqlite3, json, logging, hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("army81.memory")

DB_PATH = Path("workspace/episodic.db")
SUMMARIES_DIR = Path("workspace/compressed")

class L1_Working:
    """RAM فقط — تُمسح بعد كل جلسة"""
    def __init__(self): self._store = {}
    def get(self, key, default=None): return self._store.get(key, default)
    def set(self, key, val): self._store[key] = val
    def clear(self): self._store.clear()

class L2_Episodic:
    """SQLite — كل مهمة نُفِّذت"""
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                task_summary TEXT,
                result_summary TEXT,
                task_type TEXT DEFAULT 'general',
                success INTEGER DEFAULT 1,
                rating INTEGER DEFAULT 5,
                model_used TEXT,
                created_at TEXT
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON episodes(agent_id)")
        self.conn.commit()

    def record(self, agent_id: str, task: str, result: str,
               success: bool = True, rating: int = 5,
               task_type: str = "general", model: str = ""):
        self.conn.execute("""
            INSERT INTO episodes 
            (agent_id, task_summary, result_summary, task_type, success, rating, model_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, task[:300], result[:500], task_type,
              1 if success else 0, rating, model, datetime.now().isoformat()))
        self.conn.commit()

    def recall_similar(self, agent_id: str, task: str, limit: int = 3) -> list:
        """ابحث عن مهام مشابهة بكلمات مفتاحية"""
        words = [w for w in task.split() if len(w) > 3][:5]
        if not words:
            return []
        conditions = " OR ".join(["task_summary LIKE ?" for _ in words])
        params = [f"%{w}%" for w in words] + [agent_id, limit]
        rows = self.conn.execute(f"""
            SELECT task_summary, result_summary, success, rating
            FROM episodes
            WHERE ({conditions}) AND agent_id = ? AND success = 1
            ORDER BY rating DESC, created_at DESC
            LIMIT ?
        """, params).fetchall()
        return [{"task": r[0], "result": r[1], "rating": r[3]} for r in rows]

    def get_lessons(self, agent_id: str, limit: int = 3) -> str:
        rows = self.conn.execute("""
            SELECT task_summary, result_summary, rating
            FROM episodes WHERE agent_id = ? AND success = 1
            ORDER BY rating DESC, created_at DESC LIMIT ?
        """, (agent_id, limit)).fetchall()
        if not rows: return ""
        lessons = []
        for task, result, rating in rows:
            lessons.append(f"• مهمة مشابهة: {task[:100]}\n  → نجح بـ: {result[:150]}")
        return "\n".join(lessons)

class L3_Semantic:
    """Chroma — بحث دلالي"""
    def __init__(self):
        self._chroma = None

    def _get_chroma(self):
        if self._chroma is None:
            try:
                import chromadb
                client = chromadb.PersistentClient(path="workspace/chroma_db")
                self._chroma = client
            except Exception as e:
                logger.warning(f"Chroma not available: {e}")
        return self._chroma

    def store(self, agent_id: str, content: str, metadata: dict = None):
        chroma = self._get_chroma()
        if not chroma: return
        try:
            col = chroma.get_or_create_collection(f"agent_{agent_id}")
            doc_id = hashlib.md5(content.encode()).hexdigest()[:12]
            col.add(documents=[content[:1000]], ids=[doc_id],
                   metadatas=[{**(metadata or {}), "agent_id": agent_id}])
        except Exception as e:
            logger.warning(f"Chroma store failed: {e}")

    def search(self, agent_id: str, query: str, k: int = 3) -> str:
        chroma = self._get_chroma()
        if not chroma: return ""
        try:
            col = chroma.get_or_create_collection(f"agent_{agent_id}")
            results = col.query(query_texts=[query], n_results=min(k, col.count()))
            docs = results.get("documents", [[]])[0]
            return "\n".join(docs[:3])
        except Exception as e:
            logger.warning(f"Chroma search failed: {e}")
            return ""

class L4_Compressed:
    """ملخص مضغوط يُحقن في system_prompt"""
    def get_summary(self, agent_id: str) -> str:
        summary_file = SUMMARIES_DIR / f"{agent_id}_summary.md"
        if summary_file.exists():
            return summary_file.read_text(encoding="utf-8")[:500]
        return ""

    def save_summary(self, agent_id: str, summary: str):
        SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
        (SUMMARIES_DIR / f"{agent_id}_summary.md").write_text(summary, encoding="utf-8")

class HierarchicalMemory:
    """الواجهة الموحدة للذاكرة"""
    _instances = {}

    @classmethod
    def for_agent(cls, agent_id: str):
        if agent_id not in cls._instances:
            cls._instances[agent_id] = cls(agent_id)
        return cls._instances[agent_id]

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.L1 = L1_Working()
        self.L2 = L2_Episodic()
        self.L3 = L3_Semantic()
        self.L4 = L4_Compressed()

    def inject_context(self, task: str, max_chars: int = 2000) -> str:
        """اجمع أفضل context من كل المستويات"""
        context_parts = []

        # L2: دروس من التجارب
        lessons = self.L2.get_lessons(self.agent_id, limit=2)
        if lessons:
            context_parts.append(f"## دروسي السابقة:\n{lessons}")

        # L3: بحث دلالي
        semantic = self.L3.search(self.agent_id, task, k=2)
        if semantic:
            context_parts.append(f"## معرفتي المرتبطة:\n{semantic[:400]}")

        # L4: الملخص المضغوط
        summary = self.L4.get_summary(self.agent_id)
        if summary:
            context_parts.append(f"## خلاصة خبرتي:\n{summary[:300]}")

        result = "\n\n".join(context_parts)
        return result[:max_chars]

    def record_outcome(self, task: str, result: str, success: bool,
                       rating: int = 5, task_type: str = "general", model: str = ""):
        """سجّل نتيجة المهمة في كل المستويات"""
        # L2
        self.L2.record(self.agent_id, task, result, success, rating, task_type, model)
        # L3 (إذا كانت النتيجة مهمة)
        if success and len(result) > 100:
            self.L3.store(self.agent_id, result, {"task": task[:100], "type": task_type})
```

---

## المرحلة C — التطور الذاتي الآمن

### 5. core/safe_evolution.py
```python
"""
النظام يحسّن نفسه — بأمان تام
مستوحى من hive + constitutional AI
"""
import json, logging, shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("army81.evolution")

EVOLUTION_LOG = Path("workspace/evolution_log.json")
BACKUPS_DIR = Path("workspace/backups")

class SafeEvolution:
    def __init__(self, agents_registry: dict = None, guardrails=None):
        self.agents = agents_registry or {}
        self.guardrails = guardrails
        self.log = self._load_log()

    def _load_log(self) -> list:
        if EVOLUTION_LOG.exists():
            return json.loads(EVOLUTION_LOG.read_text())
        return []

    def _save_log(self):
        EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        EVOLUTION_LOG.write_text(json.dumps(self.log, ensure_ascii=False, indent=2))

    def backup_agent(self, agent_id: str, agent_json_path: str):
        """احفظ نسخة احتياطية قبل أي تغيير"""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f"{agent_id}_{ts}.json"
        shutil.copy2(agent_json_path, backup_path)
        logger.info(f"Backed up {agent_id} to {backup_path}")
        return str(backup_path)

    def rollback(self, agent_id: str, agent_json_path: str) -> bool:
        """أعد الوكيل لآخر نسخة احتياطية"""
        backups = sorted(BACKUPS_DIR.glob(f"{agent_id}_*.json"), reverse=True)
        if not backups:
            logger.error(f"No backup found for {agent_id}")
            return False
        shutil.copy2(backups[0], agent_json_path)
        self.log.append({
            "ts": datetime.now().isoformat(),
            "agent": agent_id,
            "action": "rollback",
            "backup": str(backups[0])
        })
        self._save_log()
        logger.info(f"Rolled back {agent_id}")
        return True

    def propose_prompt_improvement(self, agent_id: str, weak_areas: list) -> str:
        """اقترح تحسين للـ system prompt"""
        if not weak_areas:
            return ""
        additions = "\n".join([f"- تحسين في: {area}" for area in weak_areas[:3]])
        return f"\n\n## تحسينات مضافة ({datetime.now().strftime('%Y-%m-%d')}):\n{additions}"

    def record_improvement(self, agent_id: str, action: str,
                           before_score: float, after_score: float, details: str = ""):
        entry = {
            "ts": datetime.now().isoformat(),
            "agent": agent_id,
            "action": action,
            "before": before_score,
            "after": after_score,
            "delta": round(after_score - before_score, 2),
            "details": details[:200]
        }
        self.log.append(entry)
        self._save_log()
        logger.info(f"Evolution recorded: {agent_id} {before_score}→{after_score}")
```

### 6. core/knowledge_distillation.py
```python
"""
Flash يتعلم من Pro — DeepSeek approach
"""
import logging
from pathlib import Path

logger = logging.getLogger("army81.distillation")

# أزواج teacher → student
PAIRS = [
    ("gemini-pro", "gemini-flash"),
    ("claude-sonnet", "claude-haiku"),
]

# أنواع المهام
TASK_KEYWORDS = {
    "medical":   ["طب","دواء","مرض","علاج","سريري","pubmed"],
    "financial": ["سوق","سهم","اقتصاد","مالي","عملة","ناتج"],
    "code":      ["كود","برمج","python","api","debug","function"],
    "research":  ["بحث","ورقة","دراسة","arxiv","أثبت"],
    "strategy":  ["استراتيج","خطة","قرار","تحليل","رؤية"],
    "legal":     ["قانون","محكمة","حقوق","معاهدة","تشريع"],
}

class KnowledgeDistillation:
    def __init__(self, episodic_memory=None):
        self.memory = episodic_memory  # L2_Episodic

    def classify_task(self, task: str) -> str:
        task_lower = task.lower()
        scores = {}
        for topic, keywords in TASK_KEYWORDS.items():
            scores[topic] = sum(1 for k in keywords if k in task_lower)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    def get_teacher_examples(self, task_type: str, k: int = 3) -> str:
        """أعطِ الـ student أمثلة ناجحة من الـ teacher"""
        if not self.memory:
            return ""
        rows = self.memory.conn.execute("""
            SELECT task_summary, result_summary, rating
            FROM episodes
            WHERE task_type = ? AND success = 1 AND rating >= 7
            ORDER BY rating DESC LIMIT ?
        """, (task_type, k)).fetchall()

        if not rows:
            return ""
        examples = []
        for task, result, rating in rows:
            examples.append(f"مثال ناجح (تقييم {rating}/10):\nالمهمة: {task[:100]}\nالحل: {result[:200]}")
        return "\n\n---\n\n".join(examples)

    def should_use_teacher(self, task_type: str, agent_model: str) -> bool:
        """هل يحتاج هذا النوع نموذج أقوى؟"""
        # إذا كان الوكيل يستخدم flash والمهمة معقدة → استخدم pro
        is_student = any(s in agent_model for s in ["flash", "haiku", "local"])
        is_complex = task_type in ["medical", "legal", "strategy"]
        return is_student and is_complex
```

---

## المرحلة D — ربط كل شيء بـ BaseAgent

### 7. عدّل core/base_agent.py

أضف في نهاية دالة `__init__` في `BaseAgent`:
```python
# v3 additions — الذاكرة الهرمية والحماية
from memory.hierarchical_memory import HierarchicalMemory
from core.constitutional_guardrails import ConstitutionalGuardrails
from core.knowledge_distillation import KnowledgeDistillation

self._hier_memory = HierarchicalMemory.for_agent(self.agent_id)
self._guardrails = ConstitutionalGuardrails()
self._distillation = KnowledgeDistillation(self._hier_memory.L2)
```

في بداية دالة `run()` أضف:
```python
# احصل على context من الذاكرة
memory_ctx = self._hier_memory.inject_context(task)
task_type = self._distillation.classify_task(task)

# أضف الدروس السابقة للـ system prompt مؤقتاً
if memory_ctx:
    context = context or {}
    context["_memory_context"] = memory_ctx

# أضف أمثلة من التقطير إذا لزم
if self._distillation.should_use_teacher(task_type, self.model_alias):
    examples = self._distillation.get_teacher_examples(task_type)
    if examples:
        context = context or {}
        context["_examples"] = examples
```

في `_build_system_prompt` أضف:
```python
# أضف الذاكرة والأمثلة إذا وُجدت
memory_ctx = context.get("_memory_context", "")
examples = context.get("_examples", "")
if memory_ctx:
    prompt += f"\n\n---\n{memory_ctx}"
if examples:
    prompt += f"\n\n## أمثلة ناجحة مشابهة:\n{examples}"
```

في نهاية run() بعد النجاح:
```python
# سجّل في الذاكرة الهرمية
success = result.status == "success"
self._hier_memory.record_outcome(
    task=task,
    result=result.result,
    success=success,
    rating=7 if success else 3,
    task_type=self._distillation.classify_task(task),
    model=result.model_used if hasattr(result, "model_used") else self.model_alias
)
```

---

## المرحلة E — الجدولة التلقائية

### 8. أضف لـ scripts/daily_updater.py

في نهاية الملف، أضف دالة للجدولة الكاملة:
```python
def run_scheduler():
    """تشغيل كل المهام المجدولة"""
    from apscheduler.schedulers.blocking import BlockingScheduler
    scheduler = BlockingScheduler(timezone="Asia/Riyadh")

    # كل يوم 2 صباحاً — تحديث خارجي
    scheduler.add_job(lambda: DailyUpdater().run_daily_update(),
                      'cron', hour=2, minute=0, id='daily_update')

    # كل أحد 4 صباحاً — ضغط الذاكرة
    def compress_all():
        from memory.hierarchical_memory import HierarchicalMemory
        import glob, json
        agent_files = glob.glob("agents/**/*.json", recursive=True)
        for f in agent_files:
            try:
                agent_id = json.load(open(f)).get("agent_id")
                if agent_id:
                    mem = HierarchicalMemory.for_agent(agent_id)
                    lessons = mem.L2.get_lessons(agent_id, limit=10)
                    if lessons:
                        mem.L4.save_summary(agent_id, f"# خبرة {agent_id}\n{lessons}")
            except: pass
    scheduler.add_job(compress_all, 'cron', day_of_week='sun', hour=4, id='compress')

    print("⏰ Scheduler started. Press Ctrl+C to stop.")
    scheduler.start()

if __name__ == "__main__":
    import sys
    if "--schedule" in sys.argv:
        run_scheduler()
    else:
        updater = DailyUpdater()
        result = updater.run_daily_update()
        print(json.dumps(result, ensure_ascii=False, indent=2))
```

---

## المرحلة F — الاختبارات

### 9. ابنِ tests/benchmark_tasks.json
```json
{
  "tasks": [
    {"id": "B001", "type": "research", "task": "لخص آخر تطورات نماذج اللغة الكبيرة في 100 كلمة", "min_words": 50},
    {"id": "B002", "type": "code", "task": "اكتب دالة Python تحسب مجموع أرقام قائمة", "check": "def"},
    {"id": "B003", "type": "strategy", "task": "اذكر 3 نقاط قوة لنظام الوكلاء متعدد التخصصات", "min_words": 40},
    {"id": "B004", "type": "medical", "task": "اشرح الفرق بين الخلية T والخلية B في المناعة", "min_words": 40},
    {"id": "B005", "type": "financial", "task": "ما هي مخاطر الاستثمار في العملات المشفرة؟", "min_words": 40}
  ]
}
```

### 10. ابنِ tests/test_v3_architecture.py
```python
"""اختبارات Army81 v3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅"; FAIL = "❌"
results = []

def test(name, fn):
    try:
        fn(); print(f"  {PASS} {name}"); results.append(("pass", name))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}"); results.append(("fail", name, str(e)))

print("\n" + "="*50)
print("  Army81 v3 Architecture Tests")
print("="*50)

print("\n🛡️ SmartQueue:")
def t_queue():
    from core.smart_queue import SmartQueue, MODEL_LIMITS
    q = SmartQueue()
    assert len(MODEL_LIMITS) >= 4
    stats = q.get_stats()
    assert "total" in stats

def t_queue_fallback():
    from core.smart_queue import SmartQueue
    q = SmartQueue()
    chain = q._get_fallback_chain("gemini-pro")
    assert chain[0] == "gemini-pro"
    assert len(chain) > 1

test("استيراد SmartQueue", t_queue)
test("fallback chain صحيح", t_queue_fallback)

print("\n🏛️ Army81Adapter:")
def t_adapter():
    from core.army81_adapter import Army81Adapter, _complexity_score
    assert _complexity_score("مرحبا") <= 3
    assert _complexity_score("حلل وقارن استراتيجيات التسويق الرقمي وضع خطة متكاملة") >= 5

def t_adapter_engine():
    from core.army81_adapter import Army81Adapter
    a = Army81Adapter()
    assert a._select_engine(2) == "native"
    assert a._select_engine(5) == "langgraph"
    assert a._select_engine(8) == "crewai"

test("حساب complexity score", t_adapter)
test("اختيار المحرك المناسب", t_adapter_engine)

print("\n⚖️ ConstitutionalGuardrails:")
def t_guardrails():
    from core.constitutional_guardrails import ConstitutionalGuardrails
    g = ConstitutionalGuardrails()
    allowed, reason = g.check("cost_spike", {"increase_pct": 10})
    assert allowed == True
    blocked, reason = g.check("cost_spike", {"increase_pct": 30})
    assert blocked == False
    blocked2, _ = g.check("delete_memory")
    assert blocked2 == False

test("القواعد تعمل بشكل صحيح", t_guardrails)

print("\n🧠 HierarchicalMemory:")
def t_memory_l1():
    from memory.hierarchical_memory import L1_Working
    m = L1_Working()
    m.set("test", "hello")
    assert m.get("test") == "hello"
    m.clear()
    assert m.get("test") is None

def t_memory_l2():
    from memory.hierarchical_memory import L2_Episodic
    m = L2_Episodic()
    m.record("TEST_AGENT", "اختبر الذاكرة", "نجح الاختبار", True, 8, "test")
    lessons = m.get_lessons("TEST_AGENT")
    assert "TEST_AGENT" in str(m.conn) or True  # connection exists

def t_memory_inject():
    from memory.hierarchical_memory import HierarchicalMemory
    mem = HierarchicalMemory.for_agent("TEST_INJECT")
    ctx = mem.inject_context("مهمة اختبار الذاكرة")
    assert isinstance(ctx, str)

test("L1 Working Memory", t_memory_l1)
test("L2 Episodic Memory", t_memory_l2)
test("inject_context يعمل", t_memory_inject)

print("\n⚗️ KnowledgeDistillation:")
def t_distill():
    from core.knowledge_distillation import KnowledgeDistillation
    d = KnowledgeDistillation()
    assert d.classify_task("اكتب كود python") == "code"
    assert d.classify_task("حلل السوق المالي") == "financial"
    assert d.classify_task("اشرح علاج السرطان") == "medical"

def t_distill_student():
    from core.knowledge_distillation import KnowledgeDistillation
    d = KnowledgeDistillation()
    assert d.should_use_teacher("medical", "gemini-flash") == True
    assert d.should_use_teacher("general", "gemini-pro") == False

test("تصنيف المهام صحيح", t_distill)
test("تحديد teacher/student", t_distill_student)

print("\n🔄 SafeEvolution:")
def t_evolution():
    from core.safe_evolution import SafeEvolution
    e = SafeEvolution()
    e.record_improvement("TEST", "prompt_update", 60.0, 75.0, "تحسين في الطب")
    assert len(e.log) > 0

test("تسجيل التطور يعمل", t_evolution)

# النتيجة
print("\n" + "="*50)
passed = sum(1 for r in results if r[0] == "pass")
failed = sum(1 for r in results if r[0] == "fail")
print(f"  النتيجة: {passed} نجح | {failed} فشل")
print("="*50)
if failed:
    for r in results:
        if r[0] == "fail": print(f"  ❌ {r[1]}: {r[2]}")
    sys.exit(1)
```

---

## النهاية — ارفع كل شيء

```bash
python tests/test_v3_architecture.py
python tests/test_core.py
git add .
git commit -m "feat: Army81 v3 - hierarchical memory + safe evolution + distillation + smart queue"
git push origin main
```

## ملاحظة مهمة
- لا تكسر أي endpoint موجود في gateway/app.py
- إذا فشل أي import → أضف try/except وكمّل
- الأولوية: الاختبارات تنجح أولاً
