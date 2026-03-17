"""
Army81 Gateway — FastAPI
نقطة الدخول الوحيدة للنظام
v1.3.0 — Phase 3: /workflow endpoint + 40 agents
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.base_agent import BaseAgent, load_agent_from_json
from router.smart_router import SmartRouter
from tools.web_search import web_search, fetch_news
from tools.registry import build_tools_registry
from core.base_agent import Tool
from protocols.a2a import A2AProtocol

# ── Logging ──────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/army81.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("army81")

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="Army81",
    description="نظام 81 وكيل ذكاء اصطناعي متكامل",
    version="2.1.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

router = SmartRouter()
a2a = A2AProtocol(router)

# ── سجل الأدوات الكامل ────────────────────────────────────
TOOLS_REGISTRY: Dict[str, Tool] = build_tools_registry()


def load_all_agents():
    """تحميل جميع الوكلاء من ملفات JSON"""
    agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agents")
    count = 0
    errors = 0

    for cat_dir in sorted(os.listdir(agents_dir)):
        cat_path = os.path.join(agents_dir, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith(".json"):
                fpath = os.path.join(cat_path, fname)
                try:
                    agent = load_agent_from_json(fpath, TOOLS_REGISTRY)
                    router.register(agent)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to load {fpath}: {e}")
                    errors += 1

    logger.info(f"Loaded {count} agents ({errors} errors)")
    return count, errors


# ── Request Models ────────────────────────────────────────
class TaskRequest(BaseModel):
    task: str
    agent_id: Optional[str] = None
    category: Optional[str] = None
    context: Optional[Dict] = None

class PipelineRequest(BaseModel):
    task: str
    agent_ids: List[str]
    context: Optional[Dict] = None

class BroadcastRequest(BaseModel):
    task: str
    category: Optional[str] = None

class WorkflowRequest(BaseModel):
    workflow: str                    # "research_pipeline" | "analysis_pipeline" | "decision_support" | "custom"
    task: str
    agent_ids: Optional[List[str]] = None   # للـ custom workflow فقط
    context: Optional[Dict] = None

class A2ARequest(BaseModel):
    from_agent: str
    to_agent: str
    content: str
    msg_type: str = "task"
    priority: int = 5
    context: Optional[Dict] = None

class A2AChainRequest(BaseModel):
    from_agent: str
    agent_chain: List[str]
    task: str
    context: Optional[Dict] = None

# ── Endpoints ─────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    count, errors = load_all_agents()
    logger.info(f"Army81 started — {count} agents ready, {errors} errors")

@app.get("/")
async def root():
    return {
        "name": "Army81",
        "version": "1.0.0",
        "agents": len(router.agents),
        "status": "operational",
        "time": datetime.now().isoformat(),
    }

@app.get("/status")
async def status():
    return router.status()

@app.get("/agents")
async def list_agents():
    return {"total": len(router.agents),
            "agents": [a.info() for a in router.agents.values()]}

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in router.agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return router.agents[agent_id].info()

@app.post("/task")
async def run_task(req: TaskRequest):
    """تنفيذ مهمة — التوجيه التلقائي"""
    return router.route(
        task=req.task,
        agent_id=req.agent_id,
        category=req.category,
        context=req.context,
    )

@app.post("/pipeline")
async def run_pipeline(req: PipelineRequest):
    """تنفيذ مهمة عبر سلسلة وكلاء"""
    return router.pipeline(req.task, req.agent_ids, req.context)

@app.post("/broadcast")
async def broadcast(req: BroadcastRequest):
    """إرسال مهمة لكل وكلاء فئة"""
    results = router.broadcast(req.task, req.category)
    return {"count": len(results), "results": results}

@app.post("/workflow")
async def run_workflow(req: WorkflowRequest):
    """
    تنفيذ مهمة عبر LangGraph workflow
    workflow: "research_pipeline" | "analysis_pipeline" | "decision_support" | "custom"
    مثال: {"workflow": "research_pipeline", "task": "حلّل مستقبل الذكاء الاصطناعي"}
    """
    from workflows.langgraph_flows import (
        build_research_workflow,
        build_analysis_workflow,
        build_decision_workflow,
        build_custom_workflow,
    )
    from core.llm_client import LLMClient

    agents_dict = router.agents
    llm = LLMClient("gemini-flash")

    WORKFLOW_MAP = {
        "research_pipeline": lambda: build_research_workflow(agents_dict, llm),
        "analysis_pipeline": lambda: build_analysis_workflow(agents_dict, llm),
        "decision_support":  lambda: build_decision_workflow(agents_dict, llm),
    }

    if req.workflow == "custom":
        if not req.agent_ids:
            raise HTTPException(400, "agent_ids مطلوب للـ custom workflow")
        wf = build_custom_workflow(req.agent_ids, agents_dict, llm, name="custom")
    elif req.workflow in WORKFLOW_MAP:
        wf = WORKFLOW_MAP[req.workflow]()
    else:
        raise HTTPException(
            400,
            f"workflow '{req.workflow}' غير معروف. الخيارات: {list(WORKFLOW_MAP.keys()) + ['custom']}"
        )

    if not wf.agents:
        raise HTTPException(
            503,
            f"لا يوجد وكلاء كافيين لـ '{req.workflow}'. تأكد من تحميل الوكلاء."
        )

    result = wf.run(req.task, req.context or {})
    return result

@app.get("/workflows")
async def list_workflows():
    """عرض الـ workflows المتاحة وأعضاؤها"""
    from workflows.langgraph_flows import (
        build_research_workflow, build_analysis_workflow, build_decision_workflow
    )
    from core.llm_client import LLMClient

    agents_dict = router.agents
    llm = LLMClient("gemini-flash")

    workflows_info = {}
    for name, builder in [
        ("research_pipeline", build_research_workflow),
        ("analysis_pipeline", build_analysis_workflow),
        ("decision_support",  build_decision_workflow),
    ]:
        wf = builder(agents_dict, llm)
        workflows_info[name] = {
            "agents": [a.agent_id for a in wf.agents],
            "agent_names": [a.name_ar for a in wf.agents],
            "ready": len(wf.agents) > 0,
        }

    return {
        "available_workflows": workflows_info,
        "custom": "POST /workflow با workflow='custom' و agent_ids=['A01','A04',...]",
    }

@app.post("/a2a/send")
async def a2a_send(req: A2ARequest):
    """إرسال رسالة أو مهمة بين وكيلين"""
    return a2a.send(
        from_agent=req.from_agent,
        to_agent=req.to_agent,
        content=req.content,
        msg_type=req.msg_type,
        priority=req.priority,
        metadata=req.context or {},
    )

@app.post("/a2a/chain")
async def a2a_chain(req: A2AChainRequest):
    """سلسلة تفويض بين وكلاء"""
    return a2a.chain(
        from_agent=req.from_agent,
        agent_chain=req.agent_chain,
        task=req.task,
        context=req.context or {},
    )

@app.get("/a2a/inbox/{agent_id}")
async def a2a_inbox(agent_id: str):
    """صندوق وارد وكيل"""
    return {"agent_id": agent_id, "messages": a2a.get_inbox(agent_id)}

@app.get("/a2a/status")
async def a2a_status():
    """حالة بروتوكول A2A"""
    return a2a.status()

@app.get("/health")
async def health():
    return {"status": "healthy", "agents": len(router.agents), "version": "2.1.0"}

# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181, log_level="info")
