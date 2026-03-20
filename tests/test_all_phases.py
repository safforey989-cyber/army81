"""
Army81 — اختبارات شاملة لكل المراحل
Phase 1: أدوات حقيقية
Phase 2: تخصيص الوكلاء
Phase 3: البنية التحتية
Phase 4: التطور الذاتي
"""
import os
import sys
import json
import unittest

# إضافة المسار الرئيسي
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPhase1Tools(unittest.TestCase):
    """المرحلة 1: أدوات حقيقية"""

    def test_web_search_import(self):
        """web_search يُستورد بدون أخطاء"""
        from tools.web_search import web_search, deep_search, fetch_news
        self.assertTrue(callable(web_search))
        self.assertTrue(callable(deep_search))
        self.assertTrue(callable(fetch_news))

    def test_news_fetcher_import(self):
        """news_fetcher يُستورد بدون أخطاء"""
        from tools.news_fetcher import (
            fetch_news, fetch_news_rss, fetch_news_api,
            fetch_news_headlines, fetch_rss, list_available_feeds,
            RSS_FEEDS, TOPIC_FEEDS
        )
        self.assertTrue(callable(fetch_news))
        self.assertTrue(callable(fetch_news_rss))
        self.assertTrue(callable(fetch_rss))
        self.assertGreater(len(RSS_FEEDS), 10)
        self.assertIn("ai", TOPIC_FEEDS)
        self.assertIn("tech", TOPIC_FEEDS)

    def test_news_fetcher_topic_mapping(self):
        """تحويل المواضيع يعمل"""
        from tools.news_fetcher import _map_topic_to_rss
        self.assertEqual(_map_topic_to_rss("artificial intelligence"), "ai")
        self.assertEqual(_map_topic_to_rss("ذكاء اصطناعي"), "ai")
        self.assertEqual(_map_topic_to_rss("اقتصاد"), "economy")
        self.assertEqual(_map_topic_to_rss("technology"), "tech")

    def test_news_fetcher_available_feeds(self):
        """عرض المصادر المتاحة"""
        from tools.news_fetcher import list_available_feeds
        result = list_available_feeds()
        self.assertIn("RSS", result)
        self.assertIn("techcrunch", result)

    def test_file_ops_import(self):
        """file_ops يعمل"""
        from tools.file_ops import read_file, write_file, list_files
        self.assertTrue(callable(read_file))
        self.assertTrue(callable(write_file))

    def test_code_runner_import(self):
        """code_runner يعمل"""
        from tools.code_runner import run_code_safe
        self.assertTrue(callable(run_code_safe))

    def test_registry_has_news_tools(self):
        """سجل الأدوات يحتوي أدوات الأخبار"""
        from tools.registry import build_tools_registry
        registry = build_tools_registry()
        self.assertIn("fetch_news", registry)
        self.assertIn("fetch_news_rss", registry)
        self.assertIn("fetch_headlines", registry)
        self.assertIn("web_search", registry)
        self.assertIn("deep_search", registry)

    def test_registry_category_tools(self):
        """كل فئة لها أدوات"""
        from tools.registry import CATEGORY_TOOLS
        self.assertGreaterEqual(len(CATEGORY_TOOLS), 10)
        for cat, tools in CATEGORY_TOOLS.items():
            self.assertGreater(len(tools), 0, f"{cat} has no tools")


class TestPhase2AgentSpecialization(unittest.TestCase):
    """المرحلة 2: تخصيص الوكلاء"""

    def test_all_agents_load(self):
        """كل الوكلاء يُحمّلون بنجاح"""
        from core.base_agent import load_agent_from_json
        from tools.registry import build_tools_registry

        registry = build_tools_registry()
        agents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")

        loaded = 0
        errors = []
        for root, dirs, files in os.walk(agents_dir):
            for fname in files:
                if fname.endswith(".json"):
                    path = os.path.join(root, fname)
                    try:
                        agent = load_agent_from_json(path, registry)
                        loaded += 1
                    except Exception as e:
                        errors.append(f"{fname}: {e}")

        self.assertGreaterEqual(loaded, 81, f"Expected 81+ agents, got {loaded}")
        self.assertEqual(len(errors), 0, f"Errors: {errors}")

    def test_agents_have_tools(self):
        """الوكلاء لديهم أدوات مربوطة"""
        from core.base_agent import load_agent_from_json
        from tools.registry import build_tools_registry

        registry = build_tools_registry()
        agents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")

        agents_with_tools = 0
        total_agents = 0

        for root, dirs, files in os.walk(agents_dir):
            for fname in files:
                if fname.endswith(".json"):
                    path = os.path.join(root, fname)
                    try:
                        agent = load_agent_from_json(path, registry)
                        total_agents += 1
                        if agent.tools:
                            agents_with_tools += 1
                    except Exception:
                        pass

        # على الأقل 50% من الوكلاء لديهم أدوات
        self.assertGreater(agents_with_tools, total_agents * 0.5,
                          f"Only {agents_with_tools}/{total_agents} have tools")

    def test_agents_have_system_prompts(self):
        """كل وكيل لديه system prompt"""
        agents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")

        for root, dirs, files in os.walk(agents_dir):
            for fname in files:
                if fname.endswith(".json"):
                    path = os.path.join(root, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    prompt = data.get("system_prompt", "")
                    self.assertGreater(len(prompt), 50,
                                      f"{fname} has short system_prompt ({len(prompt)} chars)")

    def test_agent_categories_covered(self):
        """كل الفئات ممثلة"""
        agents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
        categories = set()

        for root, dirs, files in os.walk(agents_dir):
            for fname in files:
                if fname.endswith(".json"):
                    path = os.path.join(root, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    categories.add(data.get("category", ""))

        self.assertGreaterEqual(len(categories), 6, f"Only {len(categories)} categories")


class TestPhase3Infrastructure(unittest.TestCase):
    """المرحلة 3: البنية التحتية"""

    def test_firestore_memory_import(self):
        """Firestore memory يُستورد"""
        from core.firestore_memory import FirestoreMemory, get_firestore_memory
        mem = get_firestore_memory()
        self.assertIsNotNone(mem)
        self.assertFalse(mem.is_cloud)  # لا يوجد GCP_PROJECT_ID

    def test_firestore_memory_local_ops(self):
        """عمليات الذاكرة المحلية تعمل"""
        from core.firestore_memory import FirestoreMemory
        mem = FirestoreMemory()

        # حفظ واسترجاع
        result = mem.store_episode("A01", "test task", "test result", success=True)
        self.assertIn("local:", result)

        episodes = mem.get_agent_episodes("A01", limit=5)
        self.assertIsInstance(episodes, list)

    def test_firestore_memory_status(self):
        """حالة الذاكرة"""
        from core.firestore_memory import get_firestore_memory
        status = get_firestore_memory().status()
        self.assertIn("backend", status)
        self.assertIn("collections", status)

    def test_pubsub_import(self):
        """Pub/Sub يُستورد"""
        from core.pubsub_comm import PubSubComm, get_pubsub
        ps = get_pubsub()
        self.assertIsNotNone(ps)
        self.assertFalse(ps.is_cloud)

    def test_pubsub_local_messaging(self):
        """رسائل محلية تعمل"""
        from core.pubsub_comm import PubSubComm
        ps = PubSubComm()

        # نشر رسالة
        result = ps.publish("test-topic", {
            "type": "task",
            "content": "test message",
            "from_agent": "A01",
        })
        self.assertIn("local:", result)

        # جلب الرسائل
        messages = ps.get_pending_messages("test-topic")
        self.assertGreater(len(messages), 0)
        self.assertEqual(messages[0]["from_agent"], "A01")

    def test_pubsub_publish_task(self):
        """نشر مهمة"""
        from core.pubsub_comm import PubSubComm
        ps = PubSubComm()
        result = ps.publish_task("A01", "A04", "اجمع أخبار التقنية")
        self.assertIn("local:", result)

    def test_pubsub_status(self):
        """حالة Pub/Sub"""
        from core.pubsub_comm import get_pubsub
        status = get_pubsub().status()
        self.assertIn("backend", status)
        self.assertEqual(status["backend"], "local_queue")

    def test_deploy_script_exists(self):
        """سكربت النشر موجود"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    "scripts", "deploy_cloudrun.sh")
        self.assertTrue(os.path.exists(script_path))

    def test_scheduler_script_exists(self):
        """سكربت الجدولة موجود"""
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    "scripts", "setup_scheduler.py")
        self.assertTrue(os.path.exists(script_path))

    def test_scheduler_imports(self):
        """setup_scheduler يُستورد"""
        from scripts.setup_scheduler import (
            setup_cloud_scheduler, setup_local_scheduler,
            setup_pubsub_topics, setup_firestore
        )
        self.assertTrue(callable(setup_cloud_scheduler))
        self.assertTrue(callable(setup_local_scheduler))


class TestPhase4SelfEvolution(unittest.TestCase):
    """المرحلة 4: التطور الذاتي"""

    def test_agent_monitor_import(self):
        """Agent Monitor يُستورد"""
        from core.agent_monitor import AgentMonitor, get_monitor
        monitor = get_monitor()
        self.assertIsNotNone(monitor)

    def test_agent_monitor_record(self):
        """تسجيل مهمة في المراقب"""
        from core.agent_monitor import AgentMonitor
        monitor = AgentMonitor()

        monitor.record_task("A01", "test task", "test result",
                           success=True, elapsed_seconds=2.5,
                           tokens_used=100, quality_score=8)

        perf = monitor.get_agent_performance("A01")
        self.assertEqual(perf["tasks_total"], 1)
        self.assertEqual(perf["success_rate"], 1.0)

    def test_agent_monitor_multiple_records(self):
        """مراقبة عدة مهام"""
        from core.agent_monitor import AgentMonitor
        monitor = AgentMonitor()

        for i in range(10):
            monitor.record_task("A02", f"task {i}", f"result {i}",
                               success=(i % 3 != 0),
                               elapsed_seconds=float(i + 1),
                               quality_score=7)

        perf = monitor.get_agent_performance("A02")
        self.assertEqual(perf["tasks_total"], 10)
        self.assertGreater(perf["success_rate"], 0)
        self.assertLess(perf["success_rate"], 1)

    def test_agent_monitor_overview(self):
        """نظرة عامة على النظام"""
        from core.agent_monitor import AgentMonitor
        monitor = AgentMonitor()

        # أضف بيانات
        for aid in ["A01", "A04", "A07"]:
            for i in range(5):
                monitor.record_task(aid, f"task {i}", f"result {i}",
                                   success=True, elapsed_seconds=2.0)

        overview = monitor.get_system_overview()
        self.assertEqual(overview["agents_monitored"], 3)
        self.assertGreater(overview["total_tasks"], 0)

    def test_agent_monitor_leaderboard(self):
        """ترتيب الوكلاء"""
        from core.agent_monitor import AgentMonitor
        monitor = AgentMonitor()

        for aid in ["A01", "A04", "A07"]:
            for i in range(6):
                monitor.record_task(aid, f"task {i}", f"result {i}",
                                   success=(aid != "A07" or i > 2),
                                   elapsed_seconds=2.0)

        leaderboard = monitor.get_leaderboard()
        self.assertIsInstance(leaderboard, list)

    def test_agent_monitor_report(self):
        """تقرير التحسينات"""
        from core.agent_monitor import AgentMonitor
        monitor = AgentMonitor()

        for i in range(10):
            monitor.record_task("A01", f"task {i}", f"result {i}",
                               success=True, elapsed_seconds=2.0)

        report = monitor.generate_improvement_report()
        self.assertIn("تقرير", report)

    def test_auto_prompt_optimizer_import(self):
        """Auto Prompt Optimizer يُستورد"""
        from core.auto_prompt_optimizer import AutoPromptOptimizer, get_auto_optimizer
        opt = get_auto_optimizer()
        self.assertIsNotNone(opt)

    def test_auto_prompt_optimizer_analyze(self):
        """تحليل وكيل"""
        from core.auto_prompt_optimizer import AutoPromptOptimizer
        opt = AutoPromptOptimizer()

        history = [
            {"task": "بحث عن AI", "result": "نتيجة جيدة", "success": True, "quality_score": 8},
            {"task": "تحليل اقتصادي", "result": "خطأ في البيانات", "success": False, "quality_score": 2},
            {"task": "بحث علمي", "result": "نتيجة ممتازة", "success": True, "quality_score": 9},
        ]

        analysis = opt.analyze_agent("A01", history)
        self.assertEqual(analysis["tasks_analyzed"], 3)
        self.assertIsInstance(analysis["suggestions"], list)

    def test_auto_prompt_optimizer_batch(self):
        """تحليل دفعي"""
        from core.auto_prompt_optimizer import AutoPromptOptimizer
        opt = AutoPromptOptimizer()

        data = {
            "A01": [{"task": "t", "result": "r", "success": True}] * 5,
            "A04": [{"task": "t", "result": "خطأ", "success": False}] * 5,
        }

        result = opt.batch_analyze(data)
        self.assertEqual(result["agents_analyzed"], 2)

    def test_lesson_collector_import(self):
        """Lesson Collector يُستورد"""
        from core.lesson_collector import LessonCollector, get_lesson_collector
        lc = get_lesson_collector()
        self.assertIsNotNone(lc)

    def test_lesson_collector_collect(self):
        """جمع درس"""
        from core.lesson_collector import LessonCollector
        lc = LessonCollector()

        lesson_id = lc.collect("A01", "test task", "test result",
                               success=True, importance=7,
                               tags=["test", "ai"])
        self.assertTrue(lesson_id.startswith("L"))

    def test_lesson_collector_retrieve(self):
        """استرجاع دروس"""
        from core.lesson_collector import LessonCollector
        lc = LessonCollector()

        lc.collect("A01", "task about AI", "great result", success=True, importance=8)
        lc.collect("A01", "task about economy", "error", success=False, importance=6)

        lessons = lc.get_lessons_for_agent("A01")
        self.assertGreater(len(lessons), 0)

    def test_lesson_collector_context(self):
        """حقن سياق الدروس"""
        from core.lesson_collector import LessonCollector
        lc = LessonCollector()

        lc.collect("A01", "AI research task", "excellent analysis",
                   success=True, importance=9)

        context = lc.inject_lessons_context("A01", "AI research new topic")
        # May or may not have context depending on matching
        self.assertIsInstance(context, str)

    def test_lesson_collector_summary(self):
        """ملخص الدروس"""
        from core.lesson_collector import LessonCollector
        lc = LessonCollector()

        for i in range(5):
            lc.collect(f"A0{i+1}", f"task {i}", f"result {i}", success=True)

        summary = lc.get_summary()
        self.assertGreater(summary["total_lessons"], 0)
        self.assertIn("by_type", summary)


class TestGatewayIntegration(unittest.TestCase):
    """اختبار تكامل Gateway"""

    def test_gateway_import(self):
        """Gateway يُستورد"""
        from gateway.app import app
        self.assertIsNotNone(app)


if __name__ == "__main__":
    print("=" * 60)
    print("Army81 — Comprehensive Tests (All Phases)")
    print("=" * 60)
    unittest.main(verbosity=2)
