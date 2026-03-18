"""
Army81 — Swarm Memory System
ذاكرة السرب: ذاكرة فردية لكل وكيل + ذاكرة نواة مشتركة
تُبنى أثناء جلسات التعارف والسرب
"""
import json
import os
import sqlite3
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.swarm_memory")

WORKSPACE = Path("workspace")
SWARM_DB = WORKSPACE / "swarm_memory.db"
AGENT_MEMORIES_DIR = WORKSPACE / "agent_memories"
CORE_MEMORY_FILE = WORKSPACE / "core_memory.json"


class AgentPersonalMemory:
    """
    ذاكرة شخصية لوكيل واحد — معزولة عن الآخرين
    يتذكر: من تعرّف عليهم، ما تعلّمه، قراراته، تعاوناته
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memory_file = AGENT_MEMORIES_DIR / f"{agent_id}.json"
        AGENT_MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "agent_id": self.agent_id,
            "created_at": datetime.now().isoformat(),
            "known_agents": {},       # وكلاء تعرّفت عليهم
            "skills_learned": [],     # مهارات اكتسبتها
            "collaborations": [],     # تعاونات سابقة
            "decisions": [],          # قرارات اتخذتها
            "insights": [],           # رؤى واستنتاجات
            "strengths": [],          # نقاط قوة اكتشفتها
            "weaknesses": [],         # نقاط ضعف يجب تحسينها
            "interaction_count": 0,
            "last_active": None,
        }

    def _save(self):
        self.memory_file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def remember_agent(self, other_id: str, other_name: str,
                       specialty: str, interaction_summary: str):
        """تذكّر وكيل آخر"""
        if other_id not in self.data["known_agents"]:
            self.data["known_agents"][other_id] = {
                "name": other_name,
                "specialty": specialty,
                "first_met": datetime.now().isoformat(),
                "interactions": [],
                "trust_score": 0.5,
                "collaboration_count": 0,
            }

        agent_memory = self.data["known_agents"][other_id]
        agent_memory["interactions"].append({
            "summary": interaction_summary[:300],
            "timestamp": datetime.now().isoformat(),
        })
        # احتفظ بآخر 20 تفاعل فقط
        agent_memory["interactions"] = agent_memory["interactions"][-20:]
        agent_memory["collaboration_count"] += 1

        self.data["interaction_count"] += 1
        self.data["last_active"] = datetime.now().isoformat()
        self._save()

    def learn_skill(self, skill: str, source: str = ""):
        """تعلّم مهارة جديدة"""
        self.data["skills_learned"].append({
            "skill": skill[:200],
            "source": source,
            "learned_at": datetime.now().isoformat(),
        })
        self.data["skills_learned"] = self.data["skills_learned"][-50:]
        self._save()

    def record_collaboration(self, partners: List[str], task: str,
                              result: str, success: bool):
        """سجّل تعاون"""
        self.data["collaborations"].append({
            "partners": partners,
            "task": task[:200],
            "result": result[:300],
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })
        self.data["collaborations"] = self.data["collaborations"][-30:]

        # حدّث trust للشركاء
        for p in partners:
            if p in self.data["known_agents"]:
                delta = 0.05 if success else -0.02
                score = self.data["known_agents"][p].get("trust_score", 0.5)
                self.data["known_agents"][p]["trust_score"] = max(0, min(1, score + delta))

        self._save()

    def record_decision(self, decision: str, reasoning: str):
        """سجّل قرار"""
        self.data["decisions"].append({
            "decision": decision[:200],
            "reasoning": reasoning[:300],
            "timestamp": datetime.now().isoformat(),
        })
        self.data["decisions"] = self.data["decisions"][-20:]
        self._save()

    def add_insight(self, insight: str, topic: str = ""):
        """أضف رؤية أو استنتاج"""
        self.data["insights"].append({
            "insight": insight[:300],
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
        })
        self.data["insights"] = self.data["insights"][-30:]
        self._save()

    def get_known_agent(self, other_id: str) -> Optional[Dict]:
        """هل أعرف هذا الوكيل؟"""
        return self.data["known_agents"].get(other_id)

    def get_best_collaborators(self, k: int = 5) -> List[Dict]:
        """أفضل شركاء تعاون"""
        agents = []
        for aid, info in self.data["known_agents"].items():
            agents.append({
                "agent_id": aid,
                "name": info["name"],
                "trust": info.get("trust_score", 0.5),
                "collaborations": info.get("collaboration_count", 0),
            })
        return sorted(agents, key=lambda x: x["trust"], reverse=True)[:k]

    def inject_personal_context(self, partner_id: str = "") -> str:
        """حقن سياق شخصي قبل المهمة"""
        ctx = ""

        # من أعرف
        known_count = len(self.data["known_agents"])
        if known_count > 0:
            ctx += f"## ذاكرتي الشخصية:\nأعرف {known_count} وكيل.\n"

        # هل أعرف الشريك الحالي؟
        if partner_id and partner_id in self.data["known_agents"]:
            partner = self.data["known_agents"][partner_id]
            ctx += f"أعرف {partner['name']} — تعاونا {partner['collaboration_count']} مرة. "
            ctx += f"ثقتي به: {partner.get('trust_score', 0.5):.0%}\n"
            if partner["interactions"]:
                last = partner["interactions"][-1]
                ctx += f"آخر تفاعل: {last['summary'][:100]}\n"

        # آخر رؤى
        if self.data["insights"]:
            ctx += "\n## رؤاي الأخيرة:\n"
            for ins in self.data["insights"][-3:]:
                ctx += f"- {ins['insight'][:100]}\n"

        return ctx[:1000]

    def get_stats(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "known_agents": len(self.data["known_agents"]),
            "skills": len(self.data["skills_learned"]),
            "collaborations": len(self.data["collaborations"]),
            "decisions": len(self.data["decisions"]),
            "insights": len(self.data["insights"]),
            "interactions": self.data["interaction_count"],
        }


class CoreMemory:
    """
    ذاكرة النواة — مشتركة بين كل الـ 81 وكيل
    القرارات الجماعية، المعرفة المشتركة، حالة النظام
    """

    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        WORKSPACE.mkdir(exist_ok=True)
        if CORE_MEMORY_FILE.exists():
            try:
                return json.loads(CORE_MEMORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "created_at": datetime.now().isoformat(),
            "collective_decisions": [],    # قرارات جماعية
            "shared_knowledge": [],        # معرفة مشتركة
            "system_rules": [],            # قواعد اتفق عليها الوكلاء
            "active_goals": [],            # أهداف حالية
            "completed_goals": [],         # أهداف مكتملة
            "pending_approvals": [],       # طلبات موافقة للمالك
            "network_state": {
                "total_interactions": 0,
                "total_collaborations": 0,
                "strongest_bonds": [],     # أقوى العلاقات
            },
            "evolution_log": [],           # سجل التطور
        }

    def _save(self):
        CORE_MEMORY_FILE.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def add_collective_decision(self, decision: str, participants: List[str],
                                  reasoning: str):
        """قرار جماعي"""
        self.data["collective_decisions"].append({
            "decision": decision[:300],
            "participants": participants,
            "reasoning": reasoning[:300],
            "timestamp": datetime.now().isoformat(),
            "status": "active",
        })
        self.data["collective_decisions"] = self.data["collective_decisions"][-50:]
        self._save()

    def add_shared_knowledge(self, knowledge: str, contributor: str,
                               topic: str, confidence: float = 0.8):
        """معرفة مشتركة"""
        self.data["shared_knowledge"].append({
            "knowledge": knowledge[:500],
            "contributor": contributor,
            "topic": topic,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        })
        self.data["shared_knowledge"] = self.data["shared_knowledge"][-100:]
        self._save()

    def add_system_rule(self, rule: str, proposed_by: str, voted_by: List[str]):
        """قاعدة اتفق عليها الوكلاء"""
        self.data["system_rules"].append({
            "rule": rule[:200],
            "proposed_by": proposed_by,
            "voted_by": voted_by,
            "votes": len(voted_by),
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def add_goal(self, goal: str, assigned_to: List[str]):
        """هدف جديد"""
        self.data["active_goals"].append({
            "goal": goal[:200],
            "assigned_to": assigned_to,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        })
        self._save()

    def request_approval(self, title: str, description: str,
                          requested_by: str):
        """طلب موافقة من المالك"""
        req = {
            "id": hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()[:10],
            "title": title[:200],
            "description": description[:500],
            "requested_by": requested_by,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }
        self.data["pending_approvals"].append(req)
        self._save()
        return req

    def update_network_stats(self, interaction_count: int = 0,
                               collab_count: int = 0):
        """تحديث إحصائيات الشبكة"""
        self.data["network_state"]["total_interactions"] += interaction_count
        self.data["network_state"]["total_collaborations"] += collab_count
        self._save()

    def get_context_for_agent(self, agent_id: str) -> str:
        """سياق النواة لوكيل"""
        ctx = "## ذاكرة النواة المشتركة:\n"

        # أهداف نشطة
        active = [g for g in self.data["active_goals"] if g["status"] == "active"]
        if active:
            ctx += f"أهداف نشطة: {len(active)}\n"
            for g in active[-3:]:
                ctx += f"- {g['goal'][:80]}\n"

        # قرارات حديثة
        if self.data["collective_decisions"]:
            ctx += f"\nآخر قرار جماعي: {self.data['collective_decisions'][-1]['decision'][:100]}\n"

        # قواعد النظام
        if self.data["system_rules"]:
            ctx += f"\nقواعد متفق عليها: {len(self.data['system_rules'])}\n"

        # إحصائيات
        ns = self.data["network_state"]
        ctx += f"\nالشبكة: {ns['total_interactions']} تفاعل، {ns['total_collaborations']} تعاون\n"

        return ctx[:800]

    def get_stats(self) -> Dict:
        return {
            "decisions": len(self.data["collective_decisions"]),
            "shared_knowledge": len(self.data["shared_knowledge"]),
            "rules": len(self.data["system_rules"]),
            "active_goals": len([g for g in self.data["active_goals"] if g["status"] == "active"]),
            "pending_approvals": len([a for a in self.data["pending_approvals"] if a["status"] == "pending"]),
            "total_interactions": self.data["network_state"]["total_interactions"],
        }


class SwarmMemoryManager:
    """
    مدير ذاكرة السرب — يربط الذاكرة الفردية بالنواة
    يُستخدم أثناء جلسات السرب
    """

    _instance = None

    @classmethod
    def get_instance(cls) -> "SwarmMemoryManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.core = CoreMemory()
        self._agent_memories: Dict[str, AgentPersonalMemory] = {}
        logger.info("SwarmMemoryManager initialized")

    def get_agent_memory(self, agent_id: str) -> AgentPersonalMemory:
        """يجلب ذاكرة وكيل (أو ينشئها)"""
        if agent_id not in self._agent_memories:
            self._agent_memories[agent_id] = AgentPersonalMemory(agent_id)
        return self._agent_memories[agent_id]

    def record_introduction(self, agent_a: str, name_a: str, spec_a: str,
                             agent_b: str, name_b: str, spec_b: str,
                             interaction_summary: str):
        """تسجيل تعارف بين وكيلين"""
        mem_a = self.get_agent_memory(agent_a)
        mem_b = self.get_agent_memory(agent_b)

        mem_a.remember_agent(agent_b, name_b, spec_b, interaction_summary)
        mem_b.remember_agent(agent_a, name_a, spec_a, f"تعرّف عليّ {name_a}")

        self.core.update_network_stats(interaction_count=1)
        logger.info(f"🤝 تعارف: {agent_a} ↔ {agent_b}")

    def record_collaboration(self, leader_id: str, team_ids: List[str],
                               task: str, result: str, success: bool):
        """تسجيل تعاون"""
        for aid in [leader_id] + team_ids:
            mem = self.get_agent_memory(aid)
            partners = [p for p in [leader_id] + team_ids if p != aid]
            mem.record_collaboration(partners, task, result, success)

        self.core.update_network_stats(collab_count=1)

        # إذا نجح → أضف للمعرفة المشتركة
        if success and len(result) > 50:
            self.core.add_shared_knowledge(
                result[:500], leader_id,
                topic=task[:50], confidence=0.8
            )

    def record_insight(self, agent_id: str, insight: str, topic: str = ""):
        """تسجيل رؤية"""
        mem = self.get_agent_memory(agent_id)
        mem.add_insight(insight, topic)
        # رؤى مهمة تذهب للنواة أيضاً
        if len(insight) > 50:
            self.core.add_shared_knowledge(insight, agent_id, topic, 0.7)

    def record_collective_decision(self, decision: str, participants: List[str],
                                     reasoning: str):
        """قرار جماعي"""
        self.core.add_collective_decision(decision, participants, reasoning)
        for aid in participants:
            mem = self.get_agent_memory(aid)
            mem.record_decision(decision, reasoning)

    def inject_context(self, agent_id: str, partner_id: str = "") -> str:
        """حقن سياق كامل (شخصي + نواة)"""
        ctx = ""
        mem = self.get_agent_memory(agent_id)
        ctx += mem.inject_personal_context(partner_id)
        ctx += "\n" + self.core.get_context_for_agent(agent_id)
        return ctx[:1500]

    def get_full_stats(self) -> Dict:
        """إحصائيات شاملة"""
        agent_stats = {}
        for aid, mem in self._agent_memories.items():
            agent_stats[aid] = mem.get_stats()

        # أيضاً من الملفات
        if AGENT_MEMORIES_DIR.exists():
            for f in AGENT_MEMORIES_DIR.glob("*.json"):
                aid = f.stem
                if aid not in agent_stats:
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        agent_stats[aid] = {
                            "known_agents": len(data.get("known_agents", {})),
                            "interactions": data.get("interaction_count", 0),
                        }
                    except Exception:
                        pass

        return {
            "core": self.core.get_stats(),
            "agents_with_memory": len(agent_stats),
            "total_interactions": sum(a.get("interactions", 0) for a in agent_stats.values()),
            "agent_stats": agent_stats,
        }
