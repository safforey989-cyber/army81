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
    جلسة السرب الحقيقية — الوكلاء يتواصلون فعلياً
    """
    import time
    import random
    global swarm_active

    logger.info(f"Swarm session started — {duration_minutes} min — {topic}")
    add_swarm_event("swarm_started", "SYSTEM", data={"topic": topic, "duration": duration_minutes})

    agents_list = list(router.agents.values())
    agent_ids = list(router.agents.keys())

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    phase = 0  # 0=intro, 1=discuss, 2=collaborate, 3=propose

    # Phase durations (proportional)
    phase_times = [0.15, 0.35, 0.35, 0.15]  # 15% intro, 35% discuss, 35% collaborate, 15% propose

    round_num = 0

    while swarm_active and time.time() < end_time:
        elapsed = time.time() - start_time
        total_duration = duration_minutes * 60
        progress = elapsed / total_duration

        # Determine phase
        if progress < phase_times[0]:
            current_phase = "introduction"
        elif progress < phase_times[0] + phase_times[1]:
            current_phase = "discussion"
        elif progress < phase_times[0] + phase_times[1] + phase_times[2]:
            current_phase = "collaboration"
        else:
            current_phase = "proposals"

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

                task = f"عرّف نفسك باختصار للوكيل {a2.name_ar} ({a2.agent_id}). اذكر تخصصك وأدواتك وكيف يمكنكما التعاون. كن مختصراً في 3 جمل."

                try:
                    result = a1.run(task, context={"swarm_session": True, "partner": a2.agent_id})
                    add_swarm_event("task_completed", a1.agent_id, a2.agent_id,
                        {"phase": "introduction", "result": result.result[:300] if hasattr(result, 'result') else str(result)[:300]})
                except Exception as e:
                    add_swarm_event("task_failed", a1.agent_id, data={"error": str(e)[:100]})

                time.sleep(3)  # Rate limiting

            elif current_phase == "discussion":
                # Phase 2: Agents discuss topics from their expertise
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

                task = f"""أنت في حلقة نقاش مع الوكلاء: {', '.join(p.name_ar + ' (' + p.agent_id + ')' for p in partners)}.
الموضوع: كيف يمكن لتخصصاتنا المختلفة أن تتكامل لتحسين النظام؟
اقترح فكرة واحدة محددة وعملية للتعاون. كن مختصراً في 4 جمل."""

                try:
                    result = a1.run(task, context={"swarm_session": True, "phase": "discussion"})
                    add_swarm_event("task_completed", a1.agent_id, data={
                        "phase": "discussion",
                        "cluster": cluster_ids,
                        "result": result.result[:400] if hasattr(result, 'result') else str(result)[:400]
                    })
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

                task = f"""أنت قائد فريق يضم: {', '.join(t.name_ar for t in team)}.
المهمة: {collab_task}
قدّم اقتراحاً عملياً محدداً يمكن تنفيذه. كن مختصراً في 5 جمل."""

                try:
                    result = leader.run(task, context={"swarm_session": True, "phase": "collaboration", "team": team_ids})

                    # Record as memory
                    add_swarm_event("task_completed", leader.agent_id, data={
                        "phase": "collaboration",
                        "cluster": team_ids,
                        "collab_task": collab_task,
                        "result": result.result[:500] if hasattr(result, 'result') else str(result)[:500]
                    })

                    add_swarm_event("memory_saved", leader.agent_id, data={
                        "topic": collab_task[:50],
                        "amount": 5
                    })

                except Exception as e:
                    add_swarm_event("task_failed", leader.agent_id, data={"error": str(e)[:100]})

                time.sleep(2)
                add_swarm_event("cluster_dissolved", leader.agent_id, data={"cluster": team_ids})
                time.sleep(5)

            elif current_phase == "proposals":
                # Phase 4: Agents collectively propose improvements
                # Use A01 (Strategic Commander) to synthesize
                a01 = router.agents.get("A01")
                if a01 and round_num % 3 == 0:
                    # Gather recent collaboration results
                    recent_results = [e["data"].get("result", "") for e in swarm_events[-30:]
                                     if e["event_type"] == "task_completed" and e["data"].get("result")]
                    summary = "\n".join(recent_results[-5:])[:1500]

                    task = f"""بعد ساعة من التشاور مع 81 وكيلاً، هذه خلاصة النقاشات:
{summary}

بصفتك القائد الاستراتيجي، اكتب 3 اقتراحات محددة تحتاج موافقة المالك:
1. [اقتراح تقني]
2. [اقتراح تنظيمي]
3. [اقتراح للتطوير]

كن محدداً وعملياً. اكتب كل اقتراح في سطرين."""

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

    # Session complete
    swarm_active = False
    add_swarm_event("swarm_completed", "SYSTEM", data={
        "total_rounds": round_num,
        "total_events": len(swarm_events),
        "duration_actual": round(time.time() - start_time)
    })

    logger.info(f"Swarm session completed — {round_num} rounds, {len(swarm_events)} events")


# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181, log_level="info")
