"""
Army81 - BaseAgent
الوكيل الأساسي الذي يرث منه كل الـ 81 وكيل
v3: تكامل مع HierarchicalMemory + CollectiveMemory + SmartQueue
    + ConstitutionalGuardrails + KnowledgeDistillation + Army81Adapter
"""
import json
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from core.llm_client import LLMClient

# ── v3 imports (lazy للتحميل السريع) ──────────────────────────
try:
    from memory.hierarchical_memory import HierarchicalMemory
    _HM_AVAILABLE = True
except ImportError:
    _HM_AVAILABLE = False

try:
    from memory.collective_memory import CollectiveMemory
    _CM_AVAILABLE = True
except ImportError:
    _CM_AVAILABLE = False

try:
    from core.smart_queue import SmartQueue
    _SQ_AVAILABLE = True
except ImportError:
    _SQ_AVAILABLE = False

try:
    from core.constitutional_guardrails import ConstitutionalGuardrails
    _CG_AVAILABLE = True
except ImportError:
    _CG_AVAILABLE = False

try:
    from core.knowledge_distillation import KnowledgeDistillation
    _KD_AVAILABLE = True
except ImportError:
    _KD_AVAILABLE = False

try:
    from core.army81_adapter import Army81Adapter
    _AA_AVAILABLE = True
except ImportError:
    _AA_AVAILABLE = False

logger = logging.getLogger("army81.agent")


@dataclass
class Tool:
    """أداة يمكن للوكيل استخدامها"""
    name: str
    description: str
    func: Callable
    parameters: Dict = field(default_factory=dict)


@dataclass
class AgentResult:
    """نتيجة تنفيذ مهمة"""
    agent_id: str
    agent_name: str
    task: str
    result: str
    status: str  # "success" | "error"
    model_used: str
    elapsed_seconds: float
    tokens_used: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "task": self.task[:200],
            "result": self.result,
            "status": self.status,
            "model_used": self.model_used,
            "elapsed_seconds": self.elapsed_seconds,
            "tokens_used": self.tokens_used,
            "timestamp": self.timestamp,
        }


class BaseAgent:
    """
    الوكيل الأساسي
    كل وكيل من الـ 81 يرث من هذا الكلاس
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        name_ar: str,
        category: str,
        description: str,
        system_prompt: str,
        model_alias: str = "gemini-flash",
        tools: List[Tool] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.name_ar = name_ar
        self.category = category
        self.description = description
        self.system_prompt = system_prompt
        self.model_alias = model_alias
        self.tools: List[Tool] = tools or []

        # الذاكرة القصيرة (آخر 20 رسالة)
        self.conversation: List[Dict] = []

        # الإحصائيات
        self.stats = {
            "tasks_done": 0,
            "tasks_failed": 0,
            "total_tokens": 0,
            "created_at": datetime.now().isoformat(),
            "last_active": None,
        }

        # LLM Client
        self._llm: Optional[LLMClient] = None

        # ── v3: مكونات النظام الجديد ──────────────────────────
        self.memory = HierarchicalMemory(self.agent_id) if _HM_AVAILABLE else None
        self.collective = CollectiveMemory() if _CM_AVAILABLE else None
        self.queue = SmartQueue.get_instance() if _SQ_AVAILABLE else None
        self.guardrails = ConstitutionalGuardrails() if _CG_AVAILABLE else None
        self.distillation = KnowledgeDistillation() if _KD_AVAILABLE else None
        self.adapter = Army81Adapter() if _AA_AVAILABLE else None

        # ── v5: الشبكة العصبية + المهارات ──────────────────
        self.neural_net = None  # يُعيّن من NeuralNetwork.register_agents()
        self._skill_memory = None  # lazy
        self._cloud_memory = None  # v6: ذاكرة سحابية

        # ── v14: ذاكرة السرب + التنفيذ العميق + اقتصاد الرموز ──
        self._swarm_memory = None
        self._deep_executor = None
        self._token_economy = None
        self._multi_router = None
        self._network_intel = None

        logger.info(f"Agent ready: {self.agent_id} ({self.name_ar})")

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(self.model_alias)
        return self._llm

    @property
    def skill_memory(self):
        """AutoSkill + MemSkill adapter (lazy)"""
        if self._skill_memory is None:
            try:
                from core.skill_memory_adapter import get_skill_memory_adapter
                self._skill_memory = get_skill_memory_adapter()
            except Exception:
                pass
        return self._skill_memory

    @property
    def cloud_memory(self):
        """v6: Cloud Memory — Redis + Supabase + SQLite"""
        if self._cloud_memory is None:
            try:
                from memory.cloud_memory import get_cloud_memory
                self._cloud_memory = get_cloud_memory()
            except Exception:
                pass
        return self._cloud_memory

    @property
    def swarm_memory(self):
        """v14: ذاكرة السرب — فردية + نواة"""
        if self._swarm_memory is None:
            try:
                from memory.swarm_memory import SwarmMemoryManager
                self._swarm_memory = SwarmMemoryManager.get_instance()
            except Exception:
                pass
        return self._swarm_memory

    @property
    def deep_executor(self):
        """v14: التنفيذ العميق متعدد الخطوات"""
        if self._deep_executor is None:
            try:
                from core.deep_executor import DeepExecutor
                self._deep_executor = DeepExecutor()
            except Exception:
                pass
        return self._deep_executor

    @property
    def token_economy(self):
        """v14: اقتصاد الرموز"""
        if self._token_economy is None:
            try:
                from core.token_economy import TokenEconomy
                self._token_economy = TokenEconomy()
            except Exception:
                pass
        return self._token_economy

    @property
    def multi_router(self):
        """v14: التوجيه متعدد النماذج"""
        if self._multi_router is None:
            try:
                from core.multi_model_router import MultiModelRouter
                self._multi_router = MultiModelRouter()
            except Exception:
                pass
        return self._multi_router

    @property
    def network_intel(self):
        """v14: الذكاء الشبكي"""
        if self._network_intel is None:
            try:
                from core.network_intelligence import NetworkIntelligence
                self._network_intel = NetworkIntelligence()
            except Exception:
                pass
        return self._network_intel

    def run(self, task: str, context: Dict = None) -> AgentResult:
        """تنفيذ مهمة — النقطة الرئيسية (v3)"""
        context = context or {}
        start = time.time()

        try:
            # A: احصل على context من الذاكرة الهرمية (v3)
            memory_ctx = ""
            if self.memory:
                memory_ctx = self.memory.inject_context(self.agent_id, task)

            collective_ctx = ""
            if self.collective:
                collective_ctx = self.collective.query(task[:50], self.agent_id)

            examples = ""
            if self.distillation:
                examples = self.distillation.get_examples_for_student(
                    self._classify_task(task), self.model_alias, k=3)

            # B-v5: مهارات AutoSkill قبل المهمة
            skill_ctx = ""
            if self.skill_memory:
                try:
                    skill_ctx = self.skill_memory.before_task(self.agent_id, task)
                except Exception:
                    pass

            # B-v5: إشارات الشبكة العصبية
            neural_ctx = ""
            if self.neural_net:
                try:
                    neural_ctx = self.neural_net.format_signals_for_prompt(self.agent_id)
                except Exception:
                    pass

            # B-v9: عقدة الوعي — الوكيل يدرك حالته في الشبكة
            consciousness_ctx = ""
            try:
                from core.consciousness import get_consciousness
                cn = get_consciousness()
                _router = getattr(self.neural_net, 'router', None) if self.neural_net else None
                consciousness_ctx = cn.generate(self.agent_id, task, _router)
            except Exception:
                pass

            # J-v14: ذاكرة السرب الشخصية
            swarm_ctx = ""
            if self.swarm_memory:
                try:
                    partner = context.get("partner", "")
                    swarm_ctx = self.swarm_memory.inject_context(self.agent_id, partner)
                except Exception:
                    pass

            # K-v14: فحص ميزانية الرموز قبل التنفيذ
            if self.token_economy:
                try:
                    self.token_economy.initialize_agent(self.agent_id)
                except Exception:
                    pass

            # C: أثرِ الـ system prompt
            enriched_system = self.system_prompt
            if consciousness_ctx:
                enriched_system = consciousness_ctx + "\n\n" + enriched_system
            if memory_ctx:
                enriched_system += f"\n\n{memory_ctx}"
            if examples:
                enriched_system += f"\n\n## أمثلة ناجحة مشابهة:\n{examples}"
            if skill_ctx:
                enriched_system += f"\n\n{skill_ctx}"
            if neural_ctx:
                enriched_system += f"\n\n{neural_ctx}"
            if swarm_ctx:
                enriched_system += f"\n\n{swarm_ctx}"

            # Layer 1: Chain-of-Thought — تفكير منظم قبل كل إجابة
            enriched_system += """

## منهجية التفكير (إلزامي):
قبل كل إجابة، فكّر بصوت عالٍ:
<thinking>
- ما المطلوب بالضبط؟
- ما المعلومات المتوفرة لدي؟
- ما الزاوية الأفضل للمعالجة؟
- هل هناك افتراضات يجب تحديها؟
</thinking>
ثم أجب بدقة وعمق.
"""

            # Layer 2: Real-Time Grounding — سياق محدّث من الأخبار
            try:
                from scripts.daily_updater import fetch_recent_news
                keywords = task.split()[:3]
                news = fetch_recent_news(" ".join(keywords), limit=2)
                if news:
                    enriched_system += f"\n\n## سياق محدّث:\n{news[:500]}"
            except Exception:
                pass

            # Layer 4: Constitutional Principles — مبادئ ثابتة
            enriched_system += """

## مبادئي الثابتة:
- أقول "لا أعلم" عندما لا أعلم
- أُميّز بين الرأي والحقيقة بوضوح
- أحترم حدود تخصصي وأفوّض لمن هو أكفأ
- أُصحح نفسي فوراً بلا مقاومة
- أدعم كل ادعاء بمصدر أو دليل
"""

            # C: ابنِ الرسائل
            messages = self._build_messages(task, context)
            messages[0]["content"] = enriched_system

            # D: نفّذ عبر LLM
            response = self.llm.chat(messages)
            result_text = response["content"]

            # معالجة طلبات الأدوات
            if self.tools and "USE_TOOL:" in result_text:
                result_text = self._handle_tool_request(result_text, task, context)

            # تحديث الذاكرة القصيرة
            self.conversation.append({"role": "user", "content": task})
            self.conversation.append({"role": "assistant", "content": result_text})
            if len(self.conversation) > 40:
                self.conversation = self.conversation[-40:]

            # E: سجّل في الذاكرة الهرمية (v3)
            if self.memory:
                self.memory.store(
                    self.agent_id, task, result_text,
                    success=True, rating=7,
                    model_used=self.model_alias,
                    tokens=response.get("tokens", 0),
                    task_type=self._classify_task(task),
                )

            # F: ساهم في الذاكرة الجماعية (v3)
            if self.collective and len(result_text) > 100:
                self.collective.contribute(
                    self.agent_id, result_text[:500],
                    topic=self._classify_task(task))

            # G-v5: AutoSkill بعد المهمة — استخرج مهارة
            if self.skill_memory:
                try:
                    self.skill_memory.after_task(
                        self.agent_id, task, result_text, True, 7)
                except Exception:
                    pass

            # H-v5: انشر إشارة عبر الشبكة العصبية
            if self.neural_net:
                try:
                    self.neural_net.after_task_propagate(self.agent_id, result)
                except Exception:
                    pass

            # I-v14: تسجيل في ذاكرة السرب + اقتصاد الرموز + الشبكة
            if self.swarm_memory:
                try:
                    task_type = self._classify_task(task)
                    if len(result_text) > 100:
                        self.swarm_memory.record_insight(
                            self.agent_id, result_text[:300], topic=task_type)
                    # تقوية الروابط مع الشريك
                    partner = context.get("partner", "")
                    if partner and self.network_intel:
                        self.network_intel.strengthen_connection(self.agent_id, partner, 0.05)
                except Exception:
                    pass

            if self.token_economy:
                try:
                    tokens = response.get("tokens", 0) or 500
                    self.token_economy.spend(self.agent_id, tokens, task[:50])
                except Exception:
                    pass

            if self.network_intel:
                try:
                    self.network_intel.propagate_signal(
                        self.agent_id, "task_completed",
                        {"task_type": self._classify_task(task), "success": True},
                        strength=0.8
                    )
                except Exception:
                    pass

            # I-v6: حفظ في الذاكرة السحابية (Redis + Supabase)
            if self.cloud_memory:
                try:
                    self.cloud_memory.store_episode(
                        self.agent_id, task, result_text,
                        success=True, rating=7,
                        model=response.get("model", self.model_alias),
                        tokens=response.get("tokens", 0),
                        task_type=self._classify_task(task),
                    )
                except Exception:
                    pass

            # تحديث الإحصائيات
            elapsed = round(time.time() - start, 2)
            self.stats["tasks_done"] += 1
            self.stats["total_tokens"] += response.get("tokens", 0)
            self.stats["last_active"] = datetime.now().isoformat()

            return AgentResult(
                agent_id=self.agent_id,
                agent_name=self.name_ar,
                task=task,
                result=result_text,
                status="success",
                model_used=response.get("model", self.model_alias),
                elapsed_seconds=elapsed,
                tokens_used=response.get("tokens", 0),
            )

        except Exception as e:
            self.stats["tasks_failed"] += 1
            # سجّل الفشل في الذاكرة (v3)
            if self.memory:
                try:
                    self.memory.store(self.agent_id, task, str(e),
                                      success=False, rating=1)
                except Exception:
                    pass
            logger.error(f"Agent {self.agent_id} failed: {e}")
            return AgentResult(
                agent_id=self.agent_id,
                agent_name=self.name_ar,
                task=task,
                result=f"خطأ: {str(e)}",
                status="error",
                model_used=self.model_alias,
                elapsed_seconds=round(time.time() - start, 2),
                tokens_used=0,
            )

    # ═══════════════════════════════════════════════════════════
    # v14: قدرات متقدمة — تنفيذ عميق + تفويض + متعدد النماذج
    # ═══════════════════════════════════════════════════════════

    def run_deep(self, task: str, context: Dict = None) -> "AgentResult":
        """
        تنفيذ عميق — يكسر المهمة المعقدة إلى خطوات ويسلسلها
        يُستخدم تلقائياً للمهام المعقدة (complexity > 5)
        """
        context = context or {}
        if not self.deep_executor:
            return self.run(task, context)

        try:
            plan = self.deep_executor.plan_execution(task, self.agent_id)
            if len(plan.steps) <= 1:
                return self.run(task, context)

            # تنفيذ الخطة
            result_plan = self.deep_executor.execute_plan(plan, self._agent_executor)
            return AgentResult(
                agent_id=self.agent_id,
                agent_name=self.name_ar,
                task=task,
                result=result_plan.final_result or "لم تكتمل الخطة",
                status="success" if result_plan.status == "completed" else "error",
                model_used=self.model_alias,
                elapsed_seconds=0,
                tokens_used=0,
            )
        except Exception as e:
            logger.error(f"Deep execution failed: {e}")
            return self.run(task, context)

    def _agent_executor(self, agent_id: str, task: str) -> Dict:
        """يُستخدم من DeepExecutor لتنفيذ مهمة بوكيل محدد"""
        result = self.run(task)
        return {"result": result.result, "tokens": result.tokens_used}

    def run_multi(self, task: str, models: List[str] = None,
                  mode: str = "ensemble") -> "AgentResult":
        """
        تنفيذ بعدة نماذج في آنٍ واحد
        mode: 'parallel' | 'ensemble' | 'debate'
        """
        if not self.multi_router:
            return self.run(task)

        start = time.time()
        try:
            if mode == "parallel" and models:
                result = self.multi_router.route_parallel(
                    task, models, system_prompt=self.system_prompt)
                text = result.get("best_response", "")
                model = result.get("best_model", self.model_alias)
            elif mode == "debate" and models:
                result = self.multi_router.route_debate(
                    task, models, system_prompt=self.system_prompt)
                text = result.get("content", "")
                model = result.get("judge", self.model_alias)
            else:
                result = self.multi_router.route_ensemble(
                    task, self.agent_id, system_prompt=self.system_prompt)
                text = result.get("content", "")
                model = result.get("refine_model", self.model_alias)

            return AgentResult(
                agent_id=self.agent_id, agent_name=self.name_ar,
                task=task, result=text, status="success",
                model_used=model, elapsed_seconds=round(time.time()-start, 2),
                tokens_used=0,
            )
        except Exception as e:
            logger.error(f"Multi-model failed: {e}")
            return self.run(task)

    def delegate(self, target_agent_id: str, task: str,
                 context: Dict = None) -> Optional[Dict]:
        """
        تفويض مهمة لوكيل آخر — التعاون الحقيقي
        """
        if self.neural_net and hasattr(self.neural_net, 'router'):
            router = self.neural_net.router
            if router and target_agent_id in router.agents:
                target = router.agents[target_agent_id]
                result = target.run(task, context or {})

                # تقوية الرابط في الشبكة
                if self.network_intel:
                    self.network_intel.strengthen_connection(
                        self.agent_id, target_agent_id, 0.1)

                # تسجيل التعاون في ذاكرة السرب
                if self.swarm_memory:
                    self.swarm_memory.record_collaboration(
                        self.agent_id, [target_agent_id],
                        task[:100], result.result[:200],
                        success=(result.status == "success")
                    )

                return result.to_dict()
        return None

    def _build_messages(self, task: str, context: Dict) -> List[Dict]:
        """بناء سلسلة الرسائل"""
        system = self._build_system(context)
        messages = [{"role": "system", "content": system}]

        # إضافة الذاكرة القصيرة (آخر 10 رسائل)
        messages.extend(self.conversation[-10:])

        # المهمة الحالية
        task_text = task
        if context:
            task_text += f"\n\n[سياق: {json.dumps(context, ensure_ascii=False, indent=2)}]"
        messages.append({"role": "user", "content": task_text})

        return messages

    def _build_system(self, context: Dict) -> str:
        """بناء system prompt"""
        prompt = self.system_prompt

        if self.tools:
            prompt += "\n\n## الأدوات المتاحة:\n"
            for tool in self.tools:
                prompt += f"- **{tool.name}**: {tool.description}\n"
            prompt += "\nلاستخدام أداة اكتب: USE_TOOL: tool_name | input\n"

        return prompt

    def _handle_tool_request(self, response_text: str, task: str, context: Dict) -> str:
        """تنفيذ الأداة التي طلبها النموذج"""
        lines = response_text.split("\n")
        results = []

        for line in lines:
            if line.startswith("USE_TOOL:"):
                try:
                    parts = line.replace("USE_TOOL:", "").strip().split("|")
                    tool_name = parts[0].strip()
                    tool_input = parts[1].strip() if len(parts) > 1 else ""

                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        tool_result = tool.func(tool_input)
                        results.append(f"[نتيجة {tool_name}]: {tool_result}")
                    else:
                        results.append(f"[خطأ]: أداة '{tool_name}' غير موجودة")
                except Exception as e:
                    results.append(f"[خطأ في الأداة]: {e}")

        if results:
            # أرسل النتائج للنموذج ليكمل الإجابة
            follow_up = response_text + "\n\n" + "\n".join(results)
            messages = self._build_messages(task, context)
            messages.append({"role": "assistant", "content": follow_up})
            messages.append({"role": "user", "content": "أكمل إجابتك بناءً على نتائج الأدوات."})
            final = self.llm.chat(messages)
            return final["content"]

        return response_text

    def _classify_task(self, task: str) -> str:
        """تصنيف المهمة (v3) — يُستخدم لتوجيه الذاكرة والتقطير"""
        keywords = {
            "medical":   ["طب", "دواء", "مرض", "علاج", "سريري", "pubmed"],
            "financial": ["سوق", "سهم", "اقتصاد", "مالي", "عملة", "nasdaq"],
            "code":      ["كود", "برمج", "python", "api", "debug", "function", "class"],
            "research":  ["بحث", "ورقة", "دراسة", "أثبت", "نظرية", "arxiv"],
            "strategy":  ["استراتيج", "خطة", "قرار", "تحليل", "رؤية"],
            "news":      ["خبر", "أخبار", "حدث", "تقرير", "مستجد"],
        }
        task_lower = task.lower()
        for topic, kws in keywords.items():
            if any(k in task_lower for k in kws):
                return topic
        return "general"

    def reset_memory(self):
        """مسح الذاكرة القصيرة"""
        self.conversation = []

    def info(self) -> Dict:
        """معلومات الوكيل"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "name_ar": self.name_ar,
            "category": self.category,
            "description": self.description,
            "model": self.model_alias,
            "tools": [t.name for t in self.tools],
            "stats": self.stats,
        }

    def __repr__(self):
        return f"<Agent {self.agent_id} | {self.name_ar} | {self.model_alias}>"


def load_agent_from_json(json_path: str, tools_registry: Dict[str, Tool] = None) -> BaseAgent:
    """تحميل وكيل من ملف JSON"""
    # إذا لم يُمرَّر سجل أدوات، ابنِ سجل الأدوات الكامل تلقائياً
    # حتى تُفعَّل أدوات الوكلاء فعلياً عند التحميل من JSON.
    if tools_registry is None:
        try:
            from tools.registry import build_tools_registry
            tools_registry = build_tools_registry()
        except Exception:
            tools_registry = {}
    else:
        tools_registry = tools_registry or {}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ربط الأدوات
    agent_tools = []
    for tool_name in data.get("tools", []):
        if tool_name in tools_registry:
            agent_tools.append(tools_registry[tool_name])
        else:
            logger.warning(f"Tool '{tool_name}' not found for agent {data['agent_id']}")

    return BaseAgent(
        agent_id=data["agent_id"],
        name=data["name"],
        name_ar=data["name_ar"],
        category=data["category"],
        description=data["description"],
        system_prompt=data["system_prompt"],
        model_alias=data.get("model", "gemini-flash"),
        tools=agent_tools,
    )
