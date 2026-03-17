"""
Army81 - Agent-to-Agent Communication Protocol (A2A)
بروتوكول التواصل بين الوكلاء — يسمح لكل وكيل بإرسال رسائل/مهام لوكلاء آخرين
"""
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("army81.a2a")


@dataclass
class A2AMessage:
    """رسالة بين وكيلين"""
    from_agent: str
    to_agent: str
    content: str
    msg_type: str = "task"  # "task" | "response" | "info" | "request_help"
    priority: int = 5       # 1 (أعلى) → 10 (أدنى)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content[:500],
            "type": self.msg_type,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class A2AProtocol:
    """
    بروتوكول التواصل بين الوكلاء
    يدير قوائم الرسائل والتوصيل بين الوكلاء
    """

    def __init__(self, router=None):
        self.router = router
        self.inbox: Dict[str, List[A2AMessage]] = {}  # agent_id → messages
        self.history: List[Dict] = []
        self.stats = {
            "total_messages": 0,
            "total_delegations": 0,
            "by_type": {},
        }

    def set_router(self, router):
        """ربط الروتر (يُستدعى بعد تحميل الوكلاء)"""
        self.router = router

    def send(self, from_agent: str, to_agent: str, content: str,
             msg_type: str = "task", priority: int = 5,
             metadata: Dict = None) -> Dict:
        """
        إرسال رسالة من وكيل لآخر
        إذا كان النوع 'task' يُنفَّذ فوراً عبر الروتر
        """
        msg = A2AMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            msg_type=msg_type,
            priority=priority,
            metadata=metadata or {},
        )

        # أضف للصندوق الوارد
        if to_agent not in self.inbox:
            self.inbox[to_agent] = []
        self.inbox[to_agent].append(msg)

        # تحديث الإحصائيات
        self.stats["total_messages"] += 1
        self.stats["by_type"][msg_type] = self.stats["by_type"].get(msg_type, 0) + 1

        # سجّل
        self.history.append(msg.to_dict())
        if len(self.history) > 500:
            self.history = self.history[-500:]

        logger.info(f"A2A: {from_agent} → {to_agent} ({msg_type})")

        # إذا كان مهمة وفيه روتر → نفّذها
        if msg_type == "task" and self.router:
            return self._execute_task(msg)

        return {"status": "delivered", "message": msg.to_dict()}

    def _execute_task(self, msg: A2AMessage) -> Dict:
        """تنفيذ مهمة مُفوَّضة"""
        if not self.router or msg.to_agent not in self.router.agents:
            return {
                "status": "error",
                "result": f"الوكيل {msg.to_agent} غير موجود",
            }

        self.stats["total_delegations"] += 1

        context = {
            "delegated_by": msg.from_agent,
            "priority": msg.priority,
            **msg.metadata,
        }

        result = self.router.route(
            task=msg.content,
            agent_id=msg.to_agent,
            context=context,
        )

        # أرسل الرد للوكيل الأصلي
        response = A2AMessage(
            from_agent=msg.to_agent,
            to_agent=msg.from_agent,
            content=str(result.get("result", result)),
            msg_type="response",
            metadata={"original_task": msg.content[:100]},
        )
        if msg.from_agent not in self.inbox:
            self.inbox[msg.from_agent] = []
        self.inbox[msg.from_agent].append(response)

        return result

    def delegate(self, from_agent: str, to_agent: str, task: str,
                 context: Dict = None) -> Dict:
        """
        تفويض مهمة من وكيل لآخر (اختصار لـ send مع type=task)
        """
        return self.send(
            from_agent=from_agent,
            to_agent=to_agent,
            content=task,
            msg_type="task",
            metadata=context or {},
        )

    def broadcast_to_category(self, from_agent: str, category: str,
                               content: str, msg_type: str = "info") -> List[Dict]:
        """إرسال رسالة لكل وكلاء فئة معينة"""
        if not self.router:
            return []

        results = []
        for agent_id, agent in self.router.agents.items():
            if agent.category == category and agent_id != from_agent:
                r = self.send(from_agent, agent_id, content, msg_type)
                results.append(r)

        return results

    def get_inbox(self, agent_id: str, unread_only: bool = False) -> List[Dict]:
        """قراءة صندوق وارد وكيل"""
        messages = self.inbox.get(agent_id, [])
        return [m.to_dict() for m in messages]

    def clear_inbox(self, agent_id: str):
        """مسح صندوق وارد وكيل"""
        self.inbox[agent_id] = []

    def chain(self, from_agent: str, agent_chain: List[str], task: str,
              context: Dict = None) -> Dict:
        """
        سلسلة تفويض: A → B → C
        نتيجة كل وكيل تذهب للتالي
        """
        current_task = task
        context = context or {}
        results = []

        for to_agent in agent_chain:
            context["chain_position"] = len(results) + 1
            context["chain_total"] = len(agent_chain)

            r = self.delegate(from_agent, to_agent, current_task, context)
            results.append(r)

            if isinstance(r, dict) and r.get("status") == "error":
                return {
                    "status": "chain_error",
                    "failed_at": to_agent,
                    "step": len(results),
                    "results": results,
                }

            # نتيجة هذا الوكيل تصبح مهمة التالي
            result_text = r.get("result", str(r)) if isinstance(r, dict) else str(r)
            current_task = f"بناءً على التحليل السابق:\n{result_text}\n\nالمهمة الأصلية: {task}"
            from_agent = to_agent  # التالي يُفوَّض من الأخير

        return {
            "status": "success",
            "steps": len(results),
            "final": results[-1] if results else None,
            "all_results": results,
        }

    def status(self) -> Dict:
        """حالة بروتوكول A2A"""
        return {
            "stats": self.stats,
            "active_inboxes": len(self.inbox),
            "pending_messages": sum(len(m) for m in self.inbox.values()),
            "recent": self.history[-10:] if self.history else [],
        }
