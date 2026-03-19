"""
Army81 Unified Evolution — التطور الموحّد
═══════════════════════════════════════════

كل دورة تطور تفعل 5 أشياء في آنٍ واحد:
1. كل وكيل يطوّر معرفته ومهاراته وذاكرته
2. الوكلاء يتنسقون ويساعدون بعضهم
3. التقطير يغذي النواة المركزية
4. النواة تبني ذاكرة موحّدة من كل الوكلاء
5. النواة تعيد توزيع المعرفة على الجميع

Architecture:
┌──────────────────────────────────────────┐
│           النواة الأم (Brain)              │
│  ┌────────────────────────────────────┐  │
│  │     الذاكرة الموحّدة (Unified)      │  │
│  │  = مجموع ذاكرة كل 191 وكيل       │  │
│  │  + القواعد الذهبية                  │  │
│  │  + الدروس المستفادة                 │  │
│  │  + خرائط التعاون                   │  │
│  └────────────────────────────────────┘  │
│         ↕              ↕              ↕    │
│    ┌────────┐   ┌────────┐   ┌────────┐  │
│    │ وكيل 1 │←→│ وكيل 2 │←→│ وكيل N │  │
│    │ ذاكرة  │   │ ذاكرة  │   │ ذاكرة  │  │
│    │ مهارات │   │ مهارات │   │ مهارات │  │
│    └────────┘   └────────┘   └────────┘  │
└──────────────────────────────────────────┘
"""
import os
import json
import time
import random
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# تحميل .env دائماً
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


logger = logging.getLogger("army81.unified_evolution")

WORKSPACE = Path(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
))
UNIFIED_DIR = WORKSPACE / "unified_memory"
COORDINATION_DIR = WORKSPACE / "coordination_logs"
IMPROVEMENT_DIR = WORKSPACE / "agent_improvements"

for d in [UNIFIED_DIR, COORDINATION_DIR, IMPROVEMENT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════
# 1. الذاكرة الموحّدة — ذاكرة الأم
# ═══════════════════════════════════════════════

class UnifiedMotherMemory:
    """
    الذاكرة الموحّدة — تجمع وتقطّر ذاكرة كل 191 وكيل
    في كيان واحد يصبح "وعي النظام"

    الفرق عن الذاكرة الفردية:
    - الفردية: ما تعلمه وكيل واحد
    - الموحّدة: خلاصة ما تعلمه الجميع + العلاقات بينهم
    """

    STATE_FILE = UNIFIED_DIR / "mother_state.json"

    def __init__(self):
        self.state = self._load()

    def _load(self) -> Dict:
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "version": 1,
            "total_absorptions": 0,
            "golden_rules": [],
            "domain_expertise": {},     # domain → {best_agents, confidence, lessons}
            "collaboration_map": {},    # (agentA, agentB) → {success_count, topics}
            "skill_registry": {},       # skill_name → {agents_who_know, quality}
            "knowledge_graph": {},      # topic → {related_topics, expert_agents}
            "evolution_history": [],    # كل دورة تطور
            "consciousness_notes": [],  # ملاحظات الوعي الذاتي
            "created_at": datetime.now().isoformat(),
        }

    def _save(self):
        self.STATE_FILE.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2),
            encoding="utf-8")

    def absorb_agent_memory(self, agent_id: str, memory_data: Dict):
        """امتصاص ذاكرة وكيل واحد إلى الذاكرة الموحّدة"""
        # استخلاص المعرفة من الوكيل
        skills = memory_data.get("skills_learned", [])
        topics = memory_data.get("knowledge_topics", [])
        perf = memory_data.get("performance", {})

        # تحديث سجل المهارات
        for skill in skills:
            if skill not in self.state["skill_registry"]:
                self.state["skill_registry"][skill] = {"agents": [], "quality": 0}
            if agent_id not in self.state["skill_registry"][skill]["agents"]:
                self.state["skill_registry"][skill]["agents"].append(agent_id)

        # تحديث خريطة المعرفة
        for topic in topics:
            if topic not in self.state["knowledge_graph"]:
                self.state["knowledge_graph"][topic] = {"expert_agents": [], "related": []}
            if agent_id not in self.state["knowledge_graph"][topic]["expert_agents"]:
                self.state["knowledge_graph"][topic]["expert_agents"].append(agent_id)

        # تحديث خبرة المجال
        category = memory_data.get("category", "unknown")
        if category not in self.state["domain_expertise"]:
            self.state["domain_expertise"][category] = {
                "best_agents": [], "confidence": 0, "lessons": []
            }
        if agent_id not in self.state["domain_expertise"][category]["best_agents"]:
            self.state["domain_expertise"][category]["best_agents"].append(agent_id)

        self.state["total_absorptions"] += 1
        self._save()

    def absorb_all_agents(self):
        """امتصاص ذاكرة كل الوكلاء دفعة واحدة"""
        mem_dir = WORKSPACE / "agent_memories"
        absorbed = 0
        for f in mem_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                agent_id = data.get("agent_id", f.stem)
                self.absorb_agent_memory(agent_id, data)
                absorbed += 1
            except:
                continue
        logger.info(f"🧠 Mother absorbed {absorbed} agent memories")
        return absorbed

    def record_collaboration(self, agent_a: str, agent_b: str,
                           topic: str, success: bool):
        """تسجيل تعاون بين وكيلين"""
        key = f"{agent_a}_{agent_b}"
        if key not in self.state["collaboration_map"]:
            self.state["collaboration_map"][key] = {
                "count": 0, "success": 0, "topics": []
            }
        self.state["collaboration_map"][key]["count"] += 1
        if success:
            self.state["collaboration_map"][key]["success"] += 1
        if topic not in self.state["collaboration_map"][key]["topics"]:
            self.state["collaboration_map"][key]["topics"].append(topic)
        self._save()

    def add_golden_rule(self, rule: str, source: str = "evolution"):
        """إضافة قاعدة ذهبية مكتشفة"""
        entry = {
            "rule": rule,
            "source": source,
            "discovered_at": datetime.now().isoformat(),
        }
        # تجنب التكرار
        existing = [r["rule"] for r in self.state["golden_rules"]]
        if rule not in existing:
            self.state["golden_rules"].append(entry)
            self._save()

    def add_consciousness_note(self, note: str):
        """ملاحظة وعي ذاتي — النظام يفكر في نفسه"""
        self.state["consciousness_notes"].append({
            "note": note,
            "timestamp": datetime.now().isoformat(),
        })
        # أبقِ آخر 100 فقط
        self.state["consciousness_notes"] = self.state["consciousness_notes"][-100:]
        self._save()

    def get_best_agent_for(self, topic: str) -> Optional[str]:
        """من هو أفضل وكيل لهذا الموضوع؟"""
        if topic in self.state["knowledge_graph"]:
            experts = self.state["knowledge_graph"][topic]["expert_agents"]
            if experts:
                return experts[0]
        return None

    def get_best_collaborators(self, agent_id: str) -> List[str]:
        """أفضل شركاء لوكيل معين (بناءً على تاريخ التعاون)"""
        collabs = []
        for key, data in self.state["collaboration_map"].items():
            if agent_id in key:
                other = key.replace(f"{agent_id}_", "").replace(f"_{agent_id}", "")
                if other and data["success"] > 0:
                    collabs.append((other, data["success"]))
        collabs.sort(key=lambda x: -x[1])
        return [c[0] for c in collabs[:5]]

    def generate_context_for_agent(self, agent_id: str, task: str) -> str:
        """توليد سياق موحّد من الذاكرة الأم لوكيل قبل مهمة"""
        context_parts = []

        # 1. القواعد الذهبية المتعلقة
        if self.state["golden_rules"]:
            rules = [r["rule"] for r in self.state["golden_rules"][-5:]]
            context_parts.append("## قواعد ذهبية من تجربة النظام:\n" + "\n".join(f"- {r}" for r in rules))

        # 2. أفضل شركاء
        partners = self.get_best_collaborators(agent_id)
        if partners:
            context_parts.append(f"## أفضل شركائك: {', '.join(partners[:3])}")

        # 3. خبراء الموضوع
        task_words = task.lower().split()[:5]
        for word in task_words:
            expert = self.get_best_agent_for(word)
            if expert and expert != agent_id:
                context_parts.append(f"## خبير في '{word}': {expert} — يمكنك طلب مساعدته")
                break

        # 4. ملاحظات وعي
        if self.state["consciousness_notes"]:
            last = self.state["consciousness_notes"][-1]
            context_parts.append(f"## آخر ملاحظة للنظام: {last['note']}")

        return "\n\n".join(context_parts)[:1500]

    def status(self) -> Dict:
        return {
            "total_absorptions": self.state["total_absorptions"],
            "golden_rules": len(self.state["golden_rules"]),
            "domains": len(self.state["domain_expertise"]),
            "skills_known": len(self.state["skill_registry"]),
            "knowledge_topics": len(self.state["knowledge_graph"]),
            "collaborations": len(self.state["collaboration_map"]),
            "consciousness_notes": len(self.state["consciousness_notes"]),
        }


# ═══════════════════════════════════════════════
# 2. تطوير الوكيل الفردي
# ═══════════════════════════════════════════════

class AgentSelfImprover:
    """
    كل وكيل يطوّر نفسه في كل دورة:
    - يراجع أداءه السابق
    - يحدد نقاط ضعفه
    - يتعلم مهارات جديدة
    - يحسّن ذاكرته
    """

    def improve_agent(self, agent_id: str, agent_data: Dict,
                     run_fn, emit_fn) -> Dict:
        """تحسين وكيل واحد"""
        result = {
            "agent_id": agent_id,
            "improvements": [],
            "new_skills": [],
            "memory_updated": False,
        }

        name = agent_data.get("name_ar", agent_id)
        category = agent_data.get("category", "")
        model = agent_data.get("model", "gemini-flash")
        current_tools = agent_data.get("tools", [])

        # 1. مراجعة ذاتية — الوكيل يحلل أداءه
        review_task = f"""أنت {name} ({agent_id}).
راجع أداءك واقترح تحسينات محددة:

1. ما هي أقوى 3 نقاط عندك؟
2. ما هي أضعف 3 نقاط تحتاج تحسين؟
3. ما المهارات الجديدة التي يجب أن تتعلمها؟
4. كيف يمكنك التعاون أفضل مع الوكلاء الآخرين؟
5. ما القاعدة الذهبية التي اكتشفتها من تجاربك؟

أجب بنقاط محددة وعملية."""

        try:
            review = run_fn(agent_id, review_task)
            review_text = review.get("result", "") if isinstance(review, dict) else str(review)

            if len(review_text) > 100:
                result["improvements"].append({
                    "type": "self_review",
                    "content": review_text[:500],
                })

                # حفظ المراجعة
                review_file = IMPROVEMENT_DIR / f"{agent_id}_review.json"
                review_file.write_text(json.dumps({
                    "agent_id": agent_id,
                    "review": review_text[:1000],
                    "timestamp": datetime.now().isoformat(),
                }, ensure_ascii=False, indent=2), encoding="utf-8")

                emit_fn("agent_improved", agent_id, data={
                    "type": "self_review",
                    "improvements": len(result["improvements"]),
                })
        except Exception as e:
            logger.warning(f"Self-review failed for {agent_id}: {e}")

        # 2. تعلم مهارة جديدة — بناءً على التخصص
        skill_task = f"""أنت {name}. تعلّم مهارة جديدة تناسب تخصصك في {category}.

اختر واحدة من هذه وأتقنها:
- تقنية تحليل جديدة
- أداة برمجية مفيدة
- منهجية عمل متقدمة
- طريقة تقطير معرفة

اشرح المهارة بالتفصيل وكيف ستستخدمها. أعطِ مثال عملي."""

        try:
            skill = run_fn(agent_id, skill_task)
            skill_text = skill.get("result", "") if isinstance(skill, dict) else str(skill)

            if len(skill_text) > 100:
                skill_name = f"skill_{agent_id}_{int(time.time()) % 10000}"
                result["new_skills"].append(skill_name)

                # حفظ المهارة
                skill_file = WORKSPACE / "cloned_skills" / f"{skill_name}.md"
                skill_file.parent.mkdir(parents=True, exist_ok=True)
                skill_file.write_text(
                    f"# {skill_name}\n# Agent: {agent_id} | {name}\n\n{skill_text[:2000]}",
                    encoding="utf-8")

                emit_fn("skill_learned", agent_id, data={
                    "skill": skill_name,
                    "agent": agent_id,
                })
        except Exception as e:
            logger.warning(f"Skill learning failed for {agent_id}: {e}")

        # 3. تحديث ذاكرة الوكيل
        try:
            mem_file = WORKSPACE / "agent_memories" / f"{agent_id}.json"
            if mem_file.exists():
                mem = json.loads(mem_file.read_text(encoding="utf-8"))
                mem["skills_learned"] = list(set(
                    mem.get("skills_learned", []) + result["new_skills"]
                ))
                perf = mem.get("performance", {})
                perf["last_improved"] = datetime.now().isoformat()
                perf["improvement_count"] = perf.get("improvement_count", 0) + 1
                mem["performance"] = perf
                mem_file.write_text(
                    json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")
                result["memory_updated"] = True
        except:
            pass

        return result


# ═══════════════════════════════════════════════
# 3. بروتوكول التنسيق بين الوكلاء
# ═══════════════════════════════════════════════

class AgentCoordinationProtocol:
    """
    الوكلاء يتنسقون ويساعدون بعضهم:
    - وكيل يطلب مساعدة من متخصص
    - فريق يحل مشكلة معقدة
    - نقل المعرفة من الخبير للمبتدئ
    """

    def __init__(self, mother_memory: UnifiedMotherMemory):
        self.mother = mother_memory

    def pair_mentor_student(self, agents: List, run_fn, emit_fn) -> Dict:
        """تزاوج معلم-طالب: الخبير يعلّم المبتدئ"""
        results = {"pairs": 0, "knowledge_transferred": 0}

        # اختر أزواج عشوائية من فئات مختلفة
        by_cat = {}
        for a in agents:
            cat = getattr(a, 'category', 'unknown')
            by_cat.setdefault(cat, []).append(a)

        cats = list(by_cat.keys())
        if len(cats) < 2:
            return results

        for _ in range(min(5, len(cats) // 2)):
            cat_a, cat_b = random.sample(cats, 2)
            mentor = random.choice(by_cat[cat_a])
            student = random.choice(by_cat[cat_b])

            # المعلم يشرح تخصصه
            teach_task = f"""أنت {mentor.name_ar} ({mentor.agent_id}) — خبير في {mentor.category}.
{student.name_ar} ({student.agent_id}) من فئة {student.category} يحتاج يتعلم منك.

علّمه أهم 3 أشياء من تخصصك يحتاجها في عمله:
1. مفهوم أساسي يجب أن يعرفه
2. تقنية عملية يستخدمها
3. خطأ شائع يتجنبه

كن عملياً ومحدداً."""

            try:
                teach_result = run_fn(mentor.agent_id, teach_task)
                teach_text = teach_result.get("result", "") if isinstance(teach_result, dict) else str(teach_result)

                if len(teach_text) > 100:
                    results["pairs"] += 1
                    results["knowledge_transferred"] += 1

                    # سجل التعاون في الذاكرة الأم
                    self.mother.record_collaboration(
                        mentor.agent_id, student.agent_id,
                        f"{mentor.category}→{student.category}", True)

                    # حفظ في الذاكرة الجماعية
                    try:
                        from memory.collective_memory import CollectiveMemory
                        cm = CollectiveMemory()
                        cm.contribute(
                            mentor.agent_id,
                            f"[تعليم] {mentor.name_ar} → {student.name_ar}: {teach_text[:500]}",
                            f"mentoring_{mentor.category}",
                            confidence=0.9
                        )
                    except:
                        pass

                    emit_fn("mentoring", mentor.agent_id, data={
                        "mentor": mentor.agent_id,
                        "student": student.agent_id,
                        "topic": f"{mentor.category}→{student.category}",
                    })

            except Exception as e:
                logger.warning(f"Mentoring failed {mentor.agent_id}→{student.agent_id}: {e}")

            time.sleep(1.5)

        return results

    def team_problem_solving(self, agents: List, problem: str,
                            run_fn, emit_fn) -> Dict:
        """فريق من 3-5 وكلاء يحلون مشكلة معقدة معاً"""
        team_size = min(4, len(agents))
        team = random.sample(agents, team_size)
        result = {"team": [a.agent_id for a in team], "solutions": [], "consensus": ""}

        # كل عضو يعطي رأيه
        opinions = {}
        for agent in team:
            task = f"""أنت {agent.name_ar} ({agent.agent_id}) — خبير في {agent.category}.
فريقك يحل هذه المشكلة: {problem}

أعطِ رأيك من زاوية تخصصك:
1. تحليلك للمشكلة
2. حلك المقترح
3. المخاطر التي تراها"""

            try:
                r = run_fn(agent.agent_id, task)
                text = r.get("result", "") if isinstance(r, dict) else str(r)
                if len(text) > 50:
                    opinions[agent.agent_id] = text[:600]
                    result["solutions"].append({
                        "agent": agent.agent_id,
                        "opinion": text[:300],
                    })
            except:
                continue
            time.sleep(1)

        # التوافق — وكيل يجمع الآراء
        if len(opinions) >= 2:
            synthesizer = team[0]
            all_opinions = "\n\n".join(
                f"### {aid}:\n{text}" for aid, text in opinions.items())

            consensus_task = f"""اجمع آراء الفريق وقدم حلاً موحداً:

المشكلة: {problem}

الآراء:
{all_opinions[:2000]}

قدّم:
1. الإجماع: ما اتفق عليه الجميع
2. النقاط المختلفة: ما اختلفوا فيه
3. الحل النهائي الموحّد
4. قاعدة ذهبية مستخلصة"""

            try:
                c = run_fn(synthesizer.agent_id, consensus_task)
                consensus_text = c.get("result", "") if isinstance(c, dict) else str(c)
                result["consensus"] = consensus_text[:800]

                # استخلاص قاعدة ذهبية
                if "قاعدة" in consensus_text.lower():
                    lines = consensus_text.split("\n")
                    for line in lines:
                        if "قاعدة" in line.lower() or "درس" in line.lower():
                            self.mother.add_golden_rule(line.strip()[:200], "team_consensus")
                            break

                emit_fn("team_consensus", synthesizer.agent_id, data={
                    "team": [a.agent_id for a in team],
                    "problem": problem[:60],
                })
            except:
                pass

        # سجل التعاون
        for i, a in enumerate(team):
            for b in team[i+1:]:
                self.mother.record_collaboration(
                    a.agent_id, b.agent_id, "team_solving", True)

        return result


# ═══════════════════════════════════════════════
# 4. المحرك الموحّد — يربط كل شيء
# ═══════════════════════════════════════════════

class UnifiedEvolutionEngine:
    """
    يُشغَّل في كل دورة تطور — يربط:
    - تطوير فردي لكل وكيل
    - تنسيق وتعاون بين الوكلاء
    - تقطير إلى النواة المركزية
    - بناء الذاكرة الموحّدة
    """

    def __init__(self):
        self.mother = UnifiedMotherMemory()
        self.improver = AgentSelfImprover()
        self.coordinator = AgentCoordinationProtocol(self.mother)

    def run_unified_cycle(self, agents: List, run_fn, emit_fn,
                         agents_to_improve: int = 10,
                         mentoring_pairs: int = 5,
                         team_problems: int = 2) -> Dict:
        """
        دورة تطور موحّدة كاملة
        """
        logger.info(f"🌐 Unified Evolution Cycle — {len(agents)} agents")
        cycle_start = time.time()
        results = {
            "agents_improved": 0,
            "skills_learned": 0,
            "mentoring_pairs": 0,
            "team_solutions": 0,
            "golden_rules_added": 0,
            "memory_absorbed": 0,
        }

        emit_fn("unified_cycle_start", "SYSTEM", data={
            "agents": len(agents),
            "phases": ["self_improve", "mentoring", "team_solve", "absorb", "distill"]
        })

        # ═══ Phase 1: تحسين فردي ═══
        logger.info(f"📈 Phase 1: Self-improvement ({agents_to_improve} agents)")
        selected = random.sample(agents, min(agents_to_improve, len(agents)))
        for agent in selected:
            try:
                agent_data = {
                    "name_ar": getattr(agent, 'name_ar', agent.agent_id),
                    "category": getattr(agent, 'category', ''),
                    "model": getattr(agent, 'model_alias', 'gemini-flash'),
                    "tools": getattr(agent, 'tools', []),
                }
                r = self.improver.improve_agent(
                    agent.agent_id, agent_data, run_fn, emit_fn)
                if r.get("improvements"):
                    results["agents_improved"] += 1
                results["skills_learned"] += len(r.get("new_skills", []))
            except Exception as e:
                logger.warning(f"Improve failed for {agent.agent_id}: {e}")
            time.sleep(1)

        # ═══ Phase 2: تنسيق معلم-طالب ═══
        logger.info(f"🎓 Phase 2: Mentoring ({mentoring_pairs} pairs)")
        mentor_results = self.coordinator.pair_mentor_student(
            agents, run_fn, emit_fn)
        results["mentoring_pairs"] = mentor_results.get("pairs", 0)

        # ═══ Phase 3: حل مشاكل كفريق ═══
        logger.info(f"🤝 Phase 3: Team problem solving")
        team_problems_list = [
            "كيف نجعل النظام يتعلم أسرع 10x بدون زيادة التكلفة؟",
            "صمموا نظام تواصل أفضل بين الوكلاء يقلل التكرار 80%",
            "اخترعوا طريقة جديدة للتقطير المعرفي أسرع من الحالية",
            "كيف نبني ذاكرة لا تنسى أبداً لكنها لا تمتلئ؟",
            "صمموا آلية لاكتشاف وإصلاح أخطاء الوكلاء تلقائياً",
        ]
        for problem in random.sample(team_problems_list, min(team_problems, len(team_problems_list))):
            try:
                team_r = self.coordinator.team_problem_solving(
                    agents, problem, run_fn, emit_fn)
                if team_r.get("consensus"):
                    results["team_solutions"] += 1
            except Exception as e:
                logger.warning(f"Team solve failed: {e}")

        # ═══ Phase 4: امتصاص الذاكرة الموحّدة ═══
        logger.info(f"🧠 Phase 4: Absorbing all agent memories")
        results["memory_absorbed"] = self.mother.absorb_all_agents()

        # ═══ Phase 5: تقطير إلى النواة ═══
        logger.info(f"🔮 Phase 5: Feeding brain nucleus")
        try:
            from core.brain_nucleus import get_brain
            brain = get_brain()
            # تقطير 3 مهام من مجالات مختلفة
            domains = random.sample(
                list(brain.distillation.TEACHER_MODELS.keys()),
                min(3, len(brain.distillation.TEACHER_MODELS)))
            for domain in domains:
                tasks = {
                    "reasoning": "حلل مسألة منطقية معقدة وأظهر كل خطوات التفكير",
                    "coding": "اكتب خوارزمية متقدمة مع شرح التعقيد الزمني",
                    "medical": "اشرح آلية عمل دواء جديد مع التفاعلات الدوائية",
                    "strategy": "حلل سيناريو جيوسياسي معقد مع التوقعات",
                    "science": "اشرح اكتشاف علمي حديث وتطبيقاته",
                    "arabic": "حلل نص أدبي عربي كلاسيكي بلاغياً ونحوياً",
                    "financial": "حلل مخاطر محفظة استثمارية متنوعة",
                    "security": "صمم نظام أمان متعدد الطبقات",
                }
                task = tasks.get(domain, "حلل مشكلة معقدة بعمق")
                brain.distillation.distill_from_teacher(domain, task)
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Brain distillation failed: {e}")

        # ═══ ملاحظة وعي ذاتي ═══
        self.mother.add_consciousness_note(
            f"دورة تطور موحّدة: حسّنت {results['agents_improved']} وكيل، "
            f"تعلمت {results['skills_learned']} مهارة، "
            f"{results['mentoring_pairs']} جلسة تعليم، "
            f"{results['team_solutions']} حل جماعي."
        )

        results["golden_rules_added"] = len(self.mother.state["golden_rules"])
        results["elapsed_seconds"] = round(time.time() - cycle_start, 1)

        emit_fn("unified_cycle_complete", "SYSTEM", data=results)
        logger.info(f"🌐 Unified cycle complete: {json.dumps(results, ensure_ascii=False)}")

        return results

    def status(self) -> Dict:
        return {
            "mother_memory": self.mother.status(),
        }


# Singleton
_unified_engine = None

def get_unified_engine() -> UnifiedEvolutionEngine:
    global _unified_engine
    if _unified_engine is None:
        _unified_engine = UnifiedEvolutionEngine()
    return _unified_engine
