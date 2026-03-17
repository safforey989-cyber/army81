"""
Army81 Workflows - LangGraph Integration
تدفق العمل بين الوكلاء باستخدام LangGraph
"""
import logging
from typing import TypedDict, List, Dict, Optional, Annotated
import operator
from datetime import datetime

from langgraph.graph import StateGraph, END

logger = logging.getLogger("army81.workflows")


# ── State تعريف الحالة المشتركة ────────────────────────────────

class AgentState(TypedDict):
    """الحالة التي تنتقل بين الوكلاء في كل workflow"""
    task: str                          # المهمة الأصلية
    results: Annotated[List[Dict], operator.add]  # نتائج كل وكيل (تتراكم)
    context: Dict                      # سياق مشترك
    current_step: str                  # الخطوة الحالية
    status: str                        # "running" | "done" | "error"
    final_answer: str                  # الإجابة النهائية


# ── Node builders ────────────────────────────────────────────

def make_agent_node(agent):
    """
    تحويل BaseAgent إلى LangGraph node
    كل node ينفذ مهمة ويمرر النتيجة للتالي
    """
    def node_fn(state: AgentState) -> AgentState:
        task = state["task"]
        context = state.get("context", {})

        # أضف نتائج الوكلاء السابقين للسياق
        prev_results = state.get("results", [])
        if prev_results:
            context["previous_results"] = prev_results

        logger.info(f"LangGraph node: {agent.agent_id} executing '{task[:50]}'")

        result = agent.run(task, context)
        result_dict = result.to_dict() if hasattr(result, "to_dict") else {"result": str(result)}

        return {
            "results": [result_dict],
            "current_step": agent.agent_id,
            "status": "running" if result_dict.get("status") == "success" else "error",
        }

    node_fn.__name__ = f"node_{agent.agent_id}"
    return node_fn


def make_summarizer_node(llm_client):
    """
    node نهائي يلخص كل نتائج الوكلاء في إجابة واحدة
    """
    def summarize(state: AgentState) -> AgentState:
        results = state.get("results", [])
        task = state["task"]

        if not results:
            return {"final_answer": "لم تُنفَّذ أي مهمة", "status": "done"}

        # بناء ملخص
        parts = [f"## نتائج تنفيذ: {task}\n"]
        for r in results:
            agent_name = r.get("agent_name", r.get("agent_id", "وكيل"))
            content = r.get("result", "")[:500]
            parts.append(f"### {agent_name}\n{content}")

        combined = "\n\n".join(parts)

        # لو هناك LLM، يمكن تلخيصه
        try:
            messages = [
                {"role": "system", "content": "أنت مساعد يلخص نتائج عمل فريق من الوكلاء."},
                {"role": "user", "content": f"لخّص هذه النتائج في فقرة واحدة:\n\n{combined}"},
            ]
            resp = llm_client.chat(messages)
            summary = resp.get("content", combined)
        except Exception:
            summary = combined

        return {
            "final_answer": summary,
            "status": "done",
            "current_step": "summarizer",
        }

    return summarize


# ── جاهزة للاستخدام: Workflows ────────────────────────────────

class Army81Workflow:
    """
    بناء workflows من قوائم وكلاء
    مثال:
        flow = Army81Workflow([a01, a04, a07])
        result = flow.run("حلّل هذا الموضوع: ...")
    """

    def __init__(self, agents: List, llm_client=None, name: str = "default"):
        self.agents = agents
        self.llm_client = llm_client
        self.name = name
        self._graph = None
        self._compiled = None

    def _build(self):
        """بناء الـ graph"""
        graph = StateGraph(AgentState)

        if not self.agents:
            raise ValueError("لا يوجد وكلاء في الـ workflow")

        # أضف node لكل وكيل
        for agent in self.agents:
            node_fn = make_agent_node(agent)
            graph.add_node(agent.agent_id, node_fn)

        # أضف node للتلخيص
        if self.llm_client:
            graph.add_node("summarizer", make_summarizer_node(self.llm_client))

        # ربط العقد بالترتيب
        agent_ids = [a.agent_id for a in self.agents]

        graph.set_entry_point(agent_ids[0])

        for i in range(len(agent_ids) - 1):
            graph.add_edge(agent_ids[i], agent_ids[i + 1])

        # الوكيل الأخير → summarizer أو END
        if self.llm_client:
            graph.add_edge(agent_ids[-1], "summarizer")
            graph.add_edge("summarizer", END)
        else:
            graph.add_edge(agent_ids[-1], END)

        self._compiled = graph.compile()
        logger.info(f"Workflow '{self.name}' built with {len(self.agents)} agents")

    def run(self, task: str, context: Dict = None) -> Dict:
        """تنفيذ الـ workflow"""
        if self._compiled is None:
            self._build()

        initial_state: AgentState = {
            "task": task,
            "results": [],
            "context": context or {},
            "current_step": "start",
            "status": "running",
            "final_answer": "",
        }

        try:
            final_state = self._compiled.invoke(initial_state)
            return {
                "status": "success",
                "workflow": self.name,
                "task": task,
                "steps": len(final_state.get("results", [])),
                "results": final_state.get("results", []),
                "final_answer": final_state.get("final_answer", ""),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Workflow '{self.name}' failed: {e}")
            return {
                "status": "error",
                "workflow": self.name,
                "error": str(e),
            }


# ── Predefined Workflows ─────────────────────────────────────

def build_research_workflow(agents_registry: Dict, llm_client=None) -> Army81Workflow:
    """
    Research Pipeline: A01 → A04 → A07 (استراتيجية → أخبار → علوم)
    """
    ids = ["A01", "A04", "A07"]
    agents = [agents_registry[i] for i in ids if i in agents_registry]
    return Army81Workflow(agents, llm_client, name="research_pipeline")


def build_analysis_workflow(agents_registry: Dict, llm_client=None) -> Army81Workflow:
    """
    Analysis Pipeline: A05 → A06 → A08 (كود → بيانات → مالي)
    """
    ids = ["A05", "A06", "A08"]
    agents = [agents_registry[i] for i in ids if i in agents_registry]
    return Army81Workflow(agents, llm_client, name="analysis_pipeline")


def build_decision_workflow(agents_registry: Dict, llm_client=None) -> Army81Workflow:
    """
    Decision Support: A04 → A08 → A14 → A01 (أخبار → مالي → إدارة → قيادة)
    """
    ids = ["A04", "A08", "A14", "A01"]
    agents = [agents_registry[i] for i in ids if i in agents_registry]
    return Army81Workflow(agents, llm_client, name="decision_support")


def build_custom_workflow(agent_ids: List[str], agents_registry: Dict,
                          llm_client=None, name: str = "custom") -> Army81Workflow:
    """بناء workflow مخصص من قائمة IDs"""
    agents = [agents_registry[i] for i in agent_ids if i in agents_registry]
    missing = [i for i in agent_ids if i not in agents_registry]
    if missing:
        logger.warning(f"Custom workflow: agents not found: {missing}")
    return Army81Workflow(agents, llm_client, name=name)


if __name__ == "__main__":
    # اختبار بسيط بدون LLM حقيقي
    print("LangGraph Workflows module loaded successfully")
    print("Available workflows: research_pipeline, analysis_pipeline, decision_support")
