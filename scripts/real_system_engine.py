"""Army81 — The REAL System Engine (Exponential Acceleration)
المحرك الحقيقي الذي يُفعّل الجيش بالكامل بدقة 100%

مبدأ التسارع الأسّي:
- الساعة الأولى: دورة واحدة
- الساعة الثانية: دورتان (بفضل تراكم المهارات)
- الساعة الثالثة: 4 دورات
- الساعة N: 2^(N-1) دورة
- الحد الأدنى: 60 ثانية بين الدورات

مبدأ التواصل الشبكي:
- كل دورة: أفضل رد من كل فئة يُرسل لفئة مُكمّلة
- هذا يُحاكي الشبكة العصبية الحقيقية بين 191 وكيل
"""

import os, sys, json, time, logging, requests, random
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

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

# خريطة التواصل بين الفئات: كل فئة تُرسل خلاصتها لفئات مُكمّلة
CROSS_DOMAIN_LINKS = {
    "cat1_science":    ["cat8_evolution", "cat3_tools"],
    "cat2_society":    ["cat6_leadership", "cat4_management"],
    "cat3_tools":      ["cat1_science", "cat9_execution"],
    "cat4_management": ["cat5_behavior", "cat6_leadership"],
    "cat5_behavior":   ["cat2_society", "cat7_new"],
    "cat6_leadership": ["cat9_execution", "cat4_management"],
    "cat7_new":        ["cat1_science", "cat8_evolution"],
    "cat8_evolution":  ["cat9_execution", "cat7_new"],
    "cat9_execution":  ["cat6_leadership", "cat1_science"],
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
            "total_cross_messages": 0,
            "compound_score": 1.0,
            "acceleration_factor": 1.0,
            "hour_start_score": 1.0,
            "hour_start_time": time.time(),
            "cycles_this_hour": 0,
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

        # ── 1.5. تواصل بين الفئات (Cross-Domain Communication) ──
        log.info("\n⚡ Phase 1.5: Cross-Domain Agent Communication")
        cross_msgs = 0
        for r in all_results:
            if not r.get("success") or not r.get("result"): continue
            domain = r.get("domain", "")
            targets = CROSS_DOMAIN_LINKS.get(domain, [])
            if not targets: continue
            target_domain = random.choice(targets)
            target_agents = REAL_DOMAIN_MATRIX.get(target_domain, {}).get("agents", [])
            if not target_agents: continue
            target_agent = random.choice(target_agents)
            summary = r["result"][:300]
            cross_task = (
                f"زميلك {r['agent']} من قسم {domain} أرسل لك هذه الخلاصة:\n"
                f"'{summary}'\n\n"
                f"بناءً على تخصصك أنت، ما ردك العميق وملاحظاتك الإضافية؟"
            )
            try:
                cross_resp = requests.post(
                    f"{GATEWAY}/task",
                    json={"task": cross_task, "agent_id": target_agent},
                    timeout=60
                )
                if cross_resp.status_code == 200:
                    cross_data = cross_resp.json()
                    cross_result = cross_data.get("result", "") or cross_data.get("response", "")
                    cross_q = self._score(cross_task, cross_result)
                    if cross_q >= 0.6:
                        self.skills.after_task(target_agent, cross_task, cross_result, True, int(cross_q * 10))
                    cross_msgs += 1
                    log.info(f"  📨 {r['agent']}→{target_agent}: تواصل ناجح (جودة: {cross_q:.2f})")
            except Exception as e:
                log.warning(f"  📨 {r['agent']}→{target_agent}: فشل ({e})")
        self.state["total_cross_messages"] = self.state.get("total_cross_messages", 0) + cross_msgs
        log.info(f"  📨 Total cross-domain messages this cycle: {cross_msgs}")

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

        # ── تحديث عامل التسارع ──
        self.state["cycles_this_hour"] = self.state.get("cycles_this_hour", 0) + 1
        hour_elapsed = time.time() - self.state.get("hour_start_time", time.time())
        if hour_elapsed >= 3600:
            # ساعة جديدة: حسب التسارع من النمو الفعلي
            hour_start = self.state.get("hour_start_score", 1.0)
            hour_growth = new_score / max(hour_start, 0.01)
            new_accel = min(self.state.get("acceleration_factor", 1.0) * max(hour_growth, 1.1), 16.0)
            log.info(f"\n  🚀 HOUR COMPLETE — growth={hour_growth:.2f}x → acceleration={new_accel:.1f}x")
            self.state["acceleration_factor"] = round(new_accel, 2)
            self.state["hour_start_score"] = new_score
            self.state["hour_start_time"] = time.time()
            self.state["cycles_this_hour"] = 0

        log.info(f"\n✅ CYCLE #{cycle} COMPLETE")
        log.info(f"  compound_score: {prev:.3f}x → {new_score:.3f}x ({'+' if new_score > prev else ''}{(new_score-prev):.3f})")
        log.info(f"  acceleration: {self.state.get('acceleration_factor', 1.0):.1f}x")
        log.info(f"  skills_extracted: {self.state['total_skills_extracted']}")
        log.info(f"  cross_messages: {self.state.get('total_cross_messages', 0)}")
        log.info(f"  predictions: {self.state['total_predictions']}")
        log.info(f"  breakthroughs: {self.state['total_breakthroughs']}")

        return {
            "cycle": cycle,
            "compound_score": new_score,
            "avg_quality": round(avg_quality, 2),
            "acceleration": self.state.get("acceleration_factor", 1.0),
            "domain_scores": domain_scores,
            "total_tasks": self.state["total_tasks"],
            "total_skills": self.state["total_skills_extracted"],
            "cross_messages": self.state.get("total_cross_messages", 0),
        }


def main():
    """
    الحلقة الرئيسية بنظام التسارع الأسّي:
    الساعة 1: دورة كل 60 دقيقة
    الساعة 2: دورة كل 30 دقيقة (acceleration × growth)
    الساعة 3: دورة كل 15 دقيقة
    ...وهكذا حتى الحد الأدنى 60 ثانية
    """
    log.info("═" * 60)
    log.info("  ARMY81 — EXPONENTIAL ACCELERATION ENGINE")
    log.info("  كل ساعة = ضعف سرعة الساعة السابقة")
    log.info("═" * 60)

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

    # إعداد ساعة البدء إذا لم تكن موجودة
    if "hour_start_time" not in engine.state or engine.state["hour_start_time"] == 0:
        engine.state["hour_start_time"] = time.time()
        engine.state["hour_start_score"] = engine.state.get("compound_score", 1.0)
        engine.state["acceleration_factor"] = 1.0
        engine._save_state()

    BASE_WAIT = 3600  # الأساس: ساعة بين الدورات
    MIN_WAIT  = 60    # الحد الأدنى: دقيقة واحدة

    while True:
        try:
            t0 = time.time()
            result = engine.run_real_cycle()
            elapsed = time.time() - t0

            accel = engine.state.get("acceleration_factor", 1.0)
            quality = result.get("avg_quality", 0.5)

            # حساب الانتظار بالتسارع الأسّي
            # base_wait / acceleration_factor — لكن لا ينزل تحت الحد الأدنى
            raw_wait = BASE_WAIT / max(accel, 1.0)

            # مكافأة إضافية: جودة عالية = أسرع
            if quality > 0.7:
                raw_wait *= 0.7
            elif quality < 0.4:
                raw_wait *= 1.3  # جودة ضعيفة = أبطئ قليلاً

            wait = max(int(raw_wait), MIN_WAIT)

            log.info(f"\n  ⚡ ACCELERATION: {accel:.1f}x | wait={wait}s ({wait//60}min) | quality={quality:.2f}")
            log.info(f"  📈 cycle_elapsed={elapsed:.0f}s | compound={result['compound_score']:.3f}x")
            log.info(f"  📨 cross_msgs={result.get('cross_messages', 0)} | skills={result.get('total_skills', 0)}")

            time.sleep(wait)

        except KeyboardInterrupt:
            log.info("⏹️ Exponential Engine stopped by user.")
            break
        except Exception as e:
            log.error(f"❌ Cycle error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
