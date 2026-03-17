"""
dashboard/army81_dashboard.py — واجهة تفاعلية كاملة لـ Army81
صفحات: الرئيسية | Chat تفاعلي | الوكلاء | التقارير | الذاكرة
"""

import json
import time
import os
import sys
import requests
import streamlit as st
from pathlib import Path
from datetime import datetime

# مسار المشروع
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── إعداد الصفحة ─────────────────────────────────────────────
st.set_page_config(
    page_title="Army81 — لوحة التحكم التفاعلية",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS مخصص ──────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { direction: rtl; }
    .block-container { max-width: 1200px; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 16px;
        color: white;
    }
    div[data-testid="stMetric"] label { color: #a0a0c0 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #e0e0ff !important; }
    .chat-msg-user {
        background: #1e3a5f; border-radius: 12px; padding: 12px 16px;
        margin: 8px 0; border-right: 4px solid #4a9eff;
    }
    .chat-msg-agent {
        background: #1a2e1a; border-radius: 12px; padding: 12px 16px;
        margin: 8px 0; border-right: 4px solid #4aff4a;
    }
    .agent-card {
        background: #0d1117; border: 1px solid #30363d; border-radius: 10px;
        padding: 16px; margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── ثوابت ─────────────────────────────────────────────────────
GATEWAY_URL = "http://localhost:8181"
AGENTS_ROOT = PROJECT_ROOT / "agents"

CATEGORY_INFO = {
    "cat1_science":    {"label": "العلوم",          "icon": "🔬", "color": "#4ecdc4"},
    "cat2_society":    {"label": "المجتمع",         "icon": "🌍", "color": "#ff6b6b"},
    "cat3_tools":      {"label": "الأدوات",         "icon": "🛠️", "color": "#ffd93d"},
    "cat4_management": {"label": "الإدارة",         "icon": "📊", "color": "#6c5ce7"},
    "cat5_behavior":   {"label": "السلوك",          "icon": "🧠", "color": "#fd79a8"},
    "cat6_leadership": {"label": "القيادة",         "icon": "👑", "color": "#fdcb6e"},
    "cat7_new":        {"label": "التطور الذاتي",   "icon": "🚀", "color": "#00b894"},
}

MODEL_ICONS = {
    "gemini-flash": "⚡", "gemini-pro": "🔵", "gemini-fast": "💨",
    "claude-fast": "🟡", "claude-smart": "🟠",
    "llama-free": "🦙", "qwen-free": "🔮",
}

# ── تحميل الوكلاء ────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_all_agents() -> list:
    agents = []
    if not AGENTS_ROOT.exists():
        return agents
    for cat_dir in sorted(AGENTS_ROOT.iterdir()):
        if not cat_dir.is_dir():
            continue
        for jf in sorted(cat_dir.glob("*.json")):
            try:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
                data["_file"] = str(jf)
                agents.append(data)
            except Exception:
                continue
    agents.sort(key=lambda a: a.get("agent_id", "A00"))
    return agents


def check_gateway() -> dict:
    try:
        resp = requests.get(f"{GATEWAY_URL}/health", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_gateway_status() -> dict:
    try:
        resp = requests.get(f"{GATEWAY_URL}/status", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def send_task(agent_id: str, task: str, timeout_sec: int = 90) -> dict:
    try:
        resp = requests.post(
            f"{GATEWAY_URL}/task",
            json={"agent_id": agent_id, "task": task},
            timeout=timeout_sec,
        )
        return resp.json()
    except Exception as e:
        return {"status": "error", "result": f"فشل الاتصال: {e}"}


def send_pipeline(agent_ids: list, task: str) -> dict:
    try:
        resp = requests.post(
            f"{GATEWAY_URL}/pipeline",
            json={"agent_ids": agent_ids, "task": task},
            timeout=120,
        )
        return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def load_reports() -> list:
    reports_dir = PROJECT_ROOT / "workspace" / "reports"
    if not reports_dir.exists():
        return []
    return sorted(reports_dir.glob("*.md"), reverse=True)


def get_chroma_stats() -> dict:
    try:
        from memory.chroma_memory import get_stats as chroma_get_stats
        return chroma_get_stats()
    except Exception:
        pass
    # fallback: check DB files
    stats = {"status": "غير متصل"}
    ws = PROJECT_ROOT / "workspace"
    episodic_db = ws / "episodic_memory.db"
    if episodic_db.exists():
        size_mb = episodic_db.stat().st_size / (1024 * 1024)
        stats["episodic_db_mb"] = round(size_mb, 2)
    compressed_dir = ws / "compressed"
    if compressed_dir.exists():
        files = list(compressed_dir.glob("*.md"))
        stats["compressed_files"] = len(files)
    chroma_dir = ws / "chroma_db"
    if chroma_dir.exists():
        stats["chroma_exists"] = True
        total = sum(f.stat().st_size for f in chroma_dir.rglob("*") if f.is_file())
        stats["chroma_db_mb"] = round(total / (1024 * 1024), 2)
    else:
        stats["chroma_exists"] = False
    return stats


# ── تحميل البيانات ────────────────────────────────────────────
all_agents = load_all_agents()
health = check_gateway()
gateway_ok = health is not None

# ── إحصائيات ─────────────────────────────────────────────────
by_category = {}
by_model = {}
for a in all_agents:
    cat = a.get("category", "unknown")
    model = a.get("model", "unknown")
    by_category[cat] = by_category.get(cat, 0) + 1
    by_model[model] = by_model.get(model, 0) + 1


# ══════════════════════════════════════════════════════════════
# الشريط الجانبي
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎖️ Army81")
    st.caption("81 وكيل ذكي تحت أمرك")
    st.divider()

    if gateway_ok:
        st.success(f"البوابة: متصلة ({health.get('agents', '?')} وكيل)")
    else:
        st.error("البوابة: غير متاحة")
        st.code("python gateway/app.py", language="bash")

    st.divider()

    page = st.radio(
        "التنقل",
        [
            "🏠 الرئيسية",
            "💬 Chat تفاعلي",
            "🤖 الوكلاء",
            "📄 التقارير",
            "🧠 الذاكرة",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(f"v3.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ══════════════════════════════════════════════════════════════
# 🏠 الرئيسية
# ══════════════════════════════════════════════════════════════
if page == "🏠 الرئيسية":
    st.title("🎖️ Army81 — مركز القيادة")
    st.markdown("**81 وكيل ذكي متخصص يعملون معاً.**")

    # بطاقات سريعة
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("الوكلاء", len(all_agents))
    c2.metric("الفئات", len(by_category))
    c3.metric("النماذج", len(by_model))
    c4.metric("البوابة", "متصلة" if gateway_ok else "منقطعة")
    reports = load_reports()
    c5.metric("التقارير", len(reports))

    st.divider()

    # توزيع الفئات
    st.subheader("توزيع الوكلاء")
    cols = st.columns(len(CATEGORY_INFO))
    for i, (cat_key, info) in enumerate(CATEGORY_INFO.items()):
        count = by_category.get(cat_key, 0)
        with cols[i]:
            st.metric(f"{info['icon']} {info['label']}", count)

    st.divider()

    # آخر تقرير
    st.subheader("📄 آخر تقرير يومي")
    if reports:
        latest = reports[0]
        st.caption(f"📅 {latest.stem.replace('daily_report_', '')}")
        with open(latest, encoding="utf-8") as f:
            content = f.read()
        with st.expander("عرض التقرير", expanded=True):
            st.markdown(content[:5000])
    else:
        st.info("لا توجد تقارير. شغّل: `python scripts/daily_updater.py`")

    # حالة gateway مفصّلة
    if gateway_ok:
        st.divider()
        st.subheader("📡 حالة النظام المباشرة")
        gw_status = get_gateway_status()
        if gw_status:
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("المهام المنفّذة", gw_status.get("total_tasks", 0))
            sc2.metric("المهام الناجحة", gw_status.get("successful", 0))
            sc3.metric("الوكلاء النشطون", gw_status.get("active_agents", len(all_agents)))


# ══════════════════════════════════════════════════════════════
# 💬 Chat تفاعلي
# ══════════════════════════════════════════════════════════════
elif page == "💬 Chat تفاعلي":
    st.title("💬 تواصل مع الوكلاء")

    if not gateway_ok:
        st.error("البوابة غير متاحة. شغّل: `python gateway/app.py`")
        st.stop()

    # اختيار الوكيل
    col_sel, col_mode = st.columns([3, 1])

    with col_sel:
        agent_map = {}
        for a in all_agents:
            aid = a.get("agent_id", "")
            cat = a.get("category", "")
            info = CATEGORY_INFO.get(cat, {"icon": "⚪", "label": cat})
            name = a.get("name_ar", a.get("name", ""))
            label = f"{info['icon']} {aid} — {name}"
            agent_map[label] = aid

        selected_label = st.selectbox("اختر الوكيل:", list(agent_map.keys()))
        selected_id = agent_map[selected_label]

    with col_mode:
        chat_mode = st.radio("الوضع", ["وكيل واحد", "سلسلة وكلاء"], horizontal=True)

    # وكلاء السلسلة
    chain_agents = []
    if chat_mode == "سلسلة وكلاء":
        chain_labels = st.multiselect(
            "اختر وكلاء السلسلة (بالترتيب):",
            list(agent_map.keys()),
            default=[selected_label],
        )
        chain_agents = [agent_map[l] for l in chain_labels]

    # عرض معلومات الوكيل المختار
    sel_agent = next((a for a in all_agents if a.get("agent_id") == selected_id), None)
    if sel_agent:
        with st.expander(f"معلومات {selected_id}", expanded=False):
            ic1, ic2, ic3 = st.columns(3)
            ic1.markdown(f"**النموذج:** `{sel_agent.get('model', '?')}`")
            ic2.markdown(f"**الفئة:** {sel_agent.get('category', '?')}")
            tools = sel_agent.get("tools", [])
            ic3.markdown(f"**الأدوات:** {len(tools)}")
            st.caption(sel_agent.get("description", ""))

    st.divider()

    # سجل المحادثة
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # عرض المحادثة
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-msg-user">👤 <b>أنت:</b><br>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                agent_name = msg.get("agent", "وكيل")
                elapsed = msg.get("elapsed", "")
                model = msg.get("model", "")
                header = f"🤖 <b>{agent_name}</b>"
                if model:
                    header += f" <small>({model})</small>"
                if elapsed:
                    header += f" <small>— {elapsed}s</small>"
                st.markdown(
                    f'<div class="chat-msg-agent">{header}<br><br>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

    # إدخال المهمة
    st.divider()
    with st.form("chat_form", clear_on_submit=True):
        task_input = st.text_area(
            "اكتب مهمتك:",
            placeholder="مثلاً: حلّل تأثير الذكاء الاصطناعي على سوق العمل...",
            height=100,
            key="chat_input",
        )
        col_send, col_clear = st.columns([1, 1])
        send_btn = col_send.form_submit_button("🚀 إرسال", type="primary")
        clear_btn = col_clear.form_submit_button("🗑️ مسح المحادثة")

    if clear_btn:
        st.session_state.chat_history = []
        st.rerun()

    if send_btn and task_input.strip():
        # حفظ رسالة المستخدم
        st.session_state.chat_history.append({
            "role": "user",
            "content": task_input.strip(),
        })

        if chat_mode == "سلسلة وكلاء" and len(chain_agents) > 1:
            # سلسلة وكلاء
            with st.spinner(f"جارٍ التنفيذ عبر {len(chain_agents)} وكلاء..."):
                t0 = time.time()
                result = send_pipeline(chain_agents, task_input.strip())
                elapsed = round(time.time() - t0, 1)

            if result.get("status") == "error":
                st.session_state.chat_history.append({
                    "role": "agent",
                    "agent": "النظام",
                    "content": f"خطأ: {result.get('error', 'غير معروف')}",
                    "elapsed": elapsed,
                })
            else:
                steps = result.get("steps", [])
                for step in steps:
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "agent": f"{step.get('agent_id', '?')} — {step.get('agent_name', '')}",
                        "content": step.get("result", ""),
                        "elapsed": step.get("elapsed_seconds", ""),
                        "model": step.get("model_used", ""),
                    })
        else:
            # وكيل واحد
            with st.spinner(f"جارٍ المعالجة بواسطة {selected_id}..."):
                t0 = time.time()
                result = send_task(selected_id, task_input.strip())
                elapsed = round(time.time() - t0, 1)

            agent_name = result.get("agent_name", selected_id)
            content = result.get("result", json.dumps(result, ensure_ascii=False, indent=2))
            model_used = result.get("model_used", "")

            st.session_state.chat_history.append({
                "role": "agent",
                "agent": f"{selected_id} — {agent_name}",
                "content": content,
                "elapsed": elapsed,
                "model": model_used,
            })

        st.rerun()


# ══════════════════════════════════════════════════════════════
# 🤖 الوكلاء
# ══════════════════════════════════════════════════════════════
elif page == "🤖 الوكلاء":
    st.title("🤖 قائمة الوكلاء — 81 وكيل")

    # فلاتر
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        cats = ["الكل"] + [f"{CATEGORY_INFO.get(c, {}).get('icon', '')} {c}" for c in sorted(by_category.keys())]
        filter_cat = st.selectbox("الفئة", cats)
    with fc2:
        filter_model = st.selectbox("النموذج", ["الكل"] + sorted(by_model.keys()))
    with fc3:
        search_q = st.text_input("بحث", placeholder="اسم أو وصف أو ID...")

    # تصفية
    filtered = all_agents
    if filter_cat != "الكل":
        cat_key = filter_cat.split(" ", 1)[-1] if " " in filter_cat else filter_cat
        filtered = [a for a in filtered if a.get("category") == cat_key]
    if filter_model != "الكل":
        filtered = [a for a in filtered if a.get("model") == filter_model]
    if search_q:
        q = search_q.lower()
        filtered = [
            a for a in filtered
            if q in a.get("name", "").lower()
            or q in a.get("name_ar", "").lower()
            or q in a.get("description", "").lower()
            or q in a.get("agent_id", "").lower()
        ]

    st.caption(f"عرض {len(filtered)} من {len(all_agents)} وكيل")

    # عرض كجدول
    view_mode = st.radio("العرض", ["جدول", "بطاقات"], horizontal=True)

    if view_mode == "جدول":
        table_data = []
        for a in filtered:
            cat = a.get("category", "")
            info = CATEGORY_INFO.get(cat, {"icon": "⚪", "label": cat})
            m = a.get("model", "")
            table_data.append({
                "ID": a.get("agent_id", ""),
                "الاسم": a.get("name_ar", a.get("name", "")),
                "الفئة": f"{info['icon']} {info['label']}",
                "النموذج": f"{MODEL_ICONS.get(m, '⚪')} {m}",
                "الأدوات": len(a.get("tools", [])),
                "الوصف": a.get("description", "")[:80],
            })
        st.dataframe(table_data, use_container_width=True, height=600)

    else:
        # بطاقات
        cols_per_row = 3
        for i in range(0, len(filtered), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(filtered):
                    break
                a = filtered[idx]
                cat = a.get("category", "")
                info = CATEGORY_INFO.get(cat, {"icon": "⚪", "label": cat})
                m = a.get("model", "")
                tools = a.get("tools", [])

                with col:
                    with st.container(border=True):
                        st.markdown(f"### {info['icon']} {a.get('agent_id')} — {a.get('name_ar', a.get('name', ''))}")
                        st.caption(a.get("description", "")[:120])
                        mc1, mc2 = st.columns(2)
                        mc1.markdown(f"**النموذج:** {MODEL_ICONS.get(m, '')} `{m}`")
                        mc2.markdown(f"**الأدوات:** {len(tools)}")
                        if tools:
                            st.code(", ".join(tools[:5]) + ("..." if len(tools) > 5 else ""))

                        # زر إرسال سريع
                        if gateway_ok:
                            with st.popover(f"💬 مهمة سريعة"):
                                quick_task = st.text_input(
                                    "المهمة:",
                                    key=f"quick_{a.get('agent_id')}",
                                    placeholder="اكتب مهمة سريعة...",
                                )
                                if st.button("إرسال", key=f"send_{a.get('agent_id')}"):
                                    if quick_task:
                                        with st.spinner("..."):
                                            res = send_task(a.get("agent_id"), quick_task)
                                        st.markdown(res.get("result", str(res))[:500])


# ══════════════════════════════════════════════════════════════
# 📄 التقارير
# ══════════════════════════════════════════════════════════════
elif page == "📄 التقارير":
    st.title("📄 التقارير اليومية")

    reports = load_reports()

    if not reports:
        st.info("لا توجد تقارير. شغّل: `python scripts/daily_updater.py`")
        st.stop()

    st.metric("عدد التقارير", len(reports))
    st.divider()

    # اختيار التقرير
    report_names = [r.stem.replace("daily_report_", "") for r in reports]
    selected_date = st.selectbox("اختر التاريخ:", report_names)
    selected_report = reports[report_names.index(selected_date)]

    with open(selected_report, encoding="utf-8") as f:
        content = f.read()

    st.markdown(f"### تقرير {selected_date}")
    st.markdown(content)

    st.divider()

    # زر تشغيل تحديث جديد
    if st.button("🔄 تشغيل تحديث يومي الآن", type="primary"):
        with st.spinner("جارٍ جمع البيانات..."):
            try:
                from scripts.daily_updater import run_daily_update
                summary = run_daily_update()
                st.success("تم التحديث!")
                st.json(summary)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"خطأ: {e}")


# ══════════════════════════════════════════════════════════════
# 🧠 الذاكرة
# ══════════════════════════════════════════════════════════════
elif page == "🧠 الذاكرة":
    st.title("🧠 ذاكرة النظام")
    st.markdown("ما تعلمه النظام من المهام والتحديثات اليومية.")

    stats = get_chroma_stats()

    # بطاقات الحالة
    mc1, mc2, mc3 = st.columns(3)

    with mc1:
        st.markdown("### 💾 الذاكرة العرضية")
        st.markdown("(Episodic Memory — SQLite)")
        db_size = stats.get("episodic_db_mb", 0)
        if db_size:
            st.metric("حجم قاعدة البيانات", f"{db_size} MB")
            # حاول قراءة عدد السجلات
            try:
                import sqlite3
                db_path = PROJECT_ROOT / "workspace" / "episodic_memory.db"
                conn = sqlite3.connect(str(db_path))
                cursor = conn.execute("SELECT COUNT(*) FROM episodes")
                count = cursor.fetchone()[0]
                conn.close()
                st.metric("عدد السجلات", count)
            except Exception:
                st.caption("تعذّر قراءة السجلات")
        else:
            st.info("لا توجد قاعدة بيانات بعد")

    with mc2:
        st.markdown("### 🔍 الذاكرة الدلالية")
        st.markdown("(Semantic Memory — Chroma)")
        if stats.get("chroma_exists"):
            st.metric("حجم Chroma", f"{stats.get('chroma_db_mb', 0)} MB")
            st.success("Chroma DB موجود")
        else:
            st.warning("Chroma DB غير موجود")
            st.caption("ثبّت: `pip install chromadb`")

    with mc3:
        st.markdown("### 📦 الذاكرة المضغوطة")
        st.markdown("(Compressed Memory — Markdown)")
        compressed = stats.get("compressed_files", 0)
        st.metric("ملفات مضغوطة", compressed)
        if compressed:
            comp_dir = PROJECT_ROOT / "workspace" / "compressed"
            files = sorted(comp_dir.glob("*.md"), reverse=True)
            if files:
                st.caption(f"آخر ملف: {files[0].name}")

    st.divider()

    # عرض محتوى الذاكرة المضغوطة
    st.subheader("📦 آخر ملخصات مضغوطة")
    comp_dir = PROJECT_ROOT / "workspace" / "compressed"
    if comp_dir.exists():
        comp_files = sorted(comp_dir.glob("*.md"), reverse=True)[:5]
        if comp_files:
            for cf in comp_files:
                with st.expander(cf.name):
                    with open(cf, encoding="utf-8") as f:
                        st.markdown(f.read()[:3000])
        else:
            st.info("لا توجد ملخصات مضغوطة بعد.")
    else:
        st.info("مجلد الذاكرة المضغوطة غير موجود.")

    st.divider()

    # عرض آخر سجلات episodic
    st.subheader("📝 آخر المهام المسجّلة")
    try:
        import sqlite3
        db_path = PROJECT_ROOT / "workspace" / "episodic_memory.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(
                "SELECT agent_id, task, success, timestamp FROM episodes ORDER BY timestamp DESC LIMIT 20"
            )
            rows = cursor.fetchall()
            conn.close()

            if rows:
                table = []
                for r in rows:
                    table.append({
                        "الوكيل": r[0],
                        "المهمة": r[1][:80] + "..." if len(r[1]) > 80 else r[1],
                        "النتيجة": "✅" if r[2] else "❌",
                        "التاريخ": r[3][:19] if r[3] else "",
                    })
                st.dataframe(table, use_container_width=True)
            else:
                st.info("لا توجد سجلات بعد.")
        else:
            st.info("قاعدة البيانات غير موجودة بعد. أرسل مهمة لوكيل لبدء التسجيل.")
    except Exception as e:
        st.caption(f"تعذّر قراءة السجلات: {e}")
