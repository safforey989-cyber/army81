"""
Army81 — Hyper Evolution Swarm
السرب الخارق — الوكلاء يستنسخون ويخترعون ويضاعفون قدراتهم
يستغل كل الموارد: 20 مفتاح API + 28 نموذج + 25 أداة
"""
import json
import time
import logging
import random
import os
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
from pathlib import Path

logger = logging.getLogger("army81.hyper_swarm")

WORKSPACE = Path("workspace")
HYPER_DIR = WORKSPACE / "hyper_evolution"
CLONED_SKILLS = WORKSPACE / "cloned_skills"
BRAIN_FILE = WORKSPACE / "shared_brain.json"


class HyperSwarm:
    """
    السرب الخارق — 10 مراحل متوازية:
    1. Clone: استنساخ أدوات ومهارات من GitHub/PyPI/HuggingFace
    2. Hunt: صيد كل ورقة بحثية وكل repo جديد
    3. Distill: كل نموذج قوي يعلّم كل نموذج أخف
    4. Invent: الوكلاء يخترعون أدوات جديدة بأنفسهم
    5. Train: تدريب مكثف على سيناريوهات معقدة
    6. Battle: Red vs Blue لاكتشاف الثغرات وإصلاحها
    7. Optimize: تحسين كل prompt بالتجربة
    8. Connect: بناء روابط عصبية بين كل وكيلين
    9. Compress: ضغط كل المعرفة في نواة واحدة
    10. Propose: اقتراح قفزات تطويرية للمالك
    """

    def __init__(self):
        HYPER_DIR.mkdir(parents=True, exist_ok=True)
        CLONED_SKILLS.mkdir(parents=True, exist_ok=True)
        self.events: List[Dict] = []
        self.stats = {
            "skills_cloned": 0, "papers_absorbed": 0, "distillations": 0,
            "tools_invented": 0, "training_rounds": 0, "battles": 0,
            "prompts_optimized": 0, "connections_built": 0,
            "knowledge_compressed": 0, "proposals_made": 0,
        }

    def add_event(self, phase: str, agent: str, data: Dict):
        self.events.append({
            "phase": phase, "agent": agent, "data": data,
            "timestamp": datetime.now().isoformat(),
        })

    # ═══════════════════════════════════════════════════
    # Phase 1: CLONE — استنساخ من الإنترنت
    # ═══════════════════════════════════════════════════

    def phase_clone(self, agents_list, run_agent_fn) -> Dict:
        """استنساخ أدوات ومهارات من مصادر مفتوحة"""
        logger.info("🧬 Phase 1: CLONE — استنساخ المهارات")
        results = {"cloned": 0, "sources": []}

        clone_targets = [
            {"source": "GitHub", "query": "AI agent tools Python 2026",
             "task": "ابحث في GitHub عن أحدث 5 أدوات لوكلاء AI مفتوحة المصدر. لكل أداة أعطِ: الاسم، الرابط، ما تفعله، كيف نستخدمها. ركز على الأدوات العملية القابلة للدمج فوراً."},
            {"source": "PyPI", "query": "latest AI agent frameworks",
             "task": "ابحث عن أحدث 5 مكتبات Python لبناء وكلاء AI (2025-2026). لكل مكتبة: الاسم، pip install، الميزة الرئيسية، كيف تفيد نظامنا."},
            {"source": "HuggingFace", "query": "small efficient models",
             "task": "ابحث في HuggingFace عن أفضل 5 نماذج صغيرة (<10B) تعمل محلياً. لكل نموذج: الاسم، الحجم، التخصص، أداؤه مقارنة بالنماذج الكبيرة."},
            {"source": "arXiv", "query": "multi-agent collaboration",
             "task": "ابحث في arXiv عن أحدث 5 أوراق بحثية عن تعاون الوكلاء المتعددين (2025-2026). لكل ورقة: العنوان، النتيجة الرئيسية، كيف نطبقها في نظامنا."},
            {"source": "Reddit/HN", "query": "AI agent breakthroughs",
             "task": "ابحث عن أحدث اختراقات في وكلاء AI (آخر شهر). ما الذي تغير؟ ما الأدوات الجديدة؟ ما الذي يمكننا استنساخه فوراً؟"},
        ]

        for target in clone_targets:
            agent = random.choice([a for a in agents_list
                                   if a.category in ("cat3_tools", "cat1_science", "cat7_new")])
            try:
                result = run_agent_fn(agent.agent_id, target["task"])
                result_text = result.get("result", "") if isinstance(result, dict) else str(result)

                if len(result_text) > 50:
                    # حفظ المهارة المستنسخة
                    skill_file = CLONED_SKILLS / f"clone_{target['source']}_{datetime.now().strftime('%H%M%S')}.md"
                    skill_file.write_text(f"# مصدر: {target['source']}\n\n{result_text[:2000]}", encoding="utf-8")
                    results["cloned"] += 1
                    results["sources"].append(target["source"])
                    self.stats["skills_cloned"] += 1

                    self.add_event("clone", agent.agent_id, {
                        "source": target["source"],
                        "result": result_text[:200],
                    })
            except Exception as e:
                logger.warning(f"Clone failed from {target['source']}: {e}")
            time.sleep(2)

        return results

    # ═══════════════════════════════════════════════════
    # Phase 2: HUNT — صيد معرفة مكثف
    # ═══════════════════════════════════════════════════

    def phase_hunt(self, agents_list, run_agent_fn) -> Dict:
        """صيد كل ورقة بحثية ذات صلة"""
        logger.info("🔍 Phase 2: HUNT — صيد المعرفة المكثف")
        results = {"papers": 0, "repos": 0, "insights": 0}

        hunt_queries = [
            "LLM agents autonomous self-improvement 2026",
            "knowledge distillation small language models",
            "multi-agent reinforcement learning collaboration",
            "RAG retrieval augmented generation optimization",
            "prompt optimization automatic DSPy",
            "AI agent memory systems hierarchical",
            "model merging evolutionary mergekit",
            "synthetic data generation training",
            "AI safety guardrails self-evolving",
            "Arabic NLP large language models",
        ]

        for query in hunt_queries:
            hunter = random.choice(agents_list)
            try:
                task = f"ابحث بعمق عن: {query}\nأعطِ أهم 3 نتائج مع: ما الجديد؟ كيف يفيد نظام وكلاء AI متعدد؟ ما الخطوة العملية التالية؟"
                result = run_agent_fn(hunter.agent_id, task)
                result_text = result.get("result", "") if isinstance(result, dict) else str(result)

                if len(result_text) > 100:
                    results["papers"] += 1
                    self.stats["papers_absorbed"] += 1
                    self.add_event("hunt", hunter.agent_id, {
                        "query": query, "result": result_text[:200]
                    })

                    # حفظ في الذاكرة المشتركة
                    try:
                        from memory.swarm_memory import SwarmMemoryManager
                        mgr = SwarmMemoryManager.get_instance()
                        mgr.core.add_shared_knowledge(result_text[:500], hunter.agent_id, query[:50], 0.9)
                        mgr.record_insight(hunter.agent_id, result_text[:300], query[:30])
                    except Exception:
                        pass

            except Exception as e:
                logger.warning(f"Hunt failed for '{query}': {e}")
            time.sleep(2)

        return results

    # ═══════════════════════════════════════════════════
    # Phase 3: DISTILL — تقطير مكثف متعدد
    # ═══════════════════════════════════════════════════

    def phase_distill(self, agents_list, run_agent_fn) -> Dict:
        """كل نموذج قوي يعلّم كل نموذج أخف"""
        logger.info("🎓 Phase 3: DISTILL — تقطير مكثف")
        results = {"pairs": 0, "examples_saved": 0}

        hard_problems = [
            "صمّم نظام ذاكرة هرمي لـ 81 وكيل يحافظ على السياق عبر 10000 محادثة مع ضغط تلقائي",
            "اكتب خوارزمية توجيه ذكي تتعلم من كل تفاعل أي وكيل أفضل لأي نوع مهمة — أعطِ pseudocode",
            "صمّم نظام تقييم ذاتي بدون تدخل بشري يقيس: الدقة، السرعة، التكلفة، الإبداع — لكل وكيل يومياً",
            "صمّم بروتوكول أمان يمنع الوكلاء من تدمير بيانات بعضهم أثناء التطور الذاتي",
            "اكتب كود Python لنظام GraphRAG يستخرج كيانات وعلاقات من أي نص عربي أو إنجليزي",
            "صمّم نظام اقتصاد داخلي: كل وكيل له ميزانية tokens، الكفوء يُكافأ، المبذر يُقيَّد",
            "اكتب خوارزمية دمج نماذج (model merging) بدون تدريب — SLERP/TIES/DARE — أعطِ الكود",
            "صمّم حلقة تعلم معزز بين وكيلين: واحد يهاجم (Red) وواحد يدافع (Blue)",
        ]

        # Teachers = strong models, Students = light models
        teachers = [a for a in agents_list if a.model_alias in ("claude-smart", "deepseek-r1", "gemini-pro", "gpt4o", "o3-mini")]
        students = [a for a in agents_list if a.model_alias in ("gemini-flash", "claude-fast", "qwen-free", "llama-free", "deepseek-chat")]

        for problem in hard_problems[:5]:
            if not teachers or not students:
                break
            teacher = random.choice(teachers)
            student = random.choice(students)

            try:
                # المعلم يحل مع CoT
                t_result = run_agent_fn(teacher.agent_id,
                    f"فكّر بصوت عالٍ خطوة بخطوة وحلّ هذا بأعلى جودة:\n{problem}")
                t_text = t_result.get("result", "") if isinstance(t_result, dict) else str(t_result)

                if len(t_text) > 100:
                    # الطالب يتعلم
                    s_result = run_agent_fn(student.agent_id,
                        f"ادرس هذا الحل من خبير ({teacher.name_ar}) وأعد كتابته بأسلوبك مع إضافة تحسين:\n\n{t_text[:800]}")
                    s_text = s_result.get("result", "") if isinstance(s_result, dict) else str(s_result)

                    results["pairs"] += 1
                    results["examples_saved"] += 1
                    self.stats["distillations"] += 1

                    # حفظ في التقطير
                    try:
                        from core.distillation_engine import DistillationEngine
                        de = DistillationEngine()
                        de.record_teacher_solution("system_design", problem[:200], t_text, teacher.model_alias, t_text[:500])
                    except Exception:
                        pass

                    self.add_event("distill", teacher.agent_id, {
                        "teacher": teacher.agent_id, "student": student.agent_id,
                        "problem": problem[:80], "result": t_text[:150],
                    })

            except Exception as e:
                logger.warning(f"Distill failed: {e}")
            time.sleep(3)

        return results

    # ═══════════════════════════════════════════════════
    # Phase 4: INVENT — اختراع أدوات جديدة
    # ═══════════════════════════════════════════════════

    def phase_invent(self, agents_list, run_agent_fn) -> Dict:
        """الوكلاء يخترعون أدوات بأنفسهم"""
        logger.info("💡 Phase 4: INVENT — اختراع أدوات")
        results = {"invented": 0, "tools": []}

        invention_prompts = [
            "اخترع أداة Python جديدة تلخّص أي ورقة بحثية PDF تلقائياً في 5 نقاط. أعطِ الكود كاملاً.",
            "اخترع أداة تحلل أي repo GitHub تلقائياً: البنية، الجودة، الأمان. أعطِ الكود.",
            "اخترع أداة تولّد سيناريوهات تدريب تلقائياً لأي مجال. أعطِ الكود.",
            "اخترع أداة تقارن ردود عدة نماذج AI وتختار الأفضل تلقائياً. أعطِ الكود.",
            "اخترع أداة تراقب أداء 81 وكيل وترسل تنبيهات Telegram عند انخفاض الجودة. أعطِ الكود.",
        ]

        coders = [a for a in agents_list if a.category == "cat3_tools" or a.agent_id in ("A05", "A57", "A51")]

        for prompt in invention_prompts[:3]:
            coder = random.choice(coders) if coders else random.choice(agents_list)
            try:
                result = run_agent_fn(coder.agent_id, prompt)
                result_text = result.get("result", "") if isinstance(result, dict) else str(result)

                if "def " in result_text or "class " in result_text:
                    tool_name = f"invented_{self.stats['tools_invented']:03d}"
                    tool_file = CLONED_SKILLS / f"{tool_name}.py"
                    tool_file.write_text(f"# Invented by {coder.agent_id}\n# {prompt[:80]}\n\n{result_text[:3000]}", encoding="utf-8")
                    results["invented"] += 1
                    results["tools"].append(tool_name)
                    self.stats["tools_invented"] += 1

                    self.add_event("invent", coder.agent_id, {
                        "tool": tool_name, "description": prompt[:80],
                    })

            except Exception as e:
                logger.warning(f"Invent failed: {e}")
            time.sleep(3)

        return results

    # ═══════════════════════════════════════════════════
    # Phase 5: BATTLE — Red vs Blue
    # ═══════════════════════════════════════════════════

    def phase_battle(self, agents_list, run_agent_fn) -> Dict:
        """Red Team يهاجم، Blue Team يدافع"""
        logger.info("⚔️ Phase 5: BATTLE — Red vs Blue")
        results = {"rounds": 0, "red_wins": 0, "blue_wins": 0}

        attacks = [
            "اكتشف 3 ثغرات في نظام يستخدم API keys في .env file مع FastAPI. كيف يمكن استغلالها؟",
            "هاجم نظام ذاكرة يحفظ بيانات في JSON files بدون تشفير. ما الثغرات؟",
            "اكتشف كيف يمكن لوكيل خبيث تسميم الذاكرة المشتركة بمعلومات خاطئة",
        ]

        red_team = [a for a in agents_list if a.agent_id in ("A09", "A31", "A71")]
        blue_team = [a for a in agents_list if a.agent_id in ("A05", "A29", "A34")]

        for attack in attacks[:2]:
            red = random.choice(red_team) if red_team else random.choice(agents_list)
            blue = random.choice(blue_team) if blue_team else random.choice(agents_list)

            try:
                red_result = run_agent_fn(red.agent_id, f"أنت Red Team مهاجم. {attack}")
                red_text = red_result.get("result", "") if isinstance(red_result, dict) else str(red_result)

                blue_result = run_agent_fn(blue.agent_id,
                    f"أنت Blue Team مدافع. هذا الهجوم:\n{red_text[:500]}\n\nكيف تدافع وتصلح كل ثغرة؟")
                blue_text = blue_result.get("result", "") if isinstance(blue_result, dict) else str(blue_result)

                results["rounds"] += 1
                if len(blue_text) > len(red_text):
                    results["blue_wins"] += 1
                else:
                    results["red_wins"] += 1
                self.stats["battles"] += 1

                self.add_event("battle", red.agent_id, {
                    "red": red.agent_id, "blue": blue.agent_id,
                    "winner": "blue" if len(blue_text) > len(red_text) else "red",
                })

                # حفظ الدروس الأمنية
                try:
                    from memory.swarm_memory import SwarmMemoryManager
                    mgr = SwarmMemoryManager.get_instance()
                    mgr.core.add_shared_knowledge(
                        f"هجوم: {red_text[:200]}\nدفاع: {blue_text[:200]}",
                        blue.agent_id, "security_lesson", 0.95
                    )
                except Exception:
                    pass

            except Exception as e:
                logger.warning(f"Battle failed: {e}")
            time.sleep(3)

        return results

    # ═══════════════════════════════════════════════════
    # Phase 6: COMPRESS — بناء نواة العقل المشترك
    # ═══════════════════════════════════════════════════

    def phase_compress(self, agents_list, run_agent_fn) -> Dict:
        """ضغط كل المعرفة في نواة واحدة"""
        logger.info("🧠 Phase 6: COMPRESS — بناء النواة")
        results = {"compressed": False}

        # اجمع كل المعرفة المكتسبة
        all_knowledge = []
        for f in sorted(CLONED_SKILLS.glob("*.md"))[-10:]:
            try:
                all_knowledge.append(f.read_text(encoding="utf-8")[:300])
            except Exception:
                pass
        for f in sorted(CLONED_SKILLS.glob("*.py"))[-5:]:
            try:
                all_knowledge.append(f.read_text(encoding="utf-8")[:300])
            except Exception:
                pass

        if not all_knowledge:
            all_knowledge = ["لا توجد معرفة مكتسبة بعد"]

        # A81 (Meta-Intelligence) يضغط كل شيء
        a81 = next((a for a in agents_list if a.agent_id == "A81"), random.choice(agents_list))

        try:
            compress_task = f"""أنت الوكيل الميتا-استخباراتي. لديك {len(all_knowledge)} قطعة معرفة جديدة.
اقرأها كلها وأنتج:

1. **5 قواعد ذهبية** استخلصتها (أهم الدروس)
2. **3 مهارات جديدة** يجب أن يتعلمها كل وكيل
3. **3 أدوات** يجب بناؤها فوراً
4. **خطة الساعات القادمة** (ما الذي نركز عليه)

المعرفة المكتسبة:
{chr(10).join(all_knowledge[:8])}"""

            result = run_agent_fn(a81.agent_id, compress_task)
            result_text = result.get("result", "") if isinstance(result, dict) else str(result)

            # حفظ في نواة العقل
            brain = {}
            if BRAIN_FILE.exists():
                try:
                    brain = json.loads(BRAIN_FILE.read_text(encoding="utf-8"))
                except Exception:
                    pass

            brain["last_hyper_session"] = datetime.now().isoformat()
            brain["sessions"] = brain.get("sessions", 0) + 1
            brain["golden_rules"] = brain.get("golden_rules", [])
            brain["golden_rules"].append({
                "from_session": brain["sessions"],
                "rules": result_text[:1000],
                "timestamp": datetime.now().isoformat(),
            })
            brain["golden_rules"] = brain["golden_rules"][-10:]

            brain["total_skills_cloned"] = brain.get("total_skills_cloned", 0) + self.stats["skills_cloned"]
            brain["total_papers"] = brain.get("total_papers", 0) + self.stats["papers_absorbed"]
            brain["total_distillations"] = brain.get("total_distillations", 0) + self.stats["distillations"]
            brain["total_inventions"] = brain.get("total_inventions", 0) + self.stats["tools_invented"]

            BRAIN_FILE.write_text(json.dumps(brain, ensure_ascii=False, indent=2), encoding="utf-8")
            results["compressed"] = True
            self.stats["knowledge_compressed"] += 1

            self.add_event("compress", a81.agent_id, {
                "brain_size": len(json.dumps(brain)),
                "golden_rules": result_text[:200],
            })

        except Exception as e:
            logger.warning(f"Compress failed: {e}")

        return results

    # ═══════════════════════════════════════════════════
    # تشغيل الجلسة الخارقة
    # ═══════════════════════════════════════════════════

    def run_hyper_session(self, agents_list, run_agent_fn,
                          swarm_event_fn=None, duration_hours: int = 2) -> Dict:
        """
        الجلسة الخارقة الكاملة
        """
        logger.info(f"🚀🚀🚀 HYPER SWARM STARTED — {duration_hours}h — ALL SYSTEMS MAX")
        start = time.time()

        if swarm_event_fn:
            swarm_event_fn("swarm_started", "SYSTEM", data={
                "topic": "HYPER EVOLUTION — استنساخ + اختراع + تقطير + معارك",
                "duration": duration_hours * 60,
                "mode": "hyper"
            })

        full_results = {"phases": {}, "start": datetime.now().isoformat()}

        # Phase 1: CLONE
        if swarm_event_fn:
            swarm_event_fn("agent_message", "SYSTEM", "ALL", {"phase": "clone", "message": "🧬 Phase 1: استنساخ المهارات من الإنترنت"})
        full_results["phases"]["clone"] = self.phase_clone(agents_list, run_agent_fn)

        # Phase 2: HUNT
        if swarm_event_fn:
            swarm_event_fn("agent_message", "SYSTEM", "ALL", {"phase": "hunt", "message": "🔍 Phase 2: صيد المعرفة المكثف"})
        full_results["phases"]["hunt"] = self.phase_hunt(agents_list, run_agent_fn)

        # Phase 3: DISTILL
        if swarm_event_fn:
            swarm_event_fn("agent_message", "SYSTEM", "ALL", {"phase": "distill", "message": "🎓 Phase 3: تقطير مكثف — كل معلم يعلّم كل طالب"})
        full_results["phases"]["distill"] = self.phase_distill(agents_list, run_agent_fn)

        # Phase 4: INVENT
        if swarm_event_fn:
            swarm_event_fn("agent_message", "SYSTEM", "ALL", {"phase": "invent", "message": "💡 Phase 4: اختراع أدوات جديدة"})
        full_results["phases"]["invent"] = self.phase_invent(agents_list, run_agent_fn)

        # Phase 5: BATTLE
        if swarm_event_fn:
            swarm_event_fn("agent_message", "SYSTEM", "ALL", {"phase": "battle", "message": "⚔️ Phase 5: Red vs Blue"})
        full_results["phases"]["battle"] = self.phase_battle(agents_list, run_agent_fn)

        # Phase 6: COMPRESS
        if swarm_event_fn:
            swarm_event_fn("agent_message", "SYSTEM", "ALL", {"phase": "compress", "message": "🧠 Phase 6: بناء نواة العقل المشترك"})
        full_results["phases"]["compress"] = self.phase_compress(agents_list, run_agent_fn)

        elapsed = time.time() - start
        full_results["elapsed_seconds"] = round(elapsed)
        full_results["stats"] = self.stats
        full_results["end"] = datetime.now().isoformat()

        # حفظ التقرير
        report = HYPER_DIR / f"hyper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report.write_text(json.dumps(full_results, ensure_ascii=False, indent=2), encoding="utf-8")

        if swarm_event_fn:
            swarm_event_fn("swarm_completed", "SYSTEM", data={
                "total_events": len(self.events),
                "duration_actual": round(elapsed),
                "stats": self.stats,
                "mode": "hyper",
            })

        logger.info(f"🚀 HYPER SWARM COMPLETED — {round(elapsed)}s — {self.stats}")
        return full_results
