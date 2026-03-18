"""
Army81 — Deep Executor
تنفيذ عميق متعدد الخطوات — يكسر المهام المعقدة ويسلسلها
"""
import json, time, logging, random
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("army81.deep_executor")
WORKSPACE = Path("workspace")
TRACES_DIR = WORKSPACE / "execution_traces"

class ExecutionStep:
    def __init__(self, step_id: int, description: str, agent_id: str = "",
                 model: str = "", depends_on: List[int] = None):
        self.step_id = step_id
        self.description = description
        self.agent_id = agent_id
        self.model = model
        self.depends_on = depends_on or []
        self.status = "pending"
        self.result = ""
        self.error = ""
        self.started_at = None
        self.completed_at = None
        self.retries = 0
        self.tokens_used = 0

    def to_dict(self):
        return {
            "step_id": self.step_id, "description": self.description,
            "agent_id": self.agent_id, "model": self.model,
            "status": self.status, "result": self.result[:500],
            "error": self.error, "retries": self.retries,
            "tokens_used": self.tokens_used,
        }

class ExecutionPlan:
    def __init__(self, task: str, steps: List[ExecutionStep] = None):
        self.task = task
        self.steps = steps or []
        self.created_at = datetime.now().isoformat()
        self.status = "pending"
        self.final_result = ""

    def to_dict(self):
        return {
            "task": self.task[:200], "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "final_result": self.final_result[:1000],
            "created_at": self.created_at,
        }

class DeepExecutor:
    """
    محرك التنفيذ العميق
    يكسر المهام المعقدة → خطوات → ينفذها → يجمع النتائج
    """

    COMPLEXITY_KEYWORDS = {
        "simple": ["ما هو", "عرّف", "اشرح", "ترجم"],
        "medium": ["حلل", "قارن", "لخص", "اكتب مقال"],
        "complex": ["صمم نظام", "ابنِ", "خطة شاملة", "استراتيجية متكاملة"],
        "expert": ["بحث متعدد", "نظام كامل", "تحليل شامل ومتعدد الأبعاد"],
    }

    AGENT_CHAINS = {
        "code_review": [
            ("A05", "اكتب الكود"),
            ("A09", "راجع الأمان"),
            ("A74", "اختبر الجودة"),
        ],
        "research": [
            ("A02", "ابحث في المصادر العلمية"),
            ("A06", "حلل البيانات"),
            ("A10", "نظّم المعرفة"),
            ("A12", "اكتب التقرير النهائي"),
        ],
        "strategy": [
            ("A31", "اجمع المعلومات الاستخباراتية"),
            ("A34", "قيّم المخاطر"),
            ("A33", "استشرف المستقبل"),
            ("A01", "اتخذ القرار الاستراتيجي"),
        ],
        "medical": [
            ("A07", "ابحث في المراجع الطبية"),
            ("A52", "قيّم سريرياً"),
            ("A38", "حلل من منظور علمي"),
        ],
        "financial": [
            ("A08", "حلل مالياً"),
            ("A42", "قيّم العملات والأصول"),
            ("A34", "قيّم المخاطر"),
            ("A41", "ضع في السياق الاقتصادي العالمي"),
        ],
        "crisis": [
            ("A29", "قيّم الأزمة"),
            ("A31", "اجمع المعلومات"),
            ("A28", "ضع الخطة التكتيكية"),
            ("A01", "اتخذ القرار"),
        ],
    }

    def __init__(self):
        self.executions = 0
        self.chains_run = 0
        TRACES_DIR.mkdir(parents=True, exist_ok=True)

    def assess_complexity(self, task: str) -> str:
        task_lower = task.lower()
        for level in ["expert", "complex", "medium", "simple"]:
            if any(kw in task_lower for kw in self.COMPLEXITY_KEYWORDS[level]):
                return level
        return "medium" if len(task) > 200 else "simple"

    def plan_execution(self, task: str, preferred_agent: str = "") -> ExecutionPlan:
        complexity = self.assess_complexity(task)

        if complexity == "simple":
            agent = preferred_agent or "A01"
            return ExecutionPlan(task, [
                ExecutionStep(1, task, agent)
            ])

        chain_type = self._detect_chain_type(task)
        chain = self.AGENT_CHAINS.get(chain_type, [])

        if not chain:
            return ExecutionPlan(task, [
                ExecutionStep(1, f"تحليل: {task}", preferred_agent or "A01"),
                ExecutionStep(2, f"تنفيذ: {task}", preferred_agent or "A05", depends_on=[1]),
                ExecutionStep(3, f"مراجعة النتائج", "A74", depends_on=[2]),
            ])

        steps = []
        for i, (agent_id, role) in enumerate(chain, 1):
            deps = [i-1] if i > 1 else []
            steps.append(ExecutionStep(i, f"{role}: {task[:100]}", agent_id, depends_on=deps))

        return ExecutionPlan(task, steps)

    def execute_plan(self, plan: ExecutionPlan, get_agent_fn: Callable = None) -> ExecutionPlan:
        plan.status = "running"
        logger.info(f"Deep execution: {len(plan.steps)} steps")

        for step in plan.steps:
            # Check dependencies
            for dep_id in step.depends_on:
                dep_step = next((s for s in plan.steps if s.step_id == dep_id), None)
                if dep_step and dep_step.status != "completed":
                    step.status = "blocked"
                    continue

            step.status = "running"
            step.started_at = datetime.now().isoformat()

            # Build context from previous steps
            prev_results = ""
            for prev in plan.steps:
                if prev.step_id < step.step_id and prev.result:
                    prev_results += f"\n[خطوة {prev.step_id} ({prev.agent_id})]:\n{prev.result[:300]}\n"

            full_task = step.description
            if prev_results:
                full_task = f"السياق من الخطوات السابقة:\n{prev_results}\n\nمهمتك الآن: {step.description}"

            # Execute with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if get_agent_fn:
                        result = get_agent_fn(step.agent_id, full_task)
                        step.result = result.get("result", "") if isinstance(result, dict) else str(result)
                        step.tokens_used = result.get("tokens", 0) if isinstance(result, dict) else 0
                        step.status = "completed"
                        break
                    else:
                        step.result = f"[محاكاة] نتيجة الخطوة {step.step_id}"
                        step.status = "completed"
                        break
                except Exception as e:
                    step.retries += 1
                    step.error = str(e)[:200]
                    if attempt == max_retries - 1:
                        step.status = "failed"
                    time.sleep(2)

            step.completed_at = datetime.now().isoformat()
            time.sleep(1)

        # Combine results
        completed = [s for s in plan.steps if s.status == "completed"]
        if completed:
            plan.final_result = "\n\n".join(
                f"## الخطوة {s.step_id} ({s.agent_id}):\n{s.result}"
                for s in completed
            )
            plan.status = "completed"
        else:
            plan.status = "failed"

        # Save trace
        trace_file = TRACES_DIR / f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        trace_file.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

        self.executions += 1
        if len(plan.steps) > 1:
            self.chains_run += 1

        return plan

    def execute_chain(self, chain_type: str, task: str, get_agent_fn: Callable = None) -> Dict:
        chain = self.AGENT_CHAINS.get(chain_type)
        if not chain:
            return {"error": f"Chain type '{chain_type}' not found"}

        steps = []
        for i, (agent_id, role) in enumerate(chain, 1):
            steps.append(ExecutionStep(i, f"{role}: {task[:100]}", agent_id, depends_on=[i-1] if i>1 else []))

        plan = ExecutionPlan(task, steps)
        result = self.execute_plan(plan, get_agent_fn)
        return result.to_dict()

    def _detect_chain_type(self, task: str) -> str:
        task_lower = task.lower()
        detectors = {
            "code_review": ["كود", "برمج", "code", "function", "api", "debug"],
            "research": ["بحث", "ورقة", "دراسة", "مراجعة أدبيات"],
            "strategy": ["استراتيج", "خطة", "قرار", "رؤية"],
            "medical": ["طب", "مريض", "علاج", "تشخيص", "دواء"],
            "financial": ["مالي", "استثمار", "سوق", "سهم", "عملة"],
            "crisis": ["أزمة", "طوارئ", "كارثة", "خطر فوري"],
        }
        for chain_type, kws in detectors.items():
            if any(k in task_lower for k in kws):
                return chain_type
        return "research"

    def get_stats(self) -> Dict:
        return {
            "total_executions": self.executions,
            "chains_run": self.chains_run,
            "available_chains": list(self.AGENT_CHAINS.keys()),
        }
