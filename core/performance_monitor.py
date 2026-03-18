"""
Army81 - Performance Monitor
مراقبة أداء الوكلاء وتحديد من يحتاج تحسين
المرحلة 4: التطور الذاتي
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.performance")

_WORKSPACE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
)
_REPORTS_DIR = os.path.join(_WORKSPACE, "performance_reports")


class PerformanceMonitor:
    """
    يراقب أداء كل 81 وكيل:
    - معدل النجاح
    - متوسط وقت الاستجابة
    - استهلاك التوكنات
    - جودة الردود (من التقييمات)
    """

    def __init__(self, router=None):
        self.router = router
        self._thresholds = {
            "min_success_rate": 0.7,     # أقل من 70% = يحتاج تحسين
            "max_avg_response_time": 30,  # أكثر من 30 ثانية = بطيء
            "min_tasks_for_eval": 3,     # أقل من 3 مهام = غير كافي
        }

    def set_router(self, router):
        """ربط الروتر"""
        self.router = router

    def evaluate_agent(self, agent) -> Dict:
        """تقييم أداء وكيل واحد"""
        stats = agent.stats
        tasks_done = stats.get("tasks_done", 0)
        tasks_failed = stats.get("tasks_failed", 0)
        total = tasks_done + tasks_failed

        # معدل النجاح
        success_rate = tasks_done / total if total > 0 else 0

        # تقييم
        issues = []
        score = 100

        if total >= self._thresholds["min_tasks_for_eval"]:
            if success_rate < self._thresholds["min_success_rate"]:
                issues.append(f"معدل نجاح منخفض: {success_rate:.0%}")
                score -= 30

            if tasks_failed > tasks_done:
                issues.append("عدد الإخفاقات أكثر من النجاحات")
                score -= 20
        else:
            issues.append(f"بيانات غير كافية ({total} مهام فقط)")

        # تقييم حسب عدد الأدوات
        if not agent.tools:
            issues.append("لا أدوات متاحة")
            score -= 10

        # تحديد الحالة
        if score >= 80:
            status = "excellent"
        elif score >= 60:
            status = "good"
        elif score >= 40:
            status = "needs_improvement"
        else:
            status = "critical"

        return {
            "agent_id": agent.agent_id,
            "name": agent.name_ar,
            "category": agent.category,
            "model": agent.model_alias,
            "tasks_done": tasks_done,
            "tasks_failed": tasks_failed,
            "success_rate": round(success_rate, 3),
            "tools_count": len(agent.tools),
            "score": max(0, score),
            "status": status,
            "issues": issues,
        }

    def generate_report(self) -> Dict:
        """إنشاء تقرير أداء شامل"""
        if not self.router:
            return {"error": "الروتر غير متصل"}

        agents = self.router.agents
        evaluations = []
        categories = {}

        for agent_id, agent in agents.items():
            eval_result = self.evaluate_agent(agent)
            evaluations.append(eval_result)

            cat = agent.category
            if cat not in categories:
                categories[cat] = {"agents": 0, "total_tasks": 0,
                                   "total_score": 0, "issues": 0}
            categories[cat]["agents"] += 1
            categories[cat]["total_tasks"] += eval_result["tasks_done"] + eval_result["tasks_failed"]
            categories[cat]["total_score"] += eval_result["score"]
            categories[cat]["issues"] += len(eval_result["issues"])

        # ترتيب حسب الأداء
        evaluations.sort(key=lambda x: x["score"])

        # أضعف الوكلاء
        weakest = [e for e in evaluations if e["status"] in ("critical", "needs_improvement")]

        # أفضل الوكلاء
        best = sorted(evaluations, key=lambda x: x["score"], reverse=True)[:10]

        # متوسطات الفئات
        for cat, data in categories.items():
            if data["agents"] > 0:
                data["avg_score"] = round(data["total_score"] / data["agents"], 1)

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(agents),
            "summary": {
                "excellent": len([e for e in evaluations if e["status"] == "excellent"]),
                "good": len([e for e in evaluations if e["status"] == "good"]),
                "needs_improvement": len([e for e in evaluations if e["status"] == "needs_improvement"]),
                "critical": len([e for e in evaluations if e["status"] == "critical"]),
            },
            "categories": categories,
            "weakest_agents": weakest[:10],
            "best_agents": best,
            "all_evaluations": evaluations,
        }

        # حفظ التقرير
        self._save_report(report)

        return report

    def get_improvement_suggestions(self) -> List[Dict]:
        """اقتراحات تحسين للوكلاء الأضعف"""
        report = self.generate_report()
        suggestions = []

        for agent_eval in report.get("weakest_agents", []):
            agent_id = agent_eval["agent_id"]
            suggestion = {
                "agent_id": agent_id,
                "name": agent_eval["name"],
                "current_score": agent_eval["score"],
                "issues": agent_eval["issues"],
                "recommendations": [],
            }

            # اقتراحات بناءً على المشاكل
            if agent_eval["success_rate"] < 0.5:
                suggestion["recommendations"].append(
                    "مراجعة system_prompt — قد يكون غير واضح أو معقد جداً"
                )
                suggestion["recommendations"].append(
                    "إضافة أمثلة ناجحة في prompt (few-shot)"
                )

            if agent_eval["tools_count"] == 0:
                suggestion["recommendations"].append(
                    "ربط أدوات مناسبة — راجع agents/registry.py"
                )

            if not suggestion["recommendations"]:
                suggestion["recommendations"].append(
                    "تشغيل المزيد من المهام لجمع بيانات كافية"
                )

            suggestions.append(suggestion)

        return suggestions

    def compare_agents(self, agent_ids: List[str]) -> Dict:
        """مقارنة بين مجموعة وكلاء"""
        if not self.router:
            return {"error": "الروتر غير متصل"}

        results = []
        for aid in agent_ids:
            if aid in self.router.agents:
                results.append(self.evaluate_agent(self.router.agents[aid]))

        return {
            "agents": results,
            "best": max(results, key=lambda x: x["score"]) if results else None,
            "worst": min(results, key=lambda x: x["score"]) if results else None,
        }

    def _save_report(self, report: Dict):
        """حفظ تقرير الأداء"""
        os.makedirs(_REPORTS_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        path = os.path.join(_REPORTS_DIR, f"performance_{date_str}.json")

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"Performance report saved: {path}")
        except Exception as e:
            logger.error(f"Save report error: {e}")

    def get_latest_report(self) -> Optional[Dict]:
        """قراءة آخر تقرير أداء"""
        report_dir = Path(_REPORTS_DIR)
        if not report_dir.exists():
            return None

        reports = sorted(report_dir.glob("performance_*.json"), reverse=True)
        if not reports:
            return None

        try:
            with open(reports[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None


if __name__ == "__main__":
    monitor = PerformanceMonitor()
    print("Performance Monitor ready.")
    print("Connect router via monitor.set_router(router) then call monitor.generate_report()")
