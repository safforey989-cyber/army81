"""
Army81 v5 — AutoSkill + MemSkill Integration Adapter
يربط نظامي AutoSkill (تعلم المهارات) و MemSkill (ذاكرة متطورة) بـ Army81

AutoSkill: يستخرج مهارات قابلة لإعادة الاستخدام من تجارب الوكلاء
MemSkill: يطوّر عمليات الذاكرة بناءً على الأداء الفعلي

كلاهما يغذّي الـ 81 وكيل بقدرات تتطور ذاتياً
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.skill_memory_adapter")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOSKILL_DIR = os.path.join(BASE_DIR, "knowledge", "autoskill")
MEMSKILL_DIR = os.path.join(BASE_DIR, "knowledge", "memskill")
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
SKILLBANK_DIR = os.path.join(WORKSPACE_DIR, "skillbank")

os.makedirs(SKILLBANK_DIR, exist_ok=True)


# ═══════════════════════════════════════════════
# AutoSkill Adapter — استخراج وتطوير المهارات
# ═══════════════════════════════════════════════

class AutoSkillAdapter:
    """
    يستخرج مهارات من تجارب الوكلاء (محادثات + نتائج)
    ويحفظها في SkillBank لإعادة استخدامها

    مستوحى من: AutoSkill (ECNU-ICALK) — Experience-Driven Lifelong Learning
    """

    def __init__(self):
        self.skillbank_path = os.path.join(SKILLBANK_DIR, "skills.json")
        self.skills = self._load_skills()

    def extract_skill_from_episode(self, agent_id: str, task: str,
                                    result: str, success: bool,
                                    rating: int = 5) -> Optional[Dict]:
        """
        يستخرج مهارة من حلقة تجربة واحدة
        مستوحى من AutoSkill ingest pipeline
        """
        if not success or rating < 6:
            return None  # فقط من التجارب الناجحة

        # حدد نوع المهمة
        task_type = self._classify_task_type(task)

        # ابنِ المهارة
        skill = {
            "id": f"skill_{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": self._generate_skill_name(task, task_type),
            "description": f"مهارة مستخرجة من تجربة {agent_id}: {task[:100]}",
            "task_type": task_type,
            "source_agent": agent_id,
            "instruction": self._extract_instruction(task, result),
            "tags": self._extract_tags(task, result),
            "version": "1.0.0",
            "quality_score": rating / 10.0,
            "usage_count": 0,
            "created_at": datetime.now().isoformat(),
            "evolved_from": None,
        }

        # تحقق من التكرار — ادمج إذا وُجدت مهارة مشابهة
        existing = self._find_similar_skill(skill)
        if existing:
            merged = self._merge_skills(existing, skill)
            self._save_skill(merged)
            logger.info(f"Merged skill: {merged['id']} (evolved from {existing['id']})")
            return merged
        else:
            self._save_skill(skill)
            logger.info(f"New skill extracted: {skill['id']} — {skill['name']}")
            return skill

    def get_skills_for_task(self, task: str, agent_id: str = None,
                            k: int = 3) -> List[Dict]:
        """
        يسترجع المهارات المناسبة لمهمة معينة
        مستوحى من AutoSkill retrieve-and-respond
        """
        task_type = self._classify_task_type(task)
        task_lower = task.lower()

        scored = []
        for skill in self.skills:
            score = 0.0

            # تطابق النوع
            if skill.get("task_type") == task_type:
                score += 0.4

            # تطابق الكلمات المفتاحية
            tags = skill.get("tags", [])
            for tag in tags:
                if tag.lower() in task_lower:
                    score += 0.2

            # جودة المهارة
            score += skill.get("quality_score", 0.5) * 0.2

            # أفضلية لمهارات من نفس الوكيل
            if agent_id and skill.get("source_agent") == agent_id:
                score += 0.1

            if score > 0.2:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:k]]

    def format_skills_for_prompt(self, skills: List[Dict]) -> str:
        """تنسيق المهارات لحقنها في system prompt"""
        if not skills:
            return ""

        lines = ["## مهارات مكتسبة من تجارب سابقة:"]
        for s in skills:
            lines.append(f"### {s['name']}")
            lines.append(f"النوع: {s.get('task_type', 'عام')}")
            lines.append(f"التعليمات: {s.get('instruction', '')[:300]}")
            lines.append("")

        return "\n".join(lines)

    def evolve_skills(self) -> Dict:
        """
        يطوّر المهارات — يدمج المتشابهة ويحسّن الأقل جودة
        يُشغَّل أسبوعياً
        """
        evolved = 0
        merged = 0

        # 1. ادمج المهارات المتشابهة
        seen_types = {}
        for skill in self.skills:
            key = (skill.get("task_type", ""), skill.get("source_agent", ""))
            if key in seen_types:
                self._merge_skills(seen_types[key], skill)
                merged += 1
            else:
                seen_types[key] = skill

        # 2. ارفع نسخة المهارات المستخدمة كثيراً
        for skill in self.skills:
            if skill.get("usage_count", 0) > 10:
                parts = skill.get("version", "1.0.0").split(".")
                parts[-1] = str(int(parts[-1]) + 1)
                skill["version"] = ".".join(parts)
                evolved += 1

        self._save_all_skills()
        return {"evolved": evolved, "merged": merged, "total": len(self.skills)}

    # ─── دوال داخلية ───────────────────────────

    def _classify_task_type(self, task: str) -> str:
        task_lower = task.lower()
        types = {
            "research": ["بحث", "دراسة", "ورقة", "research", "paper", "arxiv"],
            "analysis": ["حلل", "تحليل", "analyze", "analysis"],
            "code": ["كود", "برمج", "python", "code", "debug"],
            "writing": ["اكتب", "محتوى", "مقال", "write", "content"],
            "strategy": ["استراتيج", "خطة", "plan", "strategy"],
            "medical": ["طب", "علاج", "مرض", "medical", "health"],
            "financial": ["مال", "سوق", "استثمار", "finance", "market"],
        }
        for t, kws in types.items():
            if any(k in task_lower for k in kws):
                return t
        return "general"

    def _generate_skill_name(self, task: str, task_type: str) -> str:
        words = task[:50].replace(".", "").replace("،", "").split()
        name = "-".join(words[:4]).lower()
        return f"{task_type}-{name}"

    def _extract_instruction(self, task: str, result: str) -> str:
        """يستخرج التعليمات الجوهرية من التجربة"""
        return (
            f"عندما تُطلب مهمة مشابهة لـ: {task[:150]}\n"
            f"اتبع هذا النهج: {result[:300]}"
        )

    def _extract_tags(self, task: str, result: str) -> List[str]:
        tags = []
        combined = (task + " " + result).lower()
        all_tags = [
            "بحث", "تحليل", "كود", "استراتيجية", "طب", "مال",
            "أخبار", "ترجمة", "تعليم", "أمن", "قانون",
            "research", "analysis", "code", "strategy", "medical",
        ]
        for tag in all_tags:
            if tag in combined:
                tags.append(tag)
        return tags[:5]

    def _find_similar_skill(self, new_skill: Dict) -> Optional[Dict]:
        for skill in self.skills:
            if (skill.get("task_type") == new_skill.get("task_type") and
                skill.get("source_agent") == new_skill.get("source_agent")):
                # نفس النوع ونفس الوكيل → مشابهة
                return skill
        return None

    def _merge_skills(self, existing: Dict, new: Dict) -> Dict:
        """يدمج مهارتين"""
        existing["quality_score"] = max(
            existing.get("quality_score", 0.5),
            new.get("quality_score", 0.5)
        )
        existing["instruction"] = new.get("instruction", existing.get("instruction", ""))
        existing["evolved_from"] = existing.get("id")
        parts = existing.get("version", "1.0.0").split(".")
        parts[1] = str(int(parts[1]) + 1)
        existing["version"] = ".".join(parts)
        existing["tags"] = list(set(
            existing.get("tags", []) + new.get("tags", [])
        ))[:8]
        return existing

    def _save_skill(self, skill: Dict):
        # تحقق من التكرار قبل الإضافة
        for i, s in enumerate(self.skills):
            if s["id"] == skill["id"]:
                self.skills[i] = skill
                self._save_all_skills()
                return
        self.skills.append(skill)
        self._save_all_skills()

    def _save_all_skills(self):
        with open(self.skillbank_path, "w", encoding="utf-8") as f:
            json.dump(self.skills, f, ensure_ascii=False, indent=2)

    def _load_skills(self) -> List[Dict]:
        if os.path.exists(self.skillbank_path):
            try:
                with open(self.skillbank_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []


# ═══════════════════════════════════════════════
# MemSkill Adapter — عمليات ذاكرة متطورة
# ═══════════════════════════════════════════════

class MemSkillAdapter:
    """
    يطوّر عمليات الذاكرة (insert, update, delete, summarize)
    بناءً على الأداء الفعلي — يتعلم أي عمليات الذاكرة أنجح

    مستوحى من: MemSkill (ViktorAxelsen) — Learning and Evolving Memory Skills
    """

    def __init__(self):
        self.ops_path = os.path.join(WORKSPACE_DIR, "memory_operations.json")
        self.operations = self._load_operations()

    def record_memory_operation(self, agent_id: str, op_type: str,
                                 content: str, success: bool,
                                 reward: float = 0.5):
        """
        يسجل عملية ذاكرة ونتيجتها
        op_type: insert, update, delete, retrieve, summarize
        """
        op_key = f"{agent_id}_{op_type}"

        if op_key not in self.operations:
            self.operations[op_key] = {
                "agent_id": agent_id,
                "type": op_type,
                "usage_count": 0,
                "total_reward": 0.0,
                "avg_reward": 0.0,
                "recent_rewards": [],
                "last_used": None,
            }

        op = self.operations[op_key]
        op["usage_count"] += 1
        op["total_reward"] += reward
        op["avg_reward"] = op["total_reward"] / op["usage_count"]
        op["recent_rewards"].append(reward)
        op["recent_rewards"] = op["recent_rewards"][-20:]  # آخر 20
        op["last_used"] = datetime.now().isoformat()

        self._save_operations()

    def get_best_memory_strategy(self, agent_id: str) -> Dict:
        """
        يقترح أفضل استراتيجية ذاكرة لوكيل معين
        بناءً على تاريخ نجاح العمليات
        """
        agent_ops = {
            k: v for k, v in self.operations.items()
            if v["agent_id"] == agent_id
        }

        if not agent_ops:
            return {
                "strategy": "default",
                "insert_freq": "always",
                "summarize_freq": "weekly",
                "delete_threshold": 0.2,
            }

        # حلل الأداء
        best_ops = sorted(
            agent_ops.values(),
            key=lambda x: x["avg_reward"],
            reverse=True,
        )

        strategy = {
            "strategy": "adaptive",
            "best_operations": [
                {"type": op["type"], "avg_reward": round(op["avg_reward"], 2)}
                for op in best_ops[:3]
            ],
            "total_operations": sum(op["usage_count"] for op in agent_ops.values()),
        }

        # هل يحتاج الوكيل مزيداً من الـ retrieve أم الـ summarize؟
        retrieve_reward = next(
            (op["avg_reward"] for op in agent_ops.values() if op["type"] == "retrieve"),
            0.5,
        )
        summarize_reward = next(
            (op["avg_reward"] for op in agent_ops.values() if op["type"] == "summarize"),
            0.5,
        )

        if retrieve_reward > 0.7:
            strategy["recommendation"] = "الوكيل يستفيد كثيراً من استرجاع الذاكرة — زد حجم السياق"
        elif summarize_reward > 0.7:
            strategy["recommendation"] = "الوكيل يستفيد من الملخصات — اضغط الذاكرة أكثر"
        else:
            strategy["recommendation"] = "الوكيل يحتاج تحسين استخدام الذاكرة"

        return strategy

    def evolve_operations(self) -> Dict:
        """
        يطوّر عمليات الذاكرة — يعزز الناجحة ويضعف الفاشلة
        يُشغَّل أسبوعياً
        """
        evolved = 0
        for key, op in self.operations.items():
            recent = op.get("recent_rewards", [])
            if len(recent) >= 5:
                recent_avg = sum(recent[-5:]) / 5
                if recent_avg < 0.3:
                    # عملية ضعيفة — علّمها
                    op["needs_improvement"] = True
                    evolved += 1
                elif recent_avg > 0.8:
                    op["needs_improvement"] = False
                    op["is_proven"] = True
                    evolved += 1

        self._save_operations()
        return {"evolved": evolved, "total_operations": len(self.operations)}

    def get_stats(self) -> Dict:
        """إحصائيات عمليات الذاكرة"""
        if not self.operations:
            return {"total_ops": 0, "agents": 0}

        agents = set(op["agent_id"] for op in self.operations.values())
        by_type = {}
        for op in self.operations.values():
            t = op["type"]
            by_type.setdefault(t, {"count": 0, "avg_reward": 0})
            by_type[t]["count"] += op["usage_count"]
            by_type[t]["avg_reward"] = round(op["avg_reward"], 2)

        return {
            "total_ops": len(self.operations),
            "agents_tracked": len(agents),
            "by_type": by_type,
        }

    def _load_operations(self) -> Dict:
        if os.path.exists(self.ops_path):
            try:
                with open(self.ops_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_operations(self):
        with open(self.ops_path, "w", encoding="utf-8") as f:
            json.dump(self.operations, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
# Unified Adapter — يجمع الاثنين
# ═══════════════════════════════════════════════

class SkillMemoryAdapter:
    """
    واجهة موحّدة تجمع AutoSkill + MemSkill
    تُستخدم من BaseAgent مباشرة
    """

    def __init__(self):
        self.autoskill = AutoSkillAdapter()
        self.memskill = MemSkillAdapter()

    def after_task(self, agent_id: str, task: str, result: str,
                   success: bool, rating: int = 5):
        """يُستدعى بعد كل مهمة — يستخرج المهارات ويسجل عمليات الذاكرة"""
        # AutoSkill: استخرج مهارة إذا نجحت
        if success and rating >= 6:
            self.autoskill.extract_skill_from_episode(
                agent_id, task, result, success, rating
            )

        # MemSkill: سجل عملية الذاكرة
        reward = rating / 10.0
        self.memskill.record_memory_operation(
            agent_id, "insert" if success else "noop",
            task[:200], success, reward
        )

    def before_task(self, agent_id: str, task: str) -> str:
        """يُستدعى قبل كل مهمة — يحقن المهارات المناسبة"""
        # AutoSkill: احصل على مهارات مناسبة
        skills = self.autoskill.get_skills_for_task(task, agent_id, k=2)
        skill_text = self.autoskill.format_skills_for_prompt(skills)

        # MemSkill: سجل عملية retrieve
        self.memskill.record_memory_operation(
            agent_id, "retrieve", task[:100], True, 0.5
        )

        return skill_text

    def weekly_evolution(self) -> Dict:
        """تطوير أسبوعي لكل من المهارات وعمليات الذاكرة"""
        skill_result = self.autoskill.evolve_skills()
        mem_result = self.memskill.evolve_operations()
        return {
            "autoskill": skill_result,
            "memskill": mem_result,
            "timestamp": datetime.now().isoformat(),
        }

    def stats(self) -> Dict:
        return {
            "skills": {
                "total": len(self.autoskill.skills),
                "skillbank_path": self.autoskill.skillbank_path,
            },
            "memory_ops": self.memskill.get_stats(),
        }


# ── Singleton ────────────────────────────────
_instance: Optional[SkillMemoryAdapter] = None


def get_skill_memory_adapter() -> SkillMemoryAdapter:
    global _instance
    if _instance is None:
        _instance = SkillMemoryAdapter()
    return _instance
