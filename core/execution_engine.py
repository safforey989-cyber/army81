"""
Army81 v6 — Execution Engine
محرك تنفيذ متعدد — محلي + سحابي (E2B)

القدرات:
  - تنفيذ Python آمن في sandbox محلي
  - تنفيذ كود في السحابة عبر E2B (معزول تماماً)
  - HuggingFace Inference API — نماذج متخصصة
  - Brave Search — بحث خاص
  - Polygon.io — بيانات مالية حية
  - GitHub API — بحث وتحليل كود
"""
import os
import json
import logging
import subprocess
import tempfile
from typing import Dict, Optional
from datetime import datetime

import requests

logger = logging.getLogger("army81.execution_engine")


# ═══════════════════════════════════════════════
# E2B — تنفيذ كود سحابي آمن
# ═══════════════════════════════════════════════

class E2BExecutor:
    """E2B Code Interpreter — sandbox سحابي"""

    def __init__(self):
        self.api_key = os.getenv("E2B_API_KEY", "")
        self.available = bool(self.api_key)
        self.base_url = "https://api.e2b.dev/v1"

    def run_python(self, code: str, timeout: int = 30) -> Dict:
        """تنفيذ Python في sandbox سحابي"""
        if not self.available:
            return self._run_local(code, timeout)

        try:
            r = requests.post(
                f"{self.base_url}/sandboxes",
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"},
                json={"template": "base", "timeout": timeout},
                timeout=15,
            )
            if r.status_code in (200, 201):
                sandbox = r.json()
                sandbox_id = sandbox.get("sandboxId", sandbox.get("id", ""))

                # تنفيذ الكود
                exec_r = requests.post(
                    f"{self.base_url}/sandboxes/{sandbox_id}/code/execute",
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={"code": code, "language": "python"},
                    timeout=timeout + 10,
                )

                result = exec_r.json() if exec_r.status_code == 200 else {}
                return {
                    "output": result.get("stdout", result.get("output", "")),
                    "error": result.get("stderr", result.get("error", "")),
                    "success": exec_r.status_code == 200,
                    "executor": "e2b_cloud",
                }
            else:
                logger.warning(f"E2B sandbox creation failed: {r.status_code}")
                return self._run_local(code, timeout)

        except Exception as e:
            logger.warning(f"E2B error, falling back to local: {e}")
            return self._run_local(code, timeout)

    def _run_local(self, code: str, timeout: int = 15) -> Dict:
        """تنفيذ محلي كـ fallback"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                              delete=False, encoding='utf-8') as f:
                f.write(code)
                f.flush()
                tmp_path = f.name

            result = subprocess.run(
                ["python", tmp_path],
                capture_output=True, text=True,
                timeout=timeout,
            )
            os.unlink(tmp_path)

            return {
                "output": result.stdout,
                "error": result.stderr,
                "success": result.returncode == 0,
                "executor": "local",
            }
        except subprocess.TimeoutExpired:
            return {"output": "", "error": "Timeout", "success": False, "executor": "local"}
        except Exception as e:
            return {"output": "", "error": str(e), "success": False, "executor": "local"}


# ═══════════════════════════════════════════════
# Brave Search — بحث خاص
# ═══════════════════════════════════════════════

class BraveSearch:
    def __init__(self):
        self.api_key = os.getenv("BRAVE_API_KEY", "")
        self.available = bool(self.api_key)

    def search(self, query: str, count: int = 5) -> str:
        if not self.available:
            return "BRAVE_API_KEY غير موجود"
        try:
            r = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key,
                         "Accept": "application/json"},
                params={"q": query, "count": count},
                timeout=15,
            )
            r.raise_for_status()
            results = r.json().get("web", {}).get("results", [])
            lines = []
            for item in results[:count]:
                lines.append(
                    f"**{item.get('title', '')}**\n"
                    f"{item.get('description', '')}\n"
                    f"المصدر: {item.get('url', '')}"
                )
            return "\n\n---\n\n".join(lines) if lines else "لا نتائج"
        except Exception as e:
            return f"خطأ Brave: {e}"


# ═══════════════════════════════════════════════
# Polygon.io — بيانات مالية حية
# ═══════════════════════════════════════════════

class PolygonFinance:
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY", "")
        self.available = bool(self.api_key)
        self.base = "https://api.polygon.io"

    def get_ticker(self, symbol: str) -> str:
        if not self.available:
            return "POLYGON_API_KEY غير موجود"
        try:
            r = requests.get(
                f"{self.base}/v2/aggs/ticker/{symbol}/prev",
                params={"apiKey": self.api_key},
                timeout=10,
            )
            data = r.json()
            results = data.get("results", [{}])
            if results:
                bar = results[0]
                return (
                    f"السهم: {symbol}\n"
                    f"الافتتاح: ${bar.get('o', 0):.2f}\n"
                    f"الإغلاق: ${bar.get('c', 0):.2f}\n"
                    f"الأعلى: ${bar.get('h', 0):.2f}\n"
                    f"الأدنى: ${bar.get('l', 0):.2f}\n"
                    f"الحجم: {bar.get('v', 0):,.0f}"
                )
            return f"لا بيانات لـ {symbol}"
        except Exception as e:
            return f"خطأ Polygon: {e}"

    def search_tickers(self, query: str) -> str:
        if not self.available:
            return "POLYGON_API_KEY غير موجود"
        try:
            r = requests.get(
                f"{self.base}/v3/reference/tickers",
                params={"search": query, "limit": 5, "apiKey": self.api_key},
                timeout=10,
            )
            results = r.json().get("results", [])
            lines = [f"• {t['ticker']} — {t.get('name', '')}" for t in results[:5]]
            return "\n".join(lines) if lines else "لا نتائج"
        except Exception as e:
            return f"خطأ: {e}"


# ═══════════════════════════════════════════════
# GitHub Enhanced — بحث متقدم
# ═══════════════════════════════════════════════

class GitHubAPI:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.available = bool(self.token)
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def search_repos(self, query: str, limit: int = 5) -> str:
        if not self.available:
            return "GITHUB_TOKEN غير موجود"
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=self.headers,
                params={"q": query, "sort": "stars", "per_page": limit},
                timeout=15,
            )
            items = r.json().get("items", [])
            lines = []
            for repo in items[:limit]:
                lines.append(
                    f"⭐ **{repo['full_name']}** ({repo['stargazers_count']:,} stars)\n"
                    f"{repo.get('description', '')[:100]}\n"
                    f"{repo['html_url']}"
                )
            return "\n\n".join(lines) if lines else "لا نتائج"
        except Exception as e:
            return f"خطأ GitHub: {e}"

    def search_code(self, query: str, limit: int = 5) -> str:
        if not self.available:
            return "GITHUB_TOKEN غير موجود"
        try:
            r = requests.get(
                "https://api.github.com/search/code",
                headers=self.headers,
                params={"q": query, "per_page": limit},
                timeout=15,
            )
            items = r.json().get("items", [])
            lines = []
            for item in items[:limit]:
                lines.append(
                    f"📄 {item['repository']['full_name']}/{item['name']}\n"
                    f"{item['html_url']}"
                )
            return "\n\n".join(lines) if lines else "لا نتائج"
        except Exception as e:
            return f"خطأ: {e}"

    def get_trending(self, language: str = "python", since: str = "weekly") -> str:
        """GitHub trending — يستخدم search API بدل scraping"""
        from datetime import timedelta
        days = 7 if since == "weekly" else 1
        date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.search_repos(f"language:{language} created:>{date}", 10)


# ═══════════════════════════════════════════════
# HuggingFace Inference — نماذج متخصصة
# ═══════════════════════════════════════════════

class HuggingFaceInference:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")
        self.available = bool(self.token)
        self.base = "https://api-inference.huggingface.co/models"

    def text_generation(self, prompt: str,
                        model: str = "mistralai/Mistral-7B-Instruct-v0.3",
                        max_tokens: int = 500) -> str:
        if not self.available:
            return "HF_TOKEN غير موجود"
        try:
            r = requests.post(
                f"{self.base}/{model}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"inputs": prompt,
                      "parameters": {"max_new_tokens": max_tokens}},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    return data[0].get("generated_text", "")
                return str(data)
            return f"خطأ HF: {r.status_code}"
        except Exception as e:
            return f"خطأ: {e}"

    def summarize(self, text: str) -> str:
        return self.text_generation(
            f"Summarize this text:\n\n{text[:2000]}",
            model="facebook/bart-large-cnn",
            max_tokens=200,
        )

    def classify(self, text: str, labels: list) -> str:
        if not self.available:
            return "HF_TOKEN غير موجود"
        try:
            r = requests.post(
                f"{self.base}/facebook/bart-large-mnli",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"inputs": text, "parameters": {"candidate_labels": labels}},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                if "labels" in data:
                    return "\n".join(
                        f"• {l}: {s:.0%}" for l, s
                        in zip(data["labels"], data["scores"])
                    )
            return f"خطأ: {r.status_code}"
        except Exception as e:
            return f"خطأ: {e}"


# ═══════════════════════════════════════════════
# ExecutionEngine — الموحّد
# ═══════════════════════════════════════════════

class ExecutionEngine:
    """محرك تنفيذ موحّد — يجمع كل القدرات"""

    def __init__(self):
        self.e2b = E2BExecutor()
        self.brave = BraveSearch()
        self.polygon = PolygonFinance()
        self.github = GitHubAPI()
        self.hf = HuggingFaceInference()

    def status(self) -> Dict:
        return {
            "e2b": {"available": self.e2b.available},
            "brave_search": {"available": self.brave.available},
            "polygon": {"available": self.polygon.available},
            "github": {"available": self.github.available},
            "huggingface": {"available": self.hf.available},
            "total_available": sum([
                self.e2b.available, self.brave.available,
                self.polygon.available, self.github.available,
                self.hf.available,
            ]),
        }


# Singleton
_engine: Optional[ExecutionEngine] = None

def get_execution_engine() -> ExecutionEngine:
    global _engine
    if _engine is None:
        _engine = ExecutionEngine()
    return _engine


# ═══════════════════════════════════════════════
# Wrapper functions for tools registry
# ═══════════════════════════════════════════════

def _brave_search_wrapper(query: str, count: int = 5) -> str:
    return get_execution_engine().brave.search(query, count)

def _polygon_ticker_wrapper(symbol: str) -> str:
    return get_execution_engine().polygon.get_ticker(symbol.upper())

def _polygon_search_wrapper(query: str) -> str:
    return get_execution_engine().polygon.search_tickers(query)

def _github_code_wrapper(query: str) -> str:
    return get_execution_engine().github.search_code(query)

def _github_trending_wrapper(language: str = "python") -> str:
    return get_execution_engine().github.get_trending(language)

def _hf_generate_wrapper(prompt: str) -> str:
    return get_execution_engine().hf.text_generation(prompt)

def _hf_classify_wrapper(text: str, labels: str = "positive,negative,neutral") -> str:
    label_list = [l.strip() for l in labels.split(",")]
    return get_execution_engine().hf.classify(text, label_list)

def _e2b_run_wrapper(code: str) -> str:
    result = get_execution_engine().e2b.run_python(code)
    if result["success"]:
        return result["output"] or "تم التنفيذ بنجاح"
    return f"خطأ: {result['error']}"
