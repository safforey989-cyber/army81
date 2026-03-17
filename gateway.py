"""
Army81 Gateway - البوابة الموحدة (FastAPI)
نقطة الدخول الوحيدة لكل المهام والاستعلامات
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

# إضافة المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base_agent import BaseAgent
from router.smart_router import SmartRouter
from memory.memory_system import MemorySystem

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/army81.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("army81")

# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title="Army81 - نظام 81 وكيل ذكاء اصطناعي",
    description="البوابة الموحدة لنظام الوكلاء المتكامل",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Global State
# ============================================================
router = SmartRouter()
memory = MemorySystem(base_dir=os.path.dirname(os.path.abspath(__file__)))


def init_agents():
    """تهيئة كل الوكلاء الـ 81 من ملفات التعريف"""
    agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")
    count = 0
    for cat_dir in sorted(os.listdir(agents_dir)):
        cat_path = os.path.join(agents_dir, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith("_"):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith(".json"):
                fpath = os.path.join(cat_path, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    agent = BaseAgent(
                        agent_id=data["agent_id"],
                        name=data["name"],
                        name_ar=data["name_ar"],
                        category=data["category"],
                        description=data["description"],
                        system_prompt=data["system_prompt"],
                        model=data.get("model", "qwen3:8b"),
                        provider=data.get("provider", "ollama"),
                    )
                    router.register_agent(agent)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to load agent from {fpath}: {e}")
    logger.info(f"Initialized {count} agents")
    return count


# ============================================================
# Request/Response Models
# ============================================================
class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict] = None
    preferred_agent: Optional[str] = None
    preferred_category: Optional[str] = None

class PipelineRequest(BaseModel):
    task: str
    agent_chain: List[str]
    context: Optional[Dict] = None

class BroadcastRequest(BaseModel):
    task: str
    category: Optional[str] = None
    context: Optional[Dict] = None

class MemoryStoreRequest(BaseModel):
    key: str
    value: str
    agent_id: Optional[str] = ""
    level: Optional[str] = "working"

class MemorySearchRequest(BaseModel):
    query: str
    level: Optional[str] = "all"


# ============================================================
# API Endpoints
# ============================================================

@app.on_event("startup")
async def startup():
    os.makedirs("logs", exist_ok=True)
    count = init_agents()
    logger.info(f"Army81 Gateway started with {count} agents")


@app.get("/")
async def root():
    return {
        "name": "Army81",
        "version": "0.1.0",
        "agents_count": len(router.agents),
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status")
async def system_status():
    return {
        "router": router.get_status(),
        "memory": memory.get_status(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/agents")
async def list_agents():
    return {
        "total": len(router.agents),
        "agents": [a.to_dict() for a in router.agents.values()],
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in router.agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return router.agents[agent_id].to_dict()


@app.post("/task")
async def execute_task(req: TaskRequest):
    """تنفيذ مهمة - التوجيه التلقائي أو لوكيل محدد"""
    result = router.route(
        task=req.task,
        context=req.context,
        preferred_agent=req.preferred_agent,
        preferred_category=req.preferred_category,
    )
    # تسجيل في الذاكرة العرضية
    memory.episodic.record_episode(
        agent_id=result.get("agent_id", "unknown"),
        task=req.task,
        result=result.get("result", ""),
        success=result.get("status") == "success",
    )
    return result


@app.post("/pipeline")
async def execute_pipeline(req: PipelineRequest):
    """تنفيذ مهمة عبر سلسلة وكلاء"""
    return router.pipeline(req.task, req.agent_chain, req.context)


@app.post("/broadcast")
async def broadcast_task(req: BroadcastRequest):
    """إرسال مهمة لكل وكلاء فئة معينة"""
    results = router.broadcast(req.task, req.category, req.context)
    return {"results_count": len(results), "results": results}


@app.post("/memory/store")
async def store_memory(req: MemoryStoreRequest):
    memory.remember(req.key, req.value, req.agent_id, req.level)
    return {"status": "stored", "level": req.level}


@app.post("/memory/search")
async def search_memory(req: MemorySearchRequest):
    results = memory.recall(req.query, req.level)
    return {"results": results}


@app.get("/memory/status")
async def memory_status():
    return memory.get_status()


@app.get("/skills")
async def list_skills():
    return {"skills": memory.skills.list_all()}


@app.get("/health")
async def health():
    return {"status": "healthy", "agents": len(router.agents), "time": datetime.now().isoformat()}


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181, log_level="info")
