"""
Army81 - Pub/Sub Protocol
بروتوكول تواصل بين الوكلاء عبر Google Cloud Pub/Sub
مع fallback لقوائم محلية
"""
import os
import json
import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("army81.pubsub")


class PubSubProtocol:
    """
    بروتوكول Pub/Sub للتواصل بين الوكلاء
    يدعم:
    - Google Cloud Pub/Sub (إنتاج)
    - قوائم محلية (تطوير)
    """

    def __init__(self, use_cloud: bool = None):
        self._subscribers: Dict[str, List[Callable]] = {}  # topic → [callbacks]
        self._message_queue: Dict[str, List[Dict]] = {}     # topic → [messages]
        self._stats = {
            "published": 0,
            "delivered": 0,
            "topics": set(),
        }

        # تحديد وضع التشغيل
        if use_cloud is None:
            use_cloud = bool(os.getenv("GCP_PROJECT_ID"))
        self.use_cloud = use_cloud

        self._publisher = None
        self._subscriber_client = None
        self._project_id = os.getenv("GCP_PROJECT_ID", "")

        if self.use_cloud:
            self._init_cloud()

        logger.info(f"PubSub initialized (cloud={self.use_cloud})")

    def _init_cloud(self):
        """تهيئة Google Cloud Pub/Sub"""
        try:
            from google.cloud import pubsub_v1
            self._publisher = pubsub_v1.PublisherClient()
            self._subscriber_client = pubsub_v1.SubscriberClient()
            logger.info("Cloud Pub/Sub clients initialized")
        except ImportError:
            logger.warning("google-cloud-pubsub not installed, falling back to local")
            self.use_cloud = False
        except Exception as e:
            logger.warning(f"Cloud Pub/Sub init error: {e}, falling back to local")
            self.use_cloud = False

    # ── Publish ──────────────────────────────────────────────

    def publish(self, topic: str, message: Dict, sender: str = "system") -> bool:
        """
        نشر رسالة على موضوع
        topic: اسم الموضوع (مثل: "tasks.new", "agents.A01.results", "system.alerts")
        message: بيانات الرسالة
        sender: معرّف المُرسل
        """
        envelope = {
            "topic": topic,
            "sender": sender,
            "data": message,
            "timestamp": datetime.now().isoformat(),
        }

        self._stats["published"] += 1
        self._stats["topics"].add(topic)

        if self.use_cloud:
            return self._publish_cloud(topic, envelope)
        else:
            return self._publish_local(topic, envelope)

    def _publish_cloud(self, topic: str, envelope: Dict) -> bool:
        """نشر عبر Google Cloud Pub/Sub"""
        try:
            topic_path = self._publisher.topic_path(
                self._project_id, f"army81-{topic.replace('.', '-')}")

            data = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
            future = self._publisher.publish(topic_path, data)
            future.result(timeout=10)
            return True
        except Exception as e:
            logger.error(f"Cloud publish error: {e}")
            # fallback to local
            return self._publish_local(topic, envelope)

    def _publish_local(self, topic: str, envelope: Dict) -> bool:
        """نشر محلي (في الذاكرة)"""
        if topic not in self._message_queue:
            self._message_queue[topic] = []
        self._message_queue[topic].append(envelope)

        # حد أقصى 1000 رسالة لكل موضوع
        if len(self._message_queue[topic]) > 1000:
            self._message_queue[topic] = self._message_queue[topic][-1000:]

        # تنفيذ المشتركين
        self._deliver_local(topic, envelope)
        return True

    # ── Subscribe ────────────────────────────────────────────

    def subscribe(self, topic: str, callback: Callable, subscriber_id: str = ""):
        """
        الاشتراك في موضوع
        callback: دالة تُستدعى عند وصول رسالة callback(message_dict)
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

        if self.use_cloud:
            self._subscribe_cloud(topic, callback, subscriber_id)

        logger.info(f"Subscribed to {topic} (subscriber={subscriber_id})")

    def _subscribe_cloud(self, topic: str, callback: Callable, subscriber_id: str):
        """اشتراك عبر Cloud Pub/Sub"""
        try:
            sub_name = f"army81-{topic.replace('.', '-')}-{subscriber_id}"
            subscription_path = self._subscriber_client.subscription_path(
                self._project_id, sub_name)

            def cloud_callback(message):
                try:
                    data = json.loads(message.data.decode("utf-8"))
                    callback(data)
                    message.ack()
                except Exception as e:
                    logger.error(f"Cloud subscriber error: {e}")
                    message.nack()

            self._subscriber_client.subscribe(subscription_path, callback=cloud_callback)
        except Exception as e:
            logger.warning(f"Cloud subscribe error: {e}")

    def _deliver_local(self, topic: str, envelope: Dict):
        """توصيل الرسائل للمشتركين المحليين"""
        callbacks = self._subscribers.get(topic, [])

        # أيضاً اشتراكات الـ wildcard (مثل: "agents.*")
        for sub_topic, sub_callbacks in self._subscribers.items():
            if sub_topic.endswith(".*"):
                prefix = sub_topic[:-2]
                if topic.startswith(prefix):
                    callbacks.extend(sub_callbacks)

        for callback in callbacks:
            try:
                callback(envelope)
                self._stats["delivered"] += 1
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")

    # ── Convenience Methods ──────────────────────────────────

    def publish_task(self, agent_id: str, task: str, priority: int = 5,
                     context: Dict = None) -> bool:
        """نشر مهمة جديدة لوكيل"""
        return self.publish(
            topic=f"tasks.{agent_id}",
            message={
                "type": "task",
                "agent_id": agent_id,
                "task": task,
                "priority": priority,
                "context": context or {},
            },
            sender="router",
        )

    def publish_result(self, agent_id: str, task: str, result: str,
                       status: str = "success") -> bool:
        """نشر نتيجة مهمة"""
        return self.publish(
            topic=f"results.{agent_id}",
            message={
                "type": "result",
                "agent_id": agent_id,
                "task": task[:200],
                "result": result[:1000],
                "status": status,
            },
            sender=agent_id,
        )

    def publish_alert(self, alert_type: str, message: str,
                      severity: str = "info") -> bool:
        """نشر تنبيه نظام"""
        return self.publish(
            topic="system.alerts",
            message={
                "type": alert_type,
                "message": message,
                "severity": severity,
            },
            sender="system",
        )

    def broadcast_to_category(self, category: str, message: Dict,
                              sender: str = "system") -> bool:
        """بث رسالة لكل وكلاء فئة"""
        return self.publish(
            topic=f"category.{category}",
            message=message,
            sender=sender,
        )

    # ── Queue Management ─────────────────────────────────────

    def get_pending(self, topic: str, limit: int = 10) -> List[Dict]:
        """قراءة الرسائل المعلقة"""
        messages = self._message_queue.get(topic, [])
        return messages[-limit:]

    def clear_topic(self, topic: str):
        """مسح رسائل موضوع"""
        self._message_queue.pop(topic, None)

    # ── Cloud Setup ──────────────────────────────────────────

    def setup_cloud_topics(self) -> List[str]:
        """إنشاء المواضيع في Cloud Pub/Sub"""
        if not self.use_cloud or not self._publisher:
            return []

        topics_to_create = [
            "army81-tasks",
            "army81-results",
            "army81-system-alerts",
            "army81-category-broadcast",
            "army81-agent-communication",
        ]

        created = []
        for topic_name in topics_to_create:
            try:
                topic_path = self._publisher.topic_path(self._project_id, topic_name)
                self._publisher.create_topic(request={"name": topic_path})
                created.append(topic_name)
                logger.info(f"Created topic: {topic_name}")
            except Exception as e:
                if "ALREADY_EXISTS" in str(e):
                    created.append(topic_name)
                else:
                    logger.error(f"Create topic error [{topic_name}]: {e}")

        return created

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict:
        """حالة بروتوكول Pub/Sub"""
        return {
            "mode": "cloud" if self.use_cloud else "local",
            "stats": {
                "published": self._stats["published"],
                "delivered": self._stats["delivered"],
                "topics": len(self._stats["topics"]),
            },
            "active_topics": list(self._stats["topics"]),
            "subscribers": {
                topic: len(callbacks)
                for topic, callbacks in self._subscribers.items()
            },
            "pending_messages": {
                topic: len(msgs)
                for topic, msgs in self._message_queue.items()
            },
        }


# ── Singleton ────────────────────────────────────────────────
_instance: Optional[PubSubProtocol] = None


def get_pubsub() -> PubSubProtocol:
    """الحصول على instance واحد"""
    global _instance
    if _instance is None:
        _instance = PubSubProtocol()
    return _instance


if __name__ == "__main__":
    pubsub = PubSubProtocol(use_cloud=False)

    # اختبار
    received = []
    pubsub.subscribe("test.topic", lambda msg: received.append(msg))
    pubsub.publish("test.topic", {"hello": "world"}, sender="test")

    print(f"Messages received: {len(received)}")
    print(f"Status: {json.dumps(pubsub.status(), indent=2, ensure_ascii=False)}")
