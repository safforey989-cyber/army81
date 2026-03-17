"""
SmartQueue — حل مشكلة rate limiting و API failures
نتيجة Monte Carlo: بدون هذا → 0% نجاة بعد 90 يوم
"""
import time
import threading
import logging
from datetime import datetime
from queue import PriorityQueue
from typing import Optional, Dict, Any

logger = logging.getLogger("army81.smart_queue")


class SmartQueue:
    # أولويات المهام
    CRITICAL = 1   # A81, A01
    HIGH = 2       # مهام مع deadline
    NORMAL = 3     # مهام عادية
    LOW = 4        # daily_updater, distillation

    # حدود النماذج
    MODEL_LIMITS = {
        "gemini-flash": {"rpm": 15, "fallback": "gemini-pro"},
        "gemini-pro":   {"rpm": 2,  "fallback": "claude-haiku"},
        "claude-haiku": {"rpm": 50, "fallback": "gemini-flash"},
        "claude-sonnet":{"rpm": 50, "fallback": "claude-haiku"},
        "ollama-local": {"rpm": 999,"fallback": None},
    }

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._queue: PriorityQueue = PriorityQueue()
        self._model_request_times: Dict[str, list] = {m: [] for m in self.MODEL_LIMITS}
        self._stats = {
            "pending": 0,
            "processed": 0,
            "fallbacks_used": 0,
            "by_model": {m: 0 for m in self.MODEL_LIMITS},
            "errors": 0,
        }
        self._lock_model = threading.Lock()

    @classmethod
    def get_instance(cls) -> "SmartQueue":
        """Singleton"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = SmartQueue()
        return cls._instance

    def _normalize_model(self, model: str) -> str:
        """تحويل model alias إلى مفتاح MODEL_LIMITS"""
        mapping = {
            "gemini-flash":  "gemini-flash",
            "gemini-fast":   "gemini-flash",
            "gemini-pro":    "gemini-pro",
            "gemini-think":  "gemini-pro",
            "claude-fast":   "claude-haiku",
            "claude-smart":  "claude-sonnet",
            "local-small":   "ollama-local",
            "local-medium":  "ollama-local",
            "local-coder":   "ollama-local",
        }
        return mapping.get(model, "gemini-flash")

    def _is_rate_limited(self, model_key: str) -> bool:
        """هل النموذج وصل لحد الطلبات؟"""
        if model_key not in self.MODEL_LIMITS:
            return False
        limit = self.MODEL_LIMITS[model_key]["rpm"]
        if limit >= 999:
            return False

        now = time.time()
        with self._lock_model:
            # احتفظ فقط بطلبات آخر دقيقة
            times = [t for t in self._model_request_times.get(model_key, [])
                     if now - t < 60]
            self._model_request_times[model_key] = times
            return len(times) >= limit

    def _record_request(self, model_key: str):
        """سجّل طلباً للنموذج"""
        with self._lock_model:
            if model_key not in self._model_request_times:
                self._model_request_times[model_key] = []
            self._model_request_times[model_key].append(time.time())

    def _get_fallback(self, model_key: str) -> Optional[str]:
        """احصل على الـ fallback للنموذج"""
        info = self.MODEL_LIMITS.get(model_key, {})
        return info.get("fallback")

    def submit(self, agent_id: str, task: Any, priority: int = 3,
               model: str = "gemini-flash") -> Dict:
        """
        ضع مهمة في القائمة بالأولوية.
        إذا انتظر > 60 ثانية → انزل للـ fallback تلقائياً.
        إذا فشل الـ fallback → ollama-local.

        يعيد dict مع: model_used, waited_seconds, fallback_used
        """
        model_key = self._normalize_model(model)
        start_wait = time.time()
        fallback_used = False

        # انتظر حتى يخف الضغط (max 60 ثانية ثم fallback)
        while self._is_rate_limited(model_key):
            waited = time.time() - start_wait
            if waited > 60:
                # انزل للـ fallback
                fallback = self._get_fallback(model_key)
                if fallback and not self._is_rate_limited(fallback):
                    logger.warning(
                        f"[SmartQueue] {agent_id}: {model_key} rate-limited "
                        f"after {waited:.0f}s → fallback to {fallback}"
                    )
                    model_key = fallback
                    fallback_used = True
                    self._stats["fallbacks_used"] += 1
                    break
                else:
                    # الـ fallback مشغول أيضاً → ollama-local
                    logger.warning(
                        f"[SmartQueue] {agent_id}: all models busy → ollama-local"
                    )
                    model_key = "ollama-local"
                    fallback_used = True
                    self._stats["fallbacks_used"] += 1
                    break
            time.sleep(1)

        waited_seconds = round(time.time() - start_wait, 2)
        self._record_request(model_key)
        self._stats["processed"] += 1
        self._stats["by_model"][model_key] = self._stats["by_model"].get(model_key, 0) + 1

        return {
            "agent_id": agent_id,
            "model_used": model_key,
            "waited_seconds": waited_seconds,
            "fallback_used": fallback_used,
            "queued_at": datetime.now().isoformat(),
        }

    def stats(self) -> Dict:
        """pending, processed, fallbacks_used, by_model"""
        return dict(self._stats)
