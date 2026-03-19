"""
Army81 — Comprehensive System Tests
تشغيل: python -m pytest tests/test_system.py -v
"""
import sys
import os
import json
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCoreImports:
    """تحقق أن كل الأنظمة الأساسية تستورد بنجاح"""

    def test_base_agent(self):
        from core.base_agent import BaseAgent
        assert BaseAgent is not None

    def test_llm_client(self):
        from core.llm_client import LLMClient
        assert LLMClient is not None

    def test_neural_network(self):
        from core.neural_network import NeuralNetwork
        assert NeuralNetwork is not None

    def test_consciousness(self):
        from core.consciousness import ConsciousnessNode
        assert ConsciousnessNode is not None

    def test_evolution(self):
        from core.exponential_evolution import ExponentialEvolution
        assert ExponentialEvolution is not None

    def test_smart_router(self):
        from router.smart_router import SmartRouter
        assert SmartRouter is not None

    def test_hierarchical_memory(self):
        from memory.hierarchical_memory import HierarchicalMemory
        assert HierarchicalMemory is not None

    def test_collective_memory(self):
        from memory.collective_memory import CollectiveMemory
        assert CollectiveMemory is not None

    def test_voice_interface(self):
        from integrations.voice_interface import VoiceCommander
        assert VoiceCommander is not None

    def test_multi_model_router(self):
        from core.multi_model_router import MultiModelRouter
        assert MultiModelRouter is not None


class TestMemory:
    """تحقق من عمل الذاكرة"""

    def test_episodic_db_exists(self):
        db = Path("workspace/episodic_memory.db")
        assert db.exists(), "Episodic database missing"

    def test_episodic_has_data(self):
        conn = sqlite3.connect("workspace/episodic_memory.db")
        count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        conn.close()
        assert count > 0, f"Episodic memory empty (got {count})"

    def test_agent_memories_exist(self):
        mdir = Path("workspace/agent_memories")
        assert mdir.exists(), "Agent memories directory missing"
        files = list(mdir.glob("*.json"))
        assert len(files) >= 80, f"Expected 80+ agent memories, got {len(files)}"

    def test_shared_brain(self):
        brain = Path("workspace/shared_brain.json")
        assert brain.exists(), "Shared brain missing"
        data = json.loads(brain.read_text(encoding="utf-8"))
        assert "golden_rules" in data
        assert len(data["golden_rules"]) > 0

    def test_core_memory(self):
        cm = Path("workspace/core_memory.json")
        assert cm.exists(), "Core memory missing"
        data = json.loads(cm.read_text(encoding="utf-8"))
        assert "network_state" in data


class TestAgents:
    """تحقق من ملفات الوكلاء"""

    def test_81_agents_exist(self):
        agent_dir = Path("agents")
        all_json = list(agent_dir.rglob("*.json"))
        assert len(all_json) == 81, f"Expected 81 agents, got {len(all_json)}"

    def test_agent_has_required_fields(self):
        sample = Path("agents/cat6_leadership/A01_strategic_commander.json")
        assert sample.exists()
        data = json.loads(sample.read_text(encoding="utf-8"))
        assert "agent_id" in data
        assert "name" in data
        assert "system_prompt" in data
        assert "model" in data


class TestEvolution:
    """تحقق من بيانات التطور"""

    def test_evolution_state(self):
        state = Path("workspace/exponential_evolution/evolution_state.json")
        assert state.exists()
        data = json.loads(state.read_text(encoding="utf-8"))
        assert data["cycle_count"] >= 1
        assert data["multiplier"] >= 1.0

    def test_experiments_exist(self):
        exp_dir = Path("workspace/experiments")
        assert exp_dir.exists()
        files = list(exp_dir.glob("*.json"))
        assert len(files) > 0, "No experiments found"

    def test_skills_exist(self):
        skills = Path("workspace/cloned_skills")
        assert skills.exists()
        files = list(skills.glob("*"))
        assert len(files) > 0, "No skills found"

    def test_training_data(self):
        td = Path("workspace/training_data")
        assert td.exists()
        files = list(td.glob("*.json"))
        assert len(files) > 0, "No training data found"


class TestLLMClient:
    """تحقق من إعداد النماذج"""

    def test_models_defined(self):
        from core.llm_client import REAL_MODELS
        assert len(REAL_MODELS) >= 20, f"Expected 20+ models, got {len(REAL_MODELS)}"

    def test_fallback_chain(self):
        from core.llm_client import LLMClient
        assert hasattr(LLMClient, "FALLBACK_CHAIN")
        assert len(LLMClient.FALLBACK_CHAIN) >= 3

    def test_openrouter_key(self):
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("OPENROUTER_API_KEY", "")
        assert len(key) > 10, "OpenRouter API key missing"


class TestKnowledge:
    """تحقق من المعرفة المكتسبة"""

    def test_knowledge_dirs(self):
        kdir = Path("workspace/knowledge")
        assert kdir.exists()
        cats = [d for d in kdir.iterdir() if d.is_dir()]
        assert len(cats) >= 5, f"Expected 5+ knowledge categories, got {len(cats)}"

    def test_knowledge_files(self):
        kdir = Path("workspace/knowledge")
        files = list(kdir.rglob("*.txt"))
        assert len(files) > 10, f"Expected 10+ knowledge files, got {len(files)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
