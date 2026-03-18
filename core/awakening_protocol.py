"""
Army81 — Daily Awakening Protocol + Master Evolution Engine
بروتوكول اليقظة اليومي + محرك التطور الرئيسي
"""
import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.awakening")

WORKSPACE = Path("workspace")
EVOLUTION_LOG = WORKSPACE / "EVOLUTION_LOG.md"


class AwakeningProtocol:
    """
    بروتوكول اليقظة اليومي
    كل يوم الساعة 00:00 — ساعة تطوير ذاتي
    """

    def __init__(self):
        self.cycles_completed = 0
        WORKSPACE.mkdir(exist_ok=True)

    def run_awakening(self, components: Dict = None) -> Dict:
        """
        دورة اليقظة الكاملة — ساعة واحدة:
        1. دمج الكود الجديد (AutoResearch) — 10 min
        2. تحديث النماذج المحلية — 10 min
        3. تبلور الذاكرة — 10 min
        4. إعادة توزيع الميزانيات — 5 min
        5. كتابة تقرير التطور — 5 min
        6. تنظيف الموارد — 5 min
        7. اختبار الصحة — 5 min
        8. إعداد تقرير الصباح — 10 min
        """
        logger.info("🌅 بدء بروتوكول اليقظة")
        start_time = time.time()
        report = {
            "cycle": self.cycles_completed + 1,
            "started_at": datetime.now().isoformat(),
            "phases": {},
        }

        # المرحلة 1: AutoResearch
        report["phases"]["auto_research"] = self._phase_research(components)

        # المرحلة 2: التقطير
        report["phases"]["distillation"] = self._phase_distillation(components)

        # المرحلة 3: تبلور الذاكرة
        report["phases"]["memory_crystal"] = self._phase_crystallize(components)

        # المرحلة 4: اقتصاد الرموز
        report["phases"]["token_economy"] = self._phase_economy(components)

        # المرحلة 5: فحص الصحة
        report["phases"]["health_check"] = self._phase_health()

        # المرحلة 6: تقرير التطور
        report["phases"]["evolution_report"] = self._write_evolution_log(report)

        elapsed = time.time() - start_time
        report["elapsed_seconds"] = elapsed
        report["completed_at"] = datetime.now().isoformat()

        self.cycles_completed += 1
        logger.info(f"🌅 اكتمل بروتوكول اليقظة — {elapsed:.0f}s")

        # حفظ التقرير
        report_file = WORKSPACE / "reports" / f"awakening_{datetime.now().strftime('%Y%m%d')}.json"
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        return report

    def _phase_research(self, components: Dict) -> Dict:
        """AutoResearch"""
        try:
            if components and "auto_research" in components:
                result = components["auto_research"].daily_research_cycle()
                return {"status": "done", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "skipped"}

    def _phase_distillation(self, components: Dict) -> Dict:
        """تقطير المعرفة"""
        try:
            if components and "distillation" in components:
                result = components["distillation"].daily_distillation()
                return {"status": "done", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "skipped"}

    def _phase_crystallize(self, components: Dict) -> Dict:
        """تبلور الذاكرة"""
        try:
            if components and "crystallizer" in components:
                result = components["crystallizer"].daily_crystallization()
                return {"status": "done", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "skipped"}

    def _phase_economy(self, components: Dict) -> Dict:
        """إعادة تعيين الميزانيات"""
        try:
            if components and "economy" in components:
                components["economy"].reset_daily_budgets()
                return {"status": "done"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "skipped"}

    def _phase_health(self) -> Dict:
        """فحص الصحة"""
        health = {"gateway": False, "memory": False, "disk": False}

        # Gateway
        try:
            import requests
            r = requests.get("http://localhost:8181/health", timeout=5)
            health["gateway"] = r.status_code == 200
        except Exception:
            pass

        # Memory
        chroma_dir = WORKSPACE / "chroma_db"
        health["memory"] = chroma_dir.exists()

        # Disk
        import shutil
        disk = shutil.disk_usage("/")
        health["disk"] = disk.free > 1_000_000_000  # > 1GB free
        health["disk_free_gb"] = disk.free / (1024**3)

        return health

    def _write_evolution_log(self, report: Dict) -> Dict:
        """كتابة تقرير التطور"""
        try:
            entry = f"""
## 🌅 يوم {report['cycle']} — {datetime.now().strftime('%Y-%m-%d')}

### المراحل:
"""
            for phase, data in report.get("phases", {}).items():
                status = data.get("status", "unknown")
                emoji = "✅" if status == "done" else "❌" if status == "error" else "⏭️"
                entry += f"- {emoji} {phase}: {status}\n"

            entry += "\n---\n"

            # إلحاق بالملف
            existing = ""
            if EVOLUTION_LOG.exists():
                existing = EVOLUTION_LOG.read_text(encoding="utf-8")

            EVOLUTION_LOG.write_text(
                f"# Army81 — سجل التطور\n\n{entry}\n{existing}",
                encoding="utf-8"
            )
            return {"status": "done"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_stats(self) -> Dict:
        return {"cycles_completed": self.cycles_completed}


class MasterEvolutionEngine:
    """
    محرك التطور الرئيسي — يجمع كل الأنظمة ويشغلها 24/7
    """

    def __init__(self):
        self.running = False
        self.components = {}
        self._init_components()

    def _init_components(self):
        """تهيئة كل المكونات"""
        try:
            from core.auto_research import AutoResearch
            self.components["auto_research"] = AutoResearch()
        except ImportError:
            pass

        try:
            from core.synthetic_data import SyntheticDataGenerator, SelfPlayEngine
            self.components["synth_data"] = SyntheticDataGenerator()
            self.components["self_play"] = SelfPlayEngine()
        except ImportError:
            pass

        try:
            from core.distillation_engine import DistillationEngine, ModelMerger
            self.components["distillation"] = DistillationEngine()
            self.components["model_merger"] = ModelMerger()
        except ImportError:
            pass

        try:
            from core.web_spiders import WebSpider, ToolCloner, GraphRAG
            self.components["web_spider"] = WebSpider()
            self.components["tool_cloner"] = ToolCloner()
            self.components["graph_rag"] = GraphRAG()
        except ImportError:
            pass

        try:
            from core.prompt_optimizer import PromptOptimizer, MemoryCrystallizer
            self.components["prompt_optimizer"] = PromptOptimizer()
            self.components["crystallizer"] = MemoryCrystallizer()
        except ImportError:
            pass

        try:
            from core.token_economy import TokenEconomy, AdaptiveGuardrails
            self.components["economy"] = TokenEconomy()
            self.components["guardrails"] = AdaptiveGuardrails()
        except ImportError:
            pass

        self.components["awakening"] = AwakeningProtocol()
        logger.info(f"🧬 محرك التطور: {len(self.components)} مكون جاهز")

    def run_daily_cycle(self) -> Dict:
        """الدورة اليومية الكاملة"""
        logger.info("🔄 بدء الدورة اليومية الكاملة")
        results = {"timestamp": datetime.now().isoformat(), "phases": {}}

        # 1. زحف الويب (2 AM)
        if "web_spider" in self.components:
            try:
                results["phases"]["web_crawl"] = self.components["web_spider"].daily_crawl()
            except Exception as e:
                results["phases"]["web_crawl"] = {"error": str(e)}

        # 2. توليد بيانات اصطناعية
        if "synth_data" in self.components:
            try:
                results["phases"]["synth_data"] = self.components["synth_data"].daily_generation_cycle()
            except Exception as e:
                results["phases"]["synth_data"] = {"error": str(e)}

        # 3. تقطير المعرفة (3 AM)
        if "distillation" in self.components:
            try:
                results["phases"]["distillation"] = self.components["distillation"].daily_distillation()
            except Exception as e:
                results["phases"]["distillation"] = {"error": str(e)}

        # 4. بحث آلي (4 AM)
        if "auto_research" in self.components:
            try:
                results["phases"]["auto_research"] = self.components["auto_research"].daily_research_cycle()
            except Exception as e:
                results["phases"]["auto_research"] = {"error": str(e)}

        # 5. تبلور الذاكرة (5 AM)
        if "crystallizer" in self.components:
            try:
                results["phases"]["crystallization"] = self.components["crystallizer"].daily_crystallization()
            except Exception as e:
                results["phases"]["crystallization"] = {"error": str(e)}

        # 6. بطولة Self-Play
        if "self_play" in self.components:
            try:
                results["phases"]["self_play"] = self.components["self_play"].daily_tournament(rounds=5)
            except Exception as e:
                results["phases"]["self_play"] = {"error": str(e)}

        # 7. بروتوكول اليقظة
        if "awakening" in self.components:
            try:
                results["phases"]["awakening"] = self.components["awakening"].run_awakening(self.components)
            except Exception as e:
                results["phases"]["awakening"] = {"error": str(e)}

        # حفظ التقرير
        report_file = WORKSPACE / "reports" / f"daily_evolution_{datetime.now().strftime('%Y%m%d')}.json"
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info(f"🔄 اكتملت الدورة اليومية — {len(results['phases'])} مرحلة")
        return results

    def run_weekly_cycle(self) -> Dict:
        """الدورة الأسبوعية — كل أحد"""
        logger.info("📅 بدء الدورة الأسبوعية")
        results = {}

        # دمج النماذج
        if "model_merger" in self.components:
            try:
                results["model_merge"] = self.components["model_merger"].weekly_merge_cycle()
            except Exception as e:
                results["model_merge"] = {"error": str(e)}

        # تحسين الأوامر
        if "prompt_optimizer" in self.components:
            try:
                results["prompt_optimization"] = self.components["prompt_optimizer"].daily_optimization()
            except Exception as e:
                results["prompt_optimization"] = {"error": str(e)}

        return results

    def get_full_stats(self) -> Dict:
        """إحصائيات شاملة"""
        stats = {"components": {}, "timestamp": datetime.now().isoformat()}
        for name, comp in self.components.items():
            if hasattr(comp, "get_stats"):
                try:
                    stats["components"][name] = comp.get_stats()
                except Exception:
                    stats["components"][name] = {"error": "failed"}
        return stats
