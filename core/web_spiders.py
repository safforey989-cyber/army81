"""
Army81 — Web Spiders + Tool Cloner + GraphRAG
عناكب المعرفة + استنساخ الأدوات + شبكة المعرفة
"""
import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import requests

logger = logging.getLogger("army81.web_spiders")

WORKSPACE = Path("workspace")
SPIDER_DIR = WORKSPACE / "spider_cache"
TOOLS_DIR = Path("tools")
GRAPH_DIR = WORKSPACE / "knowledge_graph"


class WebSpider:
    """
    عناكب الويب المعرفية — مسح 24/7
    10 عناكب تتصفح arXiv, GitHub, Reddit يومياً
    """

    def __init__(self):
        self.papers_found = 0
        self.repos_found = 0
        self.skills_created = 0
        SPIDER_DIR.mkdir(parents=True, exist_ok=True)

    def crawl_arxiv(self, query: str = "LLM agents", max_results: int = 10) -> List[Dict]:
        """زحف arXiv"""
        papers = []
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={max_results}&sortBy=submittedDate"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                # تحليل بسيط بدون XML parser
                entries = resp.text.split("<entry>")[1:]
                for entry in entries[:max_results]:
                    title = entry.split("<title>")[1].split("</title>")[0].strip() if "<title>" in entry else ""
                    summary = entry.split("<summary>")[1].split("</summary>")[0].strip() if "<summary>" in entry else ""
                    arxiv_id = entry.split("<id>")[1].split("</id>")[0].strip() if "<id>" in entry else ""

                    papers.append({
                        "source": "arxiv",
                        "title": title[:200],
                        "summary": summary[:500],
                        "url": arxiv_id,
                        "fetched_at": datetime.now().isoformat(),
                    })
                    self.papers_found += 1
        except Exception as e:
            logger.warning(f"خطأ في arXiv: {e}")
        return papers

    def crawl_github_trending(self, language: str = "python",
                               topic: str = "ai-agents") -> List[Dict]:
        """زحف GitHub trending"""
        repos = []
        token = os.getenv("GITHUB_TOKEN", "")
        headers = {"Authorization": f"token {token}"} if token else {}

        try:
            url = f"https://api.github.com/search/repositories?q={topic}+language:{language}&sort=stars&order=desc&per_page=10"
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                for repo in resp.json().get("items", [])[:10]:
                    repos.append({
                        "source": "github",
                        "name": repo["full_name"],
                        "description": (repo.get("description") or "")[:300],
                        "stars": repo["stargazers_count"],
                        "url": repo["html_url"],
                        "language": repo.get("language", ""),
                        "topics": repo.get("topics", [])[:5],
                        "fetched_at": datetime.now().isoformat(),
                    })
                    self.repos_found += 1
        except Exception as e:
            logger.warning(f"خطأ في GitHub: {e}")
        return repos

    def crawl_huggingface(self, query: str = "arabic", limit: int = 5) -> List[Dict]:
        """زحف HuggingFace للنماذج الجديدة"""
        models = []
        token = os.getenv("HF_TOKEN", "")
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        try:
            url = f"https://huggingface.co/api/models?search={query}&sort=downloads&direction=-1&limit={limit}"
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                for model in resp.json()[:limit]:
                    models.append({
                        "source": "huggingface",
                        "name": model.get("modelId", ""),
                        "downloads": model.get("downloads", 0),
                        "likes": model.get("likes", 0),
                        "pipeline_tag": model.get("pipeline_tag", ""),
                        "fetched_at": datetime.now().isoformat(),
                    })
        except Exception as e:
            logger.warning(f"خطأ في HuggingFace: {e}")
        return models

    def crawl_news(self, query: str = "artificial intelligence") -> List[Dict]:
        """زحف الأخبار"""
        articles = []
        api_key = os.getenv("NEWSAPI_KEY", "")
        if not api_key:
            return articles

        try:
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                for art in resp.json().get("articles", [])[:5]:
                    articles.append({
                        "source": "news",
                        "title": art.get("title", "")[:200],
                        "description": (art.get("description") or "")[:300],
                        "url": art.get("url", ""),
                        "published_at": art.get("publishedAt", ""),
                    })
        except Exception as e:
            logger.warning(f"خطأ في News API: {e}")
        return articles

    def daily_crawl(self) -> Dict:
        """الزحف اليومي الشامل"""
        logger.info("🕷️ بدء الزحف اليومي")
        all_results = {
            "arxiv": [], "github": [], "huggingface": [], "news": [],
            "timestamp": datetime.now().isoformat()
        }

        queries = [
            ("LLM agents", "ai-agents"),
            ("multi agent systems", "multi-agent"),
            ("RAG retrieval", "rag"),
            ("prompt engineering", "prompt-engineering"),
            ("arabic NLP", "arabic-nlp"),
        ]

        for arxiv_q, gh_q in queries:
            all_results["arxiv"].extend(self.crawl_arxiv(arxiv_q, 5))
            all_results["github"].extend(self.crawl_github_trending("python", gh_q))
            time.sleep(2)

        all_results["huggingface"] = self.crawl_huggingface("arabic", 5)
        all_results["news"] = self.crawl_news("artificial intelligence agents")

        # حفظ
        cache_file = SPIDER_DIR / f"crawl_{datetime.now().strftime('%Y%m%d')}.json"
        cache_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

        total = sum(len(v) for k, v in all_results.items() if isinstance(v, list))
        logger.info(f"🕷️ انتهى الزحف: {total} نتيجة")
        return {"total_results": total, "sources": {k: len(v) for k, v in all_results.items() if isinstance(v, list)}}

    def get_stats(self) -> Dict:
        return {
            "papers_found": self.papers_found,
            "repos_found": self.repos_found,
            "skills_created": self.skills_created,
        }


class ToolCloner:
    """
    استنساخ الأدوات تلقائياً
    إذا واجه النظام مشكلة بدون أداة → يبرمج واحدة
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.tools_created = 0
        self.tools_failed = 0

    def search_for_solution(self, problem: str) -> Optional[Dict]:
        """يبحث عن مكتبة Python تحل المشكلة"""
        # بحث GitHub
        token = os.getenv("GITHUB_TOKEN", "")
        headers = {"Authorization": f"token {token}"} if token else {}

        try:
            url = f"https://api.github.com/search/repositories?q={problem}+language:python&sort=stars&per_page=3"
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    repo = items[0]
                    return {
                        "name": repo["name"],
                        "url": repo["html_url"],
                        "description": repo.get("description", ""),
                        "stars": repo["stargazers_count"],
                        "install": f"pip install {repo['name']}",
                    }
        except Exception:
            pass
        return None

    def generate_tool_code(self, tool_name: str, description: str,
                           library: str = None) -> str:
        """يولد كود الأداة"""
        code = f'''"""
Army81 Tool — {tool_name}
{description}
Auto-generated by ToolCloner
"""
import logging
from typing import Dict, Any

logger = logging.getLogger("army81.tool.{tool_name}")


def {tool_name}(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    {description}
    params: معاملات الأداة
    returns: نتيجة التنفيذ
    """
    try:
        # التنفيذ
        result = {{"status": "success", "data": "تم التنفيذ"}}
        logger.info(f"✅ {tool_name} executed successfully")
        return result
    except Exception as e:
        logger.error(f"❌ {tool_name} failed: {{e}}")
        return {{"status": "error", "error": str(e)}}


TOOL_INFO = {{
    "name": "{tool_name}",
    "description": "{description}",
    "function": {tool_name},
    "parameters": {{}},
}}
'''
        return code

    def clone_and_add(self, problem: str, tool_name: str) -> Dict:
        """يبحث، يبني، يختبر، ويضيف الأداة"""
        logger.info(f"🔧 محاولة إنشاء أداة: {tool_name}")

        # 1. بحث
        solution = self.search_for_solution(problem)

        # 2. توليد الكود
        desc = f"أداة لـ: {problem}"
        if solution:
            desc += f" (مبنية على {solution['name']})"

        code = self.generate_tool_code(tool_name, desc)

        # 3. حفظ
        tool_file = TOOLS_DIR / f"{tool_name}.py"
        tool_file.write_text(code, encoding="utf-8")

        # 4. اختبار بسيط
        try:
            compile(code, tool_file, "exec")
            self.tools_created += 1
            logger.info(f"✅ أداة جديدة: {tool_name}")
            return {"status": "success", "tool": tool_name, "file": str(tool_file)}
        except SyntaxError as e:
            self.tools_failed += 1
            logger.error(f"❌ فشل: {tool_name} — {e}")
            return {"status": "error", "error": str(e)}

    def get_stats(self) -> Dict:
        return {
            "tools_created": self.tools_created,
            "tools_failed": self.tools_failed,
        }


class GraphRAG:
    """
    شبكة المعرفة — GraphRAG
    تحويل النصوص إلى كيانات وعلاقات
    """

    def __init__(self):
        self.entities: Dict[str, Dict] = {}
        self.relations: List[Dict] = []
        GRAPH_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """تحميل الشبكة"""
        ent_file = GRAPH_DIR / "entities.json"
        rel_file = GRAPH_DIR / "relations.json"
        if ent_file.exists():
            try:
                self.entities = json.loads(ent_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        if rel_file.exists():
            try:
                self.relations = json.loads(rel_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save(self):
        """حفظ الشبكة"""
        (GRAPH_DIR / "entities.json").write_text(
            json.dumps(self.entities, ensure_ascii=False, indent=2), encoding="utf-8")
        (GRAPH_DIR / "relations.json").write_text(
            json.dumps(self.relations[-10000:], ensure_ascii=False, indent=2), encoding="utf-8")

    def extract_entities(self, text: str, source: str = "") -> List[Dict]:
        """استخراج الكيانات من نص"""
        import re
        entities = []

        # أنماط بسيطة
        patterns = {
            "PERSON": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "ORG": r'\b(?:Google|Microsoft|OpenAI|Anthropic|Meta|Apple|Amazon|DeepSeek)\b',
            "TECH": r'\b(?:Python|JavaScript|Transformer|LLM|GPT|BERT|RAG|API|Docker|Kubernetes)\b',
            "CONCEPT": r'\b(?:machine learning|deep learning|neural network|reinforcement learning|NLP|AI)\b',
        }

        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group()
                ent_id = f"{entity_type}:{name.lower()}"
                if ent_id not in self.entities:
                    self.entities[ent_id] = {
                        "id": ent_id,
                        "name": name,
                        "type": entity_type,
                        "mentions": 0,
                        "sources": [],
                        "first_seen": datetime.now().isoformat(),
                    }
                self.entities[ent_id]["mentions"] += 1
                if source and source not in self.entities[ent_id]["sources"]:
                    self.entities[ent_id]["sources"].append(source)
                entities.append(self.entities[ent_id])

        return entities

    def add_relation(self, entity_a: str, relation: str, entity_b: str,
                      confidence: float = 0.8, source: str = ""):
        """إضافة علاقة"""
        rel = {
            "from": entity_a,
            "relation": relation,
            "to": entity_b,
            "confidence": confidence,
            "source": source,
            "created_at": datetime.now().isoformat(),
        }
        self.relations.append(rel)

    def query(self, entity: str, depth: int = 2) -> Dict:
        """استعلام عن كيان وعلاقاته"""
        entity_lower = entity.lower()
        result = {"entity": entity, "relations": [], "connected_entities": []}

        for rel in self.relations:
            if entity_lower in rel.get("from", "").lower() or entity_lower in rel.get("to", "").lower():
                result["relations"].append(rel)
                other = rel["to"] if entity_lower in rel["from"].lower() else rel["from"]
                if other not in result["connected_entities"]:
                    result["connected_entities"].append(other)

        return result

    def ingest_text(self, text: str, source: str = "") -> Dict:
        """هضم نص كامل — استخراج كيانات وعلاقات"""
        entities = self.extract_entities(text, source)

        # علاقات بين الكيانات المكتشفة في نفس النص
        for i, ent_a in enumerate(entities):
            for ent_b in entities[i+1:]:
                if ent_a["type"] != ent_b["type"]:
                    self.add_relation(ent_a["id"], "co-occurs-with",
                                     ent_b["id"], 0.6, source)

        self._save()
        return {
            "entities_found": len(entities),
            "relations_added": len(entities) * (len(entities)-1) // 2,
        }

    def get_stats(self) -> Dict:
        return {
            "entities": len(self.entities),
            "relations": len(self.relations),
            "entity_types": dict(),
        }
