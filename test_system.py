"""
Army81 System Test - اختبار شامل للنظام
يتحقق من كل المكونات الأساسية
"""
import json
import os
import sys
import time

# إضافة المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = {"passed": 0, "failed": 0, "tests": []}

def test(name, func):
    try:
        func()
        print(f"  {PASS} {name}")
        results["passed"] += 1
        results["tests"].append({"name": name, "status": "pass"})
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results["failed"] += 1
        results["tests"].append({"name": name, "status": "fail", "error": str(e)})


print("\n" + "="*60)
print("  Army81 System Test")
print("="*60 + "\n")

# ============================================================
# 1. اختبار تحميل الوكلاء
# ============================================================
print(f"\n{INFO} Testing Agent Loading...")

def test_agent_files():
    agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
    count = 0
    for cat in os.listdir(agents_dir):
        cat_path = os.path.join(agents_dir, cat)
        if os.path.isdir(cat_path):
            for f in os.listdir(cat_path):
                if f.endswith(".json") and not f.endswith(".bak"):
                    count += 1
    assert count == 81, f"Expected 81 agents, found {count}"

test("81 agent JSON files exist", test_agent_files)

def test_agent_json_valid():
    agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
    for cat in os.listdir(agents_dir):
        cat_path = os.path.join(agents_dir, cat)
        if os.path.isdir(cat_path):
            for f in os.listdir(cat_path):
                if f.endswith(".json") and not f.endswith(".bak"):
                    with open(os.path.join(cat_path, f), "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    assert "agent_id" in data, f"Missing agent_id in {f}"
                    assert "system_prompt" in data, f"Missing system_prompt in {f}"
                    assert "model" in data, f"Missing model in {f}"

test("All agent JSON files are valid", test_agent_json_valid)

# ============================================================
# 2. اختبار BaseAgent
# ============================================================
print(f"\n{INFO} Testing BaseAgent...")

def test_base_agent_creation():
    from core.base_agent import BaseAgent
    agent = BaseAgent(
        agent_id="TEST01",
        name="Test Agent",
        name_ar="وكيل اختبار",
        category="test",
        description="Test agent",
        system_prompt="You are a test agent.",
        model="test-model",
        provider="test",
    )
    assert agent.agent_id == "TEST01"
    assert agent.name == "Test Agent"
    d = agent.to_dict()
    assert d["agent_id"] == "TEST01"

test("BaseAgent creation", test_base_agent_creation)

# ============================================================
# 3. اختبار Smart Router
# ============================================================
print(f"\n{INFO} Testing Smart Router...")

def test_router():
    from core.base_agent import BaseAgent
    from router.smart_router import SmartRouter
    router = SmartRouter()
    a1 = BaseAgent("T1", "Agent1", "وكيل1", "cat2_engineering", "test", "You code.", "m", "test")
    a2 = BaseAgent("T2", "Agent2", "وكيل2", "cat3_research", "test", "You research.", "m", "test")
    router.register_agent(a1)
    router.register_agent(a2)
    assert len(router.agents) == 2
    status = router.get_status()
    assert status["total_agents"] == 2

test("SmartRouter registration", test_router)

# ============================================================
# 4. اختبار Memory System
# ============================================================
print(f"\n{INFO} Testing Memory System...")

def test_short_term_memory():
    from memory.memory_system import ShortTermMemory
    stm = ShortTermMemory()
    stm.add("key1", "value1", "agent1")
    assert stm.get("key1") == "value1"
    assert stm.size() == 1

test("Short-term memory", test_short_term_memory)

def test_working_memory():
    from memory.memory_system import WorkingMemory
    import tempfile
    db = os.path.join(tempfile.mkdtemp(), "test_wm.db")
    wm = WorkingMemory(db)
    wm.store("test_key", {"data": "hello"}, "agent1")
    result = wm.retrieve("test_key")
    assert result == {"data": "hello"}

test("Working memory (SQLite)", test_working_memory)

def test_long_term_memory():
    from memory.memory_system import LongTermMemory
    import tempfile
    db = os.path.join(tempfile.mkdtemp(), "test_ltm.db")
    ltm = LongTermMemory(db)
    ltm.store("Test Title", "This is test content about AI agents", category="test")
    results = ltm.search("AI agents")
    assert len(results) > 0

test("Long-term memory (FTS5)", test_long_term_memory)

def test_episodic_memory():
    from memory.memory_system import EpisodicMemory
    import tempfile
    ep = EpisodicMemory(os.path.join(tempfile.mkdtemp(), "episodes"))
    ep.record_episode("T1", "test task", "success", True)
    episodes = ep.get_episodes("T1")
    assert len(episodes) == 1

test("Episodic memory", test_episodic_memory)

# ============================================================
# 5. اختبار A2A Protocol
# ============================================================
print(f"\n{INFO} Testing A2A Protocol...")

def test_message_bus():
    from protocols.a2a import MessageBus, A2AMessage, MessageType
    bus = MessageBus()
    bus.register("A1")
    bus.register("A2")
    msg = A2AMessage(type=MessageType.REQUEST, from_agent="A1", to_agent="A2", content="Help me")
    bus.send(msg)
    received = bus.receive("A2")
    assert len(received) == 1
    assert received[0].content == "Help me"

test("Message bus send/receive", test_message_bus)

def test_collaboration():
    from protocols.a2a import MessageBus, CollaborationManager
    bus = MessageBus()
    bus.register("A1")
    bus.register("A2")
    bus.register("A3")
    cm = CollaborationManager(bus)
    cid = cm.start_collaboration("Big task", ["A1", "A2", "A3"])
    assert cid is not None
    cm.submit_result(cid, "A1", "Result 1")
    cm.submit_result(cid, "A2", "Result 2")
    cm.submit_result(cid, "A3", "Result 3")
    collab = cm.get_collaboration(cid)
    assert collab["status"] == "completed"

test("Collaboration manager", test_collaboration)

# ============================================================
# 6. اختبار Full System Load
# ============================================================
print(f"\n{INFO} Testing Full System Load...")

def test_full_load():
    from cli import Army81System
    system = Army81System(base_dir=os.path.dirname(os.path.abspath(__file__)))
    count = system.load_agents()
    assert count == 81, f"Expected 81, loaded {count}"
    status = system.status()
    assert status["loaded"] == True
    assert status["agents"]["total_agents"] == 81

test("Full system load (81 agents)", test_full_load)

# ============================================================
# 7. اختبار Daily Updater
# ============================================================
print(f"\n{INFO} Testing Daily Updater...")

def test_updater():
    from updates.daily_updater import DailyUpdater
    import tempfile
    updater = DailyUpdater(base_dir=tempfile.mkdtemp())
    # فقط نتحقق أنه يعمل بدون أخطاء
    assert updater is not None

test("Daily updater initialization", test_updater)

def test_self_improver():
    from updates.daily_updater import SelfImprover
    improver = SelfImprover()
    eval_result = improver.evaluate_agent("TEST", [
        {"success": True, "result": "ok"},
        {"success": True, "result": "ok"},
        {"success": False, "result": "ERROR: timeout"},
    ])
    assert eval_result["success_rate"] > 0.5

test("Self improver evaluation", test_self_improver)

# ============================================================
# النتائج
# ============================================================
print(f"\n{'='*60}")
total = results["passed"] + results["failed"]
print(f"  Results: {results['passed']}/{total} passed")
if results["failed"] == 0:
    print(f"  {PASS} ALL TESTS PASSED!")
else:
    print(f"  {FAIL} {results['failed']} tests failed")
print(f"{'='*60}\n")

sys.exit(0 if results["failed"] == 0 else 1)
