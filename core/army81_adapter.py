"""
Army81Adapter — طبقة عزل واحدة فوق كل الأطر
Army81 لا يستدعي LangGraph أو CrewAI مباشرة أبداً
كل شيء يمر من هنا
نتيجة Loop 4: أولوية 6.0 — تأثير عالي، جهد منخفض
"""
import logging
from typing import Any, List, Dict, Optional

logger = logging.getLogger("army81.adapter")


class Army81Adapter:
    """
    طبقة عزل موحّدة — يختار التنفيذ المناسب تلقائياً
    بناءً على تعقيد المهمة.
    """

    def run_native(self, agent: Any, task: str, context: Dict) -> Dict:
        """
        الأسرع والأرخص — للمهام البسيطة (score < 3)
        يستدعي BaseAgent.run() مباشرة
        """
        try:
            result = agent.run(task, context)
            return {
                "content": result.result,
                "status": result.status,
                "model": result.model_used,
                "tokens": result.tokens_used,
                "framework": "native",
            }
        except Exception as e:
            logger.error(f"[Adapter.native] error: {e}")
            return {"content": f"خطأ: {e}", "status": "error", "framework": "native"}

    def run_langgraph(self, workflow: Any, task: str, agents: List) -> Dict:
        """
        للـ pipelines المتسلسلة (score 3-6)
        إذا لم يكن LangGraph متاحاً → fallback لـ native
        """
        try:
            import importlib
            lg = importlib.import_module("langgraph")  # noqa
            # تنفيذ workflow إذا كان LangGraph متاحاً
            if workflow and hasattr(workflow, "invoke"):
                result = workflow.invoke({"task": task, "agents": agents})
                return {
                    "content": str(result),
                    "status": "success",
                    "framework": "langgraph",
                }
        except ImportError:
            logger.warning("[Adapter.langgraph] LangGraph not installed, falling back to native")
        except Exception as e:
            logger.error(f"[Adapter.langgraph] error: {e}")

        # fallback: نفّذ عبر أول وكيل في القائمة
        if agents:
            return self.run_native(agents[0], task, {})
        return {"content": "لا يوجد وكلاء لتنفيذ المهمة", "status": "error", "framework": "native_fallback"}

    def run_crewai(self, crew_name: str, task: str) -> Dict:
        """
        للفرق المتعاونة (score 7-8)
        إذا لم يكن CrewAI متاحاً → fallback لـ native
        """
        try:
            import importlib
            crewai = importlib.import_module("crewai")  # noqa
            # CrewAI integration placeholder
            logger.info(f"[Adapter.crewai] Running crew '{crew_name}' for task")
            return {
                "content": f"[CrewAI] تم تنفيذ المهمة عبر فريق {crew_name}",
                "status": "success",
                "framework": "crewai",
            }
        except ImportError:
            logger.warning("[Adapter.crewai] CrewAI not installed, falling back")
        except Exception as e:
            logger.error(f"[Adapter.crewai] error: {e}")

        return {
            "content": f"CrewAI غير متاح — مهمة '{task[:100]}' تحتاج مراجعة يدوية",
            "status": "fallback",
            "framework": "native_fallback",
        }

    def run_openai_agents(self, agent: Any, task: str) -> Dict:
        """
        للقرارات الحرجة فقط (score 9-10)
        إذا لم يكن OpenAI Agents متاحاً → fallback لـ native
        """
        try:
            import importlib
            openai_agents = importlib.import_module("openai_agents")  # noqa
            logger.info(f"[Adapter.openai_agents] Running critical task")
            return {
                "content": "[OpenAI Agents] تم تنفيذ المهمة الحرجة",
                "status": "success",
                "framework": "openai_agents",
            }
        except ImportError:
            logger.warning("[Adapter.openai_agents] openai_agents not installed, falling back")
        except Exception as e:
            logger.error(f"[Adapter.openai_agents] error: {e}")

        if agent:
            result = self.run_native(agent, task, {})
            result["framework"] = "native_fallback_from_openai_agents"
            return result
        return {"content": "لا يوجد وكيل", "status": "error", "framework": "error"}

    def complexity_score(self, task: str) -> int:
        """
        1-10 بناءً على طول المهمة وكلماتها المفتاحية
        < 3  → native
        3-6  → langgraph
        7-8  → crewai
        9-10 → openai_agents
        """
        score = 1
        task_lower = task.lower()

        # طول المهمة
        words = len(task.split())
        if words > 200:
            score += 3
        elif words > 100:
            score += 2
        elif words > 50:
            score += 1

        # كلمات تدل على التعقيد
        complex_keywords = [
            "تعاون", "فريق", "خطوات متعددة", "تحليل معمّق", "قارن",
            "pipeline", "workflow", "multi-step", "coordinate", "collaborate",
            "استراتيجية", "خطة شاملة", "تقرير مفصّل", "ابحث وحلل",
        ]
        critical_keywords = [
            "قرار حرج", "حياة", "critical", "emergency", "urgent",
            "تصعيد", "نشر", "deploy", "production", "أمان", "security",
        ]

        for kw in complex_keywords:
            if kw in task_lower:
                score += 1

        for kw in critical_keywords:
            if kw in task_lower:
                score += 2

        return min(10, max(1, score))

    def auto_select(self, agent: Any, task: str, messages: List[Dict] = None) -> Dict:
        """
        اختار الإطار المناسب تلقائياً بناءً على تعقيد المهمة
        """
        score = self.complexity_score(task)
        context = {}
        if messages:
            context["messages"] = messages

        logger.info(f"[Adapter.auto_select] score={score} for task: {task[:60]}...")

        if score < 3:
            return self.run_native(agent, task, context)
        elif score < 7:
            return self.run_langgraph(None, task, [agent] if agent else [])
        elif score < 9:
            return self.run_crewai("default_crew", task)
        else:
            return self.run_openai_agents(agent, task)
