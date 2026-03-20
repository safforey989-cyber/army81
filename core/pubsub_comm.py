"""
Army81 - Pub/Sub Agent Communication
تواصل بين الوكلاء عبر Google Cloud Pub/Sub
المرحلة 3: البنية التحتية السحابية
مع fallback محلي بقائمة انتظار في الذاكرة
"""
import os
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from queue import Queue

logger = logging.getLogger("army81.pubsub")

# ── Google Cloud Pub/Sub (lazy) ──────────────────────────────
_publisher = None
_subscriber = None
_PUBSUB_AVAILABLE = False


def _init_pubsub():
    """تهيئة Pub/Sub client"""
    global _publisher, _subscriber, _PUBSUB_AVAILABLE

    project_id = os.getenv("GCP_PROJECT_ID", "")
    if not project_id:
        logger.info("GCP_PROJECT_ID not set — using local message queue")
        return False

    try:
        from google.cloud import pubsub_v1
        _publisher = pubsub_v1.PublisherClient()
        _subscriber = pubsub_v1.SubscriberClient()
        _PUBSUB_AVAILABLE = True
        logger.info(f"Pub/Sub connected to project: {project_id}")
        return True
    except ImportError:
        logger.warning("google-cloud-pubsub not installed. pip install google-cloud-pubsub")
        return False
    except Exception as e:
        logger.error(f"Pub/Sub init failed: {e}")
        return False


class PubSubComm:
    """
    نظام تواصل بين الوكلاء
    يدعم:
    - النشر على topics (agent-tasks, agent-results, agent-signals)
    - الاشتراك واستلام الرسائل
    - البث لفئة كاملة
    - Local fallback بدون GCP
    """

    # Topics الأساسية
    TOPIC_TASKS = "army81-agent-tasks"
    TOPIC_RESULTS = "army81-agent-results"
    TOPIC_SIGNALS = "army81-agent-signals"
    TOPIC_BROADCAST = "army81-broadcast"

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "")
        self.is_cloud = _init_pubsub() if self.project_id else False

        # Local message queues (fallback)
        self._local_queues: Dict[str, Queue] = defaultdict(Queue)
        self._local_subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self._message_history: List[Dict] = []
        self._lock = threading.Lock()

        # إحصائيات
        self.stats = {
            "messages_published": 0,
            "messages_received": 0,
            "topics_active": set(),
            "started_at": datetime.now().isoformat(),
        }

    def publish(self, topic: str, message: Dict, agent_id: str = "") -> str:
        """
        نشر رسالة على topic
        message يجب أن يحتوي على: type, content, from_agent
        """
        msg = {
            "type": message.get("type", "info"),
            "content": message.get("content", ""),
            "from_agent": agent_id or message.get("from_agent", "system"),
            "to_agent": message.get("to_agent", ""),
            "category": message.get("category", ""),
            "priority": message.get("priority", 5),
            "timestamp": datetime.now().isoformat(),
            "metadata": message.get("metadata", {}),
        }

        if self.is_cloud:
            return self._publish_cloud(topic, msg)
        else:
            return self._publish_local(topic, msg)

    def publish_task(self, from_agent: str, to_agent: str, task: str,
                     priority: int = 5, context: Dict = None) -> str:
        """نشر مهمة لوكيل محدد"""
        return self.publish(self.TOPIC_TASKS, {
            "type": "task",
            "content": task,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "priority": priority,
            "metadata": context or {},
        })

    def publish_result(self, agent_id: str, task: str, result: str,
                       success: bool = True) -> str:
        """نشر نتيجة مهمة"""
        return self.publish(self.TOPIC_RESULTS, {
            "type": "result",
            "content": result[:2000],
            "from_agent": agent_id,
            "metadata": {"task": task[:200], "success": success},
        })

    def publish_signal(self, agent_id: str, signal_type: str,
                       data: Dict = None) -> str:
        """نشر إشارة (heartbeat, alert, status_change)"""
        return self.publish(self.TOPIC_SIGNALS, {
            "type": signal_type,
            "content": json.dumps(data or {}, ensure_ascii=False),
            "from_agent": agent_id,
        })

    def broadcast(self, from_agent: str, content: str, category: str = "",
                  msg_type: str = "info") -> str:
        """بث رسالة لكل الوكلاء أو لفئة محددة"""
        return self.publish(self.TOPIC_BROADCAST, {
            "type": msg_type,
            "content": content,
            "from_agent": from_agent,
            "category": category,
        })

    def subscribe(self, topic: str, callback: Callable, agent_id: str = "") -> str:
        """
        الاشتراك في topic واستلام الرسائل
        callback(message: Dict) — يُستدعى لكل رسالة جديدة
        """
        if self.is_cloud:
            return self._subscribe_cloud(topic, callback, agent_id)
        else:
            return self._subscribe_local(topic, callback, agent_id)

    def get_pending_messages(self, topic: str, agent_id: str = "",
                             limit: int = 20) -> List[Dict]:
        """جلب الرسائل المعلقة من topic"""
        if self.is_cloud:
            return self._pull_cloud(topic, limit)

        with self._lock:
            queue = self._local_queues[topic]
            messages = []
            temp = []

            while not queue.empty() and len(messages) < limit:
                msg = queue.get_nowait()
                if agent_id and msg.get("to_agent") and msg["to_agent"] != agent_id:
                    temp.append(msg)
                else:
                    messages.append(msg)

            # إعادة الرسائل غير المطابقة
            for msg in temp:
                queue.put(msg)

            return messages

    def get_history(self, limit: int = 50, agent_id: str = "") -> List[Dict]:
        """سجل الرسائل"""
        with self._lock:
            if agent_id:
                filtered = [m for m in self._message_history
                           if m.get("from_agent") == agent_id or m.get("to_agent") == agent_id]
                return filtered[-limit:]
            return self._message_history[-limit:]

    def status(self) -> Dict:
        """حالة نظام التواصل"""
        return {
            "backend": "google_pubsub" if self.is_cloud else "local_queue",
            "project_id": self.project_id or "not_set",
            "messages_published": self.stats["messages_published"],
            "messages_received": self.stats["messages_received"],
            "topics_active": list(self.stats["topics_active"]),
            "local_queues": {k: q.qsize() for k, q in self._local_queues.items()},
            "history_size": len(self._message_history),
            "started_at": self.stats["started_at"],
        }

    # ── Cloud Pub/Sub Implementation ─────────────────────────────

    def _publish_cloud(self, topic: str, message: Dict) -> str:
        """نشر عبر Google Cloud Pub/Sub"""
        try:
            topic_path = _publisher.topic_path(self.project_id, topic)
            data = json.dumps(message, ensure_ascii=False).encode("utf-8")

            future = _publisher.publish(
                topic_path, data,
                agent_id=message.get("from_agent", ""),
                msg_type=message.get("type", ""),
            )
            msg_id = future.result(timeout=10)

            self.stats["messages_published"] += 1
            self.stats["topics_active"].add(topic)

            with self._lock:
                self._message_history.append(message)
                if len(self._message_history) > 1000:
                    self._message_history = self._message_history[-500:]

            return f"published:{msg_id}"

        except Exception as e:
            logger.error(f"Pub/Sub publish error: {e}")
            # Fallback to local
            return self._publish_local(topic, message)

    def _subscribe_cloud(self, topic: str, callback: Callable,
                         agent_id: str = "") -> str:
        """اشتراك عبر Google Cloud Pub/Sub"""
        try:
            sub_name = f"army81-{agent_id or 'system'}-{topic}"
            sub_path = _subscriber.subscription_path(self.project_id, sub_name)

            def _callback(message):
                try:
                    data = json.loads(message.data.decode("utf-8"))
                    self.stats["messages_received"] += 1
                    callback(data)
                    message.ack()
                except Exception as e:
                    logger.error(f"Message callback error: {e}")
                    message.nack()

            _subscriber.subscribe(sub_path, callback=_callback)
            return f"subscribed:{sub_path}"

        except Exception as e:
            logger.error(f"Pub/Sub subscribe error: {e}")
            return self._subscribe_local(topic, callback, agent_id)

    def _pull_cloud(self, topic: str, limit: int) -> List[Dict]:
        """سحب رسائل من Pub/Sub"""
        try:
            sub_name = f"army81-pull-{topic}"
            sub_path = _subscriber.subscription_path(self.project_id, sub_name)

            response = _subscriber.pull(
                request={"subscription": sub_path, "max_messages": limit}
            )

            messages = []
            ack_ids = []
            for msg in response.received_messages:
                data = json.loads(msg.message.data.decode("utf-8"))
                messages.append(data)
                ack_ids.append(msg.ack_id)

            if ack_ids:
                _subscriber.acknowledge(
                    request={"subscription": sub_path, "ack_ids": ack_ids}
                )

            self.stats["messages_received"] += len(messages)
            return messages

        except Exception as e:
            logger.error(f"Pub/Sub pull error: {e}")
            return []

    # ── Local Fallback Implementation ────────────────────────────

    def _publish_local(self, topic: str, message: Dict) -> str:
        """نشر محلي في قائمة انتظار"""
        with self._lock:
            self._local_queues[topic].put(message)
            self._message_history.append(message)
            if len(self._message_history) > 1000:
                self._message_history = self._message_history[-500:]

            self.stats["messages_published"] += 1
            self.stats["topics_active"].add(topic)

            # تنبيه المشتركين المحليين
            for callback in self._local_subscriptions.get(topic, []):
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Local callback error: {e}")

        return f"local:{topic}:{self._local_queues[topic].qsize()}"

    def _subscribe_local(self, topic: str, callback: Callable,
                         agent_id: str = "") -> str:
        """اشتراك محلي"""
        with self._lock:
            self._local_subscriptions[topic].append(callback)
        return f"local_sub:{topic}:{agent_id}"


# ── Singleton ──────────────────────────────────────────────────
_instance = None


def get_pubsub() -> PubSubComm:
    """الحصول على instance واحد"""
    global _instance
    if _instance is None:
        _instance = PubSubComm()
    return _instance
