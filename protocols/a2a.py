"""
Army81 Agent-to-Agent Protocol
بروتوكول التواصل المباشر بين الوكلاء
مستوحى من Google A2A Protocol
"""
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("army81.a2a")


class MessageType(str, Enum):
    REQUEST = "request"       # طلب مساعدة
    RESPONSE = "response"     # رد على طلب
    BROADCAST = "broadcast"   # رسالة للجميع
    NOTIFY = "notify"         # إشعار
    DELEGATE = "delegate"     # تفويض مهمة
    RESULT = "result"         # نتيجة نهائية


@dataclass
class A2AMessage:
    """رسالة بين وكيلين"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: MessageType = MessageType.REQUEST
    from_agent: str = ""
    to_agent: str = ""       # فارغ = broadcast
    content: str = ""
    context: Dict = field(default_factory=dict)
    reply_to: str = ""       # ID الرسالة المردود عليها
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 5        # 1=أعلى, 10=أدنى
    ttl: int = 300           # ثوانٍ قبل انتهاء الصلاحية


class MessageBus:
    """
    ناقل الرسائل المركزي
    يدير كل التواصل بين الوكلاء
    """

    def __init__(self):
        self.queues: Dict[str, List[A2AMessage]] = {}  # agent_id -> messages
        self.handlers: Dict[str, Callable] = {}         # agent_id -> handler
        self.message_log: List[A2AMessage] = []
        self.stats = {
            "total_messages": 0,
            "by_type": {},
        }

    def register(self, agent_id: str, handler: Callable = None):
        """تسجيل وكيل في ناقل الرسائل"""
        self.queues[agent_id] = []
        if handler:
            self.handlers[agent_id] = handler
        logger.info(f"Agent {agent_id} registered on message bus")

    def send(self, message: A2AMessage) -> str:
        """إرسال رسالة"""
        self.message_log.append(message)
        self.stats["total_messages"] += 1
        self.stats["by_type"][message.type.value] = self.stats["by_type"].get(message.type.value, 0) + 1

        if message.to_agent:
            # رسالة مباشرة
            if message.to_agent in self.queues:
                self.queues[message.to_agent].append(message)
                # إذا هناك handler مسجل، نفذه فوراً
                if message.to_agent in self.handlers:
                    try:
                        self.handlers[message.to_agent](message)
                    except Exception as e:
                        logger.error(f"Handler error for {message.to_agent}: {e}")
            else:
                logger.warning(f"Agent {message.to_agent} not registered")
        else:
            # broadcast
            for agent_id, queue in self.queues.items():
                if agent_id != message.from_agent:
                    queue.append(message)

        return message.id

    def receive(self, agent_id: str, max_messages: int = 10) -> List[A2AMessage]:
        """استلام الرسائل المعلقة"""
        if agent_id not in self.queues:
            return []

        now = time.time()
        # تصفية الرسائل المنتهية الصلاحية
        valid = []
        for msg in self.queues[agent_id]:
            msg_time = datetime.fromisoformat(msg.timestamp).timestamp()
            if now - msg_time < msg.ttl:
                valid.append(msg)

        # إرجاع الأولوية الأعلى أولاً
        valid.sort(key=lambda m: m.priority)
        result = valid[:max_messages]

        # إزالة الرسائل المقروءة
        self.queues[agent_id] = valid[max_messages:]

        return result

    def request_help(self, from_agent: str, to_agent: str, task: str, context: Dict = None) -> str:
        """طلب مساعدة من وكيل آخر"""
        msg = A2AMessage(
            type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            content=task,
            context=context or {},
            priority=3,
        )
        return self.send(msg)

    def delegate_task(self, from_agent: str, to_agent: str, task: str, context: Dict = None) -> str:
        """تفويض مهمة لوكيل آخر"""
        msg = A2AMessage(
            type=MessageType.DELEGATE,
            from_agent=from_agent,
            to_agent=to_agent,
            content=task,
            context=context or {},
            priority=2,
        )
        return self.send(msg)

    def notify_all(self, from_agent: str, content: str, priority: int = 5) -> str:
        """إشعار كل الوكلاء"""
        msg = A2AMessage(
            type=MessageType.BROADCAST,
            from_agent=from_agent,
            content=content,
            priority=priority,
        )
        return self.send(msg)

    def get_stats(self) -> Dict:
        """إحصائيات ناقل الرسائل"""
        return {
            "registered_agents": len(self.queues),
            "pending_messages": {aid: len(q) for aid, q in self.queues.items() if q},
            "total_messages": self.stats["total_messages"],
            "by_type": self.stats["by_type"],
        }


class CollaborationManager:
    """
    مدير التعاون بين الوكلاء
    ينسق المهام المعقدة التي تحتاج عدة وكلاء
    """

    def __init__(self, message_bus: MessageBus, router=None):
        self.bus = message_bus
        self.router = router
        self.active_collaborations: Dict[str, Dict] = {}

    def start_collaboration(self, task: str, participants: List[str],
                           coordinator: str = None) -> str:
        """بدء تعاون بين عدة وكلاء"""
        collab_id = str(uuid.uuid4())[:8]
        coordinator = coordinator or participants[0]

        self.active_collaborations[collab_id] = {
            "id": collab_id,
            "task": task,
            "participants": participants,
            "coordinator": coordinator,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "results": {},
        }

        # إشعار المشاركين
        for agent_id in participants:
            self.bus.send(A2AMessage(
                type=MessageType.NOTIFY,
                from_agent=coordinator,
                to_agent=agent_id,
                content=f"تم تعيينك في تعاون جديد ({collab_id}): {task}",
                context={"collaboration_id": collab_id, "role": "participant"},
                priority=2,
            ))

        logger.info(f"Collaboration {collab_id} started with {len(participants)} agents")
        return collab_id

    def submit_result(self, collab_id: str, agent_id: str, result: Any):
        """تقديم نتيجة من وكيل مشارك"""
        if collab_id in self.active_collaborations:
            self.active_collaborations[collab_id]["results"][agent_id] = {
                "result": result,
                "submitted_at": datetime.now().isoformat(),
            }

            # التحقق من اكتمال كل النتائج
            collab = self.active_collaborations[collab_id]
            if len(collab["results"]) == len(collab["participants"]):
                collab["status"] = "completed"
                collab["completed_at"] = datetime.now().isoformat()
                logger.info(f"Collaboration {collab_id} completed")

    def get_collaboration(self, collab_id: str) -> Optional[Dict]:
        return self.active_collaborations.get(collab_id)

    def list_active(self) -> List[Dict]:
        return [c for c in self.active_collaborations.values() if c["status"] == "active"]
