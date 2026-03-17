"""
Army81 - اختبارات المرحلة 2
LangGraph + Chroma + 10 وكلاء جدد
شغّل: python tests/test_phase2.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅"
FAIL = "❌"
results = []

def test(name, func):
    try:
        func()
        print(f"  {PASS} {name}")
        results.append(("pass", name))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results.append(("fail", name, str(e)))

print("\n" + "="*55)
print("  Army81 — اختبارات المرحلة 2")
print("="*55 + "\n")

# ── 1. LangGraph ──────────────────────────────────────────
print("🔗 LangGraph:")

def test_langgraph_import():
    from langgraph.graph import StateGraph, END
    from workflows.langgraph_flows import AgentState, Army81Workflow
    assert AgentState is not None
    assert Army81Workflow is not None

def test_workflow_build():
    from workflows.langgraph_flows import Army81Workflow
    from core.base_agent import BaseAgent

    a1 = BaseAgent("W01", "Agent1", "وكيل1", "cat3_tools", "d", "أنت وكيل اختبار.")
    a2 = BaseAgent("W02", "Agent2", "وكيل2", "cat3_tools", "d", "أنت وكيل اختبار.")

    wf = Army81Workflow([a1, a2], name="test_workflow")
    wf._build()  # يجب أن يُبنى بدون خطأ
    assert wf._compiled is not None

def test_workflow_factories():
    from workflows.langgraph_flows import (
        build_research_workflow,
        build_analysis_workflow,
        build_decision_workflow,
        build_custom_workflow,
    )
    # نختبر بـ registry فارغ
    wf = build_custom_workflow(["A05", "A06"], {}, name="custom_test")
    assert wf.name == "custom_test"

test("استيراد LangGraph وAgentState", test_langgraph_import)
test("بناء workflow من وكيلين", test_workflow_build)
test("مصانع الـ workflows", test_workflow_factories)

# ── 2. Chroma Memory ──────────────────────────────────────
print("\n🧠 Chroma Semantic Memory:")

def test_chroma_import():
    import chromadb
    from memory.chroma_memory import remember, recall, get_stats
    assert remember is not None
    assert recall is not None

def test_chroma_remember():
    from memory.chroma_memory import remember, recall, get_stats
    result = remember("الذكاء الاصطناعي يتطور بسرعة", "TEST_AGENT", ["ai"])
    assert "تم الحفظ" in result or "ID" in result

def test_chroma_recall():
    from memory.chroma_memory import recall
    result = recall("ذكاء اصطناعي", n_results=3)
    assert isinstance(result, str) and len(result) > 0

def test_chroma_stats():
    from memory.chroma_memory import get_stats
    stats = get_stats()
    assert "total_memories" in stats
    assert stats["status"] == "active"

test("استيراد Chroma Memory", test_chroma_import)
test("حفظ في الذاكرة الدلالية", test_chroma_remember)
test("استرجاع من الذاكرة", test_chroma_recall)
test("إحصائيات الذاكرة", test_chroma_stats)

# ── 3. الأدوات الجديدة ───────────────────────────────────
print("\n🔧 الأدوات الجديدة:")

def test_file_ops():
    from tools.file_ops import read_file, write_file
    result = write_file("test_phase2.txt", "اختبار المرحلة 2")
    assert "تم الحفظ" in result
    content = read_file("test_phase2.txt")
    assert "اختبار المرحلة 2" in content

def test_code_runner():
    from tools.code_runner import run_code_safe
    result = run_code_safe("print('Army81 Phase 2')\nprint(2 + 2)")
    assert "4" in result or "Army81" in result

def test_github_tool():
    from tools.github_tool import search_repos
    assert search_repos is not None  # فقط تحقق من الاستيراد

def test_tools_registry():
    from tools.registry import build_tools_registry
    registry = build_tools_registry()
    # تحقق من الأدوات الجديدة
    assert "semantic_remember" in registry
    assert "semantic_recall" in registry
    assert "run_code" in registry
    assert "read_file" in registry
    assert len(registry) >= 14

test("file_ops: كتابة وقراءة", test_file_ops)
test("code_runner: تنفيذ Python آمن", test_code_runner)
test("github_tool: استيراد ناجح", test_github_tool)
test("registry: يحتوي أدوات المرحلة 2", test_tools_registry)

# ── 4. الوكلاء الجدد (A05-A14) ───────────────────────────
print("\n🤖 الوكلاء الجدد A05-A14:")

NEW_AGENTS = [
    ("A05", "agents/cat3_tools/A05_code_developer.json"),
    ("A06", "agents/cat4_management/A06_data_analyst.json"),
    ("A07", "agents/cat1_science/A07_medical_research.json"),
    ("A08", "agents/cat2_society/A08_financial_analyst.json"),
    ("A09", "agents/cat3_tools/A09_security_analyst.json"),
    ("A10", "agents/cat4_management/A10_knowledge_manager.json"),
    ("A11", "agents/cat3_tools/A11_translator.json"),
    ("A12", "agents/cat2_society/A12_content_creator.json"),
    ("A13", "agents/cat2_society/A13_legal_advisor.json"),
    ("A14", "agents/cat4_management/A14_project_manager.json"),
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def make_agent_test(agent_id, json_path):
    def _test():
        from core.base_agent import load_agent_from_json
        full_path = os.path.join(BASE_DIR, json_path)
        assert os.path.exists(full_path), f"ملف JSON غير موجود: {json_path}"
        agent = load_agent_from_json(full_path)
        assert agent.agent_id == agent_id
        assert len(agent.system_prompt) > 50, "system_prompt قصير جداً"
        info = agent.info()
        assert "id" in info and "model" in info
    return _test

for aid, jpath in NEW_AGENTS:
    test(f"تحميل {aid}", make_agent_test(aid, jpath))

# ── 5. تكامل: workflow من وكلاء JSON ─────────────────────
print("\n⚡ تكامل: LangGraph + وكلاء JSON:")

def test_full_integration():
    from core.base_agent import load_agent_from_json
    from workflows.langgraph_flows import Army81Workflow

    agents = []
    for aid, jpath in NEW_AGENTS[:3]:  # A05, A06, A07
        full_path = os.path.join(BASE_DIR, jpath)
        agent = load_agent_from_json(full_path)
        agents.append(agent)

    wf = Army81Workflow(agents, name="integration_test")
    wf._build()
    assert wf._compiled is not None
    assert len(wf.agents) == 3

test("بناء workflow من 3 وكلاء حقيقيين", test_full_integration)

# ── النتيجة ───────────────────────────────────────────────
print("\n" + "="*55)
passed = sum(1 for r in results if r[0] == "pass")
failed = sum(1 for r in results if r[0] == "fail")
print(f"  النتيجة: {passed} نجح | {failed} فشل")
print("="*55 + "\n")

if failed > 0:
    print("الأخطاء:")
    for r in results:
        if r[0] == "fail":
            print(f"  ❌ {r[1]}: {r[2]}")
    sys.exit(1)
