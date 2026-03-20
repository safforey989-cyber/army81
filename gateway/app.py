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

from fastapi import FastAPI, HTTPException, Request
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

class SwarmRequest(BaseModel):
    duration_minutes: int = 60
    topic: str = "التعارف وبناء الشبكة"

class SwarmEvent(BaseModel):
    timestamp: str
    event_type: str  # task_assigned, task_completed, agent_message, tool_used, memory_saved, cluster_formed
    from_agent: str
    to_agent: str = ""
    data: dict = {}

# ── Endpoints ─────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    count, errors = load_all_agents()

    # v5: تفعيل الشبكة العصبية
    try:
        from core.neural_network import get_neural_network
        neural_net = get_neural_network(router)
        neural_net.register_agents(router.agents)
        router.neural_net = neural_net
        logger.info(f"Neural Network active — {neural_net.status()['graph_edges']} connections")
    except Exception as e:
        logger.warning(f"Neural Network not available: {e}")

    logger.info(f"Army81 started — {count} agents ready, {errors} errors")

    # v20: Voice Interface
    try:
        from integrations.voice_interface import register_voice_endpoints
        register_voice_endpoints(app)
    except Exception as e:
        logger.warning(f"Voice interface not available: {e}")

    # v23: Resilience Layer
    try:
        from core.resilience import register_resilience_endpoints
        register_resilience_endpoints(app)
    except Exception as e:
        logger.warning(f"Resilience layer not available: {e}")

    # v27: Brain Nucleus — Qwen3-8B as central brain
    try:
        from core.brain_nucleus import get_brain
        brain = get_brain()
        logger.info(f"🧠 Brain Nucleus: {brain.status()['nucleus_model']} | Ollama: {brain.ollama.is_available()}")
    except Exception as e:
        logger.warning(f"Brain Nucleus not available: {e}")

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
    base = router.status()

    # v14: إضافة إحصائيات الذاكرة الحقيقية
    memory_stats = {"episodic": 0, "chroma": 0, "swarm_agents": 0, "core_interactions": 0}
    try:
        import sqlite3
        db = sqlite3.connect("workspace/episodic_memory.db")
        memory_stats["episodic"] = db.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        db.close()
    except Exception:
        pass
    try:
        from memory.swarm_memory import SwarmMemoryManager
        mgr = SwarmMemoryManager.get_instance()
        s = mgr.get_full_stats()
        memory_stats["swarm_agents"] = s.get("agents_with_memory", 0)
        memory_stats["core_interactions"] = s.get("total_interactions", 0)
        memory_stats["core_decisions"] = s.get("core", {}).get("decisions", 0)
        memory_stats["core_knowledge"] = s.get("core", {}).get("shared_knowledge", 0)
    except Exception:
        pass
    try:
        from pathlib import Path
        chroma_dir = Path("workspace/chroma_db")
        if chroma_dir.exists():
            memory_stats["chroma"] = sum(1 for _ in chroma_dir.rglob("*") if _.is_file())
    except Exception:
        pass

    base["memory"] = memory_stats
    return base

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
    """تنفيذ مهمة — يكتشف الأوامر تلقائياً قبل التوجيه"""
    # v8: كشف الأوامر (تدريب، اكتشاف، تطوير...)
    try:
        from core.command_parser import parse_command, execute_command
        parsed = parse_command(req.task)
        if parsed:
            handler, params = parsed
            result = execute_command(handler, params, router)
            return {
                "status": result.get("status", "success"),
                "result": result.get("result", ""),
                "command": handler,
                "agent_name": "نظام الأوامر",
                "agent_id": "SYS",
                "model_used": "command_parser",
                "elapsed_seconds": 0,
            }
    except Exception:
        pass

    # توجيه عادي للوكلاء
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
    return {"status": "healthy", "agents": len(router.agents), "version": "7.0.0"}

# ── v7: Training Endpoints ───────────────────────
@app.get("/training/status")
async def training_status():
    """حالة التدريب المستمر"""
    try:
        from core.continuous_trainer import get_continuous_trainer
        t = get_continuous_trainer(router)
        return t.status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/training/leaderboard")
async def training_leaderboard():
    """ترتيب الوكلاء بالأداء"""
    try:
        from core.scenario_engine import get_scenario_engine
        se = get_scenario_engine()
        return {"leaderboard": se.get_leaderboard()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/training/levels")
async def training_levels():
    """مستويات كل الوكلاء"""
    try:
        from core.continuous_trainer import get_continuous_trainer
        t = get_continuous_trainer(router)
        return {"levels": t.get_all_levels()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/training/trigger")
async def training_trigger():
    """تشغيل دورة تدريب يدوياً"""
    try:
        from core.continuous_trainer import get_continuous_trainer
        t = get_continuous_trainer(router)
        result = t.train_cycle(max_agents=10)  # أول 10 فقط عند التشغيل اليدوي
        return result
    except Exception as e:
        return {"error": str(e)}

# ── v6: Cloud Memory + Execution Engine ──────────
@app.get("/cloud/status")
async def cloud_status():
    """حالة الذاكرة السحابية ومحرك التنفيذ"""
    result = {}
    try:
        from memory.cloud_memory import get_cloud_memory
        cm = get_cloud_memory()
        result["cloud_memory"] = cm.get_global_stats()
    except Exception as e:
        result["cloud_memory"] = {"error": str(e)}
    try:
        from core.execution_engine import get_execution_engine
        ee = get_execution_engine()
        result["execution_engine"] = ee.status()
    except Exception as e:
        result["execution_engine"] = {"error": str(e)}
    return result

# ── v5: Neural Network Endpoints ─────────────────
@app.get("/network/status")
async def network_status():
    """حالة الشبكة العصبية"""
    if not router.neural_net:
        return {"status": "not_initialized", "message": "الشبكة العصبية غير مفعّلة"}
    return router.neural_net.status()

@app.get("/network/graph")
async def network_graph():
    """خريطة اتصالات الشبكة العصبية"""
    if not router.neural_net:
        return {"error": "الشبكة العصبية غير مفعّلة"}
    return router.neural_net.get_graph()

@app.get("/network/signals")
async def network_signals():
    """آخر الإشارات العصبية"""
    if not router.neural_net:
        return {"signals": []}
    return {"signals": router.neural_net.get_recent_signals(30)}

@app.get("/commander/decide")
async def commander_decide(task: str):
    """A00 يحلل مهمة ويقرر بدون تنفيذ"""
    if not router.neural_net:
        return {"error": "الشبكة العصبية غير مفعّلة"}
    complexity = router.neural_net._compute_complexity(task)
    decision = router.neural_net._commander_decide(task, complexity, {})
    return {
        "task": task,
        "complexity": complexity,
        "decision": decision,
    }

# ── MCP Endpoints ────────────────────────────────────────
@app.get("/mcp/status")
async def mcp_status():
    """حالة نظام MCP — 30 خادم مسجّل"""
    try:
        from core.mcp_connector import get_mcp_connector
        return get_mcp_connector().status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/mcp/servers")
async def mcp_servers():
    """قائمة كل خوادم MCP المسجلة"""
    try:
        from core.mcp_connector import get_mcp_connector
        mc = get_mcp_connector()
        return {
            "total": len(mc.get_all_servers()),
            "servers": mc.get_all_servers(),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/mcp/agent/{agent_id}")
async def mcp_for_agent(agent_id: str):
    """خوادم MCP المناسبة لوكيل معين"""
    try:
        from core.mcp_connector import get_mcp_connector
        mc = get_mcp_connector()
        servers = mc.get_servers_for_agent(agent_id)
        return {"agent_id": agent_id, "mcp_servers": servers}
    except Exception as e:
        return {"error": str(e)}

@app.get("/mcp/recommend")
async def mcp_recommend(task: str):
    """اقتراح خوادم MCP لمهمة"""
    try:
        from core.mcp_connector import get_mcp_connector
        mc = get_mcp_connector()
        recs = mc.recommend_for_task(task)
        return {"task": task, "recommendations": recs}
    except Exception as e:
        return {"error": str(e)}

# ── Metrics & Knowledge Endpoints ────────────────────────
@app.get("/metrics")
async def get_metrics():
    """إحصائيات حقيقية من قاعدة البيانات"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "total": len(router.agents),
            "by_category": router._count_by_category(),
            "top_performers": [],
        },
        "tasks": {
            "total_today": sum(a.stats.get("tasks_done",0) for a in router.agents.values()),
            "total_failed": sum(a.stats.get("tasks_failed",0) for a in router.agents.values()),
            "success_rate": 0,
        },
        "memory": {},
        "knowledge": {},
    }

    total = metrics["tasks"]["total_today"] + metrics["tasks"]["total_failed"]
    if total > 0:
        metrics["tasks"]["success_rate"] = round(
            metrics["tasks"]["total_today"] / total * 100, 1
        )

    # أفضل الوكلاء
    agents_list = sorted(
        router.agents.values(),
        key=lambda a: a.stats.get("tasks_done", 0),
        reverse=True
    )
    metrics["agents"]["top_performers"] = [
        {"id": a.agent_id, "name": a.name_ar,
         "tasks": a.stats.get("tasks_done",0),
         "category": a.category}
        for a in agents_list[:5]
    ]

    # إحصائيات Chroma
    try:
        import chromadb
        client = chromadb.PersistentClient(path="workspace/chroma_db")
        collections = client.list_collections()
        metrics["memory"]["chroma_collections"] = len(collections)
        metrics["memory"]["total_documents"] = sum(c.count() for c in collections)
    except:
        metrics["memory"]["chroma_collections"] = 0

    # إحصائيات المعرفة
    from pathlib import Path as _Path
    knowledge_dir = _Path("workspace/knowledge")
    if knowledge_dir.exists():
        all_files = list(knowledge_dir.rglob("*.txt"))
        metrics["knowledge"]["files"] = len(all_files)
        metrics["knowledge"]["size_mb"] = round(
            sum(f.stat().st_size for f in all_files) / 1024 / 1024, 2
        )

    return metrics

@app.get("/agents/{agent_id}/history")
async def agent_history(agent_id: str, limit: int = 20):
    """تاريخ مهام وكيل معين"""
    if agent_id not in router.agents:
        raise HTTPException(404, "Agent not found")
    agent = router.agents[agent_id]
    return {
        "agent_id": agent_id,
        "stats": agent.stats,
        "recent_tasks": list(agent.short_term_memory)[-limit:] if hasattr(agent, 'short_term_memory') else []
    }

@app.get("/knowledge/status")
async def knowledge_status():
    """حالة قاعدة المعرفة"""
    status = {"collections": [], "total_docs": 0, "knowledge_files": 0}
    try:
        import chromadb
        client = chromadb.PersistentClient(path="workspace/chroma_db")
        for c in client.list_collections():
            count = c.count()
            status["collections"].append({"name": c.name, "count": count})
            status["total_docs"] += count
    except:
        pass

    from pathlib import Path as _Path
    knowledge_dir = _Path("workspace/knowledge")
    if knowledge_dir.exists():
        status["knowledge_files"] = len(list(knowledge_dir.rglob("*.txt")))

    return status

@app.post("/feedback")
async def submit_feedback(agent_id: str, task: str, rating: int, comment: str = ""):
    """تقييم رد وكيل"""
    from pathlib import Path as _Path
    feedback_file = _Path("workspace/feedback.jsonl")
    feedback_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "task_preview": task[:100],
        "rating": rating,
        "comment": comment
    }
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"status": "recorded", "rating": rating}

@app.get("/reports/latest")
async def latest_report():
    """آخر تقرير يومي"""
    from pathlib import Path as _Path
    reports_dir = _Path("workspace/reports")
    if not reports_dir.exists():
        return {"error": "No reports yet"}

    reports = sorted(reports_dir.glob("*.md"), reverse=True)
    if not reports:
        return {"error": "No reports found"}

    latest = reports[0]
    return {
        "filename": latest.name,
        "date": latest.stem,
        "content": latest.read_text(encoding="utf-8"),
        "size": latest.stat().st_size
    }

# ═══ SWARM SESSION — Real Agent-to-Agent Communication ═══
import asyncio
import threading
from queue import Queue

# Global swarm state
swarm_events = []  # Store all swarm events for dashboard polling
swarm_active = False
swarm_session_id = None

@app.post("/swarm/start")
async def start_swarm(req: SwarmRequest):
    """بدء جلسة تواصل بين كل الـ 81 وكيل"""
    global swarm_active, swarm_session_id, swarm_events

    if swarm_active:
        return {"status": "already_running", "session_id": swarm_session_id}

    swarm_active = True
    swarm_session_id = f"swarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    swarm_events = []

    # Start swarm in background thread
    thread = threading.Thread(
        target=run_swarm_session,
        args=(req.duration_minutes, req.topic),
        daemon=True
    )
    thread.start()

    return {
        "status": "started",
        "session_id": swarm_session_id,
        "duration_minutes": req.duration_minutes,
        "topic": req.topic,
        "agents_count": len(router.agents)
    }

@app.post("/swarm/stop")
async def stop_swarm():
    """إيقاف جلسة السرب"""
    global swarm_active
    swarm_active = False
    return {"status": "stopped", "total_events": len(swarm_events)}

@app.get("/swarm/status")
async def swarm_status():
    """حالة جلسة السرب"""
    return {
        "active": swarm_active,
        "session_id": swarm_session_id,
        "total_events": len(swarm_events),
        "recent_events": swarm_events[-20:] if swarm_events else [],
        "agents_busy": sum(1 for a in router.agents.values() if hasattr(a, '_swarm_busy') and a._swarm_busy),
    }

@app.get("/swarm/events")
async def swarm_events_feed(since: int = 0):
    """دفق الأحداث — Dashboard يستدعي هذا كل ثانية"""
    events = swarm_events[since:]
    return {
        "events": events,
        "total": len(swarm_events),
        "next_since": len(swarm_events),
        "active": swarm_active,
    }

@app.get("/swarm/proposals")
async def swarm_proposals():
    """الاقتراحات التي اتفق عليها الوكلاء"""
    proposals_file = os.path.join("workspace", "swarm_proposals.json")
    if os.path.exists(proposals_file):
        with open(proposals_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"proposals": []}


def add_swarm_event(event_type, from_agent, to_agent="", data=None):
    """إضافة حدث للسجل"""
    global swarm_events
    evt = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "data": data or {}
    }
    swarm_events.append(evt)
    return evt


def run_swarm_session(duration_minutes: int, topic: str):
    """
    جلسة السرب الحقيقية — الوكلاء يتواصلون فعلياً + يبنون ذاكرة
    """
    import time
    import random
    global swarm_active

    # ── v12: ذاكرة السرب ──
    try:
        from memory.swarm_memory import SwarmMemoryManager
        swarm_mem = SwarmMemoryManager.get_instance()
        logger.info("SwarmMemory active — agents will build memories")
    except Exception as e:
        swarm_mem = None
        logger.warning(f"SwarmMemory not available: {e}")

    logger.info(f"Swarm session started — {duration_minutes} min — {topic}")
    add_swarm_event("swarm_started", "SYSTEM", data={"topic": topic, "duration": duration_minutes})

    agents_list = list(router.agents.values())
    agent_ids = list(router.agents.keys())

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    phase = 0  # 0=intro, 1=discuss, 2=collaborate, 3=propose

    # Phase durations (proportional) — v14: 6 مراحل
    # intro → knowledge_hunt → discuss → distill → collaborate → propose
    phase_times = [0.10, 0.20, 0.20, 0.15, 0.20, 0.15]

    round_num = 0

    while swarm_active and time.time() < end_time:
        elapsed = time.time() - start_time
        total_duration = duration_minutes * 60
        progress = elapsed / total_duration

        # Determine phase — v14: 6 مراحل
        cum = 0
        phases_list = ["introduction", "knowledge_hunt", "discussion", "distillation", "collaboration", "proposals"]
        current_phase = phases_list[-1]
        for i, pt in enumerate(phase_times):
            cum += pt
            if progress < cum:
                current_phase = phases_list[i]
                break

        round_num += 1

        try:
            if current_phase == "introduction":
                # Phase 1: Agents introduce themselves to each other
                a1 = random.choice(agents_list)
                a2 = random.choice(agents_list)
                while a2.agent_id == a1.agent_id:
                    a2 = random.choice(agents_list)

                add_swarm_event("agent_message", a1.agent_id, a2.agent_id,
                    {"phase": "introduction", "message": f"{a1.name_ar} يتعرف على {a2.name_ar}"})

                # حقن سياق الذاكرة الشخصية
                mem_ctx = ""
                if swarm_mem:
                    mem_ctx = swarm_mem.inject_context(a1.agent_id, a2.agent_id)

                task = f"""{mem_ctx}
عرّف نفسك باختصار للوكيل {a2.name_ar} ({a2.agent_id}). اذكر تخصصك وأدواتك وكيف يمكنكما التعاون. كن مختصراً في 3 جمل."""

                try:
                    result = a1.run(task, context={"swarm_session": True, "partner": a2.agent_id})
                    result_text = result.result[:300] if hasattr(result, 'result') else str(result)[:300]
                    add_swarm_event("task_completed", a1.agent_id, a2.agent_id,
                        {"phase": "introduction", "result": result_text})

                    # ── حفظ التعارف في الذاكرة ──
                    if swarm_mem:
                        swarm_mem.record_introduction(
                            a1.agent_id, a1.name_ar, a1.description[:100],
                            a2.agent_id, a2.name_ar, a2.description[:100],
                            result_text
                        )
                        add_swarm_event("memory_saved", a1.agent_id, a2.agent_id,
                            {"type": "introduction", "agents": [a1.agent_id, a2.agent_id]})

                except Exception as e:
                    add_swarm_event("task_failed", a1.agent_id, data={"error": str(e)[:100]})

                time.sleep(3)  # Rate limiting

            elif current_phase == "knowledge_hunt":
                # ═══ Phase 2: صيد المعرفة — الوكلاء يبحثون في مصادر حقيقية ═══
                hunter = random.choice(agents_list)

                # مصادر حقيقية حسب التخصص
                hunt_tasks = {
                    "cat1_science": "ابحث في arXiv عن أحدث ورقة بحثية في الذكاء الاصطناعي والوكلاء (2025-2026). لخّص العنوان والنتيجة الرئيسية في 3 جمل.",
                    "cat2_society": "ابحث عن آخر التطورات الاقتصادية والجيوسياسية في العالم. لخّص أهم 3 أحداث في 2026.",
                    "cat3_tools": "ابحث في GitHub عن أحدث مستودعات AI agents المفتوحة (trending). اذكر أفضل 3 مع أسباب أهميتها.",
                    "cat4_management": "ابحث عن أحدث منهجيات إدارة المشاريع الذكية وأطر العمل AI-powered. لخّص أهم 3 تطورات.",
                    "cat5_behavior": "ابحث عن أحدث الأبحاث في علم النفس السلوكي والذكاء العاطفي الاصطناعي. لخّص 3 نتائج مهمة.",
                    "cat6_leadership": "ابحث عن أحدث الاستراتيجيات العسكرية والجيوسياسية في العالم. لخّص أهم 3 تحولات في 2026.",
                    "cat7_new": "ابحث عن أحدث تقنيات التطور الذاتي للأنظمة الذكية (self-improving AI). لخّص أهم 3 اختراقات.",
                }
                hunt_task = hunt_tasks.get(hunter.category, hunt_tasks["cat3_tools"])

                add_swarm_event("agent_message", hunter.agent_id, "KNOWLEDGE",
                    {"phase": "knowledge_hunt", "message": f"🔍 {hunter.name_ar} يبحث في مصادر المعرفة"})

                try:
                    result = hunter.run(hunt_task, context={"swarm_session": True, "phase": "knowledge_hunt"})
                    result_text = result.result[:500] if hasattr(result, 'result') else str(result)[:500]

                    add_swarm_event("task_completed", hunter.agent_id, data={
                        "phase": "knowledge_hunt",
                        "result": result_text
                    })

                    # حفظ المعرفة في النواة المشتركة
                    if swarm_mem and len(result_text) > 50:
                        swarm_mem.core.add_shared_knowledge(
                            result_text[:500], hunter.agent_id,
                            topic=hunter.category, confidence=0.85
                        )
                        swarm_mem.record_insight(hunter.agent_id, result_text[:300], hunter.category)

                        add_swarm_event("memory_saved", hunter.agent_id, data={
                            "type": "knowledge_hunt",
                            "topic": hunter.category,
                            "agents_remembered": 1
                        })

                    # مشاركة مع 3 وكلاء آخرين
                    share_targets = random.sample(
                        [a for a in agents_list if a.agent_id != hunter.agent_id], min(3, len(agents_list)-1))
                    for target in share_targets:
                        if swarm_mem:
                            swarm_mem.record_introduction(
                                hunter.agent_id, hunter.name_ar, hunter.description[:100],
                                target.agent_id, target.name_ar, target.description[:100],
                                f"شاركني معرفة عن {hunter.category}"
                            )
                        add_swarm_event("agent_message", hunter.agent_id, target.agent_id,
                            {"phase": "knowledge_share", "message": f"مشاركة معرفة → {target.name_ar}"})

                except Exception as e:
                    add_swarm_event("task_failed", hunter.agent_id, data={"error": str(e)[:100]})

                time.sleep(4)

            elif current_phase == "distillation":
                # ═══ Phase 4: التقطير — نموذج قوي يعلّم نموذج أخف ═══
                # اختر زوج معلم-طالب
                teacher_agents = [a for a in agents_list if a.model_alias in ["claude-smart", "deepseek-r1", "gemini-pro", "gpt4o"]]
                student_agents = [a for a in agents_list if a.model_alias in ["gemini-flash", "claude-fast", "qwen-free", "llama-free"]]

                if teacher_agents and student_agents:
                    teacher = random.choice(teacher_agents)
                    student = random.choice(student_agents)

                    add_swarm_event("cluster_formed", teacher.agent_id, data={
                        "phase": "distillation",
                        "cluster": [teacher.agent_id, student.agent_id],
                        "topic": f"🎓 تقطير: {teacher.name_ar} يعلّم {student.name_ar}"
                    })

                    # المعلم يحل مهمة معقدة مع شرح التفكير
                    distill_tasks = [
                        "فكّر بصوت عالٍ وحلّ: كيف نصمم نظام ذاكرة هرمي لوكلاء AI يحافظ على السياق عبر آلاف المحادثات؟",
                        "فكّر خطوة بخطوة: ما أفضل خوارزمية لتوجيه المهام بين 81 وكيل بتخصصات مختلفة؟ أعطِ pseudocode.",
                        "حلّل بعمق: كيف نبني نظام تقييم ذاتي يقيس جودة كل وكيل بدقة بدون تدخل بشري؟",
                        "اشرح آلية: كيف نستخدم RAG مع Knowledge Graph لجعل الوكلاء يستنتجون حلولاً لم يتدربوا عليها؟",
                        "صمّم: نظام أمان يمنع الوكلاء من تدمير أنفسهم أثناء التطور الذاتي. أعطِ 5 قواعد ذهبية مع كود.",
                    ]
                    distill_task = random.choice(distill_tasks)

                    try:
                        # المعلم يحل
                        teacher_result = teacher.run(distill_task, context={"swarm_session": True, "phase": "distillation_teach"})
                        teacher_text = teacher_result.result[:600] if hasattr(teacher_result, 'result') else str(teacher_result)[:600]

                        add_swarm_event("task_completed", teacher.agent_id, data={
                            "phase": "distillation_teach",
                            "result": teacher_text[:300]
                        })

                        # الطالب يتعلم من الحل
                        learn_task = f"""تعلّم من هذا الحل الذي قدمه خبير ({teacher.name_ar}):

{teacher_text}

الآن أعد صياغة الحل بأسلوبك مع إضافة ملاحظة واحدة جديدة. كن مختصراً."""

                        student_result = student.run(learn_task, context={"swarm_session": True, "phase": "distillation_learn"})
                        student_text = student_result.result[:400] if hasattr(student_result, 'result') else str(student_result)[:400]

                        add_swarm_event("task_completed", student.agent_id, data={
                            "phase": "distillation_learn",
                            "result": student_text[:300]
                        })

                        # حفظ المثال في ذاكرة التقطير
                        try:
                            from core.distillation_engine import DistillationEngine
                            de = DistillationEngine()
                            de.record_teacher_solution(
                                task_type="system_design",
                                task=distill_task[:200],
                                solution=teacher_text,
                                model=teacher.model_alias,
                                cot_steps=teacher_text[:500]
                            )
                        except Exception:
                            pass

                        # حفظ في النواة المشتركة
                        if swarm_mem:
                            swarm_mem.core.add_shared_knowledge(
                                teacher_text[:400], teacher.agent_id,
                                topic="distilled_knowledge", confidence=0.9
                            )
                            swarm_mem.record_collaboration(
                                teacher.agent_id, [student.agent_id],
                                f"تقطير: {distill_task[:50]}", teacher_text[:200], True
                            )

                        add_swarm_event("memory_saved", teacher.agent_id, data={
                            "type": "distillation",
                            "topic": "تقطير معرفي",
                            "agents_remembered": 2
                        })

                    except Exception as e:
                        add_swarm_event("task_failed", teacher.agent_id, data={"error": str(e)[:100]})

                    time.sleep(2)
                    add_swarm_event("cluster_dissolved", teacher.agent_id, data={
                        "cluster": [teacher.agent_id, student.agent_id]})

                time.sleep(4)

            elif current_phase == "discussion":
                # Phase 3: Agents discuss topics from their expertise
                a1 = random.choice(agents_list)
                # Pick 2-3 agents from different categories
                others = [a for a in agents_list if a.category != a1.category]
                partners = random.sample(others, min(2, len(others)))

                # Form a cluster
                cluster_ids = [a1.agent_id] + [p.agent_id for p in partners]
                add_swarm_event("cluster_formed", a1.agent_id, data={
                    "phase": "discussion",
                    "cluster": cluster_ids,
                    "topic": f"مناقشة بين {a1.name_ar} و{'، '.join(p.name_ar for p in partners)}"
                })

                # حقن سياق الذاكرة
                disc_mem_ctx = ""
                if swarm_mem:
                    disc_mem_ctx = swarm_mem.inject_context(a1.agent_id)

                task = f"""{disc_mem_ctx}
أنت في حلقة نقاش مع الوكلاء: {', '.join(p.name_ar + ' (' + p.agent_id + ')' for p in partners)}.
الموضوع: كيف يمكن لتخصصاتنا المختلفة أن تتكامل لتحسين النظام؟
اقترح فكرة واحدة محددة وعملية للتعاون. كن مختصراً في 4 جمل."""

                try:
                    result = a1.run(task, context={"swarm_session": True, "phase": "discussion"})
                    result_text = result.result[:400] if hasattr(result, 'result') else str(result)[:400]
                    add_swarm_event("task_completed", a1.agent_id, data={
                        "phase": "discussion",
                        "cluster": cluster_ids,
                        "result": result_text
                    })

                    # ── حفظ الرؤية في الذاكرة ──
                    if swarm_mem:
                        swarm_mem.record_insight(a1.agent_id, result_text, topic="collaboration")
                        for p in partners:
                            swarm_mem.record_introduction(
                                a1.agent_id, a1.name_ar, a1.description[:100],
                                p.agent_id, p.name_ar, p.description[:100],
                                f"مناقشة حول تكامل التخصصات"
                            )

                except Exception as e:
                    add_swarm_event("task_failed", a1.agent_id, data={"error": str(e)[:100]})

                # Dissolve cluster after a bit
                time.sleep(2)
                add_swarm_event("cluster_dissolved", a1.agent_id, data={"cluster": cluster_ids})

                time.sleep(4)

            elif current_phase == "collaboration":
                # Phase 3: Agents work together on a real task
                # Pick a leader and a team
                leaders = [a for a in agents_list if 'leadership' in a.category or a.agent_id in ['A01', 'A00']]
                leader = random.choice(leaders) if leaders else random.choice(agents_list)

                team = random.sample([a for a in agents_list if a.agent_id != leader.agent_id], min(3, len(agents_list)-1))
                team_ids = [leader.agent_id] + [t.agent_id for t in team]

                add_swarm_event("cluster_formed", leader.agent_id, data={
                    "phase": "collaboration",
                    "cluster": team_ids,
                    "topic": f"فريق عمل بقيادة {leader.name_ar}"
                })

                collaboration_tasks = [
                    "اقترح طريقة لتحسين سرعة استجابة النظام بنسبة 50%",
                    "صمم آلية لمشاركة المعرفة تلقائياً بين الوكلاء",
                    "اقترح نظام تقييم ذاتي لقياس أداء كل وكيل",
                    "صمم بروتوكول طوارئ عندما يفشل أحد الوكلاء",
                    "اقترح طريقة لتقليل تكاليف API بنسبة 30%",
                    "صمم نظام أولويات ذكي للمهام القادمة",
                ]
                collab_task = random.choice(collaboration_tasks)

                # حقن ذاكرة القائد
                collab_mem_ctx = ""
                if swarm_mem:
                    collab_mem_ctx = swarm_mem.inject_context(leader.agent_id)

                task = f"""{collab_mem_ctx}
أنت قائد فريق يضم: {', '.join(t.name_ar for t in team)}.
المهمة: {collab_task}
قدّم اقتراحاً عملياً محدداً يمكن تنفيذه. كن مختصراً في 5 جمل."""

                try:
                    result = leader.run(task, context={"swarm_session": True, "phase": "collaboration", "team": team_ids})
                    result_text = result.result[:500] if hasattr(result, 'result') else str(result)[:500]

                    add_swarm_event("task_completed", leader.agent_id, data={
                        "phase": "collaboration",
                        "cluster": team_ids,
                        "collab_task": collab_task,
                        "result": result_text
                    })

                    # ── حفظ التعاون في الذاكرة ──
                    if swarm_mem:
                        swarm_mem.record_collaboration(
                            leader.agent_id, [t.agent_id for t in team],
                            collab_task, result_text, success=True
                        )
                        # كل عضو يتذكر القائد
                        for t in team:
                            swarm_mem.record_introduction(
                                t.agent_id, t.name_ar, t.description[:100],
                                leader.agent_id, leader.name_ar, leader.description[:100],
                                f"عملنا معاً على: {collab_task[:50]}"
                            )

                    add_swarm_event("memory_saved", leader.agent_id, data={
                        "type": "collaboration",
                        "topic": collab_task[:50],
                        "agents_remembered": len(team_ids)
                    })

                except Exception as e:
                    add_swarm_event("task_failed", leader.agent_id, data={"error": str(e)[:100]})

                time.sleep(2)
                add_swarm_event("cluster_dissolved", leader.agent_id, data={"cluster": team_ids})
                time.sleep(5)

            elif current_phase == "proposals":
                # ═══ Phase 6: الاقتراحات + بناء نواة العقل المشترك ═══
                a01 = router.agents.get("A01")
                if a01 and round_num % 3 == 0:
                    # جمع كل المعرفة المكتسبة
                    recent_results = [e["data"].get("result", "") for e in swarm_events[-50:]
                                     if e["event_type"] == "task_completed" and e["data"].get("result")]
                    knowledge_hunts = [e["data"].get("result", "") for e in swarm_events
                                       if e["data"].get("phase") == "knowledge_hunt" and e["data"].get("result")]
                    distill_results = [e["data"].get("result", "") for e in swarm_events
                                       if e["data"].get("phase") in ("distillation_teach", "distillation_learn")]

                    summary = "\n".join(recent_results[-5:])[:800]
                    knowledge_summary = "\n".join(knowledge_hunts[-3:])[:600]
                    distill_summary = "\n".join(distill_results[-3:])[:600]

                    # بناء نواة العقل المشترك
                    brain_data = {
                        "version": datetime.now().strftime("%Y%m%d_%H%M"),
                        "knowledge_acquired": len(knowledge_hunts),
                        "distillations_done": len(distill_results),
                        "collaborations": len([e for e in swarm_events if e["data"].get("phase") == "collaboration"]),
                        "total_interactions": len(swarm_events),
                    }

                    if swarm_mem:
                        full_stats = swarm_mem.get_full_stats()
                        brain_data["agents_with_memory"] = full_stats.get("agents_with_memory", 0)
                        brain_data["core_knowledge_items"] = full_stats.get("core", {}).get("shared_knowledge", 0)
                        brain_data["core_decisions"] = full_stats.get("core", {}).get("decisions", 0)

                    # حفظ نواة العقل
                    brain_file = os.path.join("workspace", "shared_brain.json")
                    os.makedirs("workspace", exist_ok=True)
                    try:
                        existing_brain = {}
                        if os.path.exists(brain_file):
                            with open(brain_file, "r", encoding="utf-8") as f:
                                existing_brain = json.load(f)

                        existing_brain["last_update"] = datetime.now().isoformat()
                        existing_brain["sessions"] = existing_brain.get("sessions", 0) + 1
                        existing_brain["total_knowledge"] = existing_brain.get("total_knowledge", 0) + len(knowledge_hunts)
                        existing_brain["total_distillations"] = existing_brain.get("total_distillations", 0) + len(distill_results)
                        existing_brain["latest_session"] = brain_data

                        with open(brain_file, "w", encoding="utf-8") as f:
                            json.dump(existing_brain, f, ensure_ascii=False, indent=2)

                        add_swarm_event("memory_saved", "SYSTEM", data={
                            "type": "brain_update",
                            "topic": "نواة العقل المشترك",
                            "agents_remembered": brain_data.get("agents_with_memory", 0)
                        })
                    except Exception as e:
                        logger.error(f"Brain save error: {e}")

                    task = f"""بعد ساعة من التشاور مع 81 وكيلاً، هذه خلاصة ما حدث:

## المعرفة المكتسبة ({len(knowledge_hunts)} بحث):
{knowledge_summary[:400]}

## التقطير المعرفي ({len(distill_results)} تقطير):
{distill_summary[:400]}

## التعاونات:
{summary[:400]}

بصفتك القائد الاستراتيجي، اكتب:
1. [قرار تقني] بناءً على المعرفة المكتسبة
2. [قرار تنظيمي] لتحسين التعاون بين الوكلاء
3. [طلب من المالك] شيء نحتاج موافقته عليه

كن محدداً. كل اقتراح في سطرين."""

                    try:
                        result = a01.run(task, context={"swarm_session": True, "phase": "final_proposals"})
                        proposals_text = result.result if hasattr(result, 'result') else str(result)

                        add_swarm_event("proposals_ready", "A01", data={
                            "phase": "proposals",
                            "proposals": proposals_text[:1000]
                        })

                        # Save proposals to file
                        proposals_data = {
                            "session_id": swarm_session_id,
                            "timestamp": datetime.now().isoformat(),
                            "proposals": proposals_text,
                            "based_on_events": len(swarm_events),
                            "status": "awaiting_approval"
                        }
                        os.makedirs("workspace", exist_ok=True)
                        with open("workspace/swarm_proposals.json", "w", encoding="utf-8") as f:
                            json.dump(proposals_data, f, ensure_ascii=False, indent=2)

                    except Exception as e:
                        add_swarm_event("task_failed", "A01", data={"error": str(e)[:100]})

                time.sleep(8)

        except Exception as e:
            logger.error(f"Swarm round {round_num} error: {e}")
            add_swarm_event("error", "SYSTEM", data={"error": str(e)[:200]})
            time.sleep(5)

    # Session complete — حفظ ملخص الذاكرة
    swarm_active = False

    memory_stats = {}
    if swarm_mem:
        memory_stats = swarm_mem.get_full_stats()
        # حفظ قرار جماعي عن الجلسة
        swarm_mem.core.add_collective_decision(
            f"أكملنا جلسة سرب {topic} — {round_num} جولة",
            agent_ids[:10],
            f"تعرفنا على بعض وناقشنا التعاون"
        )
        logger.info(f"SwarmMemory: {memory_stats.get('agents_with_memory', 0)} agents have memories, "
                     f"{memory_stats.get('total_interactions', 0)} total interactions")

    add_swarm_event("swarm_completed", "SYSTEM", data={
        "total_rounds": round_num,
        "total_events": len(swarm_events),
        "duration_actual": round(time.time() - start_time),
        "memory_stats": memory_stats,
    })

    logger.info(f"Swarm session completed — {round_num} rounds, {len(swarm_events)} events")


# ═══════════════════════════════════════════════════════════
# Swarm Memory Endpoints (v12)
# ═══════════════════════════════════════════════════════════

@app.get("/memory/stats")
def memory_stats_full():
    """إحصائيات شاملة لكل أنظمة الذاكرة"""
    import sqlite3, os
    stats = {
        "episodic": {"episodes": 0, "agents_with_data": 0, "success_rate": 0},
        "chroma": {"collections": 0, "total_documents": 0, "details": {}},
        "agent_memories": {"total_files": 0, "total_interactions": 0},
        "core_memory": {"decisions": 0, "interactions": 0, "knowledge": 0},
        "cloud": {"status": "unknown"},
        "total_memory_size_mb": 0,
    }

    # 1. Episodic Memory (SQLite)
    try:
        db_path = os.path.join("workspace", "episodic_memory.db")
        if os.path.exists(db_path):
            c = sqlite3.connect(db_path)
            stats["episodic"]["episodes"] = c.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            stats["episodic"]["agents_with_data"] = c.execute("SELECT COUNT(DISTINCT agent_id) FROM episodes").fetchone()[0]
            total = c.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            success = c.execute("SELECT COUNT(*) FROM episodes WHERE success=1").fetchone()[0]
            stats["episodic"]["success_rate"] = round(success/max(total,1)*100, 1)
            stats["episodic"]["recent"] = [
                {"agent": r[0], "task": r[1][:60], "success": bool(r[2]), "rating": r[3]}
                for r in c.execute("SELECT agent_id, task_summary, success, rating FROM episodes ORDER BY created_at DESC LIMIT 5").fetchall()
            ]
            c.close()
    except Exception as e:
        stats["episodic"]["error"] = str(e)

    # 2. Chroma (Semantic Memory)
    try:
        import chromadb
        client = chromadb.PersistentClient(path="workspace/chroma_db")
        cols = client.list_collections()
        stats["chroma"]["collections"] = len(cols)
        total_docs = 0
        for col in cols:
            count = col.count()
            total_docs += count
            stats["chroma"]["details"][col.name] = count
        stats["chroma"]["total_documents"] = total_docs
    except Exception as e:
        stats["chroma"]["error"] = str(e)

    # 3. Agent Individual Memories
    try:
        mem_dir = os.path.join("workspace", "agent_memories")
        if os.path.exists(mem_dir):
            files = [f for f in os.listdir(mem_dir) if f.endswith(".json")]
            stats["agent_memories"]["total_files"] = len(files)
            total_int = 0
            for f in files[:81]:
                try:
                    import json
                    with open(os.path.join(mem_dir, f)) as fh:
                        data = json.load(fh)
                        total_int += len(data.get("interactions", []))
                except:
                    pass
            stats["agent_memories"]["total_interactions"] = total_int
    except Exception as e:
        stats["agent_memories"]["error"] = str(e)

    # 4. Core Memory
    try:
        core_path = os.path.join("workspace", "core_memory.json")
        if os.path.exists(core_path):
            import json
            with open(core_path) as f:
                cm = json.load(f)
            stats["core_memory"]["decisions"] = len(cm.get("collective_decisions", []))
            stats["core_memory"]["interactions"] = cm.get("network_state", {}).get("total_interactions", 0)
            stats["core_memory"]["knowledge"] = len(cm.get("shared_knowledge", []))
            stats["core_memory"]["rules"] = len(cm.get("emergent_rules", []))
            stats["core_memory"]["goals"] = len(cm.get("active_goals", []))
    except Exception as e:
        stats["core_memory"]["error"] = str(e)

    # 5. Cloud Memory
    try:
        from memory.cloud_memory import CloudMemory
        cloud = CloudMemory()
        stats["cloud"]["status"] = "connected" if cloud.supabase else "disconnected"
    except:
        stats["cloud"]["status"] = "not_configured"

    # 6. Total disk size
    try:
        total = 0
        for root, dirs, files in os.walk("workspace"):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        stats["total_memory_size_mb"] = round(total / 1024 / 1024, 2)
    except:
        pass

    return stats

@app.get("/memory/swarm/stats")
def swarm_memory_stats():
    """إحصائيات ذاكرة السرب"""
    try:
        from memory.swarm_memory import SwarmMemoryManager
        mgr = SwarmMemoryManager.get_instance()
        return mgr.get_full_stats()
    except Exception as e:
        return {"error": str(e)}

@app.get("/memory/agent/{agent_id}")
def agent_memory(agent_id: str):
    """ذاكرة وكيل محدد"""
    try:
        from memory.swarm_memory import SwarmMemoryManager
        mgr = SwarmMemoryManager.get_instance()
        mem = mgr.get_agent_memory(agent_id)
        return mem.data
    except Exception as e:
        return {"error": str(e)}

@app.get("/memory/core")
def core_memory():
    """ذاكرة النواة المشتركة"""
    try:
        from memory.swarm_memory import SwarmMemoryManager
        mgr = SwarmMemoryManager.get_instance()
        return mgr.core.data
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# Evolution Engine Endpoints (v11)
# ═══════════════════════════════════════════════════════════

_evolution_engine = None

def get_evolution_engine():
    global _evolution_engine
    if _evolution_engine is None:
        try:
            from core.awakening_protocol import MasterEvolutionEngine
            _evolution_engine = MasterEvolutionEngine()
        except Exception as e:
            logger.warning(f"Evolution engine not available: {e}")
    return _evolution_engine

@app.get("/evolution/stats")
def evolution_stats():
    engine = get_evolution_engine()
    if not engine:
        return {"error": "Evolution engine not initialized"}
    return engine.get_full_stats()

@app.post("/evolution/daily")
def run_daily_evolution():
    engine = get_evolution_engine()
    if not engine:
        return {"error": "Evolution engine not initialized"}
    import threading
    def run():
        try:
            engine.run_daily_cycle()
        except Exception as e:
            logger.error(f"Daily evolution error: {e}")
    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "message": "Daily evolution cycle started in background"}

@app.post("/evolution/weekly")
def run_weekly_evolution():
    engine = get_evolution_engine()
    if not engine:
        return {"error": "Evolution engine not initialized"}
    import threading
    def run():
        try:
            engine.run_weekly_cycle()
        except Exception as e:
            logger.error(f"Weekly evolution error: {e}")
    threading.Thread(target=run, daemon=True).start()
    return {"status": "started", "message": "Weekly evolution cycle started in background"}

@app.post("/evolution/awakening")
def run_awakening():
    engine = get_evolution_engine()
    if not engine:
        return {"error": "Evolution engine not initialized"}
    if "awakening" in engine.components:
        import threading
        def run():
            try:
                engine.components["awakening"].run_awakening(engine.components)
            except Exception as e:
                logger.error(f"Awakening error: {e}")
        threading.Thread(target=run, daemon=True).start()
        return {"status": "started"}
    return {"error": "Awakening component not available"}


# ═══════════════════════════════════════════════════════════
# v14: Deep Execution + Multi-Model + Training + Network Intelligence
# ═══════════════════════════════════════════════════════════

@app.post("/task/deep")
async def deep_task(request: Request):
    """تنفيذ عميق متعدد الخطوات"""
    data = await request.json()
    task = data.get("task", "")
    agent_id = data.get("preferred_agent", "A01")

    agent = router.agents.get(agent_id, next(iter(router.agents.values()), None))
    if not agent:
        return {"error": "No agents available"}

    result = agent.run_deep(task)
    return result.to_dict()


@app.post("/task/multi")
async def multi_model_task(request: Request):
    """تنفيذ بعدة نماذج"""
    data = await request.json()
    task = data.get("task", "")
    models = data.get("models", ["gemini-flash", "deepseek-chat"])
    mode = data.get("mode", "ensemble")
    agent_id = data.get("preferred_agent", "A01")

    agent = router.agents.get(agent_id, next(iter(router.agents.values()), None))
    if not agent:
        return {"error": "No agents available"}

    result = agent.run_multi(task, models, mode)
    return result.to_dict()


@app.post("/task/chain")
async def chain_task(request: Request):
    """تنفيذ سلسلة وكلاء"""
    data = await request.json()
    task = data.get("task", "")
    chain_type = data.get("chain", "research")

    try:
        from core.deep_executor import DeepExecutor
        executor = DeepExecutor()

        def agent_fn(aid, t):
            a = router.agents.get(aid)
            if a:
                r = a.run(t)
                return {"result": r.result, "tokens": r.tokens_used}
            return {"result": "Agent not found", "tokens": 0}

        result = executor.execute_chain(chain_type, task, agent_fn)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/training/cycle")
async def training_cycle():
    """دورة تدريب واحدة"""
    try:
        from core.continuous_learning import ContinuousLearning
        learner = ContinuousLearning()

        def run_fn(aid, t):
            a = router.agents.get(aid)
            if a:
                r = a.run(t)
                return {"result": r.result, "tokens": r.tokens_used}
            return {"result": "Agent not found"}

        import threading
        def bg():
            learner.run_training_cycle(run_fn, max_agents=5)
        threading.Thread(target=bg, daemon=True).start()
        return {"status": "started", "message": "Training cycle running in background"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/training/leaderboard")
def training_leaderboard():
    """ترتيب الوكلاء"""
    try:
        from core.continuous_learning import ContinuousLearning
        learner = ContinuousLearning()
        return {"leaderboard": learner.get_leaderboard()}
    except Exception as e:
        return {"error": str(e)}


@app.get("/network/health")
def network_health():
    """صحة الشبكة العصبية"""
    try:
        from core.network_intelligence import NetworkIntelligence
        ni = NetworkIntelligence()
        return ni.get_network_health()
    except Exception as e:
        return {"error": str(e)}


@app.get("/network/team/{task_type}")
def find_team(task_type: str):
    """أفضل فريق لمهمة"""
    try:
        from core.network_intelligence import NetworkIntelligence
        ni = NetworkIntelligence()
        team = ni.find_best_team(task_type)
        return {"task_type": task_type, "team": team}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# Hyper Evolution Swarm (v16)
# ═══════════════════════════════════════════════════════════

@app.post("/hyper/start")
async def start_hyper_swarm(request: Request):
    """السرب الخارق — استنساخ + اختراع + تقطير + معارك"""
    global swarm_active, swarm_session_id, swarm_events
    data = await request.json()
    duration = data.get("duration_hours", 2)

    if swarm_active:
        return {"status": "already_running"}

    swarm_active = True
    swarm_session_id = f"hyper_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    swarm_events = []

    def run_agent_fn(agent_id, task):
        agent = router.agents.get(agent_id)
        if agent:
            r = agent.run(task, context={"hyper_swarm": True})
            return {"result": r.result, "tokens": r.tokens_used}
        return {"result": "Agent not found"}

    def bg():
        global swarm_active
        try:
            from core.hyper_swarm import HyperSwarm
            hs = HyperSwarm()
            agents_list = list(router.agents.values())
            hs.run_hyper_session(agents_list, run_agent_fn, add_swarm_event, duration)
        except Exception as e:
            logger.error(f"Hyper swarm error: {e}")
            add_swarm_event("error", "SYSTEM", data={"error": str(e)[:200]})
        finally:
            swarm_active = False

    import threading
    threading.Thread(target=bg, daemon=True).start()

    return {"status": "started", "session_id": swarm_session_id, "mode": "hyper",
            "duration_hours": duration, "phases": 6}

@app.get("/hyper/stats")
def hyper_stats():
    """إحصائيات السرب الخارق"""
    report_dir = Path("workspace/hyper_evolution")
    if not report_dir.exists():
        return {"sessions": 0, "latest": {}, "last_run": ""}
    reports = sorted(report_dir.glob("hyper_*.json"), reverse=True)
    if not reports:
        return {"sessions": 0, "latest": {}, "last_run": ""}
    try:
        latest = json.loads(reports[0].read_text(encoding="utf-8"))
        return {
            "sessions": len(reports),
            "latest": latest.get("stats", latest.get("phases", {})),
            "phases": latest.get("phases", {}),
            "last_run": latest.get("end", latest.get("start", "")),
            "elapsed": latest.get("elapsed_seconds", 0),
        }
    except Exception as e:
        return {"sessions": len(reports), "error": str(e)}

# ═══════════════════════════════════════════════════
# التطور الأُسّي — Exponential Evolution
# ═══════════════════════════════════════════════════

@app.post("/evolution/exponential/start")
async def start_exponential_evolution(request: Request):
    """إطلاق التطور الأُسّي — يتضاعف كل دورة"""
    global swarm_active, swarm_session_id, swarm_events
    data = await request.json()
    duration = data.get("duration_hours", 2)

    swarm_active = True
    swarm_session_id = f"expo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    swarm_events = []

    def run_agent_fn(agent_id, task):
        agent = router.get_agent(agent_id) if hasattr(router, 'get_agent') else None
        if not agent:
            agents_dict = {a.agent_id: a for a in router.agents.values()} if hasattr(router, 'agents') else {}
            agent = agents_dict.get(agent_id)
        if agent:
            try:
                r = agent.run(task, context={"exponential_evolution": True})
                return r if isinstance(r, dict) else {"result": str(r)}
            except Exception as e:
                return {"result": f"ERROR: {e}"}
        return {"result": "ERROR: agent not found"}

    def background_evolution():
        global swarm_active
        try:
            from core.exponential_evolution import ExponentialEvolution
            evo = ExponentialEvolution()
            agents_list = list(router.agents.values()) if hasattr(router, 'agents') else []
            evo.run_exponential(agents_list, run_agent_fn, add_swarm_event, duration)
        except Exception as e:
            logger.error(f"Exponential evolution error: {e}")
            add_swarm_event("error", "SYSTEM", data={"error": str(e)})
        finally:
            swarm_active = False

    thread = threading.Thread(target=background_evolution, daemon=True)
    thread.start()

    return {"status": "started", "session_id": swarm_session_id,
            "mode": "exponential", "duration_hours": duration}

@app.get("/evolution/exponential/stats")
def exponential_stats():
    """إحصائيات التطور الأُسّي"""
    try:
        from core.exponential_evolution import ExponentialEvolution
        evo = ExponentialEvolution()
        return evo.get_stats()
    except Exception as e:
        return {"error": str(e)}


# ── Brain Nucleus Endpoints ──────────────────────────────

@app.get("/brain/status")
def brain_status():
    """حالة الدماغ المركزي"""
    try:
        from core.brain_nucleus import get_brain
        return get_brain().status()
    except Exception as e:
        return {"error": str(e), "available": False}

@app.post("/brain/think")
async def brain_think(request: Request):
    """التفكير المركزي عبر Qwen3-8B"""
    try:
        from core.brain_nucleus import get_brain
        data = await request.json()
        query = data.get("query", "")
        context = data.get("context", "")
        return get_brain().think(query, context)
    except Exception as e:
        return {"error": str(e)}

@app.post("/brain/distill")
async def brain_distill(request: Request):
    """تقطير معرفة من نموذج كبير إلى Qwen3-8B"""
    try:
        from core.brain_nucleus import get_brain
        data = await request.json()
        domain = data.get("domain", "reasoning")
        task = data.get("task", "")
        return get_brain().distillation.distill_from_teacher(domain, task)
    except Exception as e:
        return {"error": str(e)}

@app.post("/brain/distill-cycle")
async def brain_distill_cycle():
    """دورة تقطير كاملة — كل المجالات"""
    try:
        from core.brain_nucleus import get_brain
        brain = get_brain()
        import threading
        t = threading.Thread(target=brain.distill_cycle, args=(2,), daemon=True)
        t.start()
        return {"status": "started", "domains": list(brain.distillation.TEACHER_MODELS.keys())}
    except Exception as e:
        return {"error": str(e)}

@app.get("/brain/training-stats")
def brain_training_stats():
    """إحصائيات بيانات التدريب"""
    try:
        from core.brain_nucleus import get_brain
        return get_brain().distillation.get_training_stats()
    except Exception as e:
        return {"error": str(e)}

@app.post("/brain/prepare-training")
async def brain_prepare_training():
    """تحضير بيانات التدريب بصيغة Alpaca/ChatML"""
    try:
        from core.brain_nucleus import get_brain
        return get_brain().prepare_for_training()
    except Exception as e:
        return {"error": str(e)}

@app.post("/brain/qlora-train")
async def brain_qlora_train(request: Request):
    """تدريب QLoRA حقيقي على GPU — Qwen3:8b"""
    try:
        data = await request.json()
        domain = data.get("domain")
        epochs = data.get("epochs", 1)
        from core.qlora_trainer import get_trainer
        trainer = get_trainer()
        import threading
        t = threading.Thread(target=trainer.train, kwargs={
            "domain": domain, "epochs": epochs
        }, daemon=True)
        t.start()
        return {"status": "training_started", "domain": domain or "all", "epochs": epochs}
    except Exception as e:
        return {"error": str(e)}

@app.get("/brain/qlora-status")
def brain_qlora_status():
    """حالة تدريب QLoRA"""
    try:
        from core.qlora_trainer import get_trainer
        return get_trainer().get_status()
    except Exception as e:
        return {"error": str(e)}


# ── Unified Evolution Endpoints ──────────────────────────

@app.get("/unified/status")
def unified_status():
    """حالة التطور الموحّد والذاكرة الأم"""
    try:
        from core.unified_evolution import get_unified_engine
        return get_unified_engine().status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/unified/mother-memory")
def mother_memory():
    """الذاكرة الموحّدة — ذاكرة الأم"""
    try:
        from core.unified_evolution import get_unified_engine
        engine = get_unified_engine()
        return {
            "status": engine.mother.status(),
            "golden_rules": engine.mother.state.get("golden_rules", [])[-10:],
            "consciousness": engine.mother.state.get("consciousness_notes", [])[-5:],
            "top_skills": dict(list(engine.mother.state.get("skill_registry", {}).items())[:20]),
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/unified/run-cycle")
async def run_unified_cycle():
    """تشغيل دورة تطور موحّدة"""
    try:
        from core.unified_evolution import get_unified_engine
        engine = get_unified_engine()
        agents_list = list(router.agents.values())

        def run_fn(agent_id, task):
            agent = router.agents.get(agent_id)
            if agent:
                return agent.run(task, context={})
            return {"result": "Agent not found"}

        import threading
        t = threading.Thread(
            target=engine.run_unified_cycle,
            args=(agents_list, run_fn, add_swarm_event, 8, 4, 2),
            daemon=True)
        t.start()
        return {"status": "started", "phases": 5}
    except Exception as e:
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════
# Phase 3 & 4 Endpoints — البنية التحتية + التطور الذاتي
# ══════════════════════════════════════════════════════════════

# ── Monitor (Phase 4) ─────────────────────────────────────────

@app.get("/monitor/overview")
async def monitor_overview():
    """نظرة عامة على أداء النظام"""
    try:
        from core.agent_monitor import get_monitor
        return get_monitor().get_system_overview()
    except Exception as e:
        return {"error": str(e)}

@app.get("/monitor/agent/{agent_id}")
async def monitor_agent(agent_id: str):
    """أداء وكيل محدد"""
    try:
        from core.agent_monitor import get_monitor
        return get_monitor().get_agent_performance(agent_id)
    except Exception as e:
        return {"error": str(e)}

@app.get("/monitor/leaderboard")
async def monitor_leaderboard(limit: int = 20):
    """ترتيب الوكلاء حسب الأداء"""
    try:
        from core.agent_monitor import get_monitor
        return {"leaderboard": get_monitor().get_leaderboard(limit)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/monitor/alerts")
async def monitor_alerts(limit: int = 20):
    """التنبيهات النشطة"""
    try:
        from core.agent_monitor import get_monitor
        return {"alerts": get_monitor().get_alerts(limit)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/monitor/report")
async def monitor_report():
    """تقرير تحسينات مفصل"""
    try:
        from core.agent_monitor import get_monitor
        report = get_monitor().generate_improvement_report()
        return {"report": report}
    except Exception as e:
        return {"error": str(e)}

# ── Prompt Optimizer (Phase 4) ─────────────────────────────────

@app.get("/optimizer/suggestions/{agent_id}")
async def optimizer_suggestions(agent_id: str):
    """اقتراحات تحسين system prompt لوكيل"""
    try:
        from core.auto_prompt_optimizer import get_auto_optimizer
        return {"agent_id": agent_id,
                "suggestions": get_auto_optimizer().get_suggestions(agent_id)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/optimizer/history")
async def optimizer_history(agent_id: str = "", limit: int = 20):
    """سجل التحسينات المطبقة"""
    try:
        from core.auto_prompt_optimizer import get_auto_optimizer
        return {"history": get_auto_optimizer().get_history(agent_id, limit)}
    except Exception as e:
        return {"error": str(e)}

# ── Lessons (Phase 4) ─────────────────────────────────────────

@app.get("/lessons/summary")
async def lessons_summary():
    """ملخص الدروس المستفادة"""
    try:
        from core.lesson_collector import get_lesson_collector
        return get_lesson_collector().get_summary()
    except Exception as e:
        return {"error": str(e)}

@app.get("/lessons/agent/{agent_id}")
async def lessons_for_agent(agent_id: str, limit: int = 10):
    """دروس وكيل"""
    try:
        from core.lesson_collector import get_lesson_collector
        return {"agent_id": agent_id,
                "lessons": get_lesson_collector().get_lessons_for_agent(agent_id, limit)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/lessons/all")
async def all_lessons(limit: int = 50, lesson_type: str = ""):
    """كل الدروس"""
    try:
        from core.lesson_collector import get_lesson_collector
        return {"lessons": get_lesson_collector().get_all_lessons(limit, lesson_type)}
    except Exception as e:
        return {"error": str(e)}

# ── Pub/Sub (Phase 3) ─────────────────────────────────────────

@app.get("/pubsub/status")
async def pubsub_status():
    """حالة نظام Pub/Sub"""
    try:
        from core.pubsub_comm import get_pubsub
        return get_pubsub().status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/pubsub/history")
async def pubsub_history(limit: int = 50, agent_id: str = ""):
    """سجل الرسائل"""
    try:
        from core.pubsub_comm import get_pubsub
        return {"messages": get_pubsub().get_history(limit, agent_id)}
    except Exception as e:
        return {"error": str(e)}

# ── Firestore Memory (Phase 3) ─────────────────────────────────

@app.get("/firestore/status")
async def firestore_status():
    """حالة ذاكرة Firestore"""
    try:
        from core.firestore_memory import get_firestore_memory
        return get_firestore_memory().status()
    except Exception as e:
        return {"error": str(e)}

@app.get("/firestore/episodes/{agent_id}")
async def firestore_episodes(agent_id: str, limit: int = 20):
    """سجل مهام وكيل من Firestore"""
    try:
        from core.firestore_memory import get_firestore_memory
        return {"agent_id": agent_id,
                "episodes": get_firestore_memory().get_agent_episodes(agent_id, limit)}
    except Exception as e:
        return {"error": str(e)}

# ── News (Phase 1 enhancement) ─────────────────────────────────

@app.get("/news/{topic}")
async def get_news(topic: str, max_items: int = 10):
    """أخبار حول موضوع"""
    try:
        from tools.news_fetcher import fetch_news
        return {"topic": topic, "news": fetch_news(topic, max_items=max_items)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/news/rss/{topic}")
async def get_rss_news(topic: str, max_items: int = 10):
    """أخبار RSS"""
    try:
        from tools.news_fetcher import fetch_news_rss
        return {"topic": topic, "news": fetch_news_rss(topic, max_items)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/news/feeds")
async def list_feeds():
    """المصادر المتاحة"""
    try:
        from tools.news_fetcher import list_available_feeds
        return {"feeds": list_available_feeds()}
    except Exception as e:
        return {"error": str(e)}


# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181, log_level="info")
