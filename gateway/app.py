"""
Army81 Gateway — FastAPI
نقطة الدخول الوحيدة للنظام
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

from core.base_agent import BaseAgent, load_agent_from_json
from router.smart_router import SmartRouter
from tools.web_search import web_search, fetch_news
from core.base_agent import Tool

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
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

router = SmartRouter()

# ── أدوات مشتركة ──────────────────────────────────────────
TOOLS_REGISTRY: Dict[str, Tool] = {
    "web_search": Tool(
        name="web_search",
        description="بحث على الإنترنت للحصول على معلومات حديثة",
        func=web_search,
        parameters={"query": "str"},
    ),
    "fetch_news": Tool(
        name="fetch_news",
        description="جمع أخبار حديثة حول موضوع",
        func=fetch_news,
        parameters={"topic": "str"},
    ),
}


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

@app.get("/health")
async def health():
    return {"status": "healthy", "agents": len(router.agents)}

# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181, log_level="info")
