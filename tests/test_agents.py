"""
Army81 - اختبارات الوكلاء
شغّل: python tests/test_agents.py
"""
import sys
import os
import json
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


print("\n" + "=" * 50)
print("  Army81 — اختبارات الوكلاء")
print("=" * 50 + "\n")

# ── 1. تحميل كل الوكلاء ─────────────────────────────
print("📂 تحميل الوكلاء:")

AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents")


def test_all_json_valid():
    """كل ملفات JSON صالحة"""
    count = 0
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in os.listdir(cat_path):
            if fname.endswith(".json"):
                fpath = os.path.join(cat_path, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                assert "agent_id" in data, f"{fname}: missing agent_id"
                assert "name" in data, f"{fname}: missing name"
                assert "name_ar" in data, f"{fname}: missing name_ar"
                assert "category" in data, f"{fname}: missing category"
                assert "system_prompt" in data, f"{fname}: missing system_prompt"
                count += 1
    assert count >= 40, f"Expected at least 40 agents, found {count}"


def test_agent_count():
    """عدد الوكلاء = 81"""
    count = 0
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in os.listdir(cat_path):
            if fname.endswith(".json"):
                count += 1
    assert count >= 81, f"Expected at least 81 agents, found {count}"


def test_unique_ids():
    """كل معرّفات الوكلاء فريدة"""
    ids = set()
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in os.listdir(cat_path):
            if fname.endswith(".json"):
                with open(os.path.join(cat_path, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                aid = data["agent_id"]
                assert aid not in ids, f"Duplicate agent_id: {aid}"
                ids.add(aid)


def test_load_all_agents():
    """تحميل كل الوكلاء عبر load_agent_from_json"""
    from core.base_agent import load_agent_from_json
    loaded = 0
    errors = 0
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith(".json"):
                try:
                    agent = load_agent_from_json(os.path.join(cat_path, fname))
                    assert agent.agent_id
                    loaded += 1
                except Exception:
                    errors += 1
    assert loaded >= 40, f"Only loaded {loaded} agents"
    assert errors == 0, f"{errors} agents failed to load"


test("كل ملفات JSON صالحة", test_all_json_valid)
test("عدد الوكلاء = 81", test_agent_count)
test("معرّفات فريدة", test_unique_ids)
test("تحميل كل الوكلاء", test_load_all_agents)

# ── 2. اختبار الأدوات ───────────────────────────────
print("\n🔧 الأدوات:")


def test_tools_registry():
    """بناء سجل الأدوات"""
    from tools.registry import build_tools_registry
    reg = build_tools_registry()
    assert len(reg) >= 10, f"Only {len(reg)} tools"
    assert "web_search" in reg
    assert "remember" in reg
    assert "run_code" in reg


def test_tools_match_agents():
    """أدوات الوكلاء موجودة في السجل"""
    from tools.registry import build_tools_registry
    reg = build_tools_registry()
    missing = {}
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in os.listdir(cat_path):
            if fname.endswith(".json"):
                with open(os.path.join(cat_path, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for tool_name in data.get("tools", []):
                    if tool_name not in reg:
                        missing.setdefault(tool_name, []).append(data["agent_id"])
    # تحذير فقط — بعض الأدوات شرطية (تحتاج API keys)
    if missing:
        conditional = {"deep_search", "research", "github_search"}
        real_missing = {k: v for k, v in missing.items() if k not in conditional}
        assert len(real_missing) == 0, f"Missing tools: {real_missing}"


test("بناء سجل الأدوات", test_tools_registry)
test("أدوات الوكلاء موجودة في السجل", test_tools_match_agents)

# ── 3. بروتوكول A2A ─────────────────────────────────
print("\n📡 بروتوكول A2A:")


def test_a2a_import():
    """استيراد A2A"""
    from protocols.a2a import A2AProtocol, A2AMessage
    proto = A2AProtocol()
    assert proto.stats["total_messages"] == 0


def test_a2a_send():
    """إرسال رسالة A2A"""
    from protocols.a2a import A2AProtocol
    proto = A2AProtocol()
    result = proto.send("A01", "A02", "مهمة اختبار", msg_type="info")
    assert result["status"] == "delivered"
    assert proto.stats["total_messages"] == 1
    inbox = proto.get_inbox("A02")
    assert len(inbox) == 1


def test_a2a_status():
    """حالة A2A"""
    from protocols.a2a import A2AProtocol
    proto = A2AProtocol()
    s = proto.status()
    assert "stats" in s
    assert "pending_messages" in s


test("استيراد A2A", test_a2a_import)
test("إرسال رسالة A2A", test_a2a_send)
test("حالة A2A", test_a2a_status)

# ── 4. الروتر مع الوكلاء ──────────────────────────────
print("\n🔀 الروتر + الوكلاء:")


def test_router_with_agents():
    """تسجيل وكلاء في الروتر"""
    from router.smart_router import SmartRouter
    from core.base_agent import load_agent_from_json
    r = SmartRouter()
    loaded = 0
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith(".json"):
                try:
                    agent = load_agent_from_json(os.path.join(cat_path, fname))
                    r.register(agent)
                    loaded += 1
                except Exception:
                    pass
    assert loaded >= 40
    s = r.status()
    assert s["agents_count"] >= 40


def test_router_categories():
    """كل الفئات ممثلة"""
    from router.smart_router import SmartRouter
    from core.base_agent import load_agent_from_json
    r = SmartRouter()
    for cat_dir in os.listdir(AGENTS_DIR):
        cat_path = os.path.join(AGENTS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith(".json"):
                try:
                    agent = load_agent_from_json(os.path.join(cat_path, fname))
                    r.register(agent)
                except Exception:
                    pass
    cats = r._count_by_category()
    assert len(cats) >= 5, f"Only {len(cats)} categories"


test("تسجيل وكلاء في الروتر", test_router_with_agents)
test("كل الفئات ممثلة", test_router_categories)

# ── 5. Gateway ────────────────────────────────────────
print("\n🌐 Gateway:")


def test_gateway_import():
    """استيراد FastAPI app"""
    from gateway.app import app
    assert app.title == "Army81"


test("استيراد FastAPI app", test_gateway_import)

# ── النتيجة ───────────────────────────────────────────
print("\n" + "=" * 50)
passed = sum(1 for r in results if r[0] == "pass")
failed = sum(1 for r in results if r[0] == "fail")
print(f"  النتيجة: {passed} نجح | {failed} فشل")
print("=" * 50 + "\n")

if failed > 0:
    print("الأخطاء:")
    for r in results:
        if r[0] == "fail":
            print(f"  ❌ {r[1]}: {r[2]}")
    sys.exit(1)
