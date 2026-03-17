"""
dashboard/app.py — لوحة تحكم Army81 بـ Streamlit

الميزات:
- قائمة الـ 81 وكيل مع حالتهم وفئتهم
- إرسال مهمة واختيار workflow أو فريق CrewAI
- عرض النتائج في الوقت الفعلي
- إحصائيات الاستخدام
"""

import json
import time
import requests
import streamlit as st
from pathlib import Path

# ── إعداد الصفحة ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Army81 — نظام الوكلاء الذكيين",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── ثوابت ─────────────────────────────────────────────────────────────────────
GATEWAY_URL = "http://localhost:8181"
AGENTS_ROOT = Path(__file__).parent.parent / "agents"

CATEGORY_LABELS = {
    "cat1_science":    "🔬 العلوم",
    "cat2_society":    "🌍 المجتمع",
    "cat3_tools":      "🛠️ الأدوات",
    "cat4_management": "📊 الإدارة",
    "cat5_behavior":   "🧠 السلوك",
    "cat6_leadership": "👑 القيادة",
    "cat7_new":        "🚀 التطور الذاتي",
}

MODEL_COLORS = {
    "gemini-flash": "🟢",
    "gemini-pro":   "🔵",
    "claude-fast":  "🟡",
    "claude-smart": "🟠",
}

# ── تحميل بيانات الوكلاء ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_all_agents() -> list:
    """Load all agent JSON files from agents directory."""
    agents = []
    if not AGENTS_ROOT.exists():
        return agents
    for cat_dir in sorted(AGENTS_ROOT.iterdir()):
        if not cat_dir.is_dir():
            continue
        for json_file in sorted(cat_dir.glob("*.json")):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                data["_file"] = str(json_file)
                agents.append(data)
            except Exception:
                continue
    agents.sort(key=lambda a: a.get("agent_id", "A00"))
    return agents


def check_gateway() -> bool:
    """Check if FastAPI gateway is running."""
    try:
        resp = requests.get(f"{GATEWAY_URL}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


# ── إحصائيات ──────────────────────────────────────────────────────────────────
def get_stats(agents: list) -> dict:
    by_category = {}
    by_model = {}
    for a in agents:
        cat = a.get("category", "unknown")
        model = a.get("model", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_model[model] = by_model.get(model, 0) + 1
    return {"total": len(agents), "by_category": by_category, "by_model": by_model}


# ══════════════════════════════════════════════════════════════════════════════
# الشريط الجانبي
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🤖 Army81")
    st.caption("نظام الـ 81 وكيل ذكي")

    # حالة البوابة
    gateway_ok = check_gateway()
    if gateway_ok:
        st.success("✅ البوابة متصلة", icon="🟢")
    else:
        st.warning("⚠️ البوابة غير متاحة", icon="🔴")
        st.caption(f"تشغيل: `python gateway/app.py`")

    st.divider()

    # قائمة التنقل
    page = st.radio(
        "التنقل",
        ["🏠 الرئيسية", "🤖 الوكلاء", "📤 إرسال مهمة", "👥 فرق CrewAI", "📈 الإحصائيات"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Army81 v2.0 — Phase 4")


# ── تحميل البيانات ─────────────────────────────────────────────────────────────
all_agents = load_all_agents()
stats = get_stats(all_agents)


# ══════════════════════════════════════════════════════════════════════════════
# صفحة الرئيسية
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 الرئيسية":
    st.title("🤖 Army81 — نظام الوكلاء الذكيين")
    st.markdown("**81 وكيل ذكي متخصص يعملون معاً لتحقيق أهدافك.**")

    # بطاقات الإحصاء السريعة
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي الوكلاء", stats["total"], delta="81 هدف")
    with col2:
        st.metric("الفئات", len(stats["by_category"]))
    with col3:
        st.metric("النماذج المستخدمة", len(stats["by_model"]))
    with col4:
        gw_status = "✅ متصل" if gateway_ok else "❌ غير متاح"
        st.metric("حالة البوابة", gw_status)

    st.divider()

    # توزيع الوكلاء حسب الفئة
    st.subheader("توزيع الوكلاء حسب الفئة")
    cols = st.columns(len(stats["by_category"]))
    for i, (cat, count) in enumerate(sorted(stats["by_category"].items())):
        label = CATEGORY_LABELS.get(cat, cat)
        with cols[i]:
            st.metric(label, count)

    st.divider()

    # آخر الوكلاء
    st.subheader("🆕 أحدث الوكلاء (cat7_new)")
    cat7_agents = [a for a in all_agents if a.get("category") == "cat7_new"]
    if cat7_agents:
        for agent in cat7_agents:
            col_a, col_b = st.columns([1, 4])
            with col_a:
                model_icon = MODEL_COLORS.get(agent.get("model", ""), "⚪")
                st.markdown(f"### {model_icon} {agent.get('agent_id')}")
            with col_b:
                st.markdown(f"**{agent.get('name_ar', agent.get('name'))}**")
                st.caption(agent.get("description", ""))
    else:
        st.info("لم يتم تحميل وكلاء cat7_new بعد.")


# ══════════════════════════════════════════════════════════════════════════════
# صفحة الوكلاء
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 الوكلاء":
    st.title("🤖 قائمة الوكلاء")

    # فلاتر
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_cat = st.selectbox(
            "فلتر الفئة",
            ["الكل"] + sorted(set(a.get("category", "") for a in all_agents)),
        )
    with col_f2:
        filter_model = st.selectbox(
            "فلتر النموذج",
            ["الكل"] + sorted(set(a.get("model", "") for a in all_agents)),
        )
    with col_f3:
        search_text = st.text_input("بحث", placeholder="اسم الوكيل أو وصفه...")

    # تطبيق الفلاتر
    filtered = all_agents
    if filter_cat != "الكل":
        filtered = [a for a in filtered if a.get("category") == filter_cat]
    if filter_model != "الكل":
        filtered = [a for a in filtered if a.get("model") == filter_model]
    if search_text:
        q = search_text.lower()
        filtered = [
            a for a in filtered
            if q in a.get("name", "").lower()
            or q in a.get("name_ar", "").lower()
            or q in a.get("description", "").lower()
            or q in a.get("agent_id", "").lower()
        ]

    st.caption(f"عرض {len(filtered)} من {len(all_agents)} وكيل")

    # عرض الوكلاء في جدول
    for agent in filtered:
        cat_label = CATEGORY_LABELS.get(agent.get("category", ""), agent.get("category", ""))
        model_icon = MODEL_COLORS.get(agent.get("model", ""), "⚪")

        with st.expander(
            f"{model_icon} **{agent.get('agent_id')}** — {agent.get('name_ar', agent.get('name', ''))}",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**الاسم:** {agent.get('name')}")
                st.markdown(f"**الوصف:** {agent.get('description', 'غير محدد')}")
                st.markdown(f"**الفئة:** {cat_label}")
            with col2:
                st.markdown(f"**النموذج:** `{agent.get('model', 'غير محدد')}`")
                tools = agent.get("tools", [])
                if tools:
                    st.markdown(f"**الأدوات ({len(tools)}):**")
                    st.code(", ".join(tools))

            with st.expander("📋 System Prompt", expanded=False):
                st.text(agent.get("system_prompt", "لا يوجد"))


# ══════════════════════════════════════════════════════════════════════════════
# صفحة إرسال مهمة
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📤 إرسال مهمة":
    st.title("📤 إرسال مهمة")

    if not gateway_ok:
        st.error("⚠️ البوابة غير متاحة. شغّل: `python gateway/app.py`")
        st.stop()

    tab1, tab2 = st.tabs(["وكيل محدد", "Workflow"])

    # ── التبويب 1: وكيل محدد ──
    with tab1:
        st.subheader("إرسال مهمة لوكيل محدد")

        agent_options = {
            f"{a.get('agent_id')} — {a.get('name_ar', a.get('name', ''))}": a.get("agent_id")
            for a in all_agents
        }
        selected_label = st.selectbox("اختر الوكيل", list(agent_options.keys()))
        selected_id = agent_options[selected_label]

        task_text = st.text_area(
            "المهمة",
            placeholder="اكتب مهمتك هنا...",
            height=150,
        )

        if st.button("🚀 إرسال للوكيل", type="primary", disabled=not task_text):
            with st.spinner("جارٍ المعالجة..."):
                try:
                    t0 = time.time()
                    resp = requests.post(
                        f"{GATEWAY_URL}/task",
                        json={"agent_id": selected_id, "task": task_text},
                        timeout=60,
                    )
                    elapsed = time.time() - t0

                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"✅ تمت المعالجة في {elapsed:.1f}s")
                        st.subheader("النتيجة:")
                        st.markdown(data.get("result", str(data)))
                    else:
                        st.error(f"خطأ {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"فشل الاتصال: {e}")

    # ── التبويب 2: Workflow ──
    with tab2:
        st.subheader("تشغيل Workflow متعدد الوكلاء")

        workflow_options = {
            "research_pipeline":  "🔬 خط بحث شامل",
            "analysis_pipeline":  "📊 خط تحليل بيانات",
            "decision_support":   "🎯 دعم القرار",
            "custom":             "⚙️ مخصص",
        }
        wf_label = st.selectbox("نوع الـ Workflow", list(workflow_options.values()))
        wf_key = list(workflow_options.keys())[list(workflow_options.values()).index(wf_label)]

        wf_task = st.text_area(
            "المهمة",
            placeholder="اكتب مهمتك هنا...",
            height=150,
            key="wf_task",
        )

        if st.button("🚀 تشغيل Workflow", type="primary", disabled=not wf_task):
            with st.spinner("جارٍ تنفيذ الـ Workflow..."):
                try:
                    t0 = time.time()
                    resp = requests.post(
                        f"{GATEWAY_URL}/workflow",
                        json={"workflow": wf_key, "task": wf_task},
                        timeout=120,
                    )
                    elapsed = time.time() - t0

                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"✅ اكتمل في {elapsed:.1f}s")

                        # عرض نتائج كل وكيل
                        results = data.get("results", [])
                        if results:
                            for i, r in enumerate(results):
                                agent_id = r.get("agent_id", f"وكيل {i+1}")
                                with st.expander(f"📋 نتيجة {agent_id}", expanded=(i == len(results) - 1)):
                                    st.markdown(r.get("result", str(r)))

                        if data.get("final_answer"):
                            st.subheader("✨ الإجابة النهائية:")
                            st.markdown(data["final_answer"])
                    else:
                        st.error(f"خطأ {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"فشل الاتصال: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# صفحة فرق CrewAI
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 فرق CrewAI":
    st.title("👥 فرق CrewAI")
    st.markdown("3 فرق متخصصة تعمل بالتعاون لإنجاز مهام معقدة.")

    # بطاقات الفرق
    teams_info = [
        {
            "key": "strategic",
            "title": "🏛️ فريق التحليل الاستراتيجي",
            "agents": ["A01 — القائد الاستراتيجي", "A31 — الاستخبارات", "A32 — الجيوسياسة", "A33 — المستقبليات"],
            "desc": "يحلل التحديات الاستراتيجية من أبعاد متعددة ويقدم توصيات شاملة.",
            "placeholder": "مثال: ما التأثيرات الاستراتيجية لصعود الذكاء الاصطناعي على الاقتصاد العربي؟",
        },
        {
            "key": "research",
            "title": "🔬 فريق البحث العلمي",
            "agents": ["A07 — الطب والصحة", "A38 — الفيزياء والكم", "A39 — المناخ", "A40 — رصد التكنولوجيا"],
            "desc": "يُجري أبحاثاً متعددة التخصصات ويدمج النتائج العلمية.",
            "placeholder": "مثال: ما أحدث التطورات في الحوسبة الكمية وتطبيقاتها الطبية؟",
        },
        {
            "key": "crisis",
            "title": "🚨 فريق إدارة الأزمات",
            "agents": ["A29 — حل النزاعات", "A34 — إدارة الأزمات", "A35 — الابتكار", "A23 — إدارة التغيير"],
            "desc": "يعالج الأزمات والتحديات الحرجة بسرعة وفعالية.",
            "placeholder": "مثال: كيف نتعامل مع أزمة سمعة مؤسسية مفاجئة في وسائل التواصل؟",
        },
    ]

    for team in teams_info:
        st.subheader(team["title"])
        col1, col2 = st.columns([2, 1])

        with col1:
            st.caption(team["desc"])
            task_input = st.text_area(
                "المهمة",
                placeholder=team["placeholder"],
                height=100,
                key=f"crew_task_{team['key']}",
            )

        with col2:
            st.markdown("**الوكلاء:**")
            for agent_name in team["agents"]:
                st.markdown(f"• {agent_name}")

        use_crewai = st.checkbox(f"استخدم CrewAI الفعلي (يتطلب API key)", key=f"use_crewai_{team['key']}")

        if st.button(f"🚀 تشغيل {team['title']}", key=f"run_{team['key']}", disabled=not task_input):
            with st.spinner("جارٍ تشغيل الفريق..."):
                try:
                    # استدعاء مباشر لـ crews module
                    import sys
                    sys.path.insert(0, str(Path(__file__).parent.parent))
                    from crews.army81_crews import run_team

                    t0 = time.time()
                    result = run_team(team["key"], task_input)
                    elapsed = time.time() - t0

                    st.success(f"✅ اكتمل في {elapsed:.1f}s | وضع: {result.get('mode', 'unknown')}")
                    st.subheader("النتيجة:")
                    output = result.get("output") or result.get("combined_output") or result.get("error", "لا نتيجة")
                    st.markdown(output)

                    if result.get("individual_results"):
                        with st.expander("📋 نتائج تفصيلية"):
                            for r in result["individual_results"]:
                                st.markdown(f"**{r['agent']}:**")
                                st.markdown(r.get("result", r.get("error", "")))
                                st.divider()

                except Exception as e:
                    st.error(f"خطأ: {e}")

        st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# صفحة الإحصائيات
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 الإحصائيات":
    st.title("📈 إحصائيات النظام")

    # إحصائيات الوكلاء
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("توزيع الوكلاء حسب الفئة")
        cat_data = {CATEGORY_LABELS.get(k, k): v for k, v in stats["by_category"].items()}
        st.bar_chart(cat_data)

    with col2:
        st.subheader("توزيع الوكلاء حسب النموذج")
        st.bar_chart(stats["by_model"])

    st.divider()

    # جدول تفصيلي
    st.subheader("جدول الوكلاء الكامل")
    table_data = []
    for a in all_agents:
        table_data.append({
            "ID": a.get("agent_id", ""),
            "الاسم": a.get("name_ar", a.get("name", "")),
            "الفئة": CATEGORY_LABELS.get(a.get("category", ""), a.get("category", "")),
            "النموذج": a.get("model", ""),
            "عدد الأدوات": len(a.get("tools", [])),
        })
    st.dataframe(table_data, use_container_width=True, height=400)

    st.divider()

    # معلومات البوابة
    if gateway_ok:
        st.subheader("📡 معلومات البوابة")
        try:
            health = requests.get(f"{GATEWAY_URL}/health", timeout=2).json()
            st.json(health)
        except Exception:
            st.warning("لم يتمكن من جلب معلومات البوابة")
    else:
        st.info("البوابة غير متاحة حالياً.")

    # ملف daily report
    st.divider()
    st.subheader("📄 آخر تقرير يومي")
    reports_dir = Path(__file__).parent.parent / "workspace" / "reports"
    if reports_dir.exists():
        report_files = sorted(reports_dir.glob("*.md"), reverse=True)
        if report_files:
            latest = report_files[0]
            st.caption(f"ملف: {latest.name}")
            with open(latest, encoding="utf-8") as f:
                content = f.read()
            st.markdown(content[:3000] + ("..." if len(content) > 3000 else ""))
        else:
            st.info("لا توجد تقارير حتى الآن. شغّل: `python scripts/daily_updater.py`")
    else:
        st.info("مجلد التقارير غير موجود.")
