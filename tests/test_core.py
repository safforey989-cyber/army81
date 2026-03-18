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

# ── 5. اختبار الأدوات الجديدة ────────────────────────
print("\n🔧 أدوات جديدة:")

def test_news_fetcher_import():
    from tools.news_fetcher import fetch_news_by_topic, fetch_rss_by_topic, fetch_daily_briefing
    assert callable(fetch_news_by_topic)
    assert callable(fetch_rss_by_topic)
    assert callable(fetch_daily_briefing)

def test_agents_registry():
    from agents.registry import AGENT_TOOLS, get_tools_for_agent, validate_registry
    assert len(AGENT_TOOLS) >= 81
    tools = get_tools_for_agent("A01")
    assert "web_search" in tools
    report = validate_registry()
    assert report["valid"]

test("استيراد news_fetcher", test_news_fetcher_import)
test("سجل الوكلاء agents/registry.py", test_agents_registry)

# ── 6. اختبار البنية التحتية ──────────────────────────
print("\n🏗️ بنية تحتية:")

def test_firestore_module():
    from memory.firestore_memory import check_firestore_health, save_agent_memory
    health = check_firestore_health()
    assert "connected" in health
    assert callable(save_agent_memory)

def test_pubsub_protocol():
    from protocols.pubsub_protocol import PubSubProtocol
    ps = PubSubProtocol(use_cloud=False)
    received = []
    ps.subscribe("test.topic", lambda msg: received.append(msg))
    ps.publish("test.topic", {"test": True}, sender="test")
    assert len(received) == 1
    status = ps.status()
    assert status["stats"]["published"] == 1

def test_cloud_scheduler():
    from scripts.cloud_scheduler_setup import SCHEDULER_JOBS, setup_local_scheduler
    assert len(SCHEDULER_JOBS) >= 4
    assert SCHEDULER_JOBS[0]["schedule"] == "0 2 * * *"

test("وحدة Firestore", test_firestore_module)
test("بروتوكول Pub/Sub", test_pubsub_protocol)
test("Cloud Scheduler jobs", test_cloud_scheduler)

# ── 7. اختبار التطور الذاتي ──────────────────────────
print("\n🧬 تطور ذاتي:")

def test_performance_monitor():
    from core.performance_monitor import PerformanceMonitor
    from core.base_agent import BaseAgent
    monitor = PerformanceMonitor()
    agent = BaseAgent("T1", "Test", "اختبار", "test", "desc", "prompt")
    agent.stats["tasks_done"] = 10
    agent.stats["tasks_failed"] = 2
    result = monitor.evaluate_agent(agent)
    assert result["success_rate"] > 0.7
    assert result["status"] in ("excellent", "good", "needs_improvement", "critical")

def test_prompt_optimizer():
    from core.prompt_optimizer import PromptOptimizer
    opt = PromptOptimizer()
    lesson = opt.collect_lesson("TEST01", "مهمة اختبار", "نتيجة", True, 8)
    assert lesson["agent_id"] == "TEST01"
    lessons = opt.get_lessons("TEST01")
    assert len(lessons) >= 1
    patterns = opt.analyze_patterns("TEST01")
    assert patterns["total_lessons"] >= 1

test("مراقب الأداء", test_performance_monitor)
test("محسّن الـ Prompts", test_prompt_optimizer)

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
