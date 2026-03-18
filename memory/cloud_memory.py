"""
Army81 v6 — Cloud Memory Layer
ذاكرة سحابية تربط المحلي بالسحابة

3 طبقات:
  Redis (Upstash)  → cache سريع (< 1ms) — آخر 100 مهمة لكل وكيل
  Supabase         → PostgreSQL سحابي — كل التاريخ الدائم
  Local SQLite     → نسخة محلية (fallback إذا انقطع الإنترنت)

كل وكيل يحصل على:
  - cache فوري في Redis
  - تخزين دائم في Supabase
  - مزامنة تلقائية بين المحلي والسحابي
"""
import os
import json
import time
import hashlib
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("army81.cloud_memory")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DB = os.path.join(BASE_DIR, "workspace", "episodic_memory.db")


# ═══════════════════════════════════════════════
# Redis Cache (Upstash) — ذاكرة فورية
# ═══════════════════════════════════════════════

class RedisCache:
    """Upstash Redis — REST API (لا يحتاج مكتبة)"""

    def __init__(self):
        self.url = os.getenv("UPSTASH_REDIS_URL", "")
        self.token = os.getenv("UPSTASH_REDIS_TOKEN", "")
        self.available = bool(self.url and self.token)
        if not self.available:
            # Try constructing URL from token
            if self.token and not self.url:
                self.url = f"https://global-tops-redis.upstash.io"
                self.available = True

    def _request(self, command: List[str]) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            r = requests.post(
                f"{self.url}",
                headers={"Authorization": f"Bearer {self.token}"},
                json=command,
                timeout=5,
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.debug(f"Redis error: {e}")
        return None

    def set(self, key: str, value: str, ttl: int = 86400) -> bool:
        """حفظ قيمة مع مدة صلاحية (افتراضي 24 ساعة)"""
        result = self._request(["SET", key, value, "EX", str(ttl)])
        return result is not None

    def get(self, key: str) -> Optional[str]:
        """قراءة قيمة"""
        result = self._request(["GET", key])
        if result and result.get("result"):
            return result["result"]
        return None

    def lpush(self, key: str, value: str) -> bool:
        """إضافة لقائمة"""
        return self._request(["LPUSH", key, value]) is not None

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """قراءة قائمة"""
        result = self._request(["LRANGE", key, str(start), str(end)])
        if result and result.get("result"):
            return result["result"]
        return []

    def incr(self, key: str) -> Optional[int]:
        """زيادة عداد"""
        result = self._request(["INCR", key])
        if result:
            return result.get("result")
        return None

    def ping(self) -> bool:
        result = self._request(["PING"])
        return result is not None and result.get("result") == "PONG"


# ═══════════════════════════════════════════════
# Supabase Storage — تخزين دائم سحابي
# ═══════════════════════════════════════════════

class SupabaseStorage:
    """Supabase REST API — PostgreSQL سحابي"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
        self.available = bool(self.url and self.key)

    def _headers(self):
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    def insert(self, table: str, data: Dict) -> bool:
        if not self.available:
            return False
        try:
            r = requests.post(
                f"{self.url}/rest/v1/{table}",
                headers=self._headers(),
                json=data,
                timeout=10,
            )
            return r.status_code in (200, 201, 204)
        except Exception as e:
            logger.debug(f"Supabase insert error: {e}")
            return False

    def select(self, table: str, query: str = "",
               limit: int = 50) -> List[Dict]:
        if not self.available:
            return []
        try:
            url = f"{self.url}/rest/v1/{table}?select=*&limit={limit}"
            if query:
                url += f"&{query}"
            url += "&order=created_at.desc"
            r = requests.get(url, headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.debug(f"Supabase select error: {e}")
        return []

    def rpc(self, function_name: str, params: Dict = None) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            r = requests.post(
                f"{self.url}/rest/v1/rpc/{function_name}",
                headers=self._headers(),
                json=params or {},
                timeout=10,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def ping(self) -> bool:
        if not self.available:
            return False
        try:
            r = requests.get(
                f"{self.url}/rest/v1/",
                headers=self._headers(),
                timeout=5,
            )
            return r.status_code in (200, 404)  # 404 = no tables yet but connected
        except Exception:
            return False


# ═══════════════════════════════════════════════
# CloudMemory — الطبقة الموحّدة
# ═══════════════════════════════════════════════

class CloudMemory:
    """
    ذاكرة سحابية موحّدة لكل وكيل
    Redis (cache) + Supabase (دائم) + SQLite (محلي/fallback)
    """

    def __init__(self):
        self.redis = RedisCache()
        self.supabase = SupabaseStorage()
        self._local_db_ready = os.path.exists(LOCAL_DB)

    def store_episode(self, agent_id: str, task: str, result: str,
                      success: bool, rating: int = 7,
                      model: str = "", tokens: int = 0,
                      task_type: str = "general"):
        """
        يحفظ حلقة في 3 أماكن:
        1. Redis cache (فوري — آخر 100)
        2. Supabase (دائم سحابي)
        3. SQLite محلي (fallback)
        """
        episode = {
            "agent_id": agent_id,
            "task_summary": task[:500],
            "result_summary": result[:1000],
            "success": success,
            "rating": rating,
            "model_used": model,
            "tokens": tokens,
            "task_type": task_type,
            "created_at": datetime.now().isoformat(),
        }

        # 1. Redis — cache فوري
        if self.redis.available:
            try:
                cache_key = f"army81:episodes:{agent_id}"
                self.redis.lpush(cache_key, json.dumps(episode, ensure_ascii=False))
                # عداد المهام
                self.redis.incr(f"army81:tasks_today:{agent_id}")
                self.redis.incr("army81:tasks_total_today")
            except Exception:
                pass

        # 2. Supabase — دائم سحابي
        if self.supabase.available:
            try:
                self.supabase.insert("episodes", episode)
            except Exception as e:
                logger.debug(f"Supabase store failed: {e}")

        # 3. SQLite محلي — دائماً يعمل
        self._store_local(episode)

    def recall_recent(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """
        يسترجع آخر الحلقات — Redis أولاً (أسرع)
        """
        # 1. حاول Redis
        if self.redis.available:
            try:
                items = self.redis.lrange(f"army81:episodes:{agent_id}", 0, limit - 1)
                if items:
                    return [json.loads(i) for i in items]
            except Exception:
                pass

        # 2. حاول Supabase
        if self.supabase.available:
            results = self.supabase.select(
                "episodes",
                f"agent_id=eq.{agent_id}",
                limit=limit,
            )
            if results:
                return results

        # 3. SQLite محلي
        return self._recall_local(agent_id, limit)

    def get_agent_stats(self, agent_id: str) -> Dict:
        """إحصائيات وكيل"""
        # Redis فوري
        if self.redis.available:
            today = self.redis.get(f"army81:tasks_today:{agent_id}")
            if today:
                return {"tasks_today": int(today), "source": "redis"}

        # Supabase
        if self.supabase.available:
            results = self.supabase.select(
                "episodes",
                f"agent_id=eq.{agent_id}",
                limit=1000,
            )
            if results:
                success = sum(1 for r in results if r.get("success"))
                return {
                    "total": len(results),
                    "success": success,
                    "rate": round(success / len(results) * 100, 1) if results else 0,
                    "avg_rating": round(sum(r.get("rating", 0) for r in results) / len(results), 1),
                    "source": "supabase",
                }

        # Local
        return self._stats_local(agent_id)

    def get_global_stats(self) -> Dict:
        """إحصائيات النظام الكامل"""
        stats = {
            "redis": {"available": self.redis.available, "ping": False},
            "supabase": {"available": self.supabase.available, "ping": False},
            "local_sqlite": {"available": self._local_db_ready},
        }

        if self.redis.available:
            stats["redis"]["ping"] = self.redis.ping()
            total = self.redis.get("army81:tasks_total_today")
            stats["redis"]["tasks_today"] = int(total) if total else 0

        if self.supabase.available:
            stats["supabase"]["ping"] = self.supabase.ping()

        return stats

    def sync_local_to_cloud(self) -> Dict:
        """
        مزامنة: يرفع البيانات المحلية للسحابة
        يُشغّل يومياً أو عند الطلب
        """
        if not self.supabase.available:
            return {"synced": 0, "error": "Supabase not available"}

        synced = 0
        try:
            conn = sqlite3.connect(LOCAL_DB)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
            conn.close()

            for row in rows:
                episode = dict(row)
                episode.pop("id", None)  # Supabase يولّد ID خاص
                if self.supabase.insert("episodes", episode):
                    synced += 1
        except Exception as e:
            return {"synced": synced, "error": str(e)}

        return {"synced": synced, "total_local": len(rows) if rows else 0}

    # ── Local SQLite (fallback) ──────────────────

    def _store_local(self, episode: Dict):
        try:
            conn = sqlite3.connect(LOCAL_DB)
            conn.execute(
                """INSERT INTO episodes
                   (agent_id, task_summary, result_summary, success, rating,
                    model_used, tokens, task_type, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (episode["agent_id"], episode["task_summary"],
                 episode["result_summary"], episode["success"],
                 episode["rating"], episode["model_used"],
                 episode["tokens"], episode["task_type"],
                 episode["created_at"]),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Local store error: {e}")

    def _recall_local(self, agent_id: str, limit: int) -> List[Dict]:
        try:
            conn = sqlite3.connect(LOCAL_DB)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM episodes WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _stats_local(self, agent_id: str) -> Dict:
        try:
            conn = sqlite3.connect(LOCAL_DB)
            total = conn.execute(
                "SELECT COUNT(*) FROM episodes WHERE agent_id = ?", (agent_id,)
            ).fetchone()[0]
            success = conn.execute(
                "SELECT COUNT(*) FROM episodes WHERE agent_id = ? AND success = 1", (agent_id,)
            ).fetchone()[0]
            conn.close()
            return {
                "total": total, "success": success,
                "rate": round(success / total * 100, 1) if total else 0,
                "source": "local",
            }
        except Exception:
            return {"total": 0, "source": "local"}


# ── Singleton ────────────────────────────────
_instance: Optional[CloudMemory] = None


def get_cloud_memory() -> CloudMemory:
    global _instance
    if _instance is None:
        _instance = CloudMemory()
    return _instance
