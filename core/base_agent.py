"""
Army81 - BaseAgent
الوكيل الأساسي الذي يرث منه كل الـ 81 وكيل
"""
import json
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from core.llm_client import LLMClient

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

        logger.info(f"Agent ready: {self.agent_id} ({self.name_ar})")

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(self.model_alias)
        return self._llm

    def run(self, task: str, context: Dict = None) -> AgentResult:
        """تنفيذ مهمة — النقطة الرئيسية"""
        start = time.time()
        context = context or {}

        try:
            # بناء الرسائل
            messages = self._build_messages(task, context)

            # استدعاء النموذج
            response = self.llm.chat(messages)

            # معالجة إذا طلب النموذج استخدام أداة
            result_text = response["content"]
            if self.tools and "USE_TOOL:" in result_text:
                result_text = self._handle_tool_request(result_text, task, context)

            # تحديث الذاكرة
            self.conversation.append({"role": "user", "content": task})
            self.conversation.append({"role": "assistant", "content": result_text})
            if len(self.conversation) > 40:
                self.conversation = self.conversation[-40:]

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
