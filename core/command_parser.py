"""
Army81 v8 — Command Parser
يحلل أوامر المستخدم ويوجهها للنظام المناسب
يعمل من: Gateway API + Telegram + Dashboard

الأوامر المدعومة:
  درّب A04              → تدريب وكيل محدد
  درّب الكل             → دورة تدريب كاملة
  تدريب مكثف A01        → 5 مهام متتالية
  اكتشف                 → اكتشاف معرفة جديدة
  تقييم                 → تقييم ذاتي أسبوعي
  مستوى A04             → عرض مستوى وكيل
  مستويات               → كل المستويات
  ترتيب                 → leaderboard
  تدريب جماعي           → multi-agent drill
  زامن                  → مزامنة ذاكرة سحابية
  حالة التدريب          → training status
  شبكة                  → network status
  سيناريو علوم صعب      → سيناريو محدد
"""
import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger("army81.command_parser")


# Command patterns (Arabic + English)
COMMANDS = {
    # Training
    "train_agent": {
        "patterns": [
            r"^درّب\s+(A\d+)",
            r"^train\s+(A\d+)",
            r"^تدريب\s+(A\d+)",
        ],
        "handler": "train_agent",
    },
    "train_all": {
        "patterns": [
            r"^درّب الكل",
            r"^train all",
            r"^تدريب الكل",
            r"^دورة تدريب",
            r"^ابدأ التدريب",
        ],
        "handler": "train_all",
    },
    "intensive": {
        "patterns": [
            r"^تدريب مكثف\s+(A\d+)",
            r"^intensive\s+(A\d+)",
            r"^كثّف\s+(A\d+)",
        ],
        "handler": "intensive",
    },
    "multi_drill": {
        "patterns": [
            r"^تدريب جماعي",
            r"^drill",
            r"^تمرين جماعي",
        ],
        "handler": "multi_drill",
    },

    # Discovery
    "discover": {
        "patterns": [
            r"^اكتشف",
            r"^discover",
            r"^ابحث عن معرفة",
            r"^اكتشاف",
        ],
        "handler": "discover",
    },
    "assess": {
        "patterns": [
            r"^تقييم ذاتي",
            r"^تقييم",
            r"^assess",
            r"^قيّم النظام",
        ],
        "handler": "assess",
    },

    # Levels & Leaderboard
    "level": {
        "patterns": [
            r"^مستوى\s+(A\d+)",
            r"^level\s+(A\d+)",
        ],
        "handler": "level",
    },
    "levels": {
        "patterns": [
            r"^مستويات",
            r"^levels",
            r"^كل المستويات",
        ],
        "handler": "levels",
    },
    "leaderboard": {
        "patterns": [
            r"^ترتيب",
            r"^leaderboard",
            r"^أفضل الوكلاء",
            r"^ranking",
        ],
        "handler": "leaderboard",
    },

    # System
    "cloud_sync": {
        "patterns": [
            r"^زامن",
            r"^sync",
            r"^مزامنة",
        ],
        "handler": "cloud_sync",
    },
    "training_status": {
        "patterns": [
            r"^حالة التدريب",
            r"^training status",
        ],
        "handler": "training_status",
    },
    "network_status": {
        "patterns": [
            r"^شبكة",
            r"^network",
            r"^حالة الشبكة",
        ],
        "handler": "network_status",
    },
    "scenario": {
        "patterns": [
            r"^سيناريو\s+(\S+)\s*(سهل|متوسط|صعب|easy|medium|hard)?",
            r"^scenario\s+(\S+)\s*(easy|medium|hard)?",
        ],
        "handler": "scenario",
    },
    "evolve": {
        "patterns": [
            r"^طوّر",
            r"^evolve",
            r"^تطوير ذاتي",
            r"^ابدأ التطور",
        ],
        "handler": "evolve",
    },
}


def parse_command(text: str) -> Optional[Tuple[str, Dict]]:
    """
    يحلل النص ويكتشف إذا كان أمراً
    يعيد (handler_name, params) أو None إذا ليس أمراً
    """
    text = text.strip()

    for cmd_name, cmd_info in COMMANDS.items():
        for pattern in cmd_info["patterns"]:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                params = {"groups": match.groups()}
                return cmd_info["handler"], params

    return None


def execute_command(handler: str, params: Dict, router=None) -> Dict:
    """ينفذ الأمر ويعيد النتيجة"""

    if handler == "train_agent":
        agent_id = params["groups"][0] if params["groups"] else None
        if not agent_id:
            return {"result": "حدد الوكيل: درّب A04", "status": "error"}
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            if router and agent_id in router.agents:
                agent = router.agents[agent_id]
                r = t._train_single_agent(agent)
                return {
                    "result": f"🎯 تدريب {agent_id}:\nالنتيجة: {r['score']}/10 ({r['grade']})\nالمستوى: {t.get_level(agent_id)}\n{'⬆️ ترقية!' if r.get('leveled_up') else ''}",
                    "status": "success",
                    "data": r,
                }
            return {"result": f"الوكيل {agent_id} غير موجود", "status": "error"}
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "train_all":
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            r = t.train_cycle(max_agents=81)
            return {
                "result": f"🏋️ دورة تدريب مكتملة:\n✅ نجح: {r['passed']}/{r['trained']}\n⬆️ ترقية: {r['leveled_up']} وكيل\n⏱ {r.get('elapsed_seconds', 0)}s",
                "status": "success",
                "data": r,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "intensive":
        agent_id = params["groups"][0] if params["groups"] else None
        if not agent_id:
            return {"result": "حدد الوكيل: تدريب مكثف A04", "status": "error"}
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            r = t.intensive_training(agent_id, 5)
            return {
                "result": f"💪 تدريب مكثف {agent_id}:\nالمتوسط: {r.get('avg_score', 0)}/10\nالمهام: {r.get('tasks', 0)}",
                "status": "success",
                "data": r,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "multi_drill":
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            r = t.multi_agent_drill()
            agents = r.get("agents", [])
            return {
                "result": f"🎯 تدريب جماعي:\nالوكلاء: {' → '.join(agents)}\nالحالة: {r.get('status', '?')}\n⏱ {r.get('elapsed_seconds', 0)}s",
                "status": "success",
                "data": r,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "discover":
        try:
            from core.self_builder import SelfBuilder
            b = SelfBuilder()
            r = b.discover_and_add_knowledge()
            gh = r.get("github", [])
            return {
                "result": f"🔍 اكتشاف معرفة:\n🐙 GitHub: {len(gh)} مستودع\n" + "\n".join(f"⭐ {repo['name']} ({repo.get('stars', 0)} stars)" for repo in gh[:3]),
                "status": "success",
                "data": r,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "assess":
        try:
            from core.self_builder import SelfBuilder
            b = SelfBuilder()
            r = b.weekly_self_assessment()
            gaps = r.get("knowledge_gaps", [])
            missing = r.get("missing_skills", [])
            return {
                "result": f"📋 تقييم ذاتي:\n⚠ فجوات: {len(gaps)}\n🧩 مهارات مفقودة: {len(missing)}\n{'• ' + chr(10).join(missing[:5]) if missing else 'لا شيء'}",
                "status": "success",
                "data": r,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "level":
        agent_id = params["groups"][0] if params["groups"] else None
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            lvl = t.get_level(agent_id)
            bar = "█" * lvl + "░" * (10 - lvl)
            return {
                "result": f"📊 مستوى {agent_id}: {lvl}/10\n[{bar}]",
                "status": "success",
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "levels":
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            levels = t.get_all_levels()
            dist = {}
            for lvl in levels.values():
                dist[lvl] = dist.get(lvl, 0) + 1
            lines = [f"📊 توزيع المستويات:"]
            for lvl in sorted(dist.keys()):
                lines.append(f"  المستوى {lvl}: {dist[lvl]} وكيل")
            lines.append(f"المتوسط: {sum(levels.values())/len(levels):.1f}")
            return {"result": "\n".join(lines), "status": "success"}
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "leaderboard":
        try:
            from core.scenario_engine import get_scenario_engine
            se = get_scenario_engine()
            lb = se.get_leaderboard()
            if not lb:
                return {"result": "لا بيانات — ابدأ التدريب أولاً: درّب الكل", "status": "success"}
            lines = ["🏆 أفضل الوكلاء:"]
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, a in enumerate(lb[:10]):
                medal = medals[i] if i < 5 else f"{i+1}."
                lines.append(f"  {medal} {a['agent_id']}: {a['avg_score']}/10 ({a['grade']}) — {a['tasks_completed']} مهمة")
            return {"result": "\n".join(lines), "status": "success"}
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "cloud_sync":
        try:
            from memory.cloud_memory import get_cloud_memory
            cm = get_cloud_memory()
            r = cm.sync_local_to_cloud()
            return {
                "result": f"☁️ مزامنة سحابية:\nتم رفع: {r.get('synced', 0)} حلقة\nالإجمالي المحلي: {r.get('total_local', 0)}",
                "status": "success",
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "training_status":
        try:
            from core.continuous_trainer import get_continuous_trainer
            t = get_continuous_trainer(router)
            s = t.status()
            return {
                "result": f"🏋️ حالة التدريب:\nالوكلاء: {s['agents_tracked']}\nالمتوسط: {s['avg_level']}/10\nأعلى: {s['max_level']} | أدنى: {s['min_level']}\nالسيناريوهات: {s['scenarios']['total_scenarios']}",
                "status": "success",
                "data": s,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "network_status":
        try:
            from core.neural_network import get_neural_network
            nn = get_neural_network()
            s = nn.status()
            return {
                "result": f"🧬 الشبكة العصبية:\nالعقد: {s['graph_nodes']}\nالروابط: {s['graph_edges']}\nالإشارات: {s['stats']['signals_propagated']}\nقرارات القائد: {s['stats']['commander_decisions']}",
                "status": "success",
                "data": s,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "evolve":
        try:
            from core.safe_evolution import SafeEvolution
            se = SafeEvolution()
            r = se.weekly_cycle()
            return {
                "result": f"🧬 دورة تطور:\nتم تحسين: {len(r.get('changed', []))} وكيل\nالنتائج: {r}",
                "status": "success",
                "data": r,
            }
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    elif handler == "scenario":
        groups = params.get("groups", ())
        cat = groups[0] if len(groups) > 0 else "cat1_science"
        diff = groups[1] if len(groups) > 1 and groups[1] else "medium"
        diff_map = {"سهل": "easy", "متوسط": "medium", "صعب": "hard"}
        diff = diff_map.get(diff, diff)
        try:
            from core.scenario_engine import get_scenario_engine
            se = get_scenario_engine()
            # Map Arabic category names
            cat_map = {"علوم": "cat1_science", "مجتمع": "cat2_society", "أدوات": "cat3_tools",
                       "إدارة": "cat4_management", "سلوك": "cat5_behavior", "قيادة": "cat6_leadership",
                       "تطور": "cat7_new"}
            cat = cat_map.get(cat, cat)
            sc = se.get_scenario(cat, diff)
            if sc:
                return {"result": f"📝 سيناريو [{cat}/{diff}]:\n\n{sc['task']}", "status": "success"}
            return {"result": f"لا سيناريو لـ {cat}/{diff}", "status": "error"}
        except Exception as e:
            return {"result": f"خطأ: {e}", "status": "error"}

    return {"result": "أمر غير معروف", "status": "error"}


def is_command(text: str) -> bool:
    """هل النص أمر نظام؟"""
    return parse_command(text) is not None
