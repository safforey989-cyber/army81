"""
Army81 - Agent Performance Monitor
وكيل مراقبة أداء الوكلاء الآخرين
المرحلة 4: التطور الذاتي
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("army81.monitor")


class AgentMonitor:
    """
    يراقب أداء كل الوكلاء ويُنتج تقارير تحسين
    المهام:
    1. تتبع نسبة النجاح لكل وكيل
    2. قياس سرعة الاستجابة
    3. تحليل جودة الإجابات
    4. اكتشاف الوكلاء الضعيفين
    5. اقتراح تحسينات
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "workspace", "monitor"
        )
        os.makedirs(self.data_dir, exist_ok=True)

        # بيانات المراقبة في الذاكرة
        self._agent_records: Dict[str, List[Dict]] = defaultdict(list)
        self._alerts: List[Dict] = []
        self._recommendations: Dict[str, List[str]] = defaultdict(list)

        # حدود الأداء
        self.thresholds = {
            "min_success_rate": 0.7,        # نسبة نجاح أقل = تنبيه
            "max_avg_response_time": 30.0,   # ثواني
            "min_quality_score": 5.0,        # من 10
            "max_consecutive_failures": 3,   # فشل متتالي
            "min_tasks_for_eval": 5,         # حد أدنى للتقييم
        }

        # تحميل البيانات المحفوظة
        self._load_data()

    def record_task(self, agent_id: str, task: str, result: str,
                    success: bool, elapsed_seconds: float,
                    tokens_used: int = 0, model: str = "",
                    quality_score: int = 0) -> None:
        """تسجيل نتيجة مهمة"""
        record = {
            "task": task[:200],
            "result_preview": result[:200],
            "success": success,
            "elapsed_seconds": elapsed_seconds,
            "tokens_used": tokens_used,
            "model": model,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat(),
        }

        self._agent_records[agent_id].append(record)

        # احتفظ بآخر 100 سجل فقط لكل وكيل
        if len(self._agent_records[agent_id]) > 100:
            self._agent_records[agent_id] = self._agent_records[agent_id][-100:]

        # فحص فوري
        self._check_alerts(agent_id)

    def get_agent_performance(self, agent_id: str) -> Dict:
        """تقرير أداء وكيل واحد"""
        records = self._agent_records.get(agent_id, [])
        if not records:
            return {"agent_id": agent_id, "status": "no_data", "tasks_total": 0}

        total = len(records)
        successes = sum(1 for r in records if r["success"])
        failures = total - successes
        success_rate = successes / total if total > 0 else 0

        times = [r["elapsed_seconds"] for r in records if r["elapsed_seconds"] > 0]
        avg_time = sum(times) / len(times) if times else 0

        tokens = [r["tokens_used"] for r in records if r["tokens_used"] > 0]
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0

        scores = [r["quality_score"] for r in records if r["quality_score"] > 0]
        avg_quality = sum(scores) / len(scores) if scores else 0

        # حساب الاتجاه (آخر 10 مقابل السابق)
        recent = records[-10:]
        older = records[:-10] if len(records) > 10 else []
        trend = "stable"
        if older:
            recent_rate = sum(1 for r in recent if r["success"]) / len(recent)
            older_rate = sum(1 for r in older if r["success"]) / len(older)
            if recent_rate > older_rate + 0.1:
                trend = "improving"
            elif recent_rate < older_rate - 0.1:
                trend = "declining"

        # حالة الأداء
        status = "good"
        if success_rate < self.thresholds["min_success_rate"]:
            status = "needs_attention"
        if success_rate < 0.5:
            status = "critical"

        return {
            "agent_id": agent_id,
            "status": status,
            "trend": trend,
            "tasks_total": total,
            "tasks_success": successes,
            "tasks_failed": failures,
            "success_rate": round(success_rate, 3),
            "avg_response_time": round(avg_time, 2),
            "avg_tokens": round(avg_tokens),
            "avg_quality": round(avg_quality, 1),
            "last_active": records[-1]["timestamp"] if records else None,
            "recommendations": self._recommendations.get(agent_id, []),
        }

    def get_system_overview(self) -> Dict:
        """نظرة عامة على أداء النظام بالكامل"""
        all_agents = list(self._agent_records.keys())
        performances = [self.get_agent_performance(aid) for aid in all_agents]

        if not performances:
            return {"status": "no_data", "agents_monitored": 0}

        active = [p for p in performances if p["tasks_total"] > 0]
        good = [p for p in active if p["status"] == "good"]
        needs_attention = [p for p in active if p["status"] == "needs_attention"]
        critical = [p for p in active if p["status"] == "critical"]

        total_tasks = sum(p["tasks_total"] for p in active)
        total_success = sum(p["tasks_success"] for p in active)
        overall_rate = total_success / total_tasks if total_tasks > 0 else 0

        return {
            "agents_monitored": len(all_agents),
            "agents_active": len(active),
            "agents_good": len(good),
            "agents_needs_attention": len(needs_attention),
            "agents_critical": len(critical),
            "total_tasks": total_tasks,
            "total_success": total_success,
            "overall_success_rate": round(overall_rate, 3),
            "alerts_count": len(self._alerts),
            "top_agents": sorted(active, key=lambda x: x["success_rate"], reverse=True)[:5],
            "weak_agents": sorted(active, key=lambda x: x["success_rate"])[:5],
            "timestamp": datetime.now().isoformat(),
        }

    def get_leaderboard(self, limit: int = 20) -> List[Dict]:
        """ترتيب الوكلاء حسب الأداء"""
        performances = []
        for agent_id in self._agent_records:
            perf = self.get_agent_performance(agent_id)
            if perf["tasks_total"] >= self.thresholds["min_tasks_for_eval"]:
                # درجة مركبة: نجاح 60% + سرعة 20% + جودة 20%
                score = (
                    perf["success_rate"] * 60 +
                    max(0, (30 - perf["avg_response_time"]) / 30 * 20) +
                    (perf["avg_quality"] / 10 * 20) if perf["avg_quality"] > 0 else 0
                )
                perf["composite_score"] = round(score, 1)
                performances.append(perf)

        return sorted(performances, key=lambda x: x.get("composite_score", 0), reverse=True)[:limit]

    def get_alerts(self, limit: int = 20) -> List[Dict]:
        """التنبيهات النشطة"""
        return self._alerts[-limit:]

    def generate_improvement_report(self) -> str:
        """تقرير تحسينات مفصل"""
        overview = self.get_system_overview()
        if overview.get("status") == "no_data":
            return "لا توجد بيانات كافية لإنتاج تقرير"

        lines = [
            f"# تقرير مراقبة الأداء — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"## نظرة عامة",
            f"- وكلاء نشطون: {overview['agents_active']}",
            f"- مهام منفذة: {overview['total_tasks']}",
            f"- نسبة النجاح الإجمالية: {overview['overall_success_rate']*100:.1f}%",
            f"- وكلاء بحالة جيدة: {overview['agents_good']}",
            f"- وكلاء تحتاج اهتمام: {overview['agents_needs_attention']}",
            f"- وكلاء في حالة حرجة: {overview['agents_critical']}",
            "",
        ]

        # أفضل الوكلاء
        if overview.get("top_agents"):
            lines.append("## أفضل الوكلاء")
            for p in overview["top_agents"][:3]:
                lines.append(
                    f"- **{p['agent_id']}**: نجاح {p['success_rate']*100:.0f}% "
                    f"({p['tasks_total']} مهمة) — {p['trend']}"
                )
            lines.append("")

        # الوكلاء الضعيفون
        if overview.get("weak_agents"):
            lines.append("## وكلاء تحتاج تحسين")
            for p in overview["weak_agents"][:3]:
                if p["success_rate"] < self.thresholds["min_success_rate"]:
                    recs = self._generate_recommendations(p["agent_id"])
                    lines.append(
                        f"- **{p['agent_id']}**: نجاح {p['success_rate']*100:.0f}% — "
                        f"التوصيات: {'; '.join(recs[:2])}"
                    )
            lines.append("")

        # التنبيهات
        if self._alerts:
            lines.append(f"## تنبيهات ({len(self._alerts)})")
            for alert in self._alerts[-5:]:
                lines.append(f"- [{alert['level']}] {alert['agent_id']}: {alert['message']}")
            lines.append("")

        report = "\n".join(lines)

        # حفظ التقرير
        report_path = os.path.join(self.data_dir,
                                    f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        return report

    # ── Private Methods ──────────────────────────────────────────

    def _check_alerts(self, agent_id: str) -> None:
        """فحص وتوليد تنبيهات فورية"""
        records = self._agent_records.get(agent_id, [])
        if len(records) < 3:
            return

        # فشل متتالي
        recent = records[-self.thresholds["max_consecutive_failures"]:]
        if all(not r["success"] for r in recent):
            self._add_alert(agent_id, "warning",
                            f"فشل متتالي {len(recent)} مرات — يحتاج تدخل")

        # نسبة نجاح منخفضة (آخر 10)
        recent_10 = records[-10:]
        if len(recent_10) >= 5:
            rate = sum(1 for r in recent_10 if r["success"]) / len(recent_10)
            if rate < self.thresholds["min_success_rate"]:
                self._add_alert(agent_id, "warning",
                                f"نسبة نجاح منخفضة: {rate*100:.0f}% (آخر {len(recent_10)} مهمة)")

        # بطء شديد
        recent_times = [r["elapsed_seconds"] for r in recent_10 if r["elapsed_seconds"] > 0]
        if recent_times:
            avg = sum(recent_times) / len(recent_times)
            if avg > self.thresholds["max_avg_response_time"]:
                self._add_alert(agent_id, "info",
                                f"متوسط استجابة بطيء: {avg:.1f}s")

    def _add_alert(self, agent_id: str, level: str, message: str) -> None:
        """إضافة تنبيه"""
        # تجنب التكرار في آخر 10 تنبيهات
        for existing in self._alerts[-10:]:
            if existing["agent_id"] == agent_id and existing["message"] == message:
                return

        self._alerts.append({
            "agent_id": agent_id,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })

        # احتفظ بآخر 200 تنبيه
        if len(self._alerts) > 200:
            self._alerts = self._alerts[-200:]

        logger.warning(f"Monitor alert [{level}] {agent_id}: {message}")

    def _generate_recommendations(self, agent_id: str) -> List[str]:
        """توليد توصيات تحسين لوكيل"""
        perf = self.get_agent_performance(agent_id)
        recs = []

        if perf["success_rate"] < 0.5:
            recs.append("مراجعة system prompt وتبسيطه")
            recs.append("تغيير النموذج إلى gemini-pro لمهام أدق")

        if perf["success_rate"] < self.thresholds["min_success_rate"]:
            recs.append("إضافة أمثلة few-shot في system prompt")

        if perf["avg_response_time"] > self.thresholds["max_avg_response_time"]:
            recs.append("تقليل طول system prompt أو التبديل لنموذج أسرع")

        if perf["trend"] == "declining":
            recs.append("مراجعة المهام الأخيرة الفاشلة وتحليل الأنماط")

        if not recs:
            recs.append("الأداء جيد — استمر")

        self._recommendations[agent_id] = recs
        return recs

    def _save_data(self) -> None:
        """حفظ البيانات على القرص"""
        data = {
            "records": dict(self._agent_records),
            "alerts": self._alerts,
            "recommendations": dict(self._recommendations),
            "saved_at": datetime.now().isoformat(),
        }
        filepath = os.path.join(self.data_dir, "monitor_data.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Monitor save error: {e}")

    def _load_data(self) -> None:
        """تحميل البيانات المحفوظة"""
        filepath = os.path.join(self.data_dir, "monitor_data.json")
        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._agent_records = defaultdict(list, data.get("records", {}))
            self._alerts = data.get("alerts", [])
            self._recommendations = defaultdict(list, data.get("recommendations", {}))
            logger.info(f"Monitor data loaded: {len(self._agent_records)} agents")
        except Exception as e:
            logger.error(f"Monitor load error: {e}")


# ── Singleton ──────────────────────────────────────────────────
_instance = None


def get_monitor() -> AgentMonitor:
    """الحصول على instance واحد"""
    global _instance
    if _instance is None:
        _instance = AgentMonitor()
    return _instance
