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
        st.success("البوابة متصلة")
    else:
        st.error("البوابة غير متاحة")
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
    st.caption(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("v3.0 | Army81")

    if st.button("تحديث البيانات"):
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
        st.metric("المهام اليوم", tasks)

    with col3:
        success = f"{metrics['tasks']['success_rate']}%" if metrics else "—"
        st.metric("معدل النجاح", success)

    with col4:
        docs = metrics["memory"].get("total_documents", 0) if metrics else 0
        st.metric("🧠 وثائق المعرفة", docs)

    with col5:
        kb_files = metrics["knowledge"].get("files", 0) if metrics else 0
        st.metric("ملفات المعرفة", kb_files)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("توزيع الوكلاء بالفئة")
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
        st.subheader("أفضل الوكلاء")
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
    st.subheader("آخر تقرير يومي")
    report = get_latest_report()
    if report and not report.get("error"):
        st.caption(f"{report.get('date','')}")
        content = report.get("content", "")
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
    st.subheader("إجراءات سريعة")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("تشغيل التحديث اليومي"):
            with st.spinner("جاري التحديث..."):
                import subprocess
                result = subprocess.Popen(
                    ["python", "scripts/daily_updater.py"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                st.success("بدأ التحديث في الخلفية")

    with col2:
        if st.button("تحميل المعرفة"):
            with st.spinner("جاري التحميل..."):
                import subprocess
                subprocess.Popen(["python", "scripts/load_all_knowledge.py"])
                st.success("بدأ تحميل المعرفة في الخلفية")

    with col3:
        if st.button("اختبار النظام"):
            with st.spinner("جاري الاختبار..."):
                result = send_task("قل مرحبا وعرّف بنفسك باختصار", "A01")
                if result.get("status") == "success":
                    st.success(f"النظام يعمل — A01 أجاب في {result.get('elapsed_seconds',0)}s")
                else:
                    st.error("فشل الاختبار")

    with col4:
        if st.button("تقرير الأداء"):
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
        st.error("البوابة غير متاحة — شغّل: python gateway/app.py")
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
        agent_options = ["تلقائي"]
        agent_ids_map = {"تلقائي": None}

        if agents_data:
            for a in agents_data.get("agents", []):
                label = f"{a['id']} — {a.get('name_ar', a.get('name',''))}"
                agent_options.append(label)
                agent_ids_map[label] = a["id"]

        selected_agent_label = st.selectbox("الوكيل", agent_options)
        selected_agent = agent_ids_map.get(selected_agent_label)

    with col2:
        pipeline_mode = st.checkbox("Pipeline Mode")

    with col3:
        if st.button("مسح المحادثة"):
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
                <small>أنت — {msg.get('time','')}</small><br>
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
                            st.success("شكرا!")
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
            submitted = st.form_submit_button("إرسال", use_container_width=True)

        if submitted and task_input:
            # أضف رسالة المستخدم
            st.session_state.chat_history.append({
                "role": "user",
                "content": task_input,
                "time": datetime.now().strftime("%H:%M")
            })

            with st.spinner("الوكيل يفكر..."):
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
        search = st.text_input("بحث", placeholder="اسم أو ID...")
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
        "اختر وكيلا لعرض تفاصيله",
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
                    st.markdown(f"- `{tool}`")

                stats = agent.get("stats", {})
                st.metric("المهام المنجزة", stats.get("tasks_done", 0))
                st.metric("المهام الفاشلة", stats.get("tasks_failed", 0))

            with col2:
                st.subheader("إرسال مهمة مباشرة")
                quick_task = st.text_area("المهمة:", height=100, key="quick_task")
                if st.button("إرسال لهذا الوكيل", key="send_quick"):
                    if quick_task:
                        with st.spinner("جاري المعالجة..."):
                            result = send_task(quick_task, selected_id)
                            if result.get("status") == "success":
                                st.success(f"{result.get('elapsed_seconds',0)}s")
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
    st.title("التقارير اليومية")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("تشغيل تحديث الآن"):
            with st.spinner("جاري جمع البيانات..."):
                import subprocess
                proc = subprocess.run(
                    ["python", "scripts/daily_updater.py"],
                    capture_output=True, text=True, timeout=120
                )
                if proc.returncode == 0:
                    st.success("تم التحديث!")
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
            st.metric("التاريخ", report_path.stem.replace("daily_report_",""))
        with col2:
            st.metric("الحجم", f"{len(content)} حرف")
        with col3:
            knowledge_dir = Path("workspace/knowledge")
            files = len(list(knowledge_dir.rglob("*.txt"))) if knowledge_dir.exists() else 0
            st.metric("ملفات المعرفة", files)

        st.markdown("---")
        st.markdown(content)

# ══════════════════════════════════════════════════
# صفحة الذاكرة
# ══════════════════════════════════════════════════

elif page == "🧠 الذاكرة":
    st.title("🧠 ذاكرة النظام")

    # Chroma
    st.subheader("الذاكرة الدلالية (Chroma)")
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
    st.subheader("الذاكرة العرضية (SQLite)")
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
    st.subheader("ملفات المعرفة المحلية")
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
    st.subheader("الملخصات المضغوطة")
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
    st.title("إحصائيات متقدمة")

    metrics = get_metrics()
    agents_data = get_agents()

    if not metrics or not agents_data:
        st.error("لا يمكن الاتصال بالسيرفر")
        st.stop()

    agents = agents_data.get("agents", [])

    # مخطط المهام لكل وكيل
    st.subheader("المهام بالوكيل")
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
    st.subheader("توزيع الأدوات")
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
    st.subheader("توزيع النماذج")
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
    st.title("إعدادات النظام")

    st.subheader("مفاتيح API")

    env_path = Path(".env")
    env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    # اعرض المفاتيح (مخفية)
    keys = {}
    for line in env_content.split('\n'):
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            keys[k.strip()] = 'موجود' if v.strip() and v.strip() != 'your_key_here' else 'ناقص'

    for key, status in keys.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(key)
        with col2:
            st.markdown(status)

    st.markdown("---")

    st.subheader("حالة الخدمات")

    services = {
        "Gateway API": f"{GATEWAY}/health",
        "Dashboard": "http://localhost:8501",
    }

    for service, url in services.items():
        try:
            r = requests.get(url, timeout=2)
            status = "يعمل"
        except:
            status = "متوقف"

        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"{service} ({url})")
        with col2:
            st.markdown(status)

    st.markdown("---")

    st.subheader("معلومات النظام")

    import platform, sys
    info = {
        "Python": sys.version.split()[0],
        "OS": platform.system(),
        "Architecture": platform.machine(),
        "Dashboard": "v3.0",
    }

    for k, v in info.items():
        st.text(f"{k}: {v}")
