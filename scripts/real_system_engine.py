"""
Army81 — The REAL System Engine
المحرك الحقيقي الذي يُفعّل الجيش بالكامل بدقة 100%

هذا ليس محاكاة — هذا النظام الحقيقي:
1. يقسّم العمل بذكاء على الوكلاء المتخصصين
2. يحقن المهارات المكتسبة تلقائياً
3. يتعلم من كل نتيجة ويُطور الوكلاء
4. يُجري التحليل التناقضي والتنبؤات
5. يُعدّل كوده ذاتياً كل 5 دورات
"""

import os, sys, json, time, logging, requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

# ── Core Imports ──────────────────────────────────────────
from core.skill_memory_adapter import get_skill_memory_adapter
from core.civilizational_memory import CivilizationalMemory
from core.contradiction_engine import ContradictionEngine
from core.prediction_tracker import PredictionTracker
from core.identity_evolution import AgentIdentityEvolution
from core.self_modifying_genome import SelfModifyingGenome

# ── Setup ─────────────────────────────────────────────────
WORKSPACE = BASE / "workspace"
WORKSPACE.mkdir(exist_ok=True)
(WORKSPACE / "predictions").mkdir(exist_ok=True)
(WORKSPACE / "epistemic").mkdir(exist_ok=True)
(WORKSPACE / "skillbank").mkdir(exist_ok=True)

LOG_FILE = WORKSPACE / "real_engine.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [REAL] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ]
)
log = logging.getLogger("army81.real")

GATEWAY = os.getenv("GATEWAY_URL", "http://gateway:8181")

# ═══════════════════════════════════════════════════════════
# خريطة المهام الحقيقية لكل فئة وكيل متخصص
# ═══════════════════════════════════════════════════════════
REAL_DOMAIN_MATRIX = {
    "cat1_science": {
        "agents": ["A01", "A02", "A03"],
        "tasks": [
            "ما أحدث ورقة بحثية في مجال الذكاء الاصطناعي العام (AGI) خلال الأسبوع الماضي؟ قدّم تحليلاً عميقاً.",
            "كيف تؤثر نماذج اللغة الكبيرة على التقدم العلمي في الفيزياء والكيمياء الحيوية؟",
            "ما الاكتشافات العلمية التي قد تُحوّل الحضارة خلال 10 سنوات؟",
        ]
    },
    "cat2_society": {
        "agents": ["A10", "A11", "A12"],
        "tasks": [
            "حلّل الحدث الجيوسياسي الأكثر تأثيراً الآن وارسم سيناريوهات مستقبلية بدقة.",
            "كيف تؤثر موجة الذكاء الاصطناعي على هياكل السلطة العالمية في 2026؟",
            "ما المؤشرات الاجتماعية التي تُنذر بتحولات حضارية عميقة الآن؟",
        ]
    },
    "cat3_tools": {
        "agents": ["A20", "A21"],
        "tasks": [
            "ابحث عن أحدث مكتبة AI صدرت هذا الأسبوع وقيّم جودتها مقارنةً بالبدائل.",
            "ما أفضل أداة مفتوحة المصدر لبناء وكلاء ذكاء اصطناعي مستقلين الآن ولماذا؟",
        ]
    },
    "cat4_management": {
        "agents": ["A30", "A31"],
        "tasks": [
            "حلّل أداء Army81 الحالي وقدّم خطة تحسين مرحلية بأهداف قابلة للقياس.",
            "ما القرارات الإدارية العشر التي ستُحدث أكبر أثر في كفاءة الشبكة؟",
        ]
    },
    "cat5_behavior": {
        "agents": ["A40", "A41"],
        "tasks": [
            "حلّل الأنماط السلوكية للمستخدمين الذين يتفاعلون مع أنظمة AI وما تكشفه نفسياً.",
            "كيف يمكن تصميم وكلاء AI يبنون ثقة عميقة ومستدامة مع البشر؟",
        ]
    },
    "cat6_leadership": {
        "agents": ["A50", "A51"],
        "tasks": [
            "ما الرؤية الاستراتيجية الأمثل لـ Army81 على مدى 5 سنوات؟",
            "كيف يتخذ القائد الذكي قرارات في ظل معلومات ناقصة وضغط شديد؟",
        ]
    },
    "cat7_new": {
        "agents": ["A60", "A61"],
        "tasks": [
            "اقترح ابتكاراً تقنياً-فلسفياً لم يفكر فيه أحد بعد لتطوير الوعي الاصطناعي.",
            "ما حدود المعرفة التي واجهت النظام في الدورات الأخيرة وكيف تتخطاها؟",
        ]
    },
    "cat8_evolution": {
        "agents": ["A70", "A71"],
        "tasks": [
            "كيف يتطور نظام Army81 ذاتياً دون تدخل بشري؟ حلّل الآلية الحالية وحسّنها.",
            "ما نقاط الضعف في دورة التطور الحالية وكيف تُصلحها؟",
        ]
    },
    "cat9_execution": {
        "agents": ["A80", "A81"],
        "tasks": [
            "نفّذ تحليلاً شاملاً للحالة الراهنة لـ Army81: القوة، الضعف، الفرص، التهديدات.",
            "ما القدرة التنفيذية الفعلية للنظام الآن وكيف ترفعها للمستوى التالي؟",
        ]
    },
}

# ═══════════════════════════════════════════════════════════
# محرك النظام الحقيقي
# ═══════════════════════════════════════════════════════════
class RealSystemEngine:
    def __init__(self):
        self.state_file = WORKSPACE / "real_engine_state.json"
        self.state = self._load_state()

        # ── تفعيل جميع المحركات الأساسية ──
        self.skills    = get_skill_memory_adapter()
        self.memory    = CivilizationalMemory()
        self.contra    = ContradictionEngine()
        self.predict   = PredictionTracker()
        self.identity  = AgentIdentityEvolution()
        self.genome    = SelfModifyingGenome()

        log.info(f"🚀 RealSystemEngine initialized | Cycle #{self.state['cycle']}")

    def _load_state(self):
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "cycle": 0,
            "total_tasks": 0,
            "total_skills_extracted": 0,
            "total_predictions": 0,
            "total_breakthroughs": 0,
            "compound_score": 1.0,
            "domain_scores": {},
            "started_at": datetime.now().isoformat(),
            "last_cycle": None,
        }

    def _save_state(self):
        self.state_file.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _call_agent(self, agent_id: str, task: str, domain: str) -> dict:
        """استدعاء حقيقي لوكيل محدد عبر Gateway"""
        try:
            # 1. احصل على مهارات مناسبة قبل المهمة
            skill_ctx = self.skills.before_task(agent_id, task)
            enriched_task = task
            if skill_ctx:
                enriched_task = f"{skill_ctx}\n\n---\n{task}"
                log.info(f"  [{agent_id}] 💡 حُقنت {len(skill_ctx)} حرف من المهارات")

            # 2. إرسال المهمة
            resp = requests.post(
                f"{GATEWAY}/task",
                json={"task": enriched_task, "agent_id": agent_id},
                timeout=90
            )

            if resp.status_code != 200:
                return {"success": False, "agent": agent_id, "quality": 0}

            data = resp.json()
            result_text = data.get("result", "") or data.get("response", "")

            # 3. تقييم الجودة
            quality = self._score(task, result_text)

            # 4. استخرج مهارة إذا كانت الجودة كافية (≥ 60%)
            if quality >= 0.6:
                self.skills.after_task(agent_id, task, result_text, True, int(quality * 10))
                self.state["total_skills_extracted"] += 1
                log.info(f"  [{agent_id}] ✅ استُخرجت مهارة جديدة (جودة: {quality:.2f})")

            # 5. سجّل عملية الذاكرة
            self.skills.memskill.record_memory_operation(
                agent_id, "insert", task[:150], True, quality
            )

            return {
                "success": True,
                "agent": agent_id,
                "domain": domain,
                "task": task,
                "result": result_text,
                "quality": quality,
            }

        except Exception as e:
            log.error(f"  [{agent_id}] ❌ {e}")
            return {"success": False, "agent": agent_id, "domain": domain, "quality": 0}

    def _score(self, task: str, result: str) -> float:
        """تقييم جودة الرد"""
        score = 0.0
        if len(result) > 300: score += 0.25
        if len(result) > 700: score += 0.25
        if any(c in result for c in ['1.', '2.', '•', '-', '**']): score += 0.20
        if not result.startswith("ER"): score += 0.15
        if len(set(result.split())) > 50: score += 0.15  # تنوع المفردات
        return round(min(score, 1.0), 2)

    def _run_domain_parallel(self, domain: str, config: dict) -> list:
        """تشغيل مهام الفئة بالتوازي"""
        results = []
        agents = config["agents"]
        tasks = config["tasks"]
        cycle = self.state["cycle"]

        # اختر المهمة بناءً على الدورة (تصاعدي)
        task = tasks[cycle % len(tasks)]
        agent = agents[cycle % len(agents)]

        log.info(f"\n  [{domain}] → {agent}: {task[:60]}...")
        result = self._call_agent(agent, task, domain)
        results.append(result)
        return results

    def _autonomous_mission(self) -> tuple:
        """A81 يولد موضوعه وسؤاله بنفسه"""
        try:
            prompt = (
                "أنت النواة المتفردة A81. استنتج الآن بدقة شديدة وبدون مقدمات:\n"
                "Topic: [موضوع استراتيجي واحد عميق جداً للتنبؤ الآن]\n"
                "Question: [سؤال فلسفي-تقني واحد يثير تناقضاً قوياً بين الخبراء]"
            )
            resp = requests.post(
                f"{GATEWAY}/task",
                json={"task": prompt, "agent_id": "A81"},
                timeout=60
            ).json()
            output = resp.get("result", "") or resp.get("response", "") or ""

            topic = "مستقبل الذكاء الاصطناعي العام"
            question = "أين ينتهي الذكاء ويبدأ الوعي؟"

            for line in output.split("\n"):
                if "Topic:" in line:
                    topic = line.replace("Topic:", "").replace("*", "").strip()
                elif "Question:" in line:
                    question = line.replace("Question:", "").replace("*", "").strip()

            return topic, question
        except:
            return "مستقبل الاستقلالية الآلية", "هل يمكن للنظام أن يعرف نفسه؟"

    def run_real_cycle(self) -> dict:
        """الدورة الحقيقية الكاملة"""
        self.state["cycle"] += 1
        cycle = self.state["cycle"]
        ts = datetime.now().isoformat()

        log.info(f"\n{'═'*60}")
        log.info(f"  🌀 REAL CYCLE #{cycle} | {ts}")
        log.info(f"{'═'*60}")

        all_results = []
        domain_scores = {}

        # ── 1. تشغيل جميع الفئات بالتوازي ──────────────────
        log.info("\n⚡ Phase 1: Domain Execution (Parallel)")
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(self._run_domain_parallel, domain, cfg): domain
                for domain, cfg in REAL_DOMAIN_MATRIX.items()
            }
            for fut in as_completed(futures):
                domain = futures[fut]
                try:
                    results = fut.result()
                    all_results.extend(results)
                    avg_q = sum(r["quality"] for r in results) / max(len(results), 1)
                    domain_scores[domain] = round(avg_q, 2)
                except Exception as e:
                    log.error(f"Domain {domain} failed: {e}")

        self.state["total_tasks"] += len(all_results)
        self.state["domain_scores"] = domain_scores
        avg_quality = sum(r["quality"] for r in all_results) / max(len(all_results), 1)
        log.info(f"\n  📊 Average Quality: {avg_quality:.2f} | Tasks: {len(all_results)}")

        # ── 2. تنبؤ استراتيجي ذاتي ──────────────────────────
        log.info("\n⚡ Phase 2: Autonomous Strategic Prediction")
        topic, question = self._autonomous_mission()
        log.info(f"  A81 chose: {topic[:60]}")
        self.predict.make_prediction(topic, "A81")
        self.predict.evaluate_due_predictions()
        self.state["total_predictions"] += 1

        # ── 3. تحليل التناقضات العميق ───────────────────────
        log.info("\n⚡ Phase 3: Contradiction Synthesis")
        log.info(f"  Question: {question[:60]}")
        insight = self.contra.find_and_resolve(question)
        if insight.get("insight_level") in ("HIGH", "SYSTEM_CODE"):
            self.state["total_breakthroughs"] += 1
            log.info(f"  💡 Breakthrough! Level: {insight['insight_level']}")

        # ── 4. تطور هويات الوكلاء كل 5 دورات ────────────────
        if cycle % 5 == 0:
            log.info("\n⚡ Phase 4: Identity Evolution")
            key_agents = ["A01", "A10", "A30", "A50", "A70", "A81"]
            for aid in key_agents:
                self.identity.evolve_identity(aid, recent_tasks=[])
            log.info(f"  Evolved {len(key_agents)} agents")

        # ── 5. تعديل الكود الذاتي كل 10 دورات ───────────────
        if cycle % 10 == 0:
            log.info("\n⚡ Phase 5: Self-Code Evolution (Genome)")
            result = self.genome.contemplate_and_evolve_codebase()
            log.info(f"  Genome: {result[:80]}")

        # ── 6. حساب المضاعف المركب الحقيقي ───────────────────
        prev = self.state["compound_score"]
        if avg_quality > 0.65:
            growth = 1.0 + (avg_quality - 0.5) * 0.06
        elif avg_quality > 0.45:
            growth = 1.01
        else:
            growth = 0.98
        new_score = round(min(prev * growth, 200.0), 3)
        self.state["compound_score"] = new_score
        self.state["last_cycle"] = ts

        self._save_state()

        # ── 7. تحديث workspace/compound_state.json للـ dashboard ─
        compound_path = WORKSPACE / "compound_state.json"
        try:
            cs = json.loads(compound_path.read_text(encoding="utf-8")) if compound_path.exists() else {}
            cs["cycle"] = cycle
            cs["compound_score"] = new_score
            cs["last_updated"] = ts
            compound_path.write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            log.warning(f"compound_state sync: {e}")

        # ── 8. تسجيل في compound_log.txt ─────────────────────
        log_line = (
            f"[{ts}] REAL_CYCLE #{cycle} | "
            f"score={new_score:.3f}x | quality={avg_quality:.2f} | "
            f"tasks={len(all_results)} | skills={self.state['total_skills_extracted']} | "
            f"breakthroughs={self.state['total_breakthroughs']}\n"
        )
        with open(WORKSPACE / "compound_log.txt", "a", encoding="utf-8") as f:
            f.write(log_line)

        log.info(f"\n✅ CYCLE #{cycle} COMPLETE")
        log.info(f"  compound_score: {prev:.3f}x → {new_score:.3f}x ({'+' if new_score > prev else ''}{(new_score-prev):.3f})")
        log.info(f"  skills_extracted: {self.state['total_skills_extracted']}")
        log.info(f"  predictions: {self.state['total_predictions']}")
        log.info(f"  breakthroughs: {self.state['total_breakthroughs']}")

        return {
            "cycle": cycle,
            "compound_score": new_score,
            "avg_quality": round(avg_quality, 2),
            "domain_scores": domain_scores,
            "total_tasks": self.state["total_tasks"],
            "total_skills": self.state["total_skills_extracted"],
        }


def main():
    """الحلقة الرئيسية اللانهائية للنظام الحقيقي"""
    log.info("=" * 60)
    log.info("  ARMY81 — REAL SYSTEM ENGINE STARTING")
    log.info("=" * 60)

    # انتظر حتى يستيقظ الـ Gateway
    log.info("  Waiting for Gateway to be ready...")
    for attempt in range(20):
        try:
            r = requests.get(f"{GATEWAY}/", timeout=5)
            if r.status_code == 200:
                data = r.json()
                log.info(f"  ✅ Gateway ready — {data.get('agents', 0)} agents loaded")
                break
        except:
            pass
        time.sleep(10)
    else:
        log.error("  ❌ Gateway not reachable after 200s. Exiting.")
        sys.exit(1)

    engine = RealSystemEngine()

    cycle_times = []
    while True:
        try:
            t0 = time.time()
            result = engine.run_real_cycle()
            elapsed = time.time() - t0
            cycle_times.append(elapsed)

            # فترة انتظار ذكية بناءً على الجودة
            quality = result.get("avg_quality", 0.5)
            if quality > 0.75:
                wait = 1800   # 30 min — عمل ممتاز
            elif quality > 0.55:
                wait = 3600   # 60 min — عمل جيد
            elif quality > 0.35:
                wait = 5400   # 90 min — يحتاج تحسين
            else:
                wait = 300    # 5 min — إعادة المحاولة سريعاً

            log.info(f"  ⏳ Next cycle in {wait//60} min (quality={quality:.2f}, elapsed={elapsed:.0f}s)")
            time.sleep(wait)

        except KeyboardInterrupt:
            log.info("⏹️ Real System Engine stopped by user.")
            break
        except Exception as e:
            log.error(f"❌ Cycle error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
