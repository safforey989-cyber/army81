"""
Army81 - LLM Client
عميل موحّد — OpenRouter كمزود رئيسي + fallback محلي
"""
import os
import logging
from typing import List, Dict, Optional
import requests as req_lib

logger = logging.getLogger("army81.llm")

# ======================================================
# النماذج الحقيقية — OpenRouter يدعم 200+ نموذج
# ======================================================
REAL_MODELS = {
    # Gemini عبر OpenRouter (verified model IDs 2026-03-18)
    "gemini-flash":  {"provider": "openrouter", "model": "google/gemini-2.0-flash-001",    "tier": "free",  "rpm": 60},
    "gemini-fast":   {"provider": "openrouter", "model": "google/gemini-2.5-flash-lite",   "tier": "free",  "rpm": 60},
    "gemini-pro":    {"provider": "openrouter", "model": "google/gemini-2.5-pro",           "tier": "paid",  "rpm": 20},
    "gemini-think":  {"provider": "openrouter", "model": "google/gemini-2.5-flash",         "tier": "free",  "rpm": 10},

    # Claude عبر OpenRouter (verified model IDs 2026-03-18)
    "claude-fast":   {"provider": "openrouter", "model": "anthropic/claude-haiku-4.5",     "tier": "paid",  "rpm": 60},
    "claude-smart":  {"provider": "openrouter", "model": "anthropic/claude-sonnet-4.6",    "tier": "paid",  "rpm": 50},

    # نماذج مجانية عبر OpenRouter
    "llama-free":    {"provider": "openrouter", "model": "meta-llama/llama-3.2-3b-instruct:free", "tier": "free", "rpm": 20},
    "qwen-free":     {"provider": "openrouter", "model": "qwen/qwen-2.5-7b-instruct:free",       "tier": "free", "rpm": 20},

    # Ollama — محلي مجاني (fallback)
    "local-small":   {"provider": "ollama", "model": "llama3.2:3b",     "tier": "free", "rpm": 999},
    "local-medium":  {"provider": "ollama", "model": "qwen2.5:7b",      "tier": "free", "rpm": 999},
    "local-coder":   {"provider": "ollama", "model": "qwen2.5-coder:7b","tier": "free", "rpm": 999},
}

TASK_TO_MODEL = {
    "simple":   "gemini-flash",
    "research": "gemini-pro",
    "code":     "gemini-flash",
    "critical": "claude-smart",
    "fast":     "gemini-flash",
    "local":    "local-medium",
    "free":     "llama-free",
}

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_REFERER = "https://github.com/safforey989-cyber/army81"


class LLMClient:
    """عميل موحّد — OpenRouter أولاً، Ollama كـ fallback"""

    def __init__(self, model_alias: str = "gemini-flash"):
        if model_alias not in REAL_MODELS:
            logger.warning(f"Unknown alias '{model_alias}', using gemini-flash")
            model_alias = "gemini-flash"

        config = REAL_MODELS[model_alias]
        self.alias = model_alias
        self.provider = config["provider"]
        self.model = config["model"]
        self.tier = config["tier"]

        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.gemini_key = os.getenv("GOOGLE_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 4096) -> Dict:
        """إرسال رسائل والحصول على رد"""
        try:
            if self.provider == "openrouter":
                result = self._chat_openrouter(messages, temperature, max_tokens)
            elif self.provider == "gemini":
                result = self._chat_gemini(messages, temperature, max_tokens)
            elif self.provider == "anthropic":
                result = self._chat_anthropic(messages, temperature, max_tokens)
            elif self.provider == "ollama":
                result = self._chat_ollama(messages, temperature, max_tokens)
            else:
                result = {"content": f"ERROR: Unknown provider {self.provider}", "tokens": 0}

            # fallback لـ ollama إذا فشل OpenRouter
            if result.get("content", "").startswith("ERROR:") and self.provider == "openrouter":
                logger.warning(f"OpenRouter failed, trying ollama fallback")
                fallback = LLMClient("local-medium")
                return fallback.chat(messages, temperature, max_tokens)

            return result

        except Exception as e:
            logger.error(f"LLM error [{self.alias}]: {e}")
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_openrouter(self, messages, temperature, max_tokens):
        """OpenRouter — يدعم 200+ نموذج بمفتاح واحد"""
        if not self.openrouter_key:
            return {"content": "ERROR: OPENROUTER_API_KEY not set in .env", "tokens": 0}

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": "Army81 Multi-Agent System",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = req_lib.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"].get("content", "")
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return {"content": content, "model": self.model, "tokens": tokens}
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_gemini(self, messages, temperature, max_tokens):
        if not self.gemini_key:
            return {"content": "ERROR: GOOGLE_API_KEY not set", "tokens": 0}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        contents = []
        system_text = ""
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            elif m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})
        payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        try:
            resp = req_lib.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
            return {"content": text, "model": self.model, "tokens": tokens}
        except Exception as e:
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_anthropic(self, messages, temperature, max_tokens):
        if not self.anthropic_key:
            return {"content": "ERROR: ANTHROPIC_API_KEY not set", "tokens": 0}
        headers = {"Content-Type": "application/json", "x-api-key": self.anthropic_key, "anthropic-version": "2023-06-01"}
        system_msg = ""
        filtered = []
        for m in messages:
            if m["role"] == "system": system_msg = m["content"]
            else: filtered.append(m)
        payload = {"model": self.model, "max_tokens": max_tokens, "temperature": temperature, "messages": filtered}
        if system_msg: payload["system"] = system_msg
        try:
            resp = req_lib.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"]
            tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
            return {"content": text, "model": self.model, "tokens": tokens}
        except Exception as e:
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    def _chat_ollama(self, messages, temperature, max_tokens):
        url = f"{self.ollama_url}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": False,
                   "options": {"temperature": temperature, "num_predict": max_tokens}}
        try:
            resp = req_lib.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            text = resp.json()["message"]["content"]
            return {"content": text, "model": self.model, "tokens": 0}
        except Exception as e:
            return {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

    @staticmethod
    def for_task(task_type: str) -> "LLMClient":
        alias = TASK_TO_MODEL.get(task_type, "gemini-flash")
        return LLMClient(alias)

    def __repr__(self):
        return f"<LLMClient {self.alias} [{self.model}] {self.provider}>"
