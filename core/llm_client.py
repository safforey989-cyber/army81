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
    # ══════════════════════════════
    # Google Gemini (عبر OpenRouter)
    # ══════════════════════════════
    "gemini-flash":    {"provider": "openrouter", "model": "google/gemini-2.0-flash-001",       "tier": "fast",    "cost": 0.1,  "strengths": ["speed", "general", "arabic"]},
    "gemini-pro":      {"provider": "openrouter", "model": "google/gemini-2.5-pro",             "tier": "smart",   "cost": 1.25, "strengths": ["reasoning", "long_context", "analysis"]},
    "gemini-think":    {"provider": "openrouter", "model": "google/gemini-2.5-flash",           "tier": "reason",  "cost": 0.5,  "strengths": ["deep_thinking", "math", "science"]},
    "gemini-2-flash":  {"provider": "openrouter", "model": "google/gemini-2.5-flash-preview",   "tier": "fast",    "cost": 0.15, "strengths": ["speed", "multimodal"]},

    # ══════════════════════════════
    # Anthropic Claude (عبر OpenRouter)
    # ══════════════════════════════
    "claude-fast":     {"provider": "openrouter", "model": "anthropic/claude-haiku-4-5",        "tier": "fast",    "cost": 0.25, "strengths": ["speed", "instructions", "arabic"]},
    "claude-smart":    {"provider": "openrouter", "model": "anthropic/claude-sonnet-4-6",       "tier": "smart",   "cost": 3.0,  "strengths": ["reasoning", "coding", "analysis"]},
    "claude-opus":     {"provider": "openrouter", "model": "anthropic/claude-opus-4-6",         "tier": "premium", "cost": 15.0, "strengths": ["complex_reasoning", "creativity", "nuance"]},

    # ══════════════════════════════
    # OpenAI GPT (عبر OpenRouter)
    # ══════════════════════════════
    "gpt4o":           {"provider": "openrouter", "model": "openai/gpt-4o",                     "tier": "smart",   "cost": 2.5,  "strengths": ["reasoning", "coding", "vision"]},
    "gpt4o-mini":      {"provider": "openrouter", "model": "openai/gpt-4o-mini",                "tier": "fast",    "cost": 0.15, "strengths": ["speed", "general", "cost_effective"]},
    "o3-mini":         {"provider": "openrouter", "model": "openai/o3-mini",                    "tier": "reason",  "cost": 1.1,  "strengths": ["math", "science", "deep_reasoning"]},

    # ══════════════════════════════
    # Meta Llama (مجاني عبر OpenRouter)
    # ══════════════════════════════
    "llama-free":      {"provider": "openrouter", "model": "meta-llama/llama-3.2-3b-instruct:free", "tier": "free", "cost": 0.0, "strengths": ["general", "free"]},
    "llama-70b":       {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct", "tier": "smart",   "cost": 0.3,  "strengths": ["reasoning", "general", "cheap"]},

    # ══════════════════════════════
    # DeepSeek (الأرخص + الأذكى)
    # ══════════════════════════════
    "deepseek-chat":   {"provider": "openrouter", "model": "deepseek/deepseek-chat",            "tier": "smart",   "cost": 0.14, "strengths": ["reasoning", "coding", "cheap"]},
    "deepseek-r1":     {"provider": "openrouter", "model": "deepseek/deepseek-r1",              "tier": "reason",  "cost": 0.55, "strengths": ["deep_reasoning", "math", "science"]},
    "deepseek-r1-free":{"provider": "openrouter", "model": "deepseek/deepseek-r1:free",         "tier": "free",    "cost": 0.0,  "strengths": ["reasoning", "free"]},

    # ══════════════════════════════
    # Mistral (سريع + رخيص)
    # ══════════════════════════════
    "mistral-small":   {"provider": "openrouter", "model": "mistralai/mistral-small-3.1-24b-instruct:free", "tier": "free", "cost": 0.0, "strengths": ["speed", "multilingual", "free"]},
    "mistral-large":   {"provider": "openrouter", "model": "mistralai/mistral-large-2411",      "tier": "smart",   "cost": 2.0,  "strengths": ["reasoning", "multilingual", "coding"]},
    "codestral":       {"provider": "openrouter", "model": "mistralai/codestral-2501",          "tier": "smart",   "cost": 0.3,  "strengths": ["coding", "code_completion", "debugging"]},

    # ══════════════════════════════
    # Qwen (ممتاز للعربية والكود)
    # ══════════════════════════════
    "qwen-72b":        {"provider": "openrouter", "model": "qwen/qwen-2.5-72b-instruct",       "tier": "smart",   "cost": 0.35, "strengths": ["arabic", "coding", "multilingual"]},
    "qwen-coder":      {"provider": "openrouter", "model": "qwen/qwen-2.5-coder-32b-instruct:free", "tier": "free", "cost": 0.0, "strengths": ["coding", "debugging", "free"]},
    "qwen-free":       {"provider": "openrouter", "model": "qwen/qwen-2.5-7b-instruct:free",   "tier": "free",    "cost": 0.0,  "strengths": ["general", "free", "arabic"]},

    # ══════════════════════════════
    # xAI Grok (أحدث + متخصص)
    # ══════════════════════════════
    "grok-3":          {"provider": "openrouter", "model": "x-ai/grok-3-beta",                 "tier": "premium", "cost": 3.0,  "strengths": ["reasoning", "current_events", "analysis"]},
    "grok-mini":       {"provider": "openrouter", "model": "x-ai/grok-3-mini-beta",            "tier": "fast",    "cost": 0.3,  "strengths": ["speed", "reasoning", "current_events"]},

    # ══════════════════════════════
    # Perplexity (بحث + إجابة)
    # ══════════════════════════════
    "perplexity":      {"provider": "perplexity", "model": "sonar-pro",                        "tier": "search",  "cost": 3.0,  "strengths": ["web_search", "current_info", "citations"]},
    "perplexity-fast": {"provider": "perplexity", "model": "sonar",                            "tier": "search",  "cost": 1.0,  "strengths": ["web_search", "fast", "current_info"]},

    # ══════════════════════════════
    # Ollama محلي (fallback مجاني)
    # ══════════════════════════════
    "local-small":     {"provider": "ollama", "model": "llama3.2:3b",      "tier": "local", "cost": 0.0, "strengths": ["offline", "free", "private"]},
    "local-medium":    {"provider": "ollama", "model": "qwen2.5:7b",       "tier": "local", "cost": 0.0, "strengths": ["offline", "free", "arabic"]},
    "local-coder":     {"provider": "ollama", "model": "qwen2.5-coder:7b", "tier": "local", "cost": 0.0, "strengths": ["coding", "offline", "free"]},
}

# خريطة التخصصات → أفضل نماذج (بالترتيب)
TASK_MODEL_MAP = {
    "coding":         ["qwen-coder", "codestral", "claude-smart", "deepseek-chat"],
    "medical":        ["deepseek-r1", "gemini-think", "o3-mini", "claude-smart"],
    "legal":          ["claude-smart", "gpt4o", "mistral-large", "deepseek-r1"],
    "financial":      ["deepseek-chat", "gpt4o", "mistral-large", "gemini-pro"],
    "arabic":         ["qwen-72b", "gemini-flash", "claude-fast", "qwen-free"],
    "science":        ["deepseek-r1", "o3-mini", "gemini-think", "claude-smart"],
    "strategy":       ["claude-smart", "gpt4o", "gemini-pro", "grok-3"],
    "current_events": ["perplexity", "grok-3", "perplexity-fast"],
    "creative":       ["claude-opus", "gpt4o", "gemini-pro"],
    "fast_simple":    ["gemini-flash", "gpt4o-mini", "qwen-free", "llama-free"],
    "math":           ["o3-mini", "deepseek-r1", "gemini-think"],
    "security":       ["deepseek-r1", "claude-smart", "gemini-pro"],
    "behavior":       ["claude-smart", "gemini-pro", "deepseek-r1"],
    "leadership":     ["claude-opus", "gpt4o", "gemini-pro"],
    "research":       ["gemini-pro", "deepseek-r1", "perplexity"],
}

# Legacy mapping (backwards compatibility)
TASK_TO_MODEL = {
    "simple":    "gemini-flash",
    "research":  "deepseek-r1",
    "code":      "qwen-coder",
    "critical":  "claude-smart",
    "fast":      "gemini-flash",
    "analysis":  "deepseek-chat",
    "strategy":  "claude-smart",
    "medical":   "deepseek-r1",
    "financial": "deepseek-chat",
    "search":    "perplexity",
    "local":     "local-medium",
    "free":      "llama-free",
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
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    # سلسلة الـ fallback الذكية — إذا فشل نموذج ينتقل للتالي
    FALLBACK_CHAIN = [
        "gemini-flash",     # أسرع وأرخص
        "deepseek-chat",    # ذكي ورخيص
        "qwen-free",        # مجاني
        "llama-free",       # مجاني
        "deepseek-r1-free", # مجاني مع تفكير عميق
    ]

    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 4096, _retry: int = 0) -> Dict:
        """إرسال رسائل والحصول على رد — مع retry و fallback تلقائي"""
        import time

        # حد أقصى 3 محاولات
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if self.provider == "openrouter":
                    result = self._chat_openrouter(messages, temperature, max_tokens)
                elif self.provider == "perplexity":
                    result = self._chat_perplexity(messages, temperature, max_tokens)
                elif self.provider == "gemini":
                    result = self._chat_gemini(messages, temperature, max_tokens)
                elif self.provider == "anthropic":
                    result = self._chat_anthropic(messages, temperature, max_tokens)
                elif self.provider == "ollama":
                    result = self._chat_ollama(messages, temperature, max_tokens)
                else:
                    result = {"content": f"ERROR: Unknown provider {self.provider}", "tokens": 0}

                # نجاح — أعد النتيجة
                if not result.get("content", "").startswith("ERROR"):
                    return result

                # فشل — log وأعد المحاولة
                logger.warning(f"[{self.alias}] Attempt {attempt+1}/{max_retries} failed: {result['content'][:100]}")

            except Exception as e:
                logger.warning(f"[{self.alias}] Attempt {attempt+1}/{max_retries} exception: {e}")
                result = {"content": f"ERROR: {e}", "model": self.model, "tokens": 0}

            # انتظر قبل إعادة المحاولة (exponential backoff)
            if attempt < max_retries - 1:
                wait = min(4 * (2 ** attempt), 30)
                time.sleep(wait)

        # كل المحاولات فشلت — جرّب سلسلة الـ fallback
        if _retry == 0:  # فقط في المحاولة الأولى
            for fallback_alias in self.FALLBACK_CHAIN:
                if fallback_alias == self.alias:
                    continue  # لا تعيد نفس النموذج
                try:
                    logger.info(f"🔄 Fallback: {self.alias} → {fallback_alias}")
                    fb = LLMClient(fallback_alias)
                    fb_result = fb.chat(messages, temperature, max_tokens, _retry=1)
                    if not fb_result.get("content", "").startswith("ERROR"):
                        fb_result["fallback_from"] = self.alias
                        fb_result["fallback_to"] = fallback_alias
                        return fb_result
                except Exception:
                    continue

        logger.error(f"❌ All attempts and fallbacks failed for [{self.alias}]")
        return {"content": f"ERROR: All {max_retries} attempts failed for {self.alias}", "model": self.model, "tokens": 0}

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

    def _chat_perplexity(self, messages, temperature, max_tokens):
        """Perplexity Sonar — بحث + إجابة مع استشهادات"""
        if not self.perplexity_key:
            return {"content": "ERROR: PERPLEXITY_API_KEY not set", "tokens": 0}
        headers = {"Authorization": f"Bearer {self.perplexity_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        try:
            resp = req_lib.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            if citations:
                content += "\n\nالمصادر:\n" + "\n".join(f"• {c}" for c in citations[:5] if isinstance(c, str))
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return {"content": content, "model": self.model, "tokens": tokens}
        except Exception as e:
            logger.error(f"Perplexity error: {e}")
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
