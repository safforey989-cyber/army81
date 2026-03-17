"""
Army81 - LLM Client
عميل موحّد للتواصل مع النماذج الحقيقية فقط
"""
import os
import logging
from typing import List, Dict, Optional
import requests

logger = logging.getLogger("army81.llm")

# ======================================================
# النماذج المتاحة الحقيقية فقط
# ======================================================
REAL_MODELS = {
    # Gemini عبر OpenRouter (الافتراضي — يعمل مع OPENROUTER_API_KEY)
    "gemini-flash":   {"provider": "openrouter", "model": "google/gemini-2.0-flash-001",    "tier": "free",  "rpm": 15},
    "gemini-fast":    {"provider": "openrouter", "model": "google/gemini-flash-1.5-8b",     "tier": "free",  "rpm": 15},
    "gemini-pro":     {"provider": "openrouter", "model": "google/gemini-pro-1.5",          "tier": "paid",  "rpm": 2},
    "gemini-think":   {"provider": "openrouter", "model": "google/gemini-2.0-flash-thinking-exp:free", "tier": "free", "rpm": 10},

    # Claude عبر OpenRouter
    "claude-fast":    {"provider": "openrouter", "model": "anthropic/claude-haiku-4-5",  "tier": "paid", "rpm": 60},
    "claude-smart":   {"provider": "openrouter", "model": "anthropic/claude-sonnet-4-5", "tier": "paid", "rpm": 50},

    # Gemini مباشر (يحتاج GOOGLE_API_KEY مع billing)
    "gemini-flash-direct": {"provider": "gemini", "model": "gemini-2.0-flash",  "tier": "paid", "rpm": 15},
    "gemini-pro-direct":   {"provider": "gemini", "model": "gemini-1.5-pro",    "tier": "paid", "rpm": 2},

    # Anthropic مباشر (يحتاج ANTHROPIC_API_KEY)
    "claude-fast-direct":  {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "tier": "paid", "rpm": 60},
    "claude-smart-direct": {"provider": "anthropic", "model": "claude-sonnet-4-6",         "tier": "paid", "rpm": 50},

    # Ollama — محلي مجاني
    "local-small":    {"provider": "ollama", "model": "llama3.2:3b",     "tier": "free", "rpm": 999},
    "local-medium":   {"provider": "ollama", "model": "qwen2.5:7b",      "tier": "free", "rpm": 999},
    "local-coder":    {"provider": "ollama", "model": "qwen2.5-coder:7b","tier": "free", "rpm": 999},
}

# توجيه ذكي: مهام بسيطة → مجاني، مهام حرجة → مدفوع
TASK_TO_MODEL = {
    "simple":   "gemini-flash",   # استفسارات بسيطة
    "research": "gemini-pro",     # بحث معمّق
    "code":     "local-coder",    # كتابة كود
    "critical": "claude-smart",   # قرارات حرجة
    "fast":     "gemini-flash",   # سرعة مهمة
    "local":    "local-medium",   # خصوصية تامة
}


class LLMClient:
    """عميل موحّد - يختار النموذج الصحيح تلقائياً"""

    def __init__(self, model_alias: str = "gemini-flash"):
        if model_alias not in REAL_MODELS:
            logger.warning(f"Unknown model alias '{model_alias}', using gemini-flash")
            model_alias = "gemini-flash"

        config = REAL_MODELS[model_alias]
        self.alias = model_alias
        self.provider = config["provider"]
        self.model = config["model"]
        self.tier = config["tier"]

        # مفاتيح API
        self.gemini_key = os.getenv("GOOGLE_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 4096) -> Dict:
        """إرسال رسائل للنموذج والحصول على رد"""

        if self.provider == "openrouter":
            return self._chat_openrouter(messages, temperature, max_tokens)
        elif self.provider == "gemini":
            return self._chat_gemini(messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, temperature, max_tokens)
        elif self.provider == "ollama":
            return self._chat_ollama(messages, temperature, max_tokens)
        else:
            return {"content": "ERROR: Unknown provider", "model": self.model, "tokens": 0}

    def _chat_openrouter(self, messages, temperature, max_tokens):
        """OpenRouter — بوابة موحّدة لجميع النماذج"""
        if not self.openrouter_key:
            return {"content": "ERROR: OPENROUTER_API_KEY not set", "model": self.model, "tokens": 0}

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://army81.ai",
            "X-Title": "Army81",
        }

        # فصل system message
        system_msg = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                filtered.append(m)

        # أضف system كأول user message إذا لم يدعمها النموذج
        or_messages = []
        if system_msg:
            or_messages.append({"role": "system", "content": system_msg})
        or_messages.extend(filtered)

        payload = {
            "model": self.model,
            "messages": or_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return {"content": text, "model": self.model, "tokens": tokens}
        except Exception as e:
            logger.error(f"OpenRouter error [{self.model}]: {e}")
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_gemini(self, messages, temperature, max_tokens):
        if not self.gemini_key:
            return {"content": "ERROR: GOOGLE_API_KEY not set", "model": self.model, "tokens": 0}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"

        # تحويل الرسائل لصيغة Gemini
        contents = []
        system_text = ""
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            elif m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
            return {"content": text, "model": self.model, "tokens": tokens}
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_anthropic(self, messages, temperature, max_tokens):
        if not self.anthropic_key:
            return {"content": "ERROR: ANTHROPIC_API_KEY not set", "model": self.model, "tokens": 0}

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.anthropic_key,
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

        try:
            resp = requests.post("https://api.anthropic.com/v1/messages",
                               headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"]
            tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
            return {"content": text, "model": self.model, "tokens": tokens}
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_ollama(self, messages, temperature, max_tokens):
        url = f"{self.ollama_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            text = data["message"]["content"]
            return {"content": text, "model": self.model, "tokens": 0}
        except Exception as e:
            logger.error(f"Ollama error [{self.model}]: {e}")
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    @staticmethod
    def for_task(task_type: str) -> "LLMClient":
        """اختر النموذج المناسب للمهمة تلقائياً"""
        alias = TASK_TO_MODEL.get(task_type, "gemini-flash")
        return LLMClient(alias)

    def __repr__(self):
        return f"<LLMClient {self.alias} [{self.model}] {self.tier}>"
