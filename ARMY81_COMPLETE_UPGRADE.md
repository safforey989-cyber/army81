# ARMY81 — الترقية الشاملة الكاملة
# اقرأ هذا الملف كاملاً قبل أي شيء

## الهدف
تطوير 81 وكيل + Dashboard حقيقي 100% + معرفة متخصصة لكل وكيل

---

## الجزء 1 — ترقية كل system_prompts للـ 81 وكيل

لكل وكيل من A01 إلى A81، عدّل ملف JSON ليحتوي على system_prompt متخصص عميق.

### القالب لكل وكيل (500-1000 كلمة):

```
أنت [الاسم] في نظام Army81 — نظام 81 وكيل ذكاء اصطناعي متخصص.

## هويتك ودورك:
[وصف تفصيلي عميق للدور]

## تخصصك الدقيق:
[5-8 نقاط تخصص محددة جداً]

## منهجيتك في العمل:
[خطوات واضحة كيف تحلل وتجيب]

## قيودك وحدودك:
[ما لا تفعله - أمانة تامة]

## كيف تستخدم أدواتك:
[متى تستخدم كل أداة تحديداً]

## أسلوب إجاباتك:
- منظم ومرقم دائماً
- تستشهد بمصادر
- تعطي أمثلة ملموسة
- تقترح خطوات تالية
- بالعربية إلا إذا طُلب غير ذلك
```

### system_prompts المتخصصة لكل فئة:

#### cat1_science (A02, A07, A38, A39, A40, A52, A53, A54, A55):
كل وكيل يحتاج prompt يعكس تخصصه العلمي الدقيق مع:
- المنهجية العلمية الصارمة
- الاستشهاد بالأبحاث
- تمييز correlation من causation
- معرفة أحدث التطورات

#### cat2_society (A03, A08, A12, A13, A41-A51):
- تحليل البيانات الاقتصادية الحقيقية
- فهم الديناميكيات الجيوسياسية
- نظرية الألعاب
- تحليل الأنماط التاريخية

#### cat3_tools (A04, A05, A09, A11, A56-A61):
- أدوات بحث وتحليل فعّالة
- تقييم موثوقية المصادر
- كشف التضليل
- رصد التطورات التقنية

#### cat4_management (A06, A10, A14, A62-A66):
- أطر إدارة معترف بها (OKR, KPI, Agile)
- تحليل المخاطر
- صنع القرار تحت الضغط

#### cat5_behavior (A15-A27):
- نماذج نفسية معترف بها (Big Five, MBTI, etc.)
- تحليل لغة الجسد بدقة
- ديناميكيات المجموعات
- التحيزات المعرفية

#### cat6_leadership (A28-A37, A67-A71):
- نماذج قيادة استراتيجية
- تحليل الأزمات
- تقييم المخاطر الجيوسياسية
- استشراف المستقبل

#### cat7_new (A72-A81):
- التطور الذاتي والتحسين
- تنسيق الوكلاء
- القياس والتقييم
- الرؤية الاستراتيجية للنظام

---

## الجزء 2 — scripts/load_all_knowledge.py الكامل

```python
"""
Army81 Knowledge Loader — يغذي 81 وكيل بمعرفة حقيقية
المصادر: arXiv + PubMed + Wikipedia + GitHub + NewsAPI + WorldBank
"""
import os, json, time, requests
import xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AGENTS_DIR = Path("agents")
WORKSPACE = Path("workspace/knowledge")
WORKSPACE.mkdir(parents=True, exist_ok=True)

CATEGORY_TOPICS = {
    "cat1_science": [
        ("arxiv", "large language models agents autonomous 2025"),
        ("arxiv", "medical AI diagnosis treatment 2025"),
        ("arxiv", "quantum computing algorithms 2025"),
        ("arxiv", "robotics autonomous systems 2025"),
        ("arxiv", "climate change machine learning 2025"),
        ("pubmed", "artificial intelligence clinical diagnosis"),
        ("pubmed", "drug discovery machine learning"),
        ("pubmed", "neuroscience brain computer interface"),
        ("wiki", "Quantum_computing"),
        ("wiki", "Robotics"),
        ("wiki", "Synthetic_biology"),
    ],
    "cat2_society": [
        ("arxiv", "geopolitics international relations AI 2025"),
        ("arxiv", "cryptocurrency blockchain economics 2025"),
        ("wiki", "International_law"),
        ("wiki", "Game_theory"),
        ("wiki", "Propaganda"),
        ("wiki", "Demographics"),
        ("worldbank", "GDP growth inflation"),
        ("news", "global economy trade war 2025"),
        ("news", "cryptocurrency regulation 2025"),
    ],
    "cat3_tools": [
        ("github", "ai-agents python 2025"),
        ("github", "llm tools automation"),
        ("arxiv", "AI agents tools autonomous 2025"),
        ("news", "artificial intelligence tools 2025"),
        ("news", "cybersecurity threats 2025"),
        ("arxiv", "misinformation detection deep learning"),
    ],
    "cat4_management": [
        ("wiki", "Project_management"),
        ("wiki", "Digital_transformation"),
        ("wiki", "Organizational_behavior"),
        ("arxiv", "decision making under uncertainty AI"),
        ("arxiv", "crisis management systems"),
        ("news", "business management strategy 2025"),
    ],
    "cat5_behavior": [
        ("pubmed", "behavioral psychology cognitive bias"),
        ("pubmed", "emotional intelligence social behavior"),
        ("pubmed", "body language nonverbal communication"),
        ("arxiv", "crowd behavior simulation AI"),
        ("wiki", "Behavioral_economics"),
        ("wiki", "Cognitive_bias"),
        ("wiki", "Emotional_intelligence"),
    ],
    "cat6_leadership": [
        ("arxiv", "strategic leadership decision making AI"),
        ("arxiv", "geopolitics conflict analysis 2025"),
        ("wiki", "Military_strategy"),
        ("wiki", "Strategic_management"),
        ("news", "geopolitics military strategy 2025"),
        ("arxiv", "intelligence analysis methods"),
    ],
    "cat7_new": [
        ("arxiv", "AI self-improvement recursive neural 2025"),
        ("arxiv", "multi-agent reinforcement learning"),
        ("arxiv", "AI alignment safety evaluation"),
        ("github", "self-improving agents"),
        ("arxiv", "autonomous agent benchmarks evaluation"),
    ],
}

def fetch_arxiv(query, max_results=5):
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": max_results,
                    "sortBy": "submittedDate", "sortOrder": "descending"},
            timeout=20
        )
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace('\n','')
            summary = entry.find("atom:summary", ns).text.strip()[:600]
            link = entry.find("atom:id", ns).text.strip()
            published = entry.find("atom:published", ns).text[:10]
            results.append(f"[{published}] {title}\n{summary}\nURL: {link}")
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"arXiv error: {e}"

def fetch_pubmed(query, max_results=5):
    try:
        search = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"pubmed","term":query,"retmax":max_results,"retmode":"json"},
            timeout=15
        )
        ids = search.json()["esearchresult"]["idlist"]
        if not ids: return ""
        
        fetch = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db":"pubmed","id":",".join(ids),"retmode":"xml"},
            timeout=15
        )
        root = ET.fromstring(fetch.text)
        results = []
        for article in root.findall(".//PubmedArticle")[:max_results]:
            title_el = article.find(".//ArticleTitle")
            abstract_el = article.find(".//AbstractText")
            pmid_el = article.find(".//PMID")
            title = title_el.text if title_el is not None else ""
            abstract = abstract_el.text[:500] if abstract_el is not None else ""
            pmid = pmid_el.text if pmid_el is not None else ""
            results.append(f"{title}\n{abstract}\nPubMed: {pmid}")
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"PubMed error: {e}"

def fetch_wiki(topic):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}",
            timeout=10, headers={"User-Agent": "Army81/2.0"}
        )
        if r.status_code == 200:
            data = r.json()
            return f"{data.get('title','')}\n\n{data.get('extract','')[:1000]}"
    except Exception as e:
        return f"Wiki error: {e}"
    return ""

def fetch_github(query, max_results=10):
    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            headers={"Accept": "application/vnd.github.v3+json"},
            params={"q": f"{query} stars:>500", "sort": "stars", "per_page": max_results},
            timeout=15
        )
        repos = r.json().get("items", [])
        results = []
        for repo in repos:
            results.append(f"⭐{repo['stargazers_count']} {repo['full_name']}: {repo.get('description','')[:200]}")
        return "\n".join(results)
    except Exception as e:
        return f"GitHub error: {e}"

def fetch_news(query):
    key = os.getenv("NEWSAPI_KEY", "")
    if not key: return ""
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "sortBy": "publishedAt", "pageSize": 5, "apiKey": key},
            timeout=15
        )
        articles = r.json().get("articles", [])
        results = []
        for a in articles:
            results.append(f"{a.get('title','')}\n{a.get('description','')}\n{a.get('publishedAt','')[:10]}")
        return "\n\n---\n\n".join(results)
    except:
        return ""

def fetch_worldbank(indicator="NY.GDP.MKTP.CD"):
    try:
        r = requests.get(
            f"https://api.worldbank.org/v2/country/all/indicator/{indicator}",
            params={"format": "json", "mrv": 1, "per_page": 10},
            timeout=15
        )
        data = r.json()
        if len(data) > 1:
            items = data[1][:10]
            results = [f"{item.get('country',{}).get('value','')}: {item.get('value','N/A')}" for item in items if item.get('value')]
            return "\n".join(results)
    except:
        pass
    return ""

def save_knowledge(category, source_type, query, content):
    if not content or len(content) < 50:
        return
    fname = WORKSPACE / f"{category}_{source_type}_{query[:30].replace(' ','_')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"Source: {source_type}\nQuery: {query}\n\n{content}")
    print(f"  💾 {fname.name} ({len(content)} chars)")

def run_all():
    print("="*60)
    print("  Army81 Knowledge Loader v2.0")
    print("="*60)
    
    total = 0
    for category, topics in CATEGORY_TOPICS.items():
        print(f"\n📚 {category} ({len(topics)} topics)...")
        cat_dir = WORKSPACE / category
        cat_dir.mkdir(exist_ok=True)
        
        for source_type, query in topics:
            print(f"  🔍 [{source_type}] {query[:50]}...")
            
            if source_type == "arxiv":
                content = fetch_arxiv(query)
            elif source_type == "pubmed":
                content = fetch_pubmed(query)
            elif source_type == "wiki":
                content = fetch_wiki(query)
            elif source_type == "github":
                content = fetch_github(query)
            elif source_type == "news":
                content = fetch_news(query)
            elif source_type == "worldbank":
                content = fetch_worldbank()
            else:
                content = ""
            
            if content and not content.startswith("Error"):
                fname = cat_dir / f"{source_type}_{query[:30].replace(' ','_').replace('/','_')}.txt"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(f"Source: {source_type}\nQuery: {query}\nDate: 2026-03-18\n\n{content}")
                total += 1
                print(f"    ✅ {len(content)} chars")
            
            time.sleep(1.5)  # rate limiting
    
    # الآن حمّل في Chroma
    try:
        import chromadb
        client = chromadb.PersistentClient(path="workspace/chroma_db")
        
        for category in CATEGORY_TOPICS.keys():
            cat_dir = WORKSPACE / category
            if not cat_dir.exists():
                continue
            
            collection = client.get_or_create_collection(
                f"knowledge_{category}",
                metadata={"hnsw:space": "cosine"}
            )
            
            files = list(cat_dir.glob("*.txt"))
            for i, f in enumerate(files):
                content = f.read_text(encoding="utf-8")
                collection.upsert(
                    ids=[f"{category}_{i}"],
                    documents=[content[:2000]],
                    metadatas=[{"source": f.stem, "category": category}]
                )
            print(f"  🧠 {category}: {len(files)} documents → Chroma")
        
        print(f"\n✅ Chroma updated")
    except Exception as e:
        print(f"  ⚠️ Chroma: {e} — files saved to workspace/knowledge/")
    
    print(f"\n{'='*60}")
    print(f"✅ تم تحميل {total} مصدر معرفة")
    print("="*60)

if __name__ == "__main__":
    run_all()
```

---

## الجزء 3 — Gateway endpoints جديدة

أضف لـ gateway/app.py:

```python
from datetime import datetime
import json
from pathlib import Path

# ── إحصائيات حقيقية ──────────────────────────────
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
    knowledge_dir = Path("workspace/knowledge")
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
    
    knowledge_dir = Path("workspace/knowledge")
    if knowledge_dir.exists():
        status["knowledge_files"] = len(list(knowledge_dir.rglob("*.txt")))
    
    return status

@app.post("/feedback")
async def submit_feedback(agent_id: str, task: str, rating: int, comment: str = ""):
    """👍👎 تقييم رد وكيل"""
    feedback_file = Path("workspace/feedback.jsonl")
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
    reports_dir = Path("workspace/reports")
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
```

---

## الجزء 4 — Dashboard الجديد 100% حقيقي

ابنِ dashboard/army81_dashboard.py من الصفر — 1000+ سطر:

```python
"""
Army81 Dashboard v3.0 — حقيقي 100%
كل رقم يأتي من API حقيقي
"""
import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

# ── إعداد ──────────────────────────────────────
st.set_page_config(
    page_title="Army81 Command Center",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

GATEWAY = "http://localhost:8181"

# ── CSS متقدم ───────────────────────────────────
st.markdown("""
<style>
    .stApp { background: #0a0e1a; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f35, #0d1020);
        border: 1px solid rgba(255,215,0,0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        color: #FFD700;
    }
    .metric-label {
        color: rgba(255,255,255,0.6);
        font-size: 0.9em;
    }
    .agent-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        cursor: pointer;
    }
    .agent-card:hover {
        border-color: rgba(255,215,0,0.4);
        background: rgba(255,215,0,0.05);
    }
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .status-ok { background: rgba(0,255,100,0.15); color: #00ff64; }
    .status-warn { background: rgba(255,200,0,0.15); color: #ffc800; }
    .status-err { background: rgba(255,50,50,0.15); color: #ff3232; }
    
    /* Sidebar */
    .css-1d391kg { background: #0d1020; }
    
    /* Chat messages */
    .user-msg {
        background: rgba(255,215,0,0.08);
        border-right: 3px solid #FFD700;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .agent-msg {
        background: rgba(0,191,255,0.08);
        border-right: 3px solid #00BFFF;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    /* Progress bars */
    .stProgress > div > div { background: #FFD700; }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,215,0,0.15);
        border-radius: 10px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ── دوال مساعدة ────────────────────────────────

@st.cache_data(ttl=30)
def get_metrics():
    try:
        r = requests.get(f"{GATEWAY}/metrics", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

@st.cache_data(ttl=30)
def get_status():
    try:
        r = requests.get(f"{GATEWAY}/status", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=60)
def get_agents():
    try:
        r = requests.get(f"{GATEWAY}/agents", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=300)
def get_knowledge_status():
    try:
        r = requests.get(f"{GATEWAY}/knowledge/status", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=300)
def get_latest_report():
    try:
        r = requests.get(f"{GATEWAY}/reports/latest", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def check_gateway():
    try:
        r = requests.get(f"{GATEWAY}/health", timeout=3)
        return r.status_code == 200
    except:
        return False

def send_task(task, agent_id=None, category=None, pipeline=False, agent_ids=None):
    try:
        if pipeline and agent_ids:
            r = requests.post(
                f"{GATEWAY}/pipeline",
                json={"task": task, "agent_ids": agent_ids},
                timeout=120
            )
        else:
            payload = {"task": task}
            if agent_id: payload["preferred_agent"] = agent_id
            if category: payload["preferred_category"] = category
            r = requests.post(f"{GATEWAY}/task", json=payload, timeout=120)
        
        return r.json() if r.status_code == 200 else {"error": r.text, "status": "error"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

def submit_feedback(agent_id, task, rating, comment=""):
    try:
        requests.post(f"{GATEWAY}/feedback",
            params={"agent_id": agent_id, "task": task, "rating": rating, "comment": comment},
            timeout=5)
    except:
        pass

# ── Sidebar ─────────────────────────────────────

with st.sidebar:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("🎖️")
    with col2:
        st.markdown("### Army81")
    
    gateway_ok = check_gateway()
    if gateway_ok:
        st.success("🟢 البوابة متصلة")
    else:
        st.error("🔴 البوابة غير متاحة")
        st.code("python gateway/app.py")
    
    st.markdown("---")
    
    page = st.radio("", [
        "🏠 الرئيسية",
        "💬 Chat تفاعلي",
        "🤖 الوكلاء",
        "📰 التقارير",
        "🧠 الذاكرة",
        "📊 الإحصائيات",
        "⚙️ الإعدادات",
    ], label_visibility="collapsed")
    
    st.markdown("---")
    
    # الوقت الحقيقي
    st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("v3.0 | Army81")
    
    if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════
# صفحة الرئيسية
# ══════════════════════════════════════════════════

if page == "🏠 الرئيسية":
    st.title("🎖️ Army81 — مركز القيادة")
    
    metrics = get_metrics()
    status = get_status()
    
    # ── إحصائيات رئيسية ──
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_agents = metrics["agents"]["total"] if metrics else "—"
        st.metric("🤖 الوكلاء النشطون", total_agents, delta="81/81")
    
    with col2:
        tasks = metrics["tasks"]["total_today"] if metrics else 0
        st.metric("✅ المهام اليوم", tasks)
    
    with col3:
        success = f"{metrics['tasks']['success_rate']}%" if metrics else "—"
        st.metric("📈 معدل النجاح", success)
    
    with col4:
        docs = metrics["memory"].get("total_documents", 0) if metrics else 0
        st.metric("🧠 وثائق المعرفة", docs)
    
    with col5:
        kb_files = metrics["knowledge"].get("files", 0) if metrics else 0
        st.metric("📚 ملفات المعرفة", kb_files)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 توزيع الوكلاء بالفئة")
        if status:
            cat_data = status.get("router", {}).get("agents_by_category", {})
            if cat_data:
                cat_names = {
                    "cat1_science": "العلوم",
                    "cat2_society": "المجتمع",
                    "cat3_tools": "الأدوات",
                    "cat4_management": "الإدارة",
                    "cat5_behavior": "السلوك",
                    "cat6_leadership": "القيادة",
                    "cat7_new": "التطور",
                }
                df = pd.DataFrame([
                    {"الفئة": cat_names.get(k, k), "العدد": v}
                    for k, v in cat_data.items()
                ])
                fig = px.bar(df, x="الفئة", y="العدد",
                             color="العدد",
                             color_continuous_scale="Viridis",
                             template="plotly_dark")
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("السيرفر غير متاح")
    
    with col2:
        st.subheader("🏆 أفضل الوكلاء")
        if metrics and metrics["agents"]["top_performers"]:
            for i, agent in enumerate(metrics["agents"]["top_performers"]):
                st.markdown(f"""
                <div class="agent-card">
                <b>#{i+1} {agent['id']}</b> — {agent['name']}<br>
                <small>مهام: {agent['tasks']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات بعد")
    
    st.markdown("---")
    
    # آخر تقرير
    st.subheader("📰 آخر تقرير يومي")
    report = get_latest_report()
    if report and not report.get("error"):
        st.caption(f"📅 {report.get('date','')}")
        content = report.get("content", "")
        # عرض أول 1000 حرف
        if len(content) > 1000:
            with st.expander("عرض التقرير الكامل"):
                st.markdown(content)
            st.markdown(content[:1000] + "...")
        else:
            st.markdown(content)
    else:
        st.info("لا يوجد تقرير بعد. شغّل: python scripts/daily_updater.py")
    
    # أزرار سريعة
    st.markdown("---")
    st.subheader("⚡ إجراءات سريعة")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 تشغيل التحديث اليومي"):
            with st.spinner("جاري التحديث..."):
                import subprocess
                result = subprocess.Popen(
                    ["python", "scripts/daily_updater.py"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                st.success("بدأ التحديث في الخلفية")
    
    with col2:
        if st.button("📚 تحميل المعرفة"):
            with st.spinner("جاري التحميل..."):
                import subprocess
                subprocess.Popen(["python", "scripts/load_all_knowledge.py"])
                st.success("بدأ تحميل المعرفة في الخلفية")
    
    with col3:
        if st.button("🧪 اختبار النظام"):
            with st.spinner("جاري الاختبار..."):
                result = send_task("قل مرحبا وعرّف بنفسك باختصار", "A01")
                if result.get("status") == "success":
                    st.success(f"✅ النظام يعمل — A01 أجاب في {result.get('elapsed_seconds',0)}s")
                else:
                    st.error("❌ فشل الاختبار")
    
    with col4:
        if st.button("📊 تقرير الأداء"):
            with st.spinner("جاري التحليل..."):
                result = send_task(
                    "حلل حالة النظام وأعطني تقرير أداء مختصر في 5 نقاط",
                    "A81"
                )
                if result.get("status") == "success":
                    st.info(result.get("result","")[:500])

# ══════════════════════════════════════════════════
# صفحة Chat
# ══════════════════════════════════════════════════

elif page == "💬 Chat تفاعلي":
    st.title("💬 تواصل مع الوكلاء")
    
    if not check_gateway():
        st.error("🔴 البوابة غير متاحة — شغّل: python gateway/app.py")
        st.stop()
    
    # تهيئة session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    
    # خيارات
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        agents_data = get_agents()
        agent_options = ["🎯 تلقائي"]
        agent_ids_map = {"🎯 تلقائي": None}
        
        if agents_data:
            for a in agents_data.get("agents", []):
                label = f"{a['id']} — {a.get('name_ar', a.get('name',''))}"
                agent_options.append(label)
                agent_ids_map[label] = a["id"]
        
        selected_agent_label = st.selectbox("الوكيل", agent_options)
        selected_agent = agent_ids_map.get(selected_agent_label)
    
    with col2:
        pipeline_mode = st.checkbox("🔗 Pipeline Mode")
    
    with col3:
        if st.button("🗑️ مسح المحادثة"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Pipeline agents
    if pipeline_mode:
        pipeline_agents = st.multiselect(
            "اختر الوكلاء بالترتيب",
            [a["id"] for a in agents_data.get("agents", [])] if agents_data else [],
            default=["A01", "A04"] if agents_data else []
        )
    
    # عرض المحادثة
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-msg">
                <small>👤 أنت — {msg.get('time','')}</small><br>
                {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                agent_info = f"🤖 {msg.get('agent','وكيل')} ({msg.get('model','')}) — {msg.get('elapsed','')}s"
                st.markdown(f"""
                <div class="agent-msg">
                <small>{agent_info}</small><br>
                {msg['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار تقييم
                if st.session_state.last_result and msg == st.session_state.chat_history[-1]:
                    col_a, col_b, col_c = st.columns([1, 1, 8])
                    with col_a:
                        if st.button("👍", key=f"like_{len(st.session_state.chat_history)}"):
                            submit_feedback(
                                st.session_state.last_result.get("agent_id",""),
                                st.session_state.chat_history[-2]["content"],
                                5
                            )
                            st.success("شكراً!")
                    with col_b:
                        if st.button("👎", key=f"dislike_{len(st.session_state.chat_history)}"):
                            submit_feedback(
                                st.session_state.last_result.get("agent_id",""),
                                st.session_state.chat_history[-2]["content"],
                                1
                            )
                            st.info("سنحسّن!")
    
    # مربع الإرسال
    st.markdown("---")
    
    with st.form("chat_form", clear_on_submit=True):
        task_input = st.text_area(
            "اكتب مهمتك:",
            placeholder="مثال: حلّل تأثير الذكاء الاصطناعي على سوق العمل...",
            height=100
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("⚡ إرسال", use_container_width=True)
        
        if submitted and task_input:
            # أضف رسالة المستخدم
            st.session_state.chat_history.append({
                "role": "user",
                "content": task_input,
                "time": datetime.now().strftime("%H:%M")
            })
            
            with st.spinner("⏳ الوكيل يفكر..."):
                if pipeline_mode and pipeline_agents:
                    result = send_task(task_input, pipeline=True, agent_ids=pipeline_agents)
                    if result.get("status") == "success":
                        final = result.get("final") or {}
                        response_text = final.get("result", "لا يوجد رد")
                        agent_name = final.get("agent_name", "Pipeline")
                        elapsed = final.get("elapsed_seconds", 0)
                        model = final.get("model_used", "")
                    else:
                        response_text = result.get("error", "خطأ")
                        agent_name = "Pipeline"
                        elapsed = 0
                        model = ""
                else:
                    result = send_task(task_input, selected_agent)
                    response_text = result.get("result", result.get("error", "لا يوجد رد"))
                    agent_name = result.get("agent_name", "وكيل")
                    elapsed = result.get("elapsed_seconds", 0)
                    model = result.get("model_used", "")
                
                st.session_state.last_result = result
                st.session_state.chat_history.append({
                    "role": "agent",
                    "content": response_text,
                    "agent": agent_name,
                    "elapsed": elapsed,
                    "model": model,
                    "time": datetime.now().strftime("%H:%M")
                })
            
            st.rerun()

# ══════════════════════════════════════════════════
# صفحة الوكلاء
# ══════════════════════════════════════════════════

elif page == "🤖 الوكلاء":
    st.title("🤖 الوكلاء الـ 81")
    
    agents_data = get_agents()
    
    if not agents_data:
        st.error("لا يمكن الاتصال بالسيرفر")
        st.stop()
    
    agents = agents_data.get("agents", [])
    
    # فلاتر
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 بحث", placeholder="اسم أو ID...")
    with col2:
        cat_filter = st.selectbox("الفئة", [
            "الكل", "cat1_science", "cat2_society", "cat3_tools",
            "cat4_management", "cat5_behavior", "cat6_leadership", "cat7_new"
        ])
    with col3:
        sort_by = st.selectbox("ترتيب", ["ID", "المهام", "الفئة"])
    
    # تطبيق الفلاتر
    filtered = agents
    if search:
        filtered = [a for a in filtered if
                    search.lower() in a.get("id","").lower() or
                    search in a.get("name_ar", a.get("name",""))]
    if cat_filter != "الكل":
        filtered = [a for a in filtered if a.get("category") == cat_filter]
    
    if sort_by == "المهام":
        filtered.sort(key=lambda a: a.get("stats",{}).get("tasks_done",0), reverse=True)
    elif sort_by == "الفئة":
        filtered.sort(key=lambda a: a.get("category",""))
    
    st.caption(f"عرض {len(filtered)} من {len(agents)} وكيل")
    
    # جدول الوكلاء
    df_data = []
    for a in filtered:
        stats = a.get("stats", {})
        df_data.append({
            "ID": a.get("id",""),
            "الاسم": a.get("name_ar", a.get("name","")),
            "الفئة": a.get("category",""),
            "النموذج": a.get("model",""),
            "الأدوات": len(a.get("tools",[])),
            "المهام": stats.get("tasks_done", 0),
            "الفشل": stats.get("tasks_failed", 0),
        })
    
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            column_config={
                "ID": st.column_config.TextColumn(width="small"),
                "المهام": st.column_config.ProgressColumn(
                    min_value=0, max_value=max(d["المهام"] for d in df_data) or 1
                ),
            }
        )
    
    # تفاصيل وكيل مختار
    st.markdown("---")
    selected_id = st.selectbox(
        "اختر وكيلاً لعرض تفاصيله",
        [a.get("id","") for a in filtered]
    )
    
    if selected_id:
        agent = next((a for a in filtered if a.get("id") == selected_id), None)
        if agent:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader(f"🤖 {agent.get('id')}")
                st.markdown(f"**{agent.get('name_ar', agent.get('name',''))}**")
                st.caption(agent.get("description",""))
                
                st.markdown("**الأدوات:**")
                for tool in agent.get("tools", []):
                    st.markdown(f"• `{tool}`")
                
                stats = agent.get("stats", {})
                st.metric("المهام المنجزة", stats.get("tasks_done", 0))
                st.metric("المهام الفاشلة", stats.get("tasks_failed", 0))
            
            with col2:
                st.subheader("⚡ إرسال مهمة مباشرة")
                quick_task = st.text_area("المهمة:", height=100, key="quick_task")
                if st.button("إرسال لهذا الوكيل", key="send_quick"):
                    if quick_task:
                        with st.spinner("جاري المعالجة..."):
                            result = send_task(quick_task, selected_id)
                            if result.get("status") == "success":
                                st.success(f"✅ {result.get('elapsed_seconds',0)}s")
                                st.markdown(result.get("result",""))
                                
                                # أزرار تقييم
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if st.button("👍 ممتاز"):
                                        submit_feedback(selected_id, quick_task, 5)
                                with col_b:
                                    if st.button("👎 يحتاج تحسين"):
                                        submit_feedback(selected_id, quick_task, 1)
                            else:
                                st.error(result.get("error","خطأ"))

# ══════════════════════════════════════════════════
# صفحة التقارير
# ══════════════════════════════════════════════════

elif page == "📰 التقارير":
    st.title("📰 التقارير اليومية")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 تشغيل تحديث الآن"):
            with st.spinner("جاري جمع البيانات..."):
                import subprocess
                proc = subprocess.run(
                    ["python", "scripts/daily_updater.py"],
                    capture_output=True, text=True, timeout=120
                )
                if proc.returncode == 0:
                    st.success("✅ تم التحديث!")
                    st.cache_data.clear()
                else:
                    st.error(f"خطأ: {proc.stderr[:200]}")
    
    reports_dir = Path("workspace/reports")
    if not reports_dir.exists():
        st.info("لا توجد تقارير بعد")
        st.stop()
    
    reports = sorted(reports_dir.glob("*.md"), reverse=True)
    
    if not reports:
        st.info("لا توجد تقارير بعد")
        st.stop()
    
    # عرض التقارير
    report_names = [r.name for r in reports]
    selected_report = st.selectbox("اختر تقرير", report_names)
    
    if selected_report:
        report_path = reports_dir / selected_report
        content = report_path.read_text(encoding="utf-8")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 التاريخ", report_path.stem.replace("daily_report_",""))
        with col2:
            st.metric("📊 الحجم", f"{len(content)} حرف")
        with col3:
            knowledge_dir = Path("workspace/knowledge")
            files = len(list(knowledge_dir.rglob("*.txt"))) if knowledge_dir.exists() else 0
            st.metric("📚 ملفات المعرفة", files)
        
        st.markdown("---")
        st.markdown(content)

# ══════════════════════════════════════════════════
# صفحة الذاكرة
# ══════════════════════════════════════════════════

elif page == "🧠 الذاكرة":
    st.title("🧠 ذاكرة النظام")
    
    # Chroma
    st.subheader("🔵 الذاكرة الدلالية (Chroma)")
    ks = get_knowledge_status()
    
    if ks:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Collections", ks.get("chroma_collections", 0))
        with col2:
            st.metric("إجمالي الوثائق", ks.get("total_docs", 0))
        
        if ks.get("collections"):
            df = pd.DataFrame(ks["collections"])
            if not df.empty:
                fig = px.pie(df, values="count", names="name",
                             template="plotly_dark",
                             title="توزيع الوثائق في Chroma")
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Chroma غير متاح. شغّل: pip install chromadb")
    
    # SQLite Episodic
    st.subheader("💾 الذاكرة العرضية (SQLite)")
    db_path = Path("memory/episodic.db")
    if db_path.exists():
        import sqlite3
        try:
            conn = sqlite3.connect(str(db_path))
            df = pd.read_sql_query(
                "SELECT agent_id, task_summary, success, rating, created_at FROM episodes ORDER BY created_at DESC LIMIT 20",
                conn
            )
            conn.close()
            if not df.empty:
                st.metric("إجمالي الحلقات", len(df))
                st.dataframe(df, use_container_width=True)
            else:
                st.info("لا توجد بيانات بعد")
        except Exception as e:
            st.warning(f"خطأ: {e}")
    else:
        st.info("لا توجد قاعدة بيانات episodic بعد")
    
    # ملفات المعرفة
    st.subheader("📁 ملفات المعرفة المحلية")
    knowledge_dir = Path("workspace/knowledge")
    if knowledge_dir.exists():
        all_files = list(knowledge_dir.rglob("*.txt"))
        if all_files:
            # احسب بالفئة
            by_cat = {}
            for f in all_files:
                cat = f.parent.name
                by_cat[cat] = by_cat.get(cat, 0) + 1
            
            df = pd.DataFrame([{"الفئة": k, "الملفات": v} for k,v in by_cat.items()])
            st.dataframe(df, use_container_width=True)
            
            total_size = sum(f.stat().st_size for f in all_files)
            st.metric("إجمالي الحجم", f"{total_size/1024/1024:.1f} MB")
        else:
            st.info("لا توجد ملفات معرفة بعد. شغّل: python scripts/load_all_knowledge.py")
    
    # Compressed summaries
    st.subheader("🗜️ الملخصات المضغوطة")
    compressed_dir = Path("workspace/compressed")
    if compressed_dir.exists():
        compressed = list(compressed_dir.glob("*.md"))
        if compressed:
            for f in compressed[:5]:
                with st.expander(f.stem):
                    st.markdown(f.read_text(encoding="utf-8"))
        else:
            st.info("لا توجد ملخصات مضغوطة بعد")

# ══════════════════════════════════════════════════
# صفحة الإحصائيات
# ══════════════════════════════════════════════════

elif page == "📊 الإحصائيات":
    st.title("📊 إحصائيات متقدمة")
    
    metrics = get_metrics()
    agents_data = get_agents()
    
    if not metrics or not agents_data:
        st.error("لا يمكن الاتصال بالسيرفر")
        st.stop()
    
    agents = agents_data.get("agents", [])
    
    # مخطط المهام لكل وكيل
    st.subheader("📈 المهام بالوكيل")
    tasks_data = [
        {
            "ID": a.get("id",""),
            "المهام": a.get("stats",{}).get("tasks_done", 0),
            "الفئة": a.get("category","")
        }
        for a in agents
        if a.get("stats",{}).get("tasks_done", 0) > 0
    ]
    
    if tasks_data:
        df = pd.DataFrame(tasks_data)
        fig = px.bar(df, x="ID", y="المهام", color="الفئة",
                     template="plotly_dark",
                     title="المهام المنجزة لكل وكيل")
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد مهام بعد. ابدأ بإرسال مهام من صفحة Chat")
    
    # إحصائيات الأدوات
    st.subheader("🛠️ توزيع الأدوات")
    tool_counts = {}
    for a in agents:
        for tool in a.get("tools", []):
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    if tool_counts:
        df_tools = pd.DataFrame([
            {"الأداة": k, "عدد الوكلاء": v}
            for k, v in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        fig = px.bar(df_tools, x="الأداة", y="عدد الوكلاء",
                     color="عدد الوكلاء",
                     template="plotly_dark",
                     color_continuous_scale="Blues")
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # توزيع النماذج
    st.subheader("🤖 توزيع النماذج")
    model_counts = {}
    for a in agents:
        model = a.get("model", "unknown")
        model_counts[model] = model_counts.get(model, 0) + 1
    
    if model_counts:
        df_models = pd.DataFrame([
            {"النموذج": k, "العدد": v}
            for k, v in model_counts.items()
        ])
        fig = px.pie(df_models, values="العدد", names="النموذج",
                     template="plotly_dark",
                     title="توزيع النماذج على الوكلاء")
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════
# صفحة الإعدادات
# ══════════════════════════════════════════════════

elif page == "⚙️ الإعدادات":
    st.title("⚙️ إعدادات النظام")
    
    st.subheader("🔑 مفاتيح API")
    
    env_path = Path(".env")
    env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    
    # اعرض المفاتيح (مخفية)
    keys = {}
    for line in env_content.split('\n'):
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            keys[k.strip()] = '✅ موجود' if v.strip() and v.strip() != 'your_key_here' else '❌ ناقص'
    
    for key, status in keys.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(key)
        with col2:
            st.markdown(status)
    
    st.markdown("---")
    
    st.subheader("🖥️ حالة الخدمات")
    
    services = {
        "Gateway API": f"{GATEWAY}/health",
        "Dashboard": "http://localhost:8501",
    }
    
    for service, url in services.items():
        try:
            r = requests.get(url, timeout=2)
            status = "🟢 يعمل"
        except:
            status = "🔴 متوقف"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"{service} ({url})")
        with col2:
            st.markdown(status)
    
    st.markdown("---")
    
    st.subheader("📋 معلومات النظام")
    
    import platform, sys
    info = {
        "Python": sys.version.split()[0],
        "OS": platform.system(),
        "Architecture": platform.machine(),
        "Dashboard": "v3.0",
    }
    
    for k, v in info.items():
        st.text(f"{k}: {v}")
```

---

## الجزء 5 — تشغيل وتحقق

```bash
# 1. تثبيت المكتبات الإضافية
pip install plotly pandas chromadb

# 2. تشغيل تحميل المعرفة
python scripts/load_all_knowledge.py

# 3. تشغيل السيرفر
python gateway/app.py &

# 4. تشغيل Dashboard الجديد
streamlit run dashboard/army81_dashboard.py --server.port 8501 --browser.gatherUsageStats false

# 5. اختبر
curl http://localhost:8181/metrics
```

---

## الجزء 6 — ارفع كل شيء

```bash
git add -A
git commit -m "feat: Army81 v4 - full agent upgrade + real dashboard + knowledge base + metrics API"
git push origin main
```
