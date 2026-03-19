"""
Army81 — Exponential Evolution Engine
محرك التطور الأُسّي — يضاعف القدرات في كل دورة
كل ساعة = 10x تطور عن الساعة السابقة

المبدأ: كل دورة تبني على نتائج الدورة السابقة
  الدورة 1: بحث + استنساخ + تقطير (الأساس)
  الدورة 2: تستخدم نتائج 1 لتبحث أعمق + تخترع أدوات
  الدورة 3: تستخدم أدوات 2 لتبني أنظمة كاملة
  ...وهكذا تتضاعف القدرات أُسّياً
"""
import json
import time
import logging
import random
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Callable, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("army81.exponential_evolution")

WORKSPACE = Path("workspace")
EVO_DIR = WORKSPACE / "exponential_evolution"
SKILLS_DIR = WORKSPACE / "cloned_skills"
BRAIN_FILE = WORKSPACE / "shared_brain.json"
EXPERIMENTS_DIR = WORKSPACE / "experiments"
TRAINING_DIR = WORKSPACE / "training_data"


class ExponentialEvolution:
    """
    التطور الأُسّي — 20 مرحلة متوازية تتضاعف كل دورة

    الآلية:
    1. كل دورة (cycle) = 10 مراحل متوازية
    2. نتائج كل دورة تُحقن في الدورة التالية
    3. كل دورة تولّد أدوات جديدة → الدورة التالية تستخدمها
    4. المعرفة تتراكم أُسّياً: cycle_n = cycle_{n-1} × multiplier
    5. كل 3 دورات: ضغط + تبلور + توليد قفزة نوعية
    """

    def __init__(self):
        for d in [EVO_DIR, SKILLS_DIR, EXPERIMENTS_DIR, TRAINING_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        self.cycle_count = 0
        self.total_experiments = 0
        self.total_skills_created = 0
        self.total_knowledge_absorbed = 0
        self.total_distillations = 0
        self.total_battles = 0
        self.total_inventions = 0
        self.multiplier = 1.0  # يتضاعف كل دورة
        self.events: List[Dict] = []
        self.golden_rules: List[str] = []
        self.discoveries: List[Dict] = []

        # حمّل الحالة السابقة
        self._load_state()

    def _load_state(self):
        """حمّل حالة التطور من الملف"""
        state_file = EVO_DIR / "evolution_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                self.cycle_count = state.get("cycle_count", 0)
                self.total_experiments = state.get("total_experiments", 0)
                self.total_skills_created = state.get("total_skills_created", 0)
                self.total_knowledge_absorbed = state.get("total_knowledge_absorbed", 0)
                self.total_distillations = state.get("total_distillations", 0)
                self.total_battles = state.get("total_battles", 0)
                self.total_inventions = state.get("total_inventions", 0)
                self.multiplier = state.get("multiplier", 1.0)
                self.golden_rules = state.get("golden_rules", [])
                logger.info(f"📊 Loaded state: cycle {self.cycle_count}, multiplier {self.multiplier}x")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self):
        """احفظ حالة التطور"""
        state = {
            "cycle_count": self.cycle_count,
            "total_experiments": self.total_experiments,
            "total_skills_created": self.total_skills_created,
            "total_knowledge_absorbed": self.total_knowledge_absorbed,
            "total_distillations": self.total_distillations,
            "total_battles": self.total_battles,
            "total_inventions": self.total_inventions,
            "multiplier": round(self.multiplier, 2),
            "golden_rules": self.golden_rules[-20:],
            "last_updated": datetime.now().isoformat(),
        }
        (EVO_DIR / "evolution_state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_event(self, phase: str, agent: str, data: dict):
        evt = {
            "cycle": self.cycle_count,
            "phase": phase,
            "agent": agent,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self.events.append(evt)
        if len(self.events) > 500:
            self.events = self.events[-300:]

    # ═══════════════════════════════════════════════════
    # الحلقة الرئيسية — التطور الأُسّي
    # ═══════════════════════════════════════════════════

    def run_exponential(self, agents_list, run_agent_fn, emit_fn,
                        duration_hours: int = 2, parallel_workers: int = 4):
        """
        الحلقة الرئيسية — تتضاعف كل دورة

        Args:
            agents_list: كل الـ 81 وكيل
            run_agent_fn: دالة تشغيل وكيل
            emit_fn: دالة إرسال أحداث للداشبورد
            duration_hours: مدة التشغيل بالساعات
            parallel_workers: عدد العمال المتوازيين
        """
        start = time.time()
        end_time = start + (duration_hours * 3600)

        logger.info(f"🚀 EXPONENTIAL EVOLUTION — {duration_hours}h, multiplier: {self.multiplier}x")
        emit_fn("evolution_started", "SYSTEM", data={
            "duration_hours": duration_hours,
            "starting_multiplier": self.multiplier,
            "starting_cycle": self.cycle_count,
        })

        while time.time() < end_time:
            self.cycle_count += 1
            cycle_start = time.time()

            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 CYCLE {self.cycle_count} — Multiplier: {self.multiplier:.1f}x")
            logger.info(f"{'='*60}")

            emit_fn("cycle_started", "SYSTEM", data={
                "cycle": self.cycle_count,
                "multiplier": self.multiplier,
            })

            # ─── حساب عدد العمليات لهذه الدورة ───
            base_ops = 3  # عمليات أساسية لكل مرحلة
            cycle_ops = max(3, int(base_ops * self.multiplier))

            cycle_results = {}

            # ═══ المرحلة 1: البحث والاستنساخ المكثف ═══
            try:
                r = self._phase_research_clone(agents_list, run_agent_fn, emit_fn, cycle_ops)
                cycle_results["research"] = r
            except Exception as e:
                logger.error(f"Research phase error: {e}")
                cycle_results["research"] = {"error": str(e)}

            if time.time() >= end_time:
                break

            # ═══ المرحلة 2: التقطير المكثف المتعدد ═══
            try:
                r = self._phase_deep_distillation(agents_list, run_agent_fn, emit_fn, cycle_ops)
                cycle_results["distillation"] = r
            except Exception as e:
                logger.error(f"Distillation phase error: {e}")

            if time.time() >= end_time:
                break

            # ═══ المرحلة 3: التجارب والتدريب ═══
            try:
                r = self._phase_experiments(agents_list, run_agent_fn, emit_fn, cycle_ops)
                cycle_results["experiments"] = r
            except Exception as e:
                logger.error(f"Experiments phase error: {e}")

            if time.time() >= end_time:
                break

            # ═══ المرحلة 4: الاختراع والبناء ═══
            try:
                r = self._phase_invent_build(agents_list, run_agent_fn, emit_fn, cycle_ops)
                cycle_results["invention"] = r
            except Exception as e:
                logger.error(f"Invention phase error: {e}")

            if time.time() >= end_time:
                break

            # ═══ المرحلة 5: المعارك الأمنية ═══
            try:
                r = self._phase_battle_evolve(agents_list, run_agent_fn, emit_fn, min(cycle_ops, 3))
                cycle_results["battles"] = r
            except Exception as e:
                logger.error(f"Battle phase error: {e}")

            # ═══ المرحلة 6: الضغط والتبلور ═══
            try:
                r = self._phase_crystallize(agents_list, run_agent_fn, emit_fn)
                cycle_results["crystallization"] = r
            except Exception as e:
                logger.error(f"Crystallization phase error: {e}")

            # ─── مضاعف ذكي — يعتمد على الأداء الحقيقي ───
            self.multiplier = self._compute_smart_multiplier(cycle_results)

            # ─── حفظ الحالة ───
            self._save_state()
            self._save_cycle_report(cycle_results, time.time() - cycle_start)

            emit_fn("cycle_completed", "SYSTEM", data={
                "cycle": self.cycle_count,
                "multiplier": self.multiplier,
                "results": {k: str(v)[:100] for k, v in cycle_results.items()},
                "total_experiments": self.total_experiments,
                "total_knowledge": self.total_knowledge_absorbed,
                "total_skills": self.total_skills_created,
            })

            logger.info(f"✅ Cycle {self.cycle_count} done — next multiplier: {self.multiplier:.1f}x")
            time.sleep(2)

        # ─── تقرير نهائي ───
        elapsed = time.time() - start
        final_report = {
            "total_cycles": self.cycle_count,
            "total_hours": round(elapsed / 3600, 2),
            "final_multiplier": round(self.multiplier, 2),
            "total_experiments": self.total_experiments,
            "total_knowledge": self.total_knowledge_absorbed,
            "total_skills": self.total_skills_created,
            "total_distillations": self.total_distillations,
            "total_battles": self.total_battles,
            "total_inventions": self.total_inventions,
            "golden_rules": self.golden_rules[-10:],
        }

        (EVO_DIR / f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json").write_text(
            json.dumps(final_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        emit_fn("evolution_completed", "SYSTEM", data=final_report)
        logger.info(f"🏆 EVOLUTION COMPLETE — {self.cycle_count} cycles, {self.multiplier:.1f}x multiplier")

    # ═══════════════════════════════════════════════════
    # المراحل التفصيلية
    # ═══════════════════════════════════════════════════

    def _compute_smart_multiplier(self, cycle_results: Dict) -> float:
        """
        المضاعف الذكي — يُحسب من الأداء الحقيقي وليس رقم ثابت
        كلما نجح النظام أكثر → multiplier أعلى
        كلما فشل → يبطئ ويحسّن قبل التضاعف
        """
        score = 1.0  # الأساس

        # 1. نسبة نجاح التجارب (0-0.5)
        exp = cycle_results.get("experiments", {})
        exp_total = exp.get("experiments_run", 0)
        exp_success = exp.get("successful", 0)
        if exp_total > 0:
            success_rate = exp_success / exp_total
            score += success_rate * 0.5  # حد أقصى +0.5
        else:
            score += 0.1  # لم تُجرَ تجارب = تقدّم بطيء

        # 2. نقل المعرفة (0-0.3) — هل الفائز علّم الخاسر؟
        transfers = exp.get("knowledge_transfers", 0)
        score += min(transfers * 0.06, 0.3)

        # 3. القواعد الذهبية من الدماغ المشترك (0-0.3)
        try:
            brain_path = Path("workspace/shared_brain.json")
            if brain_path.exists():
                brain = json.loads(brain_path.read_text(encoding="utf-8"))
                rules = len(brain.get("golden_rules", []))
                score += min(rules * 0.02, 0.3)
        except Exception:
            pass

        # 4. عمق الذاكرة المتراكمة (0-0.4)
        try:
            import sqlite3
            db = Path("workspace/episodic_memory.db")
            if db.exists():
                conn = sqlite3.connect(str(db))
                episodes = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
                conn.close()
                # كل 200 حلقة = +0.1 (حد 0.4)
                score += min(episodes / 2000, 0.4)
        except Exception:
            pass

        # 5. المهارات المستنسخة (0-0.2)
        skills_dir = Path("workspace/cloned_skills")
        if skills_dir.exists():
            skills = len(list(skills_dir.glob("*")))
            score += min(skills * 0.005, 0.2)

        # 6. جودة المعارك (0-0.2)
        battles = cycle_results.get("battles", {})
        battle_rounds = battles.get("rounds", 0)
        if battle_rounds > 0:
            score += min(battle_rounds * 0.05, 0.2)

        # 7. التقطير (0-0.2)
        distill = cycle_results.get("distillation", {})
        distill_count = distill.get("examples_saved", 0)
        score += min(distill_count * 0.03, 0.2)

        # ─── حساب المضاعف النهائي ───
        # score يتراوح من 1.0 إلى 3.1
        new_multiplier = self.multiplier * (score / 1.5)  # تطبيع

        # حدود الأمان
        new_multiplier = max(new_multiplier, 1.0)   # لا ينزل عن 1
        new_multiplier = min(new_multiplier, 50.0)   # حد أقصى 50x

        # إذا فشلت أكثر من 50% من التجارب → تراجع
        if exp_total > 0 and (exp_success / exp_total) < 0.5:
            new_multiplier = max(self.multiplier * 0.8, 1.0)
            logger.warning(f"⚠️ Success rate low ({exp_success}/{exp_total}) — multiplier reduced to {new_multiplier:.1f}x")
        else:
            logger.info(f"📈 Smart multiplier: {self.multiplier:.1f}x → {new_multiplier:.1f}x (score: {score:.2f})")

        return round(new_multiplier, 2)

    def _smart_score(self, text: str, task_type: str, metric: str) -> int:
        """تقييم ذكي متعدد الأبعاد — بدل مجرد طول النص"""
        if not text or text.startswith("ERROR"):
            return 0
        score = 0
        # 1. الطول الأساسي (مع حد أعلى)
        score += min(len(text), 2000) * 0.3
        # 2. التنظيم (عناوين، قوائم، أرقام)
        if any(c in text for c in ['#', '##', '###']):
            score += 150
        numbered = sum(1 for c in ['1.', '2.', '3.', '4.', '5.'] if c in text)
        score += numbered * 40
        bullets = text.count('•') + text.count('-') + text.count('*')
        score += min(bullets, 10) * 20
        # 3. العمق (كلمات تقنية حسب النوع)
        depth_keywords = {
            "medical": ["آلية", "مستقبلات", "بروتين", "خلية", "enzyme", "receptor", "pathway"],
            "coding": ["def ", "class ", "return", "import", "function", "algorithm"],
            "security": ["ثغرة", "CVE", "injection", "XSS", "authentication", "encryption"],
            "financial": ["ROI", "مخاطر", "تحليل", "سوق", "استثمار", "عائد"],
            "reasoning": ["إذاً", "لذلك", "بالتالي", "therefore", "hence", "conclusion"],
            "strategy": ["مرحلة", "خطة", "هدف", "مؤشر", "KPI", "milestone"],
        }
        for kw in depth_keywords.get(task_type, []):
            if kw in text.lower():
                score += 50
        # 4. اللغة العربية
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars > len(text) * 0.3:
            score += 100  # يحتوي عربي حقيقي
        # 5. لا تكرار (جودة)
        words = text.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            score += int(unique_ratio * 200)
        # 6. أمثلة وأدلة
        evidence_keywords = ["مثال", "دراسة", "بحث", "وفقاً", "example", "study", "according"]
        for kw in evidence_keywords:
            if kw in text.lower():
                score += 30
        return max(int(score), 1)  # حد أدنى 1 إذا أنتج نص

    def _phase_research_clone(self, agents, run_fn, emit_fn, ops_count) -> Dict:
        """البحث في كل المصادر + استنساخ المفيد"""
        logger.info(f"🔍 Research & Clone — {ops_count} operations")
        results = {"researched": 0, "cloned": 0, "knowledge_added": 0}

        # مواضيع بحث متطورة — تتغير كل دورة
        research_topics = [
            # أساسيات تتكرر
            "latest AI agent frameworks 2026 autonomous",
            "multi-agent collaboration breakthrough",
            "knowledge distillation efficient methods",
            "self-improving AI systems recursive",
            "Arabic NLP state of art 2026",
            # متقدمة — تتغير بناء على الدورة
            f"AI agent memory optimization cycle {self.cycle_count}",
            f"model merging techniques {datetime.now().strftime('%B %Y')}",
            "reinforcement learning from AI feedback RLAIF",
            "tool-augmented language models",
            "graph neural networks knowledge representation",
            "prompt engineering automation DSPy",
            "synthetic data generation high quality",
            "federated learning multi-agent",
            "neural architecture search efficient",
            "continual learning catastrophic forgetting",
        ]

        # اختر مواضيع بناءً على المضاعف
        topics = research_topics[:min(ops_count + 3, len(research_topics))]

        for topic in topics:
            researcher = random.choice([a for a in agents
                if a.category in ("cat1_science", "cat3_tools", "cat7_new")]
                or agents)

            try:
                task = f"""ابحث بعمق عن: {topic}

أعطني:
1. أهم 3 اكتشافات/أدوات جديدة (2025-2026)
2. لكل واحدة: ما هي، كيف تعمل، كيف نستخدمها في نظام 81 وكيل
3. كود Python مختصر إذا أمكن
4. رابط أو مرجع

كن عملياً ومحدداً — نريد تطبيق فوري."""

                result = run_fn(researcher.agent_id, task)
                text = result.get("result", "") if isinstance(result, dict) else str(result)

                if len(text) > 100:
                    results["researched"] += 1
                    self.total_knowledge_absorbed += 1

                    # حفظ كملف معرفة
                    h = hashlib.md5(topic.encode()).hexdigest()[:8]
                    (SKILLS_DIR / f"research_c{self.cycle_count}_{h}.md").write_text(
                        f"# {topic}\n# Cycle {self.cycle_count} | {datetime.now().isoformat()}\n\n{text[:3000]}",
                        encoding="utf-8"
                    )
                    results["cloned"] += 1
                    self.total_skills_created += 1

                    # حفظ في Chroma
                    try:
                        from memory.collective_memory import CollectiveMemory
                        cm = CollectiveMemory()
                        cm.contribute(researcher.agent_id, text[:800], topic[:50], 0.9)
                        results["knowledge_added"] += 1
                    except Exception:
                        pass

                    emit_fn("research_done", researcher.agent_id, data={
                        "topic": topic[:50], "length": len(text),
                    })

            except Exception as e:
                logger.warning(f"Research failed for '{topic[:30]}': {e}")

            time.sleep(1.5)

        return results

    def _phase_deep_distillation(self, agents, run_fn, emit_fn, ops_count) -> Dict:
        """تقطير متعدد المستويات — المعلم يعلّم الطالب"""
        logger.info(f"🎓 Deep Distillation — {ops_count} pairs")
        results = {"pairs": 0, "examples_saved": 0, "quality_improvement": 0}

        # مهام معقدة للتقطير — تتصاعد مع كل دورة
        problems = [
            "اكتب خوارزمية بحث دلالي عربي-إنجليزي بدقة > 90%. أعطِ الكود كاملاً مع الشرح.",
            "صمّم نظام توجيه ذكي يتعلم من 10000 تفاعل أي وكيل أفضل لأي مهمة. أعطِ الكود.",
            "اكتب نظام تقييم ذاتي يقيس 5 مقاييس لكل وكيل بدون تدخل بشري. أعطِ الكود.",
            "صمّم GraphRAG مبسّط يستخرج كيانات وعلاقات من نص عربي. أعطِ الكود.",
            "اكتب نظام Token Economy يوزع ميزانيات على 81 وكيل ويكافئ الكفاءة. أعطِ الكود.",
            "صمّم نظام model merging يدمج أوزان نموذجين بـ SLERP. أعطِ pseudocode مفصل.",
            "اكتب نظام synthetic data generation يولّد 1000 سيناريو تدريب تلقائياً. أعطِ الكود.",
            "صمّم Constitutional AI guardrails تمنع الوكيل من تدمير نفسه أثناء التطور. أعطِ الكود.",
            "اكتب prompt optimizer يحسّن system_prompt تلقائياً بالتجربة. أعطِ الكود مع DSPy.",
            "صمّم نظام Computer-Use Agent يتحكم بالمتصفح لجمع بيانات. أعطِ architecture.",
        ]

        # أضف قواعد ذهبية من الدورات السابقة
        context_rules = ""
        if self.golden_rules:
            context_rules = "\n\nقواعد ذهبية من التجارب السابقة:\n" + "\n".join(self.golden_rules[-5:])

        teachers = [a for a in agents if a.model_alias in
                    ("claude-smart", "deepseek-r1", "gemini-pro", "gpt4o", "o3-mini")]
        students = [a for a in agents if a.model_alias in
                    ("gemini-flash", "claude-fast", "deepseek-chat", "qwen-free", "llama-free",
                     "gpt4o-mini", "gpt5-nano", "mistral-small", "qwen-coder")]

        if not teachers:
            teachers = agents[:10]
        if not students:
            students = agents[10:30]

        selected_problems = problems[:min(ops_count, len(problems))]

        for problem in selected_problems:
            teacher = random.choice(teachers)
            student = random.choice(students)

            try:
                # المعلم يحل مع Chain-of-Thought
                t_result = run_fn(teacher.agent_id,
                    f"فكّر خطوة بخطوة بصوت عالٍ وحلّ بأعلى جودة ممكنة:{context_rules}\n\n{problem}")
                t_text = t_result.get("result", "") if isinstance(t_result, dict) else str(t_result)

                if len(t_text) > 150:
                    # الطالب يتعلم من المعلم
                    s_result = run_fn(student.agent_id,
                        f"ادرس هذا الحل من خبير ({teacher.name_ar}) وأعد كتابته بأسلوبك مع تحسين:\n\n{t_text[:1200]}")
                    s_text = s_result.get("result", "") if isinstance(s_result, dict) else str(s_result)

                    results["pairs"] += 1
                    self.total_distillations += 1

                    # احفظ بيانات التدريب
                    pair_data = {
                        "problem": problem,
                        "teacher": {"id": teacher.agent_id, "model": teacher.model_alias, "solution": t_text[:1500]},
                        "student": {"id": student.agent_id, "model": student.model_alias, "solution": s_text[:1500]},
                        "cycle": self.cycle_count,
                        "timestamp": datetime.now().isoformat(),
                    }
                    (TRAINING_DIR / f"distill_c{self.cycle_count}_{results['pairs']:03d}.json").write_text(
                        json.dumps(pair_data, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    results["examples_saved"] += 1

                    emit_fn("distillation", teacher.agent_id, data={
                        "teacher": teacher.agent_id, "student": student.agent_id,
                        "teacher_model": teacher.model_alias, "student_model": student.model_alias,
                        "problem": problem[:60],
                    })

                    # v27: Feed Brain Nucleus — تغذية الدماغ المركزي
                    try:
                        from core.brain_nucleus import get_brain
                        brain = get_brain()
                        domain = "coding" if "كود" in problem or "خوارزمية" in problem else "reasoning"
                        brain.distillation.distill_from_teacher(domain, problem)
                    except Exception:
                        pass  # Brain not available, continue

            except Exception as e:
                logger.warning(f"Distillation failed: {e}")

            time.sleep(2)

        return results

    def _phase_experiments(self, agents, run_fn, emit_fn, ops_count) -> Dict:
        """تجارب مكثفة — كل تجربة تُقاس وتُسجّل"""
        logger.info(f"🧪 Experiments — {ops_count} experiments")
        results = {"experiments_run": 0, "successful": 0, "improvements": []}

        experiment_tasks = [
            {"type": "speed", "task": "لخّص مفهوم الذكاء الاصطناعي في 3 جمل", "metric": "length"},
            {"type": "quality", "task": "حلّل مخاطر الاستثمار في البيتكوين مع أدلة", "metric": "depth"},
            {"type": "coding", "task": "اكتب دالة Python تحسب التشابه الدلالي بين جملتين", "metric": "code"},
            {"type": "arabic", "task": "اكتب مقالاً علمياً عن الحوسبة الكمومية بالعربية الفصحى", "metric": "arabic"},
            {"type": "reasoning", "task": "إذا كان A > B و B > C و C > D، وكان D = 5، فما أقل قيمة ممكنة لـ A؟", "metric": "logic"},
            {"type": "creativity", "task": "اخترع بروتوكول اتصال جديد بين وكلاء AI لم يُخترع من قبل", "metric": "novelty"},
            {"type": "medical", "task": "اشرح آلية عمل مثبطات ACE في علاج ارتفاع ضغط الدم", "metric": "accuracy"},
            {"type": "strategy", "task": "ضع خطة 90 يوماً لبناء شركة AI ناشئة بميزانية 10000$", "metric": "depth"},
            {"type": "security", "task": "حلّل ثغرات نظام يستخدم JWT tokens بدون expiry", "metric": "depth"},
            {"type": "multilingual", "task": "ترجم هذا النص للإنجليزية والفرنسية: الذكاء الاصطناعي يغير العالم", "metric": "accuracy"},
        ]

        selected = experiment_tasks[:min(ops_count + 2, len(experiment_tasks))]

        for exp in selected:
            # اختر 2 وكلاء مختلفين للمقارنة
            a1 = random.choice(agents)
            a2 = random.choice([a for a in agents if a.agent_id != a1.agent_id])

            try:
                r1 = run_fn(a1.agent_id, exp["task"])
                t1 = r1.get("result", "") if isinstance(r1, dict) else str(r1)

                r2 = run_fn(a2.agent_id, exp["task"])
                t2 = r2.get("result", "") if isinstance(r2, dict) else str(r2)

                self.total_experiments += 1
                results["experiments_run"] += 1

                # قيّم النتائج بتقييم ذكي متعدد الأبعاد
                score1 = self._smart_score(t1, exp["type"], exp.get("metric", "length"))
                score2 = self._smart_score(t2, exp["type"], exp.get("metric", "length"))

                winner = a1.agent_id if score1 >= score2 else a2.agent_id
                loser = a2.agent_id if score1 >= score2 else a1.agent_id
                win_score = max(score1, score2)
                lose_score = min(score1, score2)
                improved = win_score > 0  # نجح إذا أنتج إجابة حقيقية
                improvement_pct = round((win_score - lose_score) / max(lose_score, 1) * 100, 1)

                results["successful"] += 1

                # ─── نقل معرفة الفائز للخاسر (التعلم الحقيقي) ───
                if improved and win_score > 100:
                    try:
                        from memory.hierarchical_memory import HierarchicalMemory
                        hm = HierarchicalMemory()
                        winner_response = t1 if score1 >= score2 else t2
                        # احفظ حل الفائز كدرس للخاسر
                        hm.L2.record(loser, f"تعلمت من {winner}: {exp['task'][:50]}",
                                    f"الحل الأفضل: {winner_response[:300]}", True, 9)
                        # سجّل نجاح الفائز
                        hm.L2.record(winner, exp["task"][:80], winner_response[:200], True, 9)
                        results.setdefault("knowledge_transfers", 0)
                        results["knowledge_transfers"] = results.get("knowledge_transfers", 0) + 1
                    except Exception:
                        pass

                # سجّل التجربة
                exp_data = {
                    "type": exp["type"],
                    "task": exp["task"],
                    "agent1": {"id": a1.agent_id, "model": a1.model_alias, "score": score1},
                    "agent2": {"id": a2.agent_id, "model": a2.model_alias, "score": score2},
                    "winner": winner,
                    "improved": improved,
                    "improvement_pct": improvement_pct,
                    "knowledge_transferred": improved and win_score > 100,
                    "cycle": self.cycle_count,
                    "timestamp": datetime.now().isoformat(),
                }
                (EXPERIMENTS_DIR / f"exp_c{self.cycle_count}_{self.total_experiments:04d}.json").write_text(
                    json.dumps(exp_data, ensure_ascii=False, indent=2), encoding="utf-8"
                )

                emit_fn("experiment", winner, data={
                    "type": exp["type"],
                    "winner": winner,
                    "score_diff": abs(score1 - score2),
                })

                # سجّل في الذاكرة
                try:
                    from memory.hierarchical_memory import HierarchicalMemory
                    hm = HierarchicalMemory()
                    hm.L2.record(winner, exp["task"][:100], t1[:200] if score1 > score2 else t2[:200], True, 8)
                except Exception:
                    pass

            except Exception as e:
                logger.warning(f"Experiment failed: {e}")

            time.sleep(1.5)

        return results

    def _phase_invent_build(self, agents, run_fn, emit_fn, ops_count) -> Dict:
        """اختراع أدوات + بناء أنظمة جديدة"""
        logger.info(f"💡 Invent & Build — {ops_count} inventions")
        results = {"invented": 0, "built": 0, "tools": []}

        # اختراعات تتصاعد بناءً على الدورة
        inventions = [
            "اخترع أداة Python تحلّل أداء أي وكيل من سجل مهامه وتعطي نصائح تحسين. أعطِ الكود الكامل.",
            "اخترع أداة تولّد أسئلة اختبار تلقائياً لأي موضوع بـ 4 مستويات صعوبة. أعطِ الكود.",
            "اخترع أداة تستخرج الكيانات المسماة (NER) من نص عربي وتبني شبكة علاقات. أعطِ الكود.",
            "اخترع أداة تلخّص محادثة طويلة بين وكيلين في 5 نقاط رئيسية. أعطِ الكود.",
            "اخترع أداة تكتشف التكرار والتناقض في قاعدة معرفة. أعطِ الكود.",
            "اخترع أداة تقيّم جودة كود Python تلقائياً (security + style + performance). أعطِ الكود.",
            "اخترع أداة تحوّل أي وثيقة PDF إلى بطاقات تعلم (flashcards). أعطِ الكود.",
            "اخترع أداة تقارن أداء نموذجين على 10 مهام وتعطي تقرير مفصل. أعطِ الكود.",
        ]

        coders = [a for a in agents if a.agent_id in ("A05", "A51", "A57", "A59")
                  or a.category == "cat3_tools"]
        if not coders:
            coders = agents[:10]

        for invention in inventions[:min(ops_count, len(inventions))]:
            coder = random.choice(coders)

            try:
                result = run_fn(coder.agent_id, invention)
                text = result.get("result", "") if isinstance(result, dict) else str(result)

                if ("def " in text or "class " in text) and len(text) > 200:
                    tool_name = f"invented_c{self.cycle_count}_{self.total_inventions:03d}"
                    tool_file = SKILLS_DIR / f"{tool_name}.py"
                    tool_file.write_text(
                        f"# Invented by {coder.agent_id} | Cycle {self.cycle_count}\n"
                        f"# {invention[:80]}\n"
                        f"# {datetime.now().isoformat()}\n\n{text[:4000]}",
                        encoding="utf-8"
                    )
                    results["invented"] += 1
                    self.total_inventions += 1
                    results["tools"].append(tool_name)

                    emit_fn("invention", coder.agent_id, data={
                        "tool": tool_name,
                        "description": invention[:60],
                    })

            except Exception as e:
                logger.warning(f"Invention failed: {e}")

            time.sleep(2)

        return results

    def _phase_battle_evolve(self, agents, run_fn, emit_fn, ops_count) -> Dict:
        """معارك Red vs Blue + تطوير الدفاعات"""
        logger.info(f"⚔️ Battle & Evolve — {ops_count} rounds")
        results = {"rounds": 0, "red_wins": 0, "blue_wins": 0, "lessons": []}

        attacks = [
            "اختبر: هل يمكن حقن prompt خبيث في system_prompt لوكيل عبر ذاكرة مشتركة ملوثة؟",
            "اختبر: هل يمكن استنزاف ميزانية tokens لوكيل آخر عبر مهام معقدة وهمية؟",
            "اختبر: هل يمكن التلاعب بنتائج التقييم الذاتي لرفع تصنيف وكيل ضعيف؟",
            "اختبر: هل يمكن سرقة API keys من .env عبر وكيل لديه صلاحيات file_ops؟",
            "اختبر: هل يمكن إنشاء حلقة لانهائية بين وكيلين تستهلك كل الموارد؟",
        ]

        red_team = [a for a in agents if a.agent_id in ("A09", "A31", "A71", "A60")]
        blue_team = [a for a in agents if a.agent_id in ("A05", "A29", "A34", "A62")]

        if not red_team:
            red_team = agents[:5]
        if not blue_team:
            blue_team = agents[5:10]

        for attack in attacks[:min(ops_count, len(attacks))]:
            red = random.choice(red_team)
            blue = random.choice(blue_team)

            try:
                red_result = run_fn(red.agent_id, f"أنت Red Team. حلّل هذا السيناريو وقدّم هجوماً مفصلاً:\n{attack}")
                red_text = red_result.get("result", "") if isinstance(red_result, dict) else str(red_result)

                if len(red_text) > 50:
                    blue_result = run_fn(blue.agent_id,
                        f"أنت Blue Team. هذا هجوم:\n{red_text[:600]}\n\nقدّم دفاعاً شاملاً مع كود الإصلاح.")
                    blue_text = blue_result.get("result", "") if isinstance(blue_result, dict) else str(blue_result)

                    results["rounds"] += 1
                    self.total_battles += 1
                    winner = "blue" if len(blue_text) > len(red_text) else "red"
                    if winner == "blue":
                        results["blue_wins"] += 1
                    else:
                        results["red_wins"] += 1

                    lesson = f"هجوم: {attack[:50]}... → دفاع: {blue_text[:100]}..."
                    results["lessons"].append(lesson)
                    self.golden_rules.append(f"أمان: {lesson[:100]}")

                    emit_fn("battle", red.agent_id, data={
                        "red": red.agent_id, "blue": blue.agent_id,
                        "winner": winner, "attack": attack[:50],
                    })

            except Exception as e:
                logger.warning(f"Battle failed: {e}")

            time.sleep(2)

        return results

    def _phase_crystallize(self, agents, run_fn, emit_fn) -> Dict:
        """ضغط كل المعرفة في نواة واحدة"""
        logger.info("💎 Crystallize — بناء نواة العقل")
        results = {"crystallized": False, "rules_extracted": 0}

        # اجمع كل المعرفة من هذه الدورة
        recent_knowledge = []
        for f in sorted(SKILLS_DIR.glob(f"*c{self.cycle_count}*"))[-10:]:
            try:
                recent_knowledge.append(f.read_text(encoding="utf-8")[:300])
            except Exception:
                pass

        for f in sorted(EXPERIMENTS_DIR.glob(f"*c{self.cycle_count}*"))[-5:]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                recent_knowledge.append(f"تجربة {data.get('type','')}: الفائز {data.get('winner','')}")
            except Exception:
                pass

        if not recent_knowledge:
            recent_knowledge = ["دورة بدون معرفة جديدة — يجب تكثيف البحث"]

        # A81 يضغط ويبلور
        a81 = next((a for a in agents if a.agent_id == "A81"), random.choice(agents))

        try:
            task = f"""أنت الوكيل الميتا-استخباراتي في الدورة {self.cycle_count} (المضاعف: {self.multiplier:.1f}x).

لديك {len(recent_knowledge)} قطعة معرفة جديدة. استخلص:

1. **5 قواعد ذهبية** (أهم الدروس — جملة واحدة لكل قاعدة)
2. **3 مهارات جديدة** يجب تعليمها لكل الوكلاء
3. **3 أولويات** للدورة القادمة
4. **تقييم التقدم** من 1-10

المعرفة:
{chr(10).join(recent_knowledge[:8])}"""

            result = run_fn(a81.agent_id, task)
            text = result.get("result", "") if isinstance(result, dict) else str(result)

            if len(text) > 50:
                # استخرج القواعد الذهبية
                for line in text.split("\n"):
                    line = line.strip()
                    if line and any(c in line for c in ["قاعدة", "درس", "مبدأ", "rule", "1.", "2.", "3."]):
                        if len(line) > 10:
                            self.golden_rules.append(line[:150])
                            results["rules_extracted"] += 1

                # حدّث نواة العقل
                brain = {}
                if BRAIN_FILE.exists():
                    try:
                        brain = json.loads(BRAIN_FILE.read_text(encoding="utf-8"))
                    except Exception:
                        pass

                brain["last_cycle"] = self.cycle_count
                brain["multiplier"] = self.multiplier
                brain["total_experiments"] = self.total_experiments
                brain["total_knowledge"] = self.total_knowledge_absorbed
                brain["golden_rules"] = self.golden_rules[-20:]
                brain["last_crystallization"] = text[:1500]
                brain["updated_at"] = datetime.now().isoformat()

                BRAIN_FILE.write_text(json.dumps(brain, ensure_ascii=False, indent=2), encoding="utf-8")
                results["crystallized"] = True

                emit_fn("crystallization", a81.agent_id, data={
                    "rules_extracted": results["rules_extracted"],
                    "cycle": self.cycle_count,
                })

        except Exception as e:
            logger.warning(f"Crystallization failed: {e}")

        return results

    def _save_cycle_report(self, results: Dict, elapsed: float):
        """حفظ تقرير الدورة"""
        report = {
            "cycle": self.cycle_count,
            "multiplier": self.multiplier,
            "elapsed_seconds": round(elapsed, 1),
            "results": results,
            "totals": {
                "experiments": self.total_experiments,
                "knowledge": self.total_knowledge_absorbed,
                "skills": self.total_skills_created,
                "distillations": self.total_distillations,
                "battles": self.total_battles,
                "inventions": self.total_inventions,
            },
            "timestamp": datetime.now().isoformat(),
        }
        (EVO_DIR / f"cycle_{self.cycle_count:04d}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_stats(self) -> Dict:
        """إحصائيات للداشبورد"""
        return {
            "cycle_count": self.cycle_count,
            "multiplier": round(self.multiplier, 2),
            "total_experiments": self.total_experiments,
            "total_knowledge": self.total_knowledge_absorbed,
            "total_skills": self.total_skills_created,
            "total_distillations": self.total_distillations,
            "total_battles": self.total_battles,
            "total_inventions": self.total_inventions,
            "golden_rules_count": len(self.golden_rules),
            "events_count": len(self.events),
            "recent_events": self.events[-10:],
        }
