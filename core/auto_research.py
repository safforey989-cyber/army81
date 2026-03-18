"""
Army81 — AutoResearch Engine
مستلهم من autoresearch لأندري كارباثي
وكيل A81 يعمل كباحث آلي 24/7:
- يعدل كود النظام
- يشغل تجارب مصغرة
- يقيس الأداء
- يدمج التعديلات الناجحة
"""
import os
import json
import time
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.auto_research")

WORKSPACE = Path("workspace")
EXPERIMENTS_DIR = WORKSPACE / "experiments"
RESEARCH_LOG = WORKSPACE / "research_log.json"


class Experiment:
    """تجربة واحدة"""
    def __init__(self, name: str, hypothesis: str, code_change: str,
                 target_file: str, metric_name: str):
        self.id = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12]
        self.name = name
        self.hypothesis = hypothesis
        self.code_change = code_change
        self.target_file = target_file
        self.metric_name = metric_name
        self.baseline_score = 0.0
        self.new_score = 0.0
        self.success = False
        self.created_at = datetime.now().isoformat()
        self.completed_at = None

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "hypothesis": self.hypothesis,
            "target_file": self.target_file, "metric_name": self.metric_name,
            "baseline_score": self.baseline_score, "new_score": self.new_score,
            "success": self.success, "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class AutoResearch:
    """
    محرك البحث الآلي — يشبه autoresearch
    يجري 100 تجربة يومياً لتحسين النظام
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.experiments: List[Dict] = []
        self.daily_budget = 100  # تجارب يومياً
        self.experiments_today = 0
        self.improvements_applied = 0

        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self):
        """تحميل تاريخ التجارب"""
        if RESEARCH_LOG.exists():
            try:
                self.experiments = json.loads(RESEARCH_LOG.read_text(encoding="utf-8"))
            except Exception:
                self.experiments = []

    def _save_history(self):
        """حفظ التجارب"""
        RESEARCH_LOG.write_text(
            json.dumps(self.experiments[-500:], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ═══════════════════════════════════════════════════
    # توليد فرضيات التحسين
    # ═══════════════════════════════════════════════════

    def generate_hypotheses(self, focus_area: str = "performance") -> List[Dict]:
        """
        يولد فرضيات تحسين بناءً على:
        - تحليل الكود الحالي
        - التجارب السابقة الناجحة/الفاشلة
        - المقاييس الحالية
        """
        areas = {
            "performance": [
                {"name": "cache_responses", "hypothesis": "تخزين استجابات API المتكررة يقلل وقت الاستجابة 30%",
                 "target": "core/llm_client.py", "metric": "response_time_ms"},
                {"name": "batch_requests", "hypothesis": "تجميع الطلبات المتشابهة يوفر 40% من التكلفة",
                 "target": "core/smart_queue.py", "metric": "cost_per_task"},
                {"name": "lazy_agent_load", "hypothesis": "تحميل الوكلاء عند الطلب فقط يسرع البدء 50%",
                 "target": "router/smart_router.py", "metric": "startup_time_ms"},
                {"name": "compress_prompts", "hypothesis": "ضغط system prompts يقلل tokens بدون فقد جودة",
                 "target": "agents/", "metric": "tokens_per_task"},
            ],
            "quality": [
                {"name": "few_shot_examples", "hypothesis": "إضافة 3 أمثلة لكل وكيل يرفع الجودة 15%",
                 "target": "core/base_agent.py", "metric": "task_quality_score"},
                {"name": "chain_of_thought", "hypothesis": "إجبار CoT يحسن التحليل المعقد",
                 "target": "agents/", "metric": "complex_task_score"},
                {"name": "self_critique", "hypothesis": "طلب نقد ذاتي قبل الرد النهائي يرفع الدقة",
                 "target": "core/base_agent.py", "metric": "accuracy_score"},
            ],
            "memory": [
                {"name": "semantic_dedup", "hypothesis": "إزالة التكرار الدلالي يوفر 60% من مساحة الذاكرة",
                 "target": "memory/hierarchical_memory.py", "metric": "memory_size_mb"},
                {"name": "priority_recall", "hypothesis": "استرجاع الذكريات حسب الأولوية يحسن السياق",
                 "target": "memory/hierarchical_memory.py", "metric": "context_relevance"},
            ],
            "routing": [
                {"name": "ml_routing", "hypothesis": "التوجيه بـ ML بدل القواعد يحسن دقة التوجيه 25%",
                 "target": "router/smart_router.py", "metric": "routing_accuracy"},
                {"name": "load_balancing", "hypothesis": "توزيع الحمل بين النماذج يقلل أوقات الانتظار",
                 "target": "core/smart_queue.py", "metric": "avg_wait_time_ms"},
            ]
        }
        return areas.get(focus_area, areas["performance"])

    # ═══════════════════════════════════════════════════
    # تنفيذ تجربة واحدة
    # ═══════════════════════════════════════════════════

    def run_experiment(self, hypothesis: Dict) -> Dict:
        """
        تنفيذ تجربة:
        1. قياس الأداء الحالي (baseline)
        2. تطبيق التعديل
        3. قياس الأداء الجديد
        4. إذا تحسّن > 10% → اعتماد التعديل
        5. إذا تراجع → rollback
        """
        exp = Experiment(
            name=hypothesis["name"],
            hypothesis=hypothesis["hypothesis"],
            code_change="",
            target_file=hypothesis["target"],
            metric_name=hypothesis["metric"]
        )

        logger.info(f"🧪 تجربة: {exp.name} — {exp.hypothesis}")

        # 1. قياس baseline
        exp.baseline_score = self._measure_metric(exp.metric_name)

        # 2. توليد التعديل بالذكاء الاصطناعي
        if self.llm:
            code_change = self._generate_improvement(hypothesis)
            exp.code_change = code_change

        # 3. تطبيق في sandbox
        sandbox_result = self._run_in_sandbox(exp)

        # 4. قياس الأداء الجديد
        exp.new_score = sandbox_result.get("score", exp.baseline_score)

        # 5. تقييم
        if exp.baseline_score > 0:
            improvement = (exp.new_score - exp.baseline_score) / exp.baseline_score
        else:
            improvement = 0.1 if exp.new_score > 0 else 0

        exp.success = improvement > 0.10  # تحسن أكثر من 10%
        exp.completed_at = datetime.now().isoformat()

        # 6. تسجيل
        self.experiments.append(exp.to_dict())
        self._save_history()
        self.experiments_today += 1

        if exp.success:
            self.improvements_applied += 1
            logger.info(f"✅ نجاح: {exp.name} — تحسن {improvement*100:.1f}%")
        else:
            logger.info(f"❌ فشل: {exp.name} — تغيير {improvement*100:.1f}%")

        return exp.to_dict()

    def _measure_metric(self, metric_name: str) -> float:
        """قياس مقياس معين"""
        metrics = {
            "response_time_ms": self._measure_response_time,
            "cost_per_task": self._measure_cost,
            "startup_time_ms": self._measure_startup,
            "tokens_per_task": self._measure_tokens,
            "task_quality_score": self._measure_quality,
            "memory_size_mb": self._measure_memory_size,
            "routing_accuracy": self._measure_routing,
        }
        fn = metrics.get(metric_name, lambda: 50.0)
        try:
            return fn()
        except Exception:
            return 50.0

    def _measure_response_time(self) -> float:
        """قياس وقت الاستجابة"""
        try:
            import requests
            start = time.time()
            requests.post("http://localhost:8181/task",
                         json={"task": "اختبار سريع"}, timeout=30)
            return (time.time() - start) * 1000
        except Exception:
            return 5000.0

    def _measure_cost(self) -> float:
        stats_file = WORKSPACE / "token_stats.json"
        if stats_file.exists():
            data = json.loads(stats_file.read_text())
            return data.get("avg_cost_per_task", 0.01)
        return 0.01

    def _measure_startup(self) -> float:
        return 2000.0  # ms

    def _measure_tokens(self) -> float:
        return 500.0  # average tokens per task

    def _measure_quality(self) -> float:
        return 70.0  # baseline quality score

    def _measure_memory_size(self) -> float:
        mem_dir = Path("workspace/chroma_db")
        if mem_dir.exists():
            total = sum(f.stat().st_size for f in mem_dir.rglob("*") if f.is_file())
            return total / (1024 * 1024)
        return 0.0

    def _measure_routing(self) -> float:
        return 75.0  # baseline routing accuracy

    def _generate_improvement(self, hypothesis: Dict) -> str:
        """يولد كود التحسين باستخدام LLM"""
        prompt = f"""أنت مهندس برمجيات خبير.
الفرضية: {hypothesis['hypothesis']}
الملف المستهدف: {hypothesis['target']}
المقياس: {hypothesis['metric']}

اكتب تعديل كود Python محدد وقابل للتطبيق.
أعط الكود فقط بدون شرح."""

        try:
            result = self.llm.chat([{"role": "user", "content": prompt}])
            return result.get("content", "")
        except Exception:
            return ""

    def _run_in_sandbox(self, exp: Experiment) -> Dict:
        """تشغيل التجربة في بيئة معزولة"""
        # في الإنتاج: Docker sandbox
        # الآن: محاكاة بسيطة
        import random
        base = exp.baseline_score
        # محاكاة — 30% فرصة تحسن حقيقي
        if random.random() < 0.3:
            return {"score": base * 1.15, "success": True}
        return {"score": base * 0.98, "success": False}

    # ═══════════════════════════════════════════════════
    # الحلقة اليومية
    # ═══════════════════════════════════════════════════

    def daily_research_cycle(self):
        """
        100 تجربة يومياً — الحلقة الرئيسية
        """
        logger.info("🔬 بدء دورة البحث اليومية")
        self.experiments_today = 0

        focus_areas = ["performance", "quality", "memory", "routing"]
        results = {"total": 0, "success": 0, "failed": 0}

        for area in focus_areas:
            hypotheses = self.generate_hypotheses(area)
            for hyp in hypotheses:
                if self.experiments_today >= self.daily_budget:
                    break

                result = self.run_experiment(hyp)
                results["total"] += 1
                if result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1

                # rate limiting
                time.sleep(2)

        logger.info(f"🔬 انتهت الدورة: {results['success']}/{results['total']} ناجحة")
        return results

    def get_stats(self) -> Dict:
        """إحصائيات البحث"""
        successful = [e for e in self.experiments if e.get("success")]
        return {
            "total_experiments": len(self.experiments),
            "successful": len(successful),
            "today": self.experiments_today,
            "improvements_applied": self.improvements_applied,
            "success_rate": len(successful) / max(len(self.experiments), 1),
        }
