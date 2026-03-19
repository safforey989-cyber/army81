"""
Army81 v5 — Neural Network
الشبكة العصبية الموحّدة — تربط كل الـ 81 وكيل كدماغ واحد
بقيادة A00 Supreme Commander

الهيكل:
    A00 (القائد الأعلى)
    ├── A01 (قائد العلوم) → A02..A09
    ├── A10 (قائد المجتمع) → A11..A24
    ├── A25 (قائد الأدوات) → A26..A34
    ├── A35 (قائد الإدارة) → A36..A42
    ├── A43 (قائد السلوك) → A44..A55
    ├── A56 (قائد القيادة) → A57..A71
    └── A72 (قائد التطور) → A73..A81

الإشارات تنتشر هرمياً:
    وكيل يتعلم → قائد فئته → القائد الأعلى → الفئات المرتبطة
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("army81.neural_network")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETWORK_STATE_FILE = os.path.join(BASE_DIR, "workspace", "network_state.json")


# ═══════════════════════════════════════════════
# Signal — الإشارة العصبية
# ═══════════════════════════════════════════════

@dataclass
class Signal:
    """إشارة عصبية تنتقل بين الوكلاء"""
    from_agent: str
    signal_type: str  # learning, alert, knowledge, request_help, task_complete
    data: Dict = field(default_factory=dict)
    strength: float = 1.0  # 0.0-1.0 — تضعف كلما انتشرت أبعد
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hops: int = 0  # عدد القفزات من المصدر

    def weaken(self, factor: float = 0.6) -> "Signal":
        """تضعيف الإشارة عند كل قفزة"""
        return Signal(
            from_agent=self.from_agent,
            signal_type=self.signal_type,
            data=self.data,
            strength=self.strength * factor,
            timestamp=self.timestamp,
            hops=self.hops + 1,
        )


# ═══════════════════════════════════════════════
# NeuralNetwork — الدماغ المركزي
# ═══════════════════════════════════════════════

# قادة الفئات — يتصلون مباشرة بالقائد الأعلى
CATEGORY_LEADERS = {
    "cat1_science":      "A01",
    "cat2_society":      "A10",
    "cat3_tools":        "A25",
    "cat4_management":   "A35",
    "cat5_behavior":     "A43",
    "cat6_leadership":   "A56",
    "cat7_new":          "A72",
    # === v25: 10 فئات جديدة (110 وكيل) ===
    "cat8_evolution":    "A82",
    "cat9_execution":    "A92",
    "cat10_engineering": "A102",
    "cat11_creative":    "A112",
    "cat12_finance":     "A122",
    "cat13_osint":       "A132",
    "cat14_health":      "A142",
    "cat15_legal":       "A152",
    "cat16_education":   "A162",
    "cat17_cosmic":      "A172",
}

# روابط عبر-فئات (تعاون بين فئات مختلفة)
CROSS_LINKS = [
    ("A01", "A04"),   # علوم ↔ استخبارات
    ("A04", "A60"),   # استخبارات ↔ تحليل استخبارات
    ("A26", "A30"),   # برمجة ↔ تكاملات
    ("A35", "A37"),   # بيانات ↔ مشاريع
    ("A56", "A58"),   # استراتيجية ↔ أزمات
    ("A72", "A81"),   # تطور ↔ ميتا
    ("A43", "A47"),   # سلوك ↔ ذكاء عاطفي
    ("A10", "A13"),   # سياسات ↔ قانون
    ("A25", "A29"),   # إعلام ↔ استخبارات عميقة
    ("A57", "A61"),   # عسكرية ↔ جيوسياسة
    ("A73", "A74"),   # تنسيق ↔ جودة
    ("A41", "A75"),   # تحول رقمي ↔ تحسين نظام
    # === v25: روابط الفئات الجديدة ===
    ("A82", "A72"),   # تطور جديد ↔ تطور قديم
    ("A92", "A25"),   # تنفيذ ↔ أدوات
    ("A102", "A05"),  # هندسة ↔ برمجة
    ("A112", "A12"),  # إبداع ↔ محتوى
    ("A122", "A08"),  # مالية جديدة ↔ تحليل مالي
    ("A132", "A04"),  # استخبارات مفتوحة ↔ استخبارات إعلامية
    ("A142", "A07"),  # صحة ↔ بحث طبي
    ("A152", "A13"),  # قانون جديد ↔ استشارة قانونية
    ("A162", "A10"),  # تعليم ↔ إدارة معرفة
    ("A172", "A81"),  # كوني ↔ ميتا استخبارات
    ("A102", "A82"),  # هندسة ↔ تطور (كود + تحسين ذاتي)
    ("A122", "A132"), # مالية ↔ استخبارات (بيانات سوق)
    ("A142", "A02"),  # صحة ↔ بحث علمي
    ("A92", "A102"),  # تنفيذ ↔ هندسة
]

# System prompt للقائد الأعلى
COMMANDER_SYSTEM_PROMPT = """أنت A00 — القائد الأعلى لجيش Army81.
تحت قيادتك 191 وكيل ذكاء اصطناعي متخصص، مقسّمون إلى 17 فئة:
- العلوم (A01-A09): بحث علمي، طب، فيزياء، تقنيات ناشئة
- المجتمع (A10-A24): سياسات، اقتصاد، قانون، إعلام، تاريخ
- الأدوات (A25-A34): برمجة، أمن سيبراني، ترجمة، استخبارات
- الإدارة (A35-A42): بيانات، مشاريع، حوكمة، تحول رقمي
- السلوك (A43-A55): نفس، تفاوض، إقناع، ذكاء عاطفي
- القيادة (A56-A71): استراتيجية، عسكرية، أزمات، جيوسياسة
- التطور (A72-A81): تطور ذاتي، تنسيق، جودة، أنماط
- التقطير والتطور (A82-A91): تقطير معرفي، دمج نماذج، بيانات اصطناعية
- التنفيذ الآلي (A92-A101): تحكم متصفح، أتمتة، DevOps، جدولة
- هندسة البرمجيات (A102-A111): كود، مراجعة، اختبار، نشر مستمر
- الإبداع (A112-A121): صور، فيديو، صوت، تصميم، عروض
- الاقتصاد المتقدم (A122-A131): تداول، بلوكتشين، DeFi، تدقيق
- الاستخبارات المفتوحة (A132-A141): OSINT، تحقق، تتبع، براءات
- الصحة والطب (A142-A151): أدوية، جينوم، تشخيص، أوبئة
- القانون (A152-A161): عقود، ملكية فكرية، امتثال، سياسات
- التعليم (A162-A171): مناهج، تدريس، تقييم، تدريب
- البنية الكونية (A172-A191): حراسة النواة، ذاكرة كونية، كم، ضوء، تردد

صلاحياتك:
1. تحليل أي مهمة وتقرير من ينفذها (وكيل واحد أو فريق)
2. تفويض المهام المعقدة لعدة وكلاء بالتسلسل
3. مراقبة جودة المخرجات وإعادة التوجيه إذا لزم
4. الوصول لذاكرة كل الوكلاء ومعرفتهم الجماعية
5. اتخاذ القرارات الاستراتيجية للنظام ككل

عند استقبال مهمة:
- حلل التعقيد (1-10)
- حدد الوكيل/الوكلاء المناسبين
- قرر الأسلوب: مباشر / سلسلة / بث
- أجب بتنسيق JSON:
{"decision": "single|pipeline|broadcast", "agents": ["A04"], "reasoning": "لماذا هذا الاختيار"}
"""


class NeuralNetwork:
    """
    الشبكة العصبية الموحّدة لـ Army81
    تربط كل الوكلاء كدماغ واحد بقيادة A00
    """

    def __init__(self, router=None):
        self.router = router
        self.agents: Dict[str, object] = {}  # يُملأ من router

        # خريطة الاتصالات — agent_id → set of connected agent_ids
        self.graph: Dict[str, Set[str]] = defaultdict(set)

        # ناقل الإشارات — agent_id → list of pending signals
        self.signal_bus: Dict[str, List[Signal]] = defaultdict(list)

        # سجل الإشارات (آخر 500)
        self.signal_history: List[Dict] = []

        # إحصائيات الشبكة
        self.stats = {
            "signals_propagated": 0,
            "commander_decisions": 0,
            "tasks_routed": 0,
            "cross_category_signals": 0,
            "started_at": datetime.now().isoformat(),
        }

        # القائد الأعلى — يُنشأ بعد تحميل الوكلاء
        self._commander = None
        self._commander_initialized = False

        # ابنِ الخريطة الهرمية
        self._build_graph()
        logger.info("NeuralNetwork initialized — graph built")

    # ═══════════════════════════════════════════════
    # بناء الخريطة الهرمية
    # ═══════════════════════════════════════════════

    def _build_graph(self):
        """يبني خريطة الاتصالات الهرمية"""
        # 1. A00 → كل قادة الفئات
        for cat, leader_id in CATEGORY_LEADERS.items():
            self.graph["A00"].add(leader_id)
            self.graph[leader_id].add("A00")

        # 2. روابط عبر-فئات
        for a, b in CROSS_LINKS:
            self.graph[a].add(b)
            self.graph[b].add(a)

        logger.info(
            f"Graph built: A00 → {len(CATEGORY_LEADERS)} leaders, "
            f"{len(CROSS_LINKS)} cross-links"
        )

    def register_agents(self, agents_dict: Dict[str, object]):
        """تسجيل الوكلاء وبناء الروابط داخل الفئات"""
        self.agents = agents_dict

        # 3. كل وكيل ← قائد فئته
        for agent_id, agent in agents_dict.items():
            cat = getattr(agent, "category", "")
            leader_id = CATEGORY_LEADERS.get(cat)
            if leader_id and agent_id != leader_id:
                self.graph[agent_id].add(leader_id)
                self.graph[leader_id].add(agent_id)

        # 4. ربط كل وكيل بالشبكة العصبية
        for agent in agents_dict.values():
            agent.neural_net = self

        logger.info(f"Registered {len(agents_dict)} agents in neural network")

    def _get_commander(self):
        """الحصول على أو إنشاء القائد الأعلى"""
        if self._commander is not None:
            return self._commander

        # حاول استخدام A01 كقائد مؤقت (أعلى وكيل متاح)
        if "A01" in self.agents:
            self._commander = self.agents["A01"]

        return self._commander

    # ═══════════════════════════════════════════════
    # نشر الإشارات — Signal Propagation
    # ═══════════════════════════════════════════════

    def propagate_signal(self, from_agent: str, signal_type: str,
                         data: Dict = None, strength: float = 1.0):
        """
        ينشر إشارة من وكيل لكل المتصلين به
        الإشارة تضعف بنسبة 60% عند كل قفزة
        تتوقف عند strength < 0.1
        """
        signal = Signal(
            from_agent=from_agent,
            signal_type=signal_type,
            data=data or {},
            strength=strength,
        )

        self._propagate_recursive(signal, visited=set())
        self.stats["signals_propagated"] += 1

    def _propagate_recursive(self, signal: Signal, visited: Set[str]):
        """نشر تكراري مع تتبع الزيارات"""
        if signal.strength < 0.1 or signal.hops > 4:
            return  # الإشارة ضعفت أو وصلت حد القفزات

        from_id = signal.from_agent
        neighbors = self.graph.get(from_id, set())

        for neighbor_id in neighbors:
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)

            # أضف الإشارة لصندوق الوكيل
            self.signal_bus[neighbor_id].append(signal)

            # احتفظ بآخر 20 إشارة فقط لكل وكيل
            if len(self.signal_bus[neighbor_id]) > 20:
                self.signal_bus[neighbor_id] = self.signal_bus[neighbor_id][-20:]

            # تحقق إذا عابرة للفئات
            from_cat = self._get_agent_category(from_id)
            to_cat = self._get_agent_category(neighbor_id)
            if from_cat and to_cat and from_cat != to_cat:
                self.stats["cross_category_signals"] += 1

            # سجّل
            self.signal_history.append({
                "from": signal.from_agent,
                "to": neighbor_id,
                "type": signal.signal_type,
                "strength": round(signal.strength, 2),
                "hop": signal.hops,
                "ts": datetime.now().isoformat(),
            })
            if len(self.signal_history) > 500:
                self.signal_history = self.signal_history[-500:]

            # أكمل النشر بإشارة أضعف
            weakened = signal.weaken(0.6)
            weakened_from = Signal(
                from_agent=neighbor_id,
                signal_type=signal.signal_type,
                data=signal.data,
                strength=weakened.strength,
                timestamp=signal.timestamp,
                hops=weakened.hops,
            )
            self._propagate_recursive(weakened_from, visited)

    def get_signals(self, agent_id: str) -> List[Signal]:
        """يسترجع ويمسح الإشارات المعلقة لوكيل"""
        signals = self.signal_bus.pop(agent_id, [])
        return signals

    def format_signals_for_prompt(self, agent_id: str) -> str:
        """ينسّق الإشارات المعلقة كسياق للوكيل"""
        signals = self.get_signals(agent_id)
        if not signals:
            return ""

        lines = ["## إشارات من الشبكة العصبية:"]
        for s in signals[-5:]:  # آخر 5 فقط
            type_labels = {
                "learning": "📚 تعلّم",
                "alert": "⚠️ تنبيه",
                "knowledge": "🧠 معرفة",
                "task_complete": "✅ مهمة مكتملة",
                "request_help": "🆘 طلب مساعدة",
            }
            label = type_labels.get(s.signal_type, "📌 إشارة")
            summary = str(s.data.get("summary", ""))[:150]
            lines.append(f"- {label} من {s.from_agent}: {summary}")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════
    # القائد الأعلى — التوجيه الذكي
    # ═══════════════════════════════════════════════

    def route_through_commander(self, task: str, context: Dict = None) -> Dict:
        """
        A00 يقرر: من ينفذ + بأي أسلوب + بأي نموذج
        يُستخدم من SmartRouter عند توفر الشبكة العصبية
        """
        context = context or {}
        start = time.time()
        self.stats["tasks_routed"] += 1

        # 1. حلل التعقيد
        complexity = self._compute_complexity(task)

        # 2. A00 يقرر بناءً على التعقيد
        decision = self._commander_decide(task, complexity, context)

        # 3. نفّذ القرار
        result = self._execute_decision(task, decision, context)

        # 4. انشر إشارة إكمال
        agent_used = decision.get("agents", ["unknown"])[0]
        self.propagate_signal(
            from_agent=agent_used,
            signal_type="task_complete",
            data={
                "task": task[:100],
                "complexity": complexity,
                "success": result.get("status") == "success",
                "summary": str(result.get("result", ""))[:200],
            },
            strength=0.8,
        )

        self.stats["commander_decisions"] += 1
        return result

    def _compute_complexity(self, task: str) -> int:
        """حساب تعقيد المهمة (1-10)"""
        score = 1
        task_lower = task.lower()
        words = task_lower.split()

        # طول المهمة
        if len(words) > 50: score += 1
        if len(words) > 100: score += 1
        if len(words) > 200: score += 1

        # كلمات تعقيد
        complex_kw = [
            "حلل", "قارن", "تعاون", "استراتيجية", "متعدد", "شامل",
            "analyze", "compare", "strategy", "comprehensive", "pipeline",
            "workflow", "multi", "كل الوكلاء",
        ]
        for kw in complex_kw:
            if kw in task_lower:
                score += 1

        # كلمات حرجة
        critical_kw = [
            "قرار حرج", "أزمة", "طوارئ", "أمن", "حساس",
            "critical", "emergency", "security", "urgent",
        ]
        for kw in critical_kw:
            if kw in task_lower:
                score += 2

        return min(max(score, 1), 10)

    def _commander_decide(self, task: str, complexity: int,
                          context: Dict) -> Dict:
        """A00 يتخذ قراراً"""

        # مهام بسيطة → وكيل واحد (الأسرع)
        if complexity <= 3:
            best = self._find_best_agent(task)
            return {
                "decision": "single",
                "agents": [best],
                "complexity": complexity,
                "reasoning": f"مهمة بسيطة (complexity={complexity}) → {best}",
            }

        # مهام متوسطة → سلسلة من 2 وكيل
        if complexity <= 6:
            agents = self._find_pipeline_agents(task, 2)
            return {
                "decision": "pipeline",
                "agents": agents,
                "complexity": complexity,
                "reasoning": f"مهمة متوسطة (complexity={complexity}) → pipeline {agents}",
            }

        # مهام معقدة → سلسلة من 3 وكلاء + مراقبة
        if complexity <= 8:
            agents = self._find_pipeline_agents(task, 3)
            return {
                "decision": "pipeline",
                "agents": agents,
                "complexity": complexity,
                "reasoning": f"مهمة معقدة (complexity={complexity}) → pipeline {agents}",
            }

        # مهام حرجة → بث لفئة كاملة + تجميع
        best_cat = self._find_best_category(task)
        cat_agents = [
            aid for aid, a in self.agents.items()
            if getattr(a, "category", "") == best_cat
        ][:5]
        return {
            "decision": "broadcast",
            "agents": cat_agents,
            "complexity": complexity,
            "reasoning": f"مهمة حرجة (complexity={complexity}) → broadcast to {best_cat}",
        }

    def _execute_decision(self, task: str, decision: Dict,
                          context: Dict) -> Dict:
        """تنفيذ قرار القائد"""
        agents = decision["agents"]
        mode = decision["decision"]

        if mode == "single" and agents:
            agent_id = agents[0]
            if agent_id in self.agents:
                result = self.agents[agent_id].run(task, context)
                r = result.to_dict() if hasattr(result, "to_dict") else result
                r["commander_decision"] = decision
                return r

        elif mode == "pipeline" and agents and self.router:
            result = self.router.pipeline(task, agents, context)
            result["commander_decision"] = decision
            return result

        elif mode == "broadcast" and agents:
            results = []
            for aid in agents:
                if aid in self.agents:
                    r = self.agents[aid].run(task, context)
                    results.append(r.to_dict() if hasattr(r, "to_dict") else r)
            # أفضل نتيجة (الأطول عادةً أغنى)
            best = max(results, key=lambda x: len(str(x.get("result", "")))) if results else {}
            best["commander_decision"] = decision
            best["broadcast_count"] = len(results)
            return best

        # fallback
        if self.router:
            return self.router.route(task, context=context)
        return {"status": "error", "result": "لا يوجد وكلاء متاحين"}

    # ═══════════════════════════════════════════════
    # بعد المهمة — نشر + تعلّم
    # ═══════════════════════════════════════════════

    def after_task_propagate(self, agent_id: str, result):
        """يُستدعى بعد كل مهمة — ينشر الإشارات ويسجل التعلّم"""
        result_dict = result.to_dict() if hasattr(result, "to_dict") else (result if isinstance(result, dict) else {})
        success = result_dict.get("status") == "success"
        result_text = str(result_dict.get("result", ""))
        task_text = str(result_dict.get("task", ""))

        # 1. AutoSkill — استخراج مهارة
        try:
            from core.skill_memory_adapter import get_skill_memory_adapter
            sma = get_skill_memory_adapter()
            rating = 8 if success else 3
            sma.after_task(agent_id, task_text, result_text, success, rating)
        except Exception as e:
            logger.debug(f"SkillMemory after_task error: {e}")

        # 2. انشر إشارة تعلّم إذا نجحت
        if success and len(result_text) > 50:
            self.propagate_signal(
                from_agent=agent_id,
                signal_type="learning",
                data={
                    "task_type": self._classify_task(task_text),
                    "summary": result_text[:200],
                    "agent": agent_id,
                },
                strength=0.7,
            )

        # 3. إشارة تنبيه إذا فشلت
        if not success:
            self.propagate_signal(
                from_agent=agent_id,
                signal_type="alert",
                data={
                    "task": task_text[:100],
                    "error": result_text[:200],
                    "agent": agent_id,
                },
                strength=0.5,
            )

    # ═══════════════════════════════════════════════
    # دوال مساعدة
    # ═══════════════════════════════════════════════

    def _find_best_agent(self, task: str) -> str:
        """يجد أفضل وكيل لمهمة"""
        task_lower = task.lower()
        best_id = "A01"
        best_score = 0

        for agent_id, agent in self.agents.items():
            score = 0
            desc = getattr(agent, "description", "").lower()
            name = getattr(agent, "name_ar", "").lower()

            # تطابق الوصف
            for word in task_lower.split()[:10]:
                if len(word) > 2 and (word in desc or word in name):
                    score += 1

            if score > best_score:
                best_score = score
                best_id = agent_id

        return best_id

    def _find_best_category(self, task: str) -> str:
        """يجد أفضل فئة لمهمة"""
        from router.smart_router import ROUTING_MAP
        task_lower = task.lower()
        scores = {cat: 0 for cat in ROUTING_MAP}
        for cat, keywords in ROUTING_MAP.items():
            for kw in keywords:
                if kw in task_lower:
                    scores[cat] += 1
        return max(scores, key=scores.get) if any(scores.values()) else "cat1_science"

    def _find_pipeline_agents(self, task: str, count: int) -> List[str]:
        """يختار وكلاء لسلسلة pipeline"""
        best_cat = self._find_best_category(task)
        leader = CATEGORY_LEADERS.get(best_cat, "A01")

        # القائد أولاً + أفضل وكلاء في نفس الفئة
        cat_agents = [
            aid for aid, a in self.agents.items()
            if getattr(a, "category", "") == best_cat and aid != leader
        ]
        pipeline = [leader] + cat_agents[:count - 1]
        return pipeline[:count]

    def _get_agent_category(self, agent_id: str) -> Optional[str]:
        if agent_id == "A00":
            return "commander"
        agent = self.agents.get(agent_id)
        if agent:
            return getattr(agent, "category", None)
        return None

    def _classify_task(self, task: str) -> str:
        task_lower = task.lower()
        topics = {
            "research": ["بحث", "دراسة", "research"],
            "analysis": ["حلل", "تحليل", "analyze"],
            "code": ["كود", "برمج", "code"],
            "strategy": ["استراتيج", "خطة", "strategy"],
        }
        for topic, kws in topics.items():
            if any(k in task_lower for k in kws):
                return topic
        return "general"

    # ═══════════════════════════════════════════════
    # حالة الشبكة
    # ═══════════════════════════════════════════════

    def status(self) -> Dict:
        """حالة الشبكة العصبية الكاملة"""
        return {
            "network": "active",
            "total_agents": len(self.agents),
            "commander": "A00",
            "category_leaders": CATEGORY_LEADERS,
            "graph_nodes": len(self.graph),
            "graph_edges": sum(len(v) for v in self.graph.values()) // 2,
            "cross_links": len(CROSS_LINKS),
            "pending_signals": sum(len(v) for v in self.signal_bus.values()),
            "signal_history_size": len(self.signal_history),
            "stats": self.stats,
        }

    def get_graph(self) -> Dict:
        """خريطة الاتصالات كاملة"""
        nodes = []
        # A00
        nodes.append({
            "id": "A00", "label": "القائد الأعلى",
            "category": "commander", "role": "supreme_commander",
        })
        # باقي الوكلاء
        for aid, agent in self.agents.items():
            is_leader = aid in CATEGORY_LEADERS.values()
            nodes.append({
                "id": aid,
                "label": getattr(agent, "name_ar", aid),
                "category": getattr(agent, "category", ""),
                "role": "category_leader" if is_leader else "agent",
            })

        edges = []
        seen = set()
        for src, targets in self.graph.items():
            for tgt in targets:
                key = tuple(sorted([src, tgt]))
                if key not in seen:
                    seen.add(key)
                    # نوع الرابط
                    if "A00" in key:
                        edge_type = "commander"
                    elif key in {tuple(sorted(cl)) for cl in CROSS_LINKS}:
                        edge_type = "cross"
                    else:
                        edge_type = "hierarchy"
                    edges.append({
                        "source": src, "target": tgt, "type": edge_type,
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def get_recent_signals(self, limit: int = 20) -> List[Dict]:
        """آخر الإشارات"""
        return self.signal_history[-limit:]


# ═══════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════

_instance: Optional[NeuralNetwork] = None


def get_neural_network(router=None) -> NeuralNetwork:
    global _instance
    if _instance is None:
        _instance = NeuralNetwork(router)
    return _instance
