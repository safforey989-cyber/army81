"""
Army81 - اختبارات أساسية
شغّل: python tests/test_core.py
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

print("\n" + "="*50)
print("  Army81 — اختبارات أساسية")
print("="*50 + "\n")

# ── 1. اختبار LLM Client ──────────────────────────────
print("📦 LLMClient:")

def test_llm_import():
    from core.llm_client import LLMClient, REAL_MODELS
    assert len(REAL_MODELS) >= 7
    client = LLMClient("gemini-flash")
    assert client.provider in ("gemini", "openrouter")

def test_llm_for_task():
    from core.llm_client import LLMClient
    c = LLMClient.for_task("simple")
    assert c is not None
    c2 = LLMClient.for_task("code")
    assert c2.alias in ("local-coder", "gemini-flash")

test("استيراد LLMClient وNماذج حقيقية", test_llm_import)
test("اختيار نموذج حسب المهمة", test_llm_for_task)

# ── 2. اختبار BaseAgent ───────────────────────────────
print("\n🤖 BaseAgent:")

def test_agent_create():
    from core.base_agent import BaseAgent
    agent = BaseAgent(
        agent_id="TEST01",
        name="Test Agent",
        name_ar="وكيل اختبار",
        category="test",
        description="اختبار",
        system_prompt="أنت وكيل اختبار.",
        model_alias="gemini-flash",
    )
    assert agent.agent_id == "TEST01"
    assert agent.stats["tasks_done"] == 0

def test_agent_info():
    from core.base_agent import BaseAgent
    agent = BaseAgent("T1", "Test", "اختبار", "test", "desc", "prompt")
    info = agent.info()
    assert "id" in info
    assert "model" in info

test("إنشاء وكيل", test_agent_create)
test("معلومات الوكيل", test_agent_info)

# ── 3. اختبار Router ──────────────────────────────────
print("\n🔀 SmartRouter:")

def test_router_register():
    from router.smart_router import SmartRouter
    from core.base_agent import BaseAgent
    r = SmartRouter()
    a = BaseAgent("R01", "R", "ر", "cat3_tools", "d", "p")
    r.register(a)
    assert "R01" in r.agents

def test_router_status():
    from router.smart_router import SmartRouter
    r = SmartRouter()
    s = r.status()
    assert "agents_count" in s

test("تسجيل وكيل في الروتر", test_router_register)
test("حالة الروتر", test_router_status)

# ── 4. اختبار تحميل الوكلاء من JSON ─────────────────
print("\n📄 Agent JSON Loading:")

def test_load_agent_json():
    from core.base_agent import load_agent_from_json
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "agents/cat6_leadership/A01_strategic_commander.json"
    )
    if os.path.exists(json_path):
        agent = load_agent_from_json(json_path)
        assert agent.agent_id == "A01"
    else:
        raise FileNotFoundError("A01 JSON not found")

test("تحميل A01 من JSON", test_load_agent_json)

# ── النتيجة ───────────────────────────────────────────
print("\n" + "="*50)
passed = sum(1 for r in results if r[0] == "pass")
failed = sum(1 for r in results if r[0] == "fail")
print(f"  النتيجة: {passed} نجح | {failed} فشل")
print("="*50 + "\n")

if failed > 0:
    print("الأخطاء:")
    for r in results:
        if r[0] == "fail":
            print(f"  ❌ {r[1]}: {r[2]}")
    sys.exit(1)
