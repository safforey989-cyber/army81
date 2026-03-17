"""
Army81 Core - BaseAgent
الوكيل الأساسي الذي يرث منه كل الوكلاء الـ 81
"""
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("army81")


@dataclass
class AgentMessage:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    agent_id: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentTool:
    name: str
    description: str
    parameters: Dict
    handler: Optional[Callable] = None


@dataclass
class AgentSkill:
    name: str
    description: str
    content: str
    version: int = 1
    success_count: int = 0
    fail_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LLMClient:
    """عميل موحد للتواصل مع أي مزود نماذج"""

    def __init__(self, provider: str, model: str, api_key: str = "", base_url: str = ""):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 4096, tools: List[Dict] = None) -> Dict:
        """إرسال رسالة للنموذج والحصول على الرد"""
        import requests

        if self.provider == "anthropic":
            return self._chat_anthropic(messages, temperature, max_tokens, tools)
        elif self.provider == "gemini":
            return self._chat_gemini(messages, temperature, max_tokens)
        else:
            # OpenAI-compatible (Ollama, OpenRouter, Groq, OpenAI, Together, etc.)
            return self._chat_openai_compat(messages, temperature, max_tokens, tools)

    def _chat_openai_compat(self, messages, temperature, max_tokens, tools=None):
        import requests
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "content": data["choices"][0]["message"].get("content", ""),
                "tool_calls": data["choices"][0]["message"].get("tool_calls", []),
                "usage": data.get("usage", {}),
                "model": data.get("model", self.model),
            }
        except Exception as e:
            logger.error(f"LLM call failed [{self.provider}/{self.model}]: {e}")
            return {"content": f"ERROR: {e}", "tool_calls": [], "usage": {}, "model": self.model}

    def _chat_anthropic(self, messages, temperature, max_tokens, tools=None):
        import requests
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        system_msg = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                filtered.append(m)

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered,
        }
        if system_msg:
            payload["system"] = system_msg
        if tools:
            payload["tools"] = [self._convert_tool_anthropic(t) for t in tools]

        try:
            resp = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            content = ""
            tool_calls = []
            for block in data.get("content", []):
                if block["type"] == "text":
                    content += block["text"]
                elif block["type"] == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "function": {"name": block["name"], "arguments": json.dumps(block["input"])}
                    })
            return {"content": content, "tool_calls": tool_calls, "usage": data.get("usage", {}), "model": self.model}
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")
            return {"content": f"ERROR: {e}", "tool_calls": [], "usage": {}, "model": self.model}

    def _chat_gemini(self, messages, temperature, max_tokens):
        import requests
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
        }
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"content": text, "tool_calls": [], "usage": {}, "model": self.model}
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return {"content": f"ERROR: {e}", "tool_calls": [], "usage": {}, "model": self.model}

    @staticmethod
    def _convert_tool_anthropic(tool):
        func = tool.get("function", tool)
        return {
            "name": func["name"],
            "description": func.get("description", ""),
            "input_schema": func.get("parameters", {})
        }


class BaseAgent:
    """
    الوكيل الأساسي - يرث منه كل الوكلاء الـ 81
    يوفر: LLM client, ذاكرة, أدوات, مهارات, تقييم ذاتي
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        name_ar: str,
        category: str,
        description: str,
        system_prompt: str,
        model: str = "qwen3:8b",
        provider: str = "ollama",
        tools: List[AgentTool] = None,
        skills: List[AgentSkill] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.name_ar = name_ar
        self.category = category
        self.description = description
        self.system_prompt = system_prompt
        self.model = model
        self.provider = provider
        self.tools = tools or []
        self.skills = skills or []

        # الذاكرة
        self.short_term_memory: List[AgentMessage] = []
        self.conversation_history: List[Dict] = []

        # الإحصائيات
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_tokens_used": 0,
            "avg_response_time": 0,
            "created_at": datetime.now().isoformat(),
            "last_active": None,
        }

        # LLM Client - يُنشأ عند الحاجة
        self._llm_client: Optional[LLMClient] = None

        logger.info(f"Agent initialized: {self.agent_id} ({self.name})")

    @property
    def llm(self) -> LLMClient:
        if self._llm_client is None:
            from army81.config.settings import PROVIDERS
            provider_config = PROVIDERS.get(self.provider)
            api_key = ""
            base_url = "http://localhost:11434/v1"
            if provider_config:
                import os
                api_key = os.getenv(provider_config.api_key_env, "") if provider_config.api_key_env else ""
                base_url = provider_config.base_url
            self._llm_client = LLMClient(self.provider, self.model, api_key, base_url)
        return self._llm_client

    def run(self, task: str, context: Dict = None) -> Dict:
        """تنفيذ مهمة - النقطة الرئيسية لاستخدام الوكيل"""
        start_time = time.time()
        context = context or {}

        try:
            # بناء الرسائل
            messages = self._build_messages(task, context)

            # استدعاء النموذج
            response = self.llm.chat(
                messages=messages,
                tools=self._get_tools_schema() if self.tools else None
            )

            # معالجة استدعاءات الأدوات
            if response.get("tool_calls"):
                response = self._handle_tool_calls(response, messages)

            # تحديث الذاكرة
            self._update_memory(task, response["content"])

            # تحديث الإحصائيات
            elapsed = time.time() - start_time
            self.stats["tasks_completed"] += 1
            self.stats["last_active"] = datetime.now().isoformat()
            usage = response.get("usage", {})
            self.stats["total_tokens_used"] += usage.get("total_tokens", 0)

            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "result": response["content"],
                "model_used": response.get("model", self.model),
                "elapsed_seconds": round(elapsed, 2),
                "tokens_used": usage.get("total_tokens", 0),
                "status": "success",
            }

        except Exception as e:
            self.stats["tasks_failed"] += 1
            logger.error(f"Agent {self.agent_id} failed: {e}")
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "result": f"ERROR: {str(e)}",
                "status": "error",
                "elapsed_seconds": round(time.time() - start_time, 2),
            }

    def _build_messages(self, task: str, context: Dict) -> List[Dict]:
        """بناء سلسلة الرسائل مع System Prompt والسياق"""
        messages = [{"role": "system", "content": self._build_system_prompt(context)}]

        # إضافة الذاكرة القصيرة
        for mem in self.short_term_memory[-10:]:
            messages.append({"role": mem.role, "content": mem.content})

        # إضافة المهمة
        task_content = task
        if context:
            task_content += f"\n\n### سياق إضافي:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        messages.append({"role": "user", "content": task_content})

        return messages

    def _build_system_prompt(self, context: Dict) -> str:
        """بناء System Prompt مع المهارات المتاحة"""
        prompt = self.system_prompt

        if self.skills:
            prompt += "\n\n## المهارات المتاحة:\n"
            for skill in self.skills:
                prompt += f"- **{skill.name}**: {skill.description}\n"

        if self.tools:
            prompt += "\n\n## الأدوات المتاحة:\n"
            for tool in self.tools:
                prompt += f"- **{tool.name}**: {tool.description}\n"

        return prompt

    def _get_tools_schema(self) -> List[Dict]:
        """تحويل الأدوات إلى صيغة OpenAI function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in self.tools
        ]

    def _handle_tool_calls(self, response: Dict, messages: List[Dict]) -> Dict:
        """معالجة استدعاءات الأدوات"""
        tool_results = []
        for call in response.get("tool_calls", []):
            func_name = call.get("function", {}).get("name", "")
            func_args = json.loads(call.get("function", {}).get("arguments", "{}"))

            # البحث عن الأداة
            tool = next((t for t in self.tools if t.name == func_name), None)
            if tool and tool.handler:
                try:
                    result = tool.handler(**func_args)
                    tool_results.append({"tool": func_name, "result": str(result)})
                except Exception as e:
                    tool_results.append({"tool": func_name, "result": f"ERROR: {e}"})

        # إرسال النتائج للنموذج
        if tool_results:
            messages.append({"role": "assistant", "content": response["content"] or ""})
            messages.append({
                "role": "user",
                "content": f"نتائج الأدوات:\n{json.dumps(tool_results, ensure_ascii=False)}\n\nأكمل المهمة بناءً على هذه النتائج."
            })
            return self.llm.chat(messages=messages)

        return response

    def _update_memory(self, task: str, response: str):
        """تحديث الذاكرة القصيرة"""
        self.short_term_memory.append(
            AgentMessage(role="user", content=task, agent_id="human")
        )
        self.short_term_memory.append(
            AgentMessage(role="assistant", content=response, agent_id=self.agent_id)
        )
        # الاحتفاظ بآخر 50 رسالة فقط
        if len(self.short_term_memory) > 50:
            self.short_term_memory = self.short_term_memory[-50:]

    def learn_skill(self, task: str, result: str, success: bool):
        """تعلم مهارة جديدة من تجربة (مستوحى من Hermes Agent)"""
        if success:
            skill_name = f"skill_{hashlib.md5(task.encode()).hexdigest()[:8]}"
            skill = AgentSkill(
                name=skill_name,
                description=f"مهارة مكتسبة من مهمة: {task[:100]}",
                content=f"## المهمة:\n{task}\n\n## الحل الناجح:\n{result}",
            )
            self.skills.append(skill)
            logger.info(f"Agent {self.agent_id} learned new skill: {skill_name}")

    def to_dict(self) -> Dict:
        """تصدير الوكيل كقاموس"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "name_ar": self.name_ar,
            "category": self.category,
            "description": self.description,
            "model": self.model,
            "provider": self.provider,
            "stats": self.stats,
            "skills_count": len(self.skills),
            "tools_count": len(self.tools),
        }

    def __repr__(self):
        return f"<Agent {self.agent_id}: {self.name} [{self.model}@{self.provider}]>"
