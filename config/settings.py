"""
Army81 - Configuration Settings
النظام البيئي المتكامل لـ 81 وكيل ذكاء اصطناعي
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ============================================================
# Model Providers - مزودو النماذج
# ============================================================

@dataclass
class ModelProvider:
    name: str
    api_key_env: str
    base_url: str
    models: List[str]
    tier: str  # "free", "freemium", "paid"
    max_rpm: int = 60  # requests per minute

PROVIDERS = {
    "ollama": ModelProvider(
        name="Ollama Local",
        api_key_env="",
        base_url="http://localhost:11434/v1",
        models=[
            "qwen3:8b", "qwen2.5:14b", "qwen2.5-coder:14b",
            "deepseek-coder:6.7b", "llama3:8b", "qwen3-next:80b"
        ],
        tier="free",
        max_rpm=999
    ),
    "ollama_cloud": ModelProvider(
        name="Ollama Cloud Models",
        api_key_env="",
        base_url="http://localhost:11434/v1",
        models=[
            "glm-5:cloud", "deepseek-v3.1:671b-cloud",
            "kimi-k2.5:cloud", "minimax-m2.5:cloud",
            "gpt-oss:120b-cloud", "qwen3-coder:480b-cloud"
        ],
        tier="free",
        max_rpm=30
    ),
    "openai": ModelProvider(
        name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        models=["gpt-4o", "gpt-4o-mini", "gpt-5"],
        tier="paid",
        max_rpm=60
    ),
    "anthropic": ModelProvider(
        name="Anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com",
        models=["claude-3-opus-20240229", "claude-sonnet-4-20250514"],
        tier="paid",
        max_rpm=60
    ),
    "gemini": ModelProvider(
        name="Google Gemini",
        api_key_env="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        models=["gemini-2.5-flash", "gemini-2.5-pro"],
        tier="freemium",
        max_rpm=60
    ),
    "openrouter": ModelProvider(
        name="OpenRouter",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        models=[
            "nvidia/nemotron-3-super-120b-a12b:free",
            "deepseek/deepseek-r1:free",
            "qwen/qwen-3-235b:free",
            "meta-llama/llama-4-maverick:free"
        ],
        tier="free",
        max_rpm=20
    ),
    "groq": ModelProvider(
        name="Groq",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        models=["llama-4-scout-17b", "qwen-qwq-32b", "deepseek-r1-distill-llama-70b"],
        tier="free",
        max_rpm=30
    ),
    "cohere": ModelProvider(
        name="Cohere",
        api_key_env="COHERE_API_KEY",
        base_url="https://api.cohere.ai/v2",
        models=["command-r-plus", "command-r"],
        tier="freemium",
        max_rpm=20
    ),
    "perplexity": ModelProvider(
        name="Perplexity",
        api_key_env="SONAR_API_KEY",
        base_url="https://api.perplexity.ai",
        models=["sonar-pro", "sonar"],
        tier="freemium",
        max_rpm=20
    ),
}

# ============================================================
# Smart Router - التوجيه الذكي للنماذج
# ============================================================

@dataclass
class ModelRoute:
    """تعريف مسار توجيه للمهام"""
    task_type: str
    primary_model: str
    primary_provider: str
    fallback_model: str
    fallback_provider: str
    max_tokens: int = 4096
    temperature: float = 0.7

ROUTING_TABLE = {
    # المهام البسيطة → محلي (مجاني 100%)
    "classification": ModelRoute("classification", "qwen3:8b", "ollama", "qwen2.5:14b", "ollama", 512, 0.1),
    "extraction": ModelRoute("extraction", "qwen3:8b", "ollama", "qwen2.5:14b", "ollama", 2048, 0.1),
    "summarization": ModelRoute("summarization", "qwen2.5:14b", "ollama", "qwen3:8b", "ollama", 2048, 0.3),
    "translation": ModelRoute("translation", "qwen3:8b", "ollama", "qwen2.5:14b", "ollama", 4096, 0.3),

    # المهام المتوسطة → APIs مجانية
    "coding": ModelRoute("coding", "qwen2.5-coder:14b", "ollama", "deepseek-r1-distill-llama-70b", "groq", 8192, 0.2),
    "analysis": ModelRoute("analysis", "deepseek-v3.1:671b-cloud", "ollama_cloud", "qwen-qwq-32b", "groq", 8192, 0.5),
    "research": ModelRoute("research", "sonar-pro", "perplexity", "glm-5:cloud", "ollama_cloud", 8192, 0.5),
    "writing": ModelRoute("writing", "qwen3:8b", "ollama", "kimi-k2.5:cloud", "ollama_cloud", 8192, 0.7),

    # المهام المعقدة → APIs مدفوعة (فقط عند الضرورة)
    "strategic_planning": ModelRoute("strategic_planning", "glm-5:cloud", "ollama_cloud", "claude-sonnet-4-20250514", "anthropic", 16384, 0.7),
    "complex_reasoning": ModelRoute("complex_reasoning", "deepseek-v3.1:671b-cloud", "ollama_cloud", "gpt-4o", "openai", 16384, 0.5),
    "creative": ModelRoute("creative", "kimi-k2.5:cloud", "ollama_cloud", "claude-sonnet-4-20250514", "anthropic", 8192, 0.9),
    "critical_decision": ModelRoute("critical_decision", "glm-5:cloud", "ollama_cloud", "gpt-5", "openai", 16384, 0.3),
}

# ============================================================
# Agent Categories - فئات الوكلاء
# ============================================================

AGENT_CATEGORIES = {
    "cat1_leadership": {
        "name": "الإدارة والقيادة الاستراتيجية",
        "name_en": "Leadership & Strategy",
        "count": 12,
        "default_model": "glm-5:cloud",
        "default_provider": "ollama_cloud",
    },
    "cat2_engineering": {
        "name": "التطوير والهندسة",
        "name_en": "Engineering & Development",
        "count": 15,
        "default_model": "qwen2.5-coder:14b",
        "default_provider": "ollama",
    },
    "cat3_research": {
        "name": "البحث والتحليل",
        "name_en": "Research & Analysis",
        "count": 12,
        "default_model": "sonar-pro",
        "default_provider": "perplexity",
    },
    "cat4_creative": {
        "name": "المحتوى والإبداع",
        "name_en": "Creative & Content",
        "count": 10,
        "default_model": "qwen3:8b",
        "default_provider": "ollama",
    },
    "cat5_operations": {
        "name": "العمليات والأتمتة",
        "name_en": "Operations & Automation",
        "count": 12,
        "default_model": "qwen3:8b",
        "default_provider": "ollama",
    },
    "cat6_security": {
        "name": "الأمن والجودة",
        "name_en": "Security & Quality",
        "count": 10,
        "default_model": "qwen2.5:14b",
        "default_provider": "ollama",
    },
    "cat7_evolution": {
        "name": "التحسين الذاتي والتضاعف",
        "name_en": "Self-Improvement & Evolution",
        "count": 10,
        "default_model": "deepseek-v3.1:671b-cloud",
        "default_provider": "ollama_cloud",
    },
}

# ============================================================
# Memory Configuration - إعدادات الذاكرة
# ============================================================

MEMORY_CONFIG = {
    "short_term": {
        "type": "in_memory",
        "max_items": 100,
        "ttl_seconds": 3600,  # ساعة واحدة
    },
    "working": {
        "type": "sqlite",
        "db_path": "memory/working_memory.db",
        "max_items": 1000,
        "ttl_seconds": 86400,  # يوم واحد
    },
    "long_term": {
        "type": "sqlite_fts",
        "db_path": "memory/long_term_memory.db",
        "embedding_model": "nomic-embed-text",
    },
    "episodic": {
        "type": "jsonl",
        "log_path": "memory/episodes/",
        "max_episodes": 10000,
    },
    "skills": {
        "type": "markdown_files",
        "skills_path": "skills/",
    },
}

# ============================================================
# Update Schedule - جدول التحديثات
# ============================================================

UPDATE_CONFIG = {
    "daily_update_time": "02:00",  # 2 صباحاً
    "sources": [
        "github_trending",
        "huggingface_new_models",
        "arxiv_ai_papers",
        "reddit_localllama",
        "tech_news_feeds",
    ],
    "auto_apply": False,  # يحتاج موافقة بشرية
    "log_path": "updates/",
}
