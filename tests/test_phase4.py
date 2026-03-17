"""
test_phase4.py — اختبارات المرحلة الرابعة

يختبر:
1. تحميل جميع الـ 81 وكيل (A01-A81)
2. وكلاء cat7_new (A72-A81)
3. بنية crews/army81_crews.py
4. بنية dashboard/app.py
5. التحقق من عدم تكرار agent_id
6. اكتمال حقول الوكلاء الإلزامية
"""

import os
import sys
import json
import unittest
from pathlib import Path

# ── إضافة المسار الجذر ─────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

AGENTS_ROOT = ROOT / "agents"


def load_all_agents() -> list:
    """Load all agent JSON files."""
    agents = []
    if not AGENTS_ROOT.exists():
        return agents
    for cat_dir in AGENTS_ROOT.iterdir():
        if not cat_dir.is_dir():
            continue
        for json_file in cat_dir.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                data["_file"] = str(json_file)
                agents.append(data)
            except Exception as e:
                print(f"  ⚠️ فشل تحميل {json_file}: {e}")
    return agents


ALL_AGENTS = load_all_agents()
AGENT_MAP = {a["agent_id"]: a for a in ALL_AGENTS if "agent_id" in a}


# ══════════════════════════════════════════════════════════════════════════════
class TestAgentCount(unittest.TestCase):
    """التحقق من عدد الوكلاء"""

    def test_total_agents_81(self):
        self.assertGreaterEqual(
            len(ALL_AGENTS), 81,
            f"يجب أن يكون هناك 81 وكيلاً على الأقل، وُجد: {len(ALL_AGENTS)}"
        )

    def test_no_duplicate_ids(self):
        ids = [a["agent_id"] for a in ALL_AGENTS if "agent_id" in a]
        self.assertEqual(
            len(ids), len(set(ids)),
            f"توجد agent_ids مكررة: {[i for i in ids if ids.count(i) > 1]}"
        )

    def test_a01_exists(self):
        self.assertIn("A01", AGENT_MAP)

    def test_a81_exists(self):
        self.assertIn("A81", AGENT_MAP)

    def test_all_ids_a01_to_a81(self):
        missing = []
        for i in range(1, 82):
            agent_id = f"A{i:02d}" if i < 10 else f"A{i}"
            if agent_id not in AGENT_MAP:
                missing.append(agent_id)
        self.assertEqual(missing, [], f"وكلاء مفقودون: {missing}")


# ══════════════════════════════════════════════════════════════════════════════
class TestAgentStructure(unittest.TestCase):
    """التحقق من هيكل كل وكيل"""

    REQUIRED_FIELDS = ["agent_id", "name", "name_ar", "category", "description", "model", "tools", "system_prompt"]

    def test_all_agents_have_required_fields(self):
        errors = []
        for agent in ALL_AGENTS:
            agent_id = agent.get("agent_id", "UNKNOWN")
            for field in self.REQUIRED_FIELDS:
                if field not in agent or not agent[field]:
                    errors.append(f"{agent_id}: حقل مفقود أو فارغ '{field}'")
        self.assertEqual(errors, [], f"أخطاء في هيكل الوكلاء:\n" + "\n".join(errors[:20]))

    def test_all_agents_have_tools_list(self):
        for agent in ALL_AGENTS:
            agent_id = agent.get("agent_id", "?")
            tools = agent.get("tools", None)
            self.assertIsInstance(tools, list, f"{agent_id}: 'tools' يجب أن تكون قائمة")

    def test_all_agents_have_valid_model(self):
        valid_models = {"gemini-flash", "gemini-pro", "claude-fast", "claude-smart",
                        "local-small", "local-coder"}
        for agent in ALL_AGENTS:
            agent_id = agent.get("agent_id", "?")
            model = agent.get("model", "")
            self.assertIn(
                model, valid_models,
                f"{agent_id}: نموذج غير معروف '{model}'. المعروفة: {valid_models}"
            )

    def test_system_prompt_not_empty(self):
        for agent in ALL_AGENTS:
            agent_id = agent.get("agent_id", "?")
            prompt = agent.get("system_prompt", "")
            self.assertGreater(
                len(prompt), 50,
                f"{agent_id}: system_prompt قصير جداً ({len(prompt)} حرف)"
            )


# ══════════════════════════════════════════════════════════════════════════════
class TestCategoryDistribution(unittest.TestCase):
    """التحقق من توزيع الفئات"""

    def _count_by_category(self) -> dict:
        counts = {}
        for a in ALL_AGENTS:
            cat = a.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def test_cat7_new_has_10_agents(self):
        counts = self._count_by_category()
        self.assertGreaterEqual(
            counts.get("cat7_new", 0), 10,
            f"cat7_new يجب أن يحتوي على 10 وكلاء على الأقل، وُجد: {counts.get('cat7_new', 0)}"
        )

    def test_cat6_leadership_exists(self):
        counts = self._count_by_category()
        self.assertGreater(counts.get("cat6_leadership", 0), 0)

    def test_cat1_science_exists(self):
        counts = self._count_by_category()
        self.assertGreater(counts.get("cat1_science", 0), 0)

    def test_all_7_categories_present(self):
        counts = self._count_by_category()
        expected_cats = {"cat1_science", "cat2_society", "cat3_tools",
                         "cat4_management", "cat5_behavior", "cat6_leadership", "cat7_new"}
        missing = expected_cats - set(counts.keys())
        self.assertEqual(missing, set(), f"فئات مفقودة: {missing}")


# ══════════════════════════════════════════════════════════════════════════════
class TestCat7NewAgents(unittest.TestCase):
    """اختبار وكلاء cat7_new"""

    CAT7_IDS = [f"A{i}" for i in range(72, 82)]

    def test_all_cat7_agents_exist(self):
        missing = [aid for aid in self.CAT7_IDS if aid not in AGENT_MAP]
        self.assertEqual(missing, [], f"وكلاء cat7 مفقودون: {missing}")

    def test_cat7_agents_category_correct(self):
        for aid in self.CAT7_IDS:
            if aid in AGENT_MAP:
                self.assertEqual(
                    AGENT_MAP[aid].get("category"), "cat7_new",
                    f"{aid}: الفئة يجب أن تكون cat7_new"
                )

    def test_a81_is_meta_intelligence(self):
        self.assertIn("A81", AGENT_MAP)
        a81 = AGENT_MAP["A81"]
        self.assertIn("meta", a81.get("name", "").lower())

    def test_a72_is_self_evolution(self):
        self.assertIn("A72", AGENT_MAP)
        a72 = AGENT_MAP["A72"]
        self.assertIn("evolution", a72.get("name", "").lower())

    def test_cat7_uses_advanced_models(self):
        """وكلاء cat7 يجب أن يستخدموا gemini-pro أو gemini-flash"""
        allowed = {"gemini-pro", "gemini-flash"}
        for aid in self.CAT7_IDS:
            if aid in AGENT_MAP:
                model = AGENT_MAP[aid].get("model", "")
                self.assertIn(model, allowed, f"{aid}: نموذج {model} غير مناسب لـ cat7")


# ══════════════════════════════════════════════════════════════════════════════
class TestCrewsModule(unittest.TestCase):
    """اختبار crews/army81_crews.py"""

    def test_crews_file_exists(self):
        crews_file = ROOT / "crews" / "army81_crews.py"
        self.assertTrue(crews_file.exists(), f"الملف غير موجود: {crews_file}")

    def test_crews_module_importable(self):
        try:
            import crews.army81_crews as cm
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"فشل استيراد crews.army81_crews: {e}")

    def test_team_registry_has_3_teams(self):
        from crews.army81_crews import TEAM_REGISTRY
        self.assertEqual(len(TEAM_REGISTRY), 3, "يجب أن يكون هناك 3 فرق")

    def test_strategic_team_ids_correct(self):
        from crews.army81_crews import STRATEGIC_TEAM_IDS
        self.assertIn("A01", STRATEGIC_TEAM_IDS)
        self.assertIn("A31", STRATEGIC_TEAM_IDS)

    def test_research_team_ids_correct(self):
        from crews.army81_crews import RESEARCH_TEAM_IDS
        self.assertIn("A07", RESEARCH_TEAM_IDS)
        self.assertIn("A38", RESEARCH_TEAM_IDS)

    def test_crisis_team_ids_correct(self):
        from crews.army81_crews import CRISIS_TEAM_IDS
        self.assertIn("A29", CRISIS_TEAM_IDS)
        self.assertIn("A34", CRISIS_TEAM_IDS)

    def test_list_teams_returns_3(self):
        from crews.army81_crews import list_teams
        teams = list_teams()
        self.assertEqual(len(teams), 3)

    def test_run_team_fallback_strategic(self):
        """يجب أن يعمل run_team في وضع fallback (بدون CrewAI)"""
        from crews.army81_crews import run_team
        result = run_team("strategic", "اختبار: ما أهم التحديات الاستراتيجية؟")
        self.assertIn("team", result)
        self.assertIn("agents", result)
        # يجب أن يُرجع نتيجة في كلا الوضعين
        has_output = "output" in result or "combined_output" in result or "error" in result
        self.assertTrue(has_output)

    def test_run_team_invalid_key(self):
        from crews.army81_crews import run_team
        result = run_team("nonexistent_team", "test")
        self.assertIn("error", result)


# ══════════════════════════════════════════════════════════════════════════════
class TestDashboardModule(unittest.TestCase):
    """اختبار dashboard/app.py (بدون تشغيل Streamlit)"""

    def test_dashboard_file_exists(self):
        dash_file = ROOT / "dashboard" / "app.py"
        self.assertTrue(dash_file.exists(), f"الملف غير موجود: {dash_file}")

    def test_dashboard_has_correct_content(self):
        dash_file = ROOT / "dashboard" / "app.py"
        content = dash_file.read_text(encoding="utf-8")
        # التحقق من العناصر الأساسية
        self.assertIn("st.set_page_config", content, "يجب أن يتضمن إعداد الصفحة")
        self.assertIn("load_all_agents", content, "يجب أن يتضمن تحميل الوكلاء")
        self.assertIn("GATEWAY_URL", content, "يجب أن يتضمن URL البوابة")
        self.assertIn("/task", content, "يجب أن يتضمن endpoint المهام")
        self.assertIn("/workflow", content, "يجب أن يتضمن endpoint الـ workflow")

    def test_dashboard_imports_streamlit(self):
        dash_file = ROOT / "dashboard" / "app.py"
        content = dash_file.read_text(encoding="utf-8")
        self.assertIn("import streamlit", content)

    def test_dashboard_has_all_pages(self):
        dash_file = ROOT / "dashboard" / "app.py"
        content = dash_file.read_text(encoding="utf-8")
        required_sections = ["الرئيسية", "الوكلاء", "إرسال مهمة", "الإحصائيات"]
        for section in required_sections:
            self.assertIn(section, content, f"القسم '{section}' مفقود من لوحة التحكم")

    def test_dashboard_references_crews(self):
        dash_file = ROOT / "dashboard" / "app.py"
        content = dash_file.read_text(encoding="utf-8")
        self.assertIn("army81_crews", content, "لوحة التحكم يجب أن تستورد crews")


# ══════════════════════════════════════════════════════════════════════════════
class TestCoreAgentLoading(unittest.TestCase):
    """اختبار تحميل الوكلاء عبر core/base_agent.py"""

    def test_load_a81_via_base_agent(self):
        try:
            from core.base_agent import load_agent_from_json
            a81_file = ROOT / "agents" / "cat7_new" / "A81_meta_intelligence.json"
            if a81_file.exists():
                agent = load_agent_from_json(str(a81_file))
                self.assertEqual(agent.agent_id, "A81")
                self.assertEqual(agent.category, "cat7_new")
        except ImportError:
            self.skipTest("core.base_agent غير متاح")

    def test_load_a72_via_base_agent(self):
        try:
            from core.base_agent import load_agent_from_json
            a72_file = ROOT / "agents" / "cat7_new" / "A72_self_evolution.json"
            if a72_file.exists():
                agent = load_agent_from_json(str(a72_file))
                self.assertEqual(agent.agent_id, "A72")
        except ImportError:
            self.skipTest("core.base_agent غير متاح")

    def test_smart_router_available(self):
        try:
            from router.smart_router import SmartRouter
            router = SmartRouter()
            self.assertIsNotNone(router)
        except ImportError:
            self.skipTest("router.smart_router غير متاح")


# ══════════════════════════════════════════════════════════════════════════════
class TestRequirementsFile(unittest.TestCase):
    """التحقق من requirements.txt"""

    def test_requirements_has_crewai(self):
        req_file = ROOT / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            self.assertIn("crewai", content.lower(), "crewai مفقود من requirements.txt")

    def test_requirements_has_streamlit(self):
        req_file = ROOT / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            self.assertIn("streamlit", content.lower(), "streamlit مفقود من requirements.txt")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Army81 — اختبارات المرحلة الرابعة")
    print("=" * 60)
    print(f"📁 الجذر: {ROOT}")
    print(f"🤖 وكلاء محمّلون: {len(ALL_AGENTS)}")
    print("=" * 60)
    unittest.main(verbosity=2)
