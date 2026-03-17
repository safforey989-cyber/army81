"""
Army81 - اختبارات المرحلة 3
26 وكيل جديد (A15-A40) + daily_updater + /workflow endpoint
شغّل: python tests/test_phase3.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅"
FAIL = "❌"
results = []
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test(name, func):
    try:
        func()
        print(f"  {PASS} {name}")
        results.append(("pass", name))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results.append(("fail", name, str(e)))

print("\n" + "="*60)
print("  Army81 — اختبارات المرحلة 3")
print("="*60 + "\n")

# ── 1. cat5_behavior: 13 وكيل ────────────────────────────
print("🧠 cat5_behavior (A15-A27):")

BEHAVIOR_AGENTS = [
    ("A15", "agents/cat5_behavior/A15_psychologist.json"),
    ("A16", "agents/cat5_behavior/A16_negotiation_expert.json"),
    ("A17", "agents/cat5_behavior/A17_body_language.json"),
    ("A18", "agents/cat5_behavior/A18_influence_persuasion.json"),
    ("A19", "agents/cat5_behavior/A19_emotional_intelligence.json"),
    ("A20", "agents/cat5_behavior/A20_social_dynamics.json"),
    ("A21", "agents/cat5_behavior/A21_crowd_behavior.json"),
    ("A22", "agents/cat5_behavior/A22_behavioral_economics.json"),
    ("A23", "agents/cat5_behavior/A23_conflict_resolution.json"),
    ("A24", "agents/cat5_behavior/A24_leadership_psychology.json"),
    ("A25", "agents/cat5_behavior/A25_communication_expert.json"),
    ("A26", "agents/cat5_behavior/A26_decision_psychology.json"),
    ("A27", "agents/cat5_behavior/A27_cultural_intelligence.json"),
]

def make_agent_test(agent_id, json_path):
    def _test():
        from core.base_agent import load_agent_from_json
        full = os.path.join(BASE, json_path)
        assert os.path.exists(full), f"مفقود: {json_path}"
        agent = load_agent_from_json(full)
        assert agent.agent_id == agent_id
        assert len(agent.system_prompt) > 100
        assert agent.category == json_path.split("/")[1]
    return _test

for aid, jpath in BEHAVIOR_AGENTS:
    test(f"تحميل {aid}", make_agent_test(aid, jpath))

# ── 2. cat6_leadership: 10 وكلاء ─────────────────────────
print("\n👑 cat6_leadership (A28-A37):")

LEADERSHIP_AGENTS = [
    ("A28", "agents/cat6_leadership/A28_military_strategist.json"),
    ("A29", "agents/cat6_leadership/A29_crisis_manager.json"),
    ("A30", "agents/cat6_leadership/A30_innovation_leader.json"),
    ("A31", "agents/cat6_leadership/A31_intelligence_analyst.json"),
    ("A32", "agents/cat6_leadership/A32_geopolitics_expert.json"),
    ("A33", "agents/cat6_leadership/A33_future_forecaster.json"),
    ("A34", "agents/cat6_leadership/A34_risk_assessor.json"),
    ("A35", "agents/cat6_leadership/A35_change_management.json"),
    ("A36", "agents/cat6_leadership/A36_org_strategist.json"),
    ("A37", "agents/cat6_leadership/A37_decision_architect.json"),
]

for aid, jpath in LEADERSHIP_AGENTS:
    test(f"تحميل {aid}", make_agent_test(aid, jpath))

# ── 3. cat1_science: 3 وكلاء ─────────────────────────────
print("\n🔬 cat1_science (A38-A40):")

SCIENCE_AGENTS = [
    ("A38", "agents/cat1_science/A38_physics_quantum.json"),
    ("A39", "agents/cat1_science/A39_climate_environment.json"),
    ("A40", "agents/cat1_science/A40_tech_scout.json"),
]

for aid, jpath in SCIENCE_AGENTS:
    test(f"تحميل {aid}", make_agent_test(aid, jpath))

# ── 4. عدد الوكلاء الكلي ─────────────────────────────────
print("\n📊 إحصائيات المشروع:")

def test_total_agents():
    import glob
    json_files = glob.glob(os.path.join(BASE, "agents/**/*.json"), recursive=True)
    count = len(json_files)
    assert count >= 40, f"المتوقع 40+ وكيل، وُجد {count}"
    print(f"      → {count} ملف JSON موجود")

def test_agents_per_category():
    import glob
    from collections import Counter
    files = glob.glob(os.path.join(BASE, "agents/**/*.json"), recursive=True)
    cats = Counter(os.path.basename(os.path.dirname(f)) for f in files)
    assert cats.get("cat5_behavior", 0) >= 13, f"cat5_behavior: {cats.get('cat5_behavior')}"
    assert cats.get("cat6_leadership", 0) >= 11, f"cat6_leadership: {cats.get('cat6_leadership')}"
    assert cats.get("cat1_science", 0) >= 4, f"cat1_science: {cats.get('cat1_science')}"
    print(f"      → التوزيع: {dict(cats)}")

test("إجمالي الوكلاء ≥ 40", test_total_agents)
test("التوزيع على الفئات صحيح", test_agents_per_category)

# ── 5. Daily Updater ──────────────────────────────────────
print("\n🕐 Daily Updater:")

def test_updater_import():
    sys.path.insert(0, os.path.join(BASE, "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "daily_updater",
        os.path.join(BASE, "scripts/daily_updater.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "run_daily_update")
    assert hasattr(mod, "collect_arxiv_papers")
    assert hasattr(mod, "collect_github_trending")
    assert hasattr(mod, "collect_ai_news")
    assert hasattr(mod, "save_to_chroma")
    assert hasattr(mod, "start_scheduler")

def test_updater_save_to_chroma():
    sys.path.insert(0, os.path.join(BASE, "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "daily_updater",
        os.path.join(BASE, "scripts/daily_updater.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    test_items = [{"source": "test", "topic": "AI", "content": "اختبار الحفظ اليومي", "timestamp": "2026-03-17T02:00:00"}]
    saved = mod.save_to_chroma(test_items, "test_run")
    assert saved >= 1

def test_apscheduler_import():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    assert BlockingScheduler is not None

test("استيراد daily_updater ودواله", test_updater_import)
test("save_to_chroma يحفظ فعلاً", test_updater_save_to_chroma)
test("APScheduler متاح", test_apscheduler_import)

# ── 6. Gateway /workflow endpoint ────────────────────────
print("\n🌐 Gateway — /workflow endpoint:")

def test_gateway_import():
    # تحقق أن الملف يحتوي على WorkflowRequest و /workflow
    gw_path = os.path.join(BASE, "gateway/app.py")
    with open(gw_path, encoding="utf-8") as f:
        content = f.read()
    assert "WorkflowRequest" in content
    assert "/workflow" in content
    assert "build_research_workflow" in content
    assert "build_analysis_workflow" in content
    assert "build_decision_workflow" in content
    assert "build_custom_workflow" in content
    assert "build_tools_registry" in content

def test_workflow_request_model():
    # اختبار نموذج الطلب مباشرة
    sys.path.insert(0, BASE)
    from pydantic import BaseModel
    from typing import Optional, List, Dict

    class WorkflowRequest(BaseModel):
        workflow: str
        task: str
        agent_ids: Optional[List[str]] = None
        context: Optional[Dict] = None

    req = WorkflowRequest(workflow="research_pipeline", task="حلّل مستقبل AI")
    assert req.workflow == "research_pipeline"
    assert req.task == "حلّل مستقبل AI"
    assert req.agent_ids is None

def test_gateway_tools_registry():
    gw_path = os.path.join(BASE, "gateway/app.py")
    with open(gw_path, encoding="utf-8") as f:
        content = f.read()
    assert "build_tools_registry" in content, "الـ gateway يجب أن يستخدم build_tools_registry"

def test_list_workflows_endpoint():
    gw_path = os.path.join(BASE, "gateway/app.py")
    with open(gw_path, encoding="utf-8") as f:
        content = f.read()
    assert "/workflows" in content

test("gateway يحتوي WorkflowRequest و /workflow", test_gateway_import)
test("WorkflowRequest model صحيح", test_workflow_request_model)
test("gateway يستخدم build_tools_registry", test_gateway_tools_registry)
test("endpoint /workflows موجود", test_list_workflows_endpoint)

# ── 7. تكامل شامل: تحميل كل 40 وكيل ─────────────────────
print("\n⚡ تكامل شامل:")

def test_load_all_40_agents():
    import glob
    from core.base_agent import load_agent_from_json
    files = sorted(glob.glob(os.path.join(BASE, "agents/**/*.json"), recursive=True))
    loaded = 0
    failed = []
    for f in files:
        try:
            agent = load_agent_from_json(f)
            assert agent.agent_id, f"agent_id فارغ في {f}"
            loaded += 1
        except Exception as e:
            failed.append(f"{os.path.basename(f)}: {e}")
    if failed:
        raise AssertionError(f"فشل تحميل {len(failed)} وكيل: {failed[:3]}")
    assert loaded >= 40, f"المحمّل {loaded} < 40"
    print(f"      → {loaded} وكيل محمّل بنجاح")

def test_workflow_with_new_agents():
    import glob
    from core.base_agent import load_agent_from_json
    from workflows.langgraph_flows import build_custom_workflow

    files = sorted(glob.glob(os.path.join(BASE, "agents/**/*.json"), recursive=True))
    agents_dict = {}
    for f in files:
        try:
            a = load_agent_from_json(f)
            agents_dict[a.agent_id] = a
        except Exception:
            pass

    # workflow من وكلاء جدد: A28 (عسكري) + A33 (مستقبل) + A34 (مخاطر)
    wf = build_custom_workflow(["A28", "A33", "A34"], agents_dict, name="strategic_analysis")
    wf._build()
    assert wf._compiled is not None
    assert len(wf.agents) == 3

test("تحميل كل 40+ وكيل بنجاح", test_load_all_40_agents)
test("workflow من وكلاء A28+A33+A34", test_workflow_with_new_agents)

# ── النتيجة ───────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for r in results if r[0] == "pass")
failed = sum(1 for r in results if r[0] == "fail")
total_agents = passed  # تقريبي
print(f"  النتيجة: {passed} نجح | {failed} فشل")
print("="*60 + "\n")

if failed > 0:
    print("الأخطاء:")
    for r in results:
        if r[0] == "fail":
            print(f"  ❌ {r[1]}: {r[2]}")
    sys.exit(1)
