"""
Army81 Smart Router - بوابة التوجيه الذكي
يستقبل المهام ويوجهها للوكيل المناسب بالنموذج المناسب
"""
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("army81.router")


class SmartRouter:
    """
    البوابة الذكية التي تستقبل كل المهام وتوزعها.
    تعمل كـ "مدير المشروع" الذي يعرف قدرات كل وكيل.
    """

    def __init__(self, agents_registry: Dict = None):
        self.agents = agents_registry or {}
        self.task_log: List[Dict] = []
        self.routing_stats = {
            "total_routed": 0,
            "by_category": {},
            "by_model": {},
            "avg_routing_time_ms": 0,
        }

    def register_agent(self, agent):
        """تسجيل وكيل في النظام"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")

    def register_agents(self, agents_list):
        """تسجيل قائمة وكلاء"""
        for agent in agents_list:
            self.register_agent(agent)

    def route(self, task: str, context: Dict = None, preferred_agent: str = None,
              preferred_category: str = None) -> Dict:
        """
        توجيه مهمة للوكيل المناسب.
        1. إذا حُدد وكيل معين، يُرسل له مباشرة
        2. إذا حُددت فئة، يختار أفضل وكيل فيها
        3. وإلا، يحلل المهمة ويختار تلقائياً
        """
        start = time.time()
        context = context or {}

        # 1. وكيل محدد
        if preferred_agent and preferred_agent in self.agents:
            agent = self.agents[preferred_agent]
            result = agent.run(task, context)
            self._log_routing(task, agent.agent_id, result, time.time() - start)
            return result

        # 2. فئة محددة
        if preferred_category:
            agent = self._best_agent_in_category(preferred_category, task)
            if agent:
                result = agent.run(task, context)
                self._log_routing(task, agent.agent_id, result, time.time() - start)
                return result

        # 3. توجيه تلقائي
        agent = self._auto_route(task, context)
        result = agent.run(task, context)
        self._log_routing(task, agent.agent_id, result, time.time() - start)
        return result

    def broadcast(self, task: str, category: str = None, context: Dict = None) -> List[Dict]:
        """إرسال مهمة لكل الوكلاء في فئة (أو كل الوكلاء)"""
        results = []
        targets = self.agents.values()
        if category:
            targets = [a for a in targets if a.category == category]

        for agent in targets:
            result = agent.run(task, context or {})
            results.append(result)

        return results

    def pipeline(self, task: str, agent_chain: List[str], context: Dict = None) -> Dict:
        """
        تنفيذ مهمة عبر سلسلة وكلاء (pipeline).
        نتيجة كل وكيل تصبح مدخل الوكيل التالي.
        """
        context = context or {}
        current_input = task
        all_results = []

        for agent_id in agent_chain:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found in pipeline, skipping")
                continue

            agent = self.agents[agent_id]
            context["pipeline_history"] = all_results
            result = agent.run(current_input, context)
            all_results.append(result)

            if result["status"] == "error":
                return {
                    "status": "pipeline_error",
                    "failed_at": agent_id,
                    "results": all_results,
                }

            current_input = f"نتيجة الخطوة السابقة ({agent.name}):\n{result['result']}\n\nأكمل المهمة الأصلية: {task}"

        return {
            "status": "success",
            "final_result": all_results[-1] if all_results else None,
            "pipeline_results": all_results,
        }

    def _auto_route(self, task: str, context: Dict):
        """توجيه تلقائي بناءً على تحليل المهمة"""
        task_lower = task.lower()

        # قواعد بسيطة وسريعة للتوجيه
        routing_rules = [
            (["كود", "برمج", "code", "program", "debug", "api", "script"], "cat2_engineering"),
            (["بحث", "research", "ابحث", "find", "search", "paper"], "cat3_research"),
            (["اكتب", "write", "محتوى", "content", "مقال", "article", "ترجم"], "cat4_creative"),
            (["خطة", "plan", "استراتيج", "strateg", "قرار", "decision", "قيادة"], "cat1_leadership"),
            (["أتمت", "automat", "جدول", "schedule", "مشروع", "project", "تقرير"], "cat5_operations"),
            (["أمن", "secur", "اختبر", "test", "جودة", "quality", "audit"], "cat6_security"),
            (["حسّن", "improve", "طوّر", "evolve", "تعلم", "learn", "skill"], "cat7_evolution"),
        ]

        for keywords, category in routing_rules:
            if any(kw in task_lower for kw in keywords):
                agent = self._best_agent_in_category(category, task)
                if agent:
                    return agent

        # افتراضي: وكيل القيادة الاستراتيجية
        return self._best_agent_in_category("cat1_leadership", task) or list(self.agents.values())[0]

    def _best_agent_in_category(self, category: str, task: str):
        """اختيار أفضل وكيل في فئة معينة"""
        candidates = [a for a in self.agents.values() if a.category == category]
        if not candidates:
            return None

        # اختيار الوكيل الأقل انشغالاً (أقل مهام منجزة مؤخراً)
        candidates.sort(key=lambda a: a.stats.get("tasks_completed", 0))
        return candidates[0]

    def _log_routing(self, task: str, agent_id: str, result: Dict, routing_time: float):
        """تسجيل عملية التوجيه"""
        self.routing_stats["total_routed"] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_preview": task[:200],
            "agent_id": agent_id,
            "status": result.get("status", "unknown"),
            "routing_time_ms": round(routing_time * 1000, 2),
        }
        self.task_log.append(entry)

        # تحديث الإحصائيات
        cat = self.agents.get(agent_id, None)
        if cat:
            cat_name = cat.category
            self.routing_stats["by_category"][cat_name] = self.routing_stats["by_category"].get(cat_name, 0) + 1

    def get_status(self) -> Dict:
        """حالة النظام الكاملة"""
        return {
            "total_agents": len(self.agents),
            "agents_by_category": self._count_by_category(),
            "routing_stats": self.routing_stats,
            "agents_status": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "category": a.category,
                    "model": a.model,
                    "tasks_done": a.stats["tasks_completed"],
                    "last_active": a.stats.get("last_active"),
                }
                for a in self.agents.values()
            ],
        }

    def _count_by_category(self) -> Dict:
        counts = {}
        for agent in self.agents.values():
            counts[agent.category] = counts.get(agent.category, 0) + 1
        return counts
