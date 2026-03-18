"""
Army81 v5 - Self Builder
النظام يبني نفسه — يضيف طبقات معرفة ومهارات وموصلات
بدون تدخل بشري إلا للموافقة
"""
import os
import json
import logging
import subprocess
import importlib
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("army81.self_builder")

# ── مسارات النظام ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
PENDING_FILE = os.path.join(WORKSPACE_DIR, "pending_approvals.json")
DISCOVERY_LOG = os.path.join(WORKSPACE_DIR, "discovery_log.json")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
AGENTS_DIR = os.path.join(BASE_DIR, "agents")

os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)


class SelfBuilder:
    """
    النظام يبني نفسه — يضيف طبقات معرفة ومهارات وموصلات
    بدون تدخل بشري إلا للموافقة
    """

    def __init__(self):
        self.serper_key = os.getenv("SERPER_API_KEY", "")
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self._load_pending()
        self._load_discovery_log()

    # ══════════════════════════════════════════════════
    # 1. اكتشاف وإضافة المعرفة
    # ══════════════════════════════════════════════════

    def discover_and_add_knowledge(self) -> Dict:
        """
        يبحث يومياً عن:
        - مستودعات GitHub trending في AI agents
        - مكتبات Python جديدة مفيدة
        - نماذج HuggingFace جديدة
        ثم يقترح إضافتها
        """
        discoveries = {
            "github": [],
            "pypi": [],
            "timestamp": datetime.now().isoformat(),
        }

        # 1. GitHub trending repos
        github_repos = self._search_github_trending()
        for repo in github_repos:
            score = self._evaluate_repo(repo)
            if score >= 0.7:
                discoveries["github"].append({
                    "name": repo["name"],
                    "full_name": repo.get("full_name", repo["name"]),
                    "stars": repo.get("stargazers_count", 0),
                    "description": repo.get("description", ""),
                    "score": score,
                    "url": repo.get("html_url", ""),
                })

        # 2. PyPI new AI packages
        pypi_pkgs = self._search_pypi_trending()
        for pkg in pypi_pkgs:
            discoveries["pypi"].append({
                "name": pkg["name"],
                "description": pkg.get("description", ""),
                "version": pkg.get("version", ""),
            })

        # 3. إنشاء طلبات موافقة للعناصر المكتشفة
        for repo in discoveries["github"][:3]:  # أفضل 3
            self._create_approval_request(
                title=f"اقتراح إضافة: {repo['name']}",
                description=(
                    f"مستودع GitHub: {repo['full_name']}\n"
                    f"النجوم: {repo['stars']}\n"
                    f"الوصف: {repo['description']}\n"
                    f"الرابط: {repo['url']}\n"
                    f"درجة الفائدة: {repo['score']:.0%}"
                ),
                action_type="add_knowledge",
                action_data={"source": "github", "repo": repo["full_name"]},
            )

        # حفظ سجل الاكتشاف
        self._save_discovery_log(discoveries)
        logger.info(
            f"Discovered: {len(discoveries['github'])} repos, "
            f"{len(discoveries['pypi'])} packages"
        )
        return discoveries

    def add_knowledge_layer(self, source: str, topic: str, agent_id: str = None):
        """
        يضيف طبقة معرفة جديدة لوكيل معين:
        - يجلب المحتوى من المصدر
        - يعالجه ويضغطه
        - يحفظه في Chroma للوكيل المناسب
        """
        content = self._fetch_knowledge(source, topic)
        if not content:
            logger.warning(f"No content fetched for topic '{topic}' from '{source}'")
            return None

        # حدد الوكيل المناسب تلقائياً
        if not agent_id:
            agent_id = self._find_best_agent(topic)

        # حفظ في Chroma
        try:
            from memory.chroma_memory import remember
            result = remember(
                f"[Knowledge Layer: {topic}]\n{content[:2000]}",
                agent_id=agent_id,
                tags=[topic, source, "knowledge_layer"],
            )
            logger.info(f"Added knowledge layer '{topic}' for agent {agent_id}")
            return {"agent_id": agent_id, "topic": topic, "status": "saved"}
        except Exception as e:
            logger.error(f"Failed to save knowledge layer: {e}")
            return {"error": str(e)}

    # ══════════════════════════════════════════════════
    # 2. إضافة مهارات جديدة
    # ══════════════════════════════════════════════════

    def add_skill(self, skill_name: str, skill_code: str) -> Dict:
        """
        يضيف مهارة جديدة للنظام:
        - يكتب الكود في skills/
        - يختبره
        - يربطه بالوكلاء المناسبين
        """
        skill_file = os.path.join(SKILLS_DIR, f"{skill_name}.py")

        # اكتب الكود
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(skill_code)

        # اختبره
        test_result = self._test_skill(skill_name, skill_file)

        if test_result["success"]:
            logger.info(f"Skill '{skill_name}' added and tested successfully")
            return {
                "skill": skill_name,
                "file": skill_file,
                "status": "added",
                "test": "passed",
            }
        else:
            # احذف الملف الفاشل
            os.remove(skill_file)
            logger.warning(f"Skill '{skill_name}' failed testing: {test_result['error']}")
            return {
                "skill": skill_name,
                "status": "failed",
                "error": test_result["error"],
            }

    # ══════════════════════════════════════════════════
    # 3. إضافة موصلات خارجية
    # ══════════════════════════════════════════════════

    def add_connector(self, service: str, api_key_needed: bool = True) -> Dict:
        """
        يضيف موصل لخدمة خارجية جديدة
        إذا احتاج API key → يطلب منك عبر نظام الموافقات
        """
        if api_key_needed:
            self._create_approval_request(
                title=f"أحتاج API Key لـ {service}",
                description=(
                    f"اكتشفت أن {service} سيفيد النظام.\n"
                    f"أحتاج مفتاح API لإضافة الموصل."
                ),
                action_type="request_api_key",
                action_data={"service": service},
            )
            return {"service": service, "status": "awaiting_api_key"}
        else:
            connector_code = self._generate_connector_template(service)
            return self.add_skill(f"{service}_connector", connector_code)

    # ══════════════════════════════════════════════════
    # 4. التقييم الذاتي الأسبوعي
    # ══════════════════════════════════════════════════

    def weekly_self_assessment(self) -> Dict:
        """
        كل أسبوع — النظام يسأل نفسه:
        ما الذي أفتقده؟ ما الذي يمكنني إضافته؟
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "knowledge_gaps": [],
            "missing_skills": [],
            "useful_connectors": [],
            "auto_items": [],
            "approval_items": [],
        }

        # 1. فجوات المعرفة
        report["knowledge_gaps"] = self.identify_knowledge_gaps()

        # 2. مهارات مفقودة
        report["missing_skills"] = self.identify_missing_skills()

        # 3. موصلات مفيدة
        report["useful_connectors"] = self.identify_useful_connectors()

        # 4. تصنيف: ما يمكن إضافته تلقائياً vs يحتاج موافقة
        for gap in report["knowledge_gaps"]:
            if gap.get("auto_fixable"):
                report["auto_items"].append(gap["topic"])
            else:
                report["approval_items"].append(gap["topic"])

        # إنشاء طلب موافقة بالتقرير
        self._create_approval_request(
            title="خطة التطوير الذاتي الأسبوعية",
            description=self._format_assessment_report(report),
            action_type="weekly_assessment",
            action_data=report,
        )

        # حفظ التقرير
        report_path = os.path.join(WORKSPACE_DIR, "reports",
                                    f"self_assessment_{datetime.now().strftime('%Y-%m-%d')}.json")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Weekly self-assessment complete: {len(report['knowledge_gaps'])} gaps found")
        return report

    def identify_knowledge_gaps(self) -> List[Dict]:
        """يحدد الفجوات المعرفية بناءً على المهام الفاشلة"""
        gaps = []
        episodes_db = os.path.join(BASE_DIR, "memory", "episodic.db")

        if os.path.exists(episodes_db):
            try:
                import sqlite3
                conn = sqlite3.connect(episodes_db)
                cursor = conn.execute(
                    "SELECT task_summary, result_summary FROM episodes "
                    "WHERE success = 0 ORDER BY created_at DESC LIMIT 20"
                )
                failed_tasks = cursor.fetchall()
                conn.close()

                # تحليل أنماط الفشل
                topic_failures = {}
                for task, result in failed_tasks:
                    topic = self._classify_topic(task)
                    topic_failures.setdefault(topic, 0)
                    topic_failures[topic] += 1

                for topic, count in topic_failures.items():
                    if count >= 2:
                        gaps.append({
                            "topic": topic,
                            "failure_count": count,
                            "auto_fixable": count < 5,
                            "suggestion": f"إضافة معرفة عن {topic} من مصادر موثوقة",
                        })
            except Exception as e:
                logger.warning(f"Could not analyze episodic DB: {e}")

        # فجوات ثابتة بناءً على قدرات النظام
        existing_skills = set()
        if os.path.exists(SKILLS_DIR):
            existing_skills = {
                f.replace(".py", "") for f in os.listdir(SKILLS_DIR)
                if f.endswith(".py") and f != "__init__.py"
            }

        expected_skills = {
            "web_scraper", "pdf_reader", "email_sender",
            "data_analyzer", "image_analyzer", "translation",
        }
        missing = expected_skills - existing_skills
        for skill in missing:
            gaps.append({
                "topic": skill,
                "failure_count": 0,
                "auto_fixable": False,
                "suggestion": f"مهارة '{skill}' غير موجودة",
            })

        return gaps

    def identify_missing_skills(self) -> List[str]:
        """يحدد المهارات المفقودة"""
        existing = set()
        if os.path.exists(SKILLS_DIR):
            existing = {
                f.replace(".py", "") for f in os.listdir(SKILLS_DIR)
                if f.endswith(".py") and f != "__init__.py"
            }

        desired = [
            "web_scraper", "pdf_reader", "email_sender",
            "data_analyzer", "image_analyzer", "translation",
            "calendar_manager", "task_tracker",
        ]
        return [s for s in desired if s not in existing]

    def identify_useful_connectors(self) -> List[Dict]:
        """يحدد الموصلات المفيدة التي يمكن إضافتها"""
        connectors = []
        env_keys = set(os.environ.keys())

        potential = [
            {"service": "telegram", "key": "TELEGRAM_BOT_TOKEN",
             "benefit": "تواصل مباشر مع المستخدم"},
            {"service": "slack", "key": "SLACK_BOT_TOKEN",
             "benefit": "تكامل مع فرق العمل"},
            {"service": "notion", "key": "NOTION_API_KEY",
             "benefit": "توثيق تلقائي"},
            {"service": "linear", "key": "LINEAR_API_KEY",
             "benefit": "إدارة المهام"},
            {"service": "huggingface", "key": "HF_TOKEN",
             "benefit": "نماذج إضافية"},
        ]

        for conn in potential:
            has_key = conn["key"] in env_keys
            connectors.append({
                "service": conn["service"],
                "configured": has_key,
                "benefit": conn["benefit"],
                "priority": "high" if not has_key else "configured",
            })

        return connectors

    # ══════════════════════════════════════════════════
    # دوال مساعدة داخلية
    # ══════════════════════════════════════════════════

    def _search_github_trending(self) -> List[Dict]:
        """بحث في GitHub عن المستودعات الرائجة"""
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": "AI agent framework language:python stars:>500 pushed:>2026-01-01",
                "sort": "stars",
                "order": "desc",
                "per_page": 10,
            }
            headers = {"Accept": "application/vnd.github.v3+json"}
            token = os.getenv("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"

            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.json().get("items", [])
        except Exception as e:
            logger.warning(f"GitHub search failed: {e}")
        return []

    def _search_pypi_trending(self) -> List[Dict]:
        """بحث عن مكتبات Python جديدة مفيدة"""
        packages = []
        keywords = ["ai-agent", "llm-tools", "langchain"]

        for kw in keywords:
            try:
                url = f"https://pypi.org/pypi/{kw}/json"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    packages.append({
                        "name": data["info"]["name"],
                        "description": data["info"]["summary"],
                        "version": data["info"]["version"],
                    })
            except Exception:
                pass

        return packages

    def _evaluate_repo(self, repo: Dict) -> float:
        """تقييم مستودع GitHub — 0 إلى 1"""
        score = 0.0
        stars = repo.get("stargazers_count", 0)
        desc = (repo.get("description") or "").lower()

        # نجوم
        if stars > 10000: score += 0.3
        elif stars > 5000: score += 0.25
        elif stars > 1000: score += 0.2
        elif stars > 500: score += 0.1

        # كلمات مفتاحية مفيدة
        useful_kw = ["agent", "llm", "tool", "rag", "memory", "multi-agent"]
        for kw in useful_kw:
            if kw in desc:
                score += 0.1

        # Python
        if repo.get("language", "").lower() == "python":
            score += 0.1

        # نشط (آخر تحديث)
        updated = repo.get("updated_at", "")
        if "2026" in updated:
            score += 0.1

        return min(score, 1.0)

    def _fetch_knowledge(self, source: str, topic: str) -> Optional[str]:
        """جلب محتوى من مصدر معين"""
        if source == "github":
            return self._fetch_from_github(topic)
        elif source == "arxiv":
            return self._fetch_from_arxiv(topic)
        elif source == "web":
            return self._fetch_from_web(topic)
        return None

    def _fetch_from_github(self, repo_name: str) -> Optional[str]:
        """جلب README من مستودع GitHub"""
        try:
            url = f"https://api.github.com/repos/{repo_name}/readme"
            headers = {"Accept": "application/vnd.github.v3.raw"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.text[:3000]
        except Exception as e:
            logger.warning(f"GitHub fetch failed: {e}")
        return None

    def _fetch_from_arxiv(self, topic: str) -> Optional[str]:
        """جلب ملخصات من arXiv"""
        try:
            from tools.science_tools import search_arxiv
            return search_arxiv(topic, max_results=3)
        except Exception:
            return None

    def _fetch_from_web(self, topic: str) -> Optional[str]:
        """بحث ويب بسيط"""
        if not self.serper_key:
            return None
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                json={"q": topic, "num": 3},
                headers={"X-API-KEY": self.serper_key},
                timeout=10,
            )
            if r.status_code == 200:
                results = r.json().get("organic", [])
                return "\n".join(
                    f"- {r['title']}: {r.get('snippet', '')}"
                    for r in results[:3]
                )
        except Exception:
            pass
        return None

    def _find_best_agent(self, topic: str) -> str:
        """يحدد أفضل وكيل لموضوع معين"""
        topic_agent_map = {
            "medical": "A10", "financial": "A07", "code": "A21",
            "research": "A04", "strategy": "A01", "news": "A04",
            "security": "A30", "education": "A41", "legal": "A55",
        }
        topic_key = self._classify_topic(topic)
        return topic_agent_map.get(topic_key, "A01")

    def _classify_topic(self, text: str) -> str:
        """تصنيف الموضوع"""
        text_lower = text.lower()
        topics = {
            "medical": ["طب", "دواء", "مرض", "علاج", "health", "medical"],
            "financial": ["سوق", "سهم", "اقتصاد", "مالي", "finance", "stock"],
            "code": ["كود", "برمج", "python", "api", "code", "programming"],
            "research": ["بحث", "ورقة", "دراسة", "research", "paper", "arxiv"],
            "strategy": ["استراتيج", "خطة", "قرار", "strategy", "plan"],
            "news": ["خبر", "أخبار", "news", "breaking"],
        }
        for topic, kws in topics.items():
            if any(k in text_lower for k in kws):
                return topic
        return "general"

    def _test_skill(self, skill_name: str, skill_file: str) -> Dict:
        """اختبار مهارة جديدة — import فقط"""
        try:
            # اختبار بسيط: هل يمكن import الملف بدون أخطاء
            spec = importlib.util.spec_from_file_location(skill_name, skill_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_connector_template(self, service: str) -> str:
        """يولّد كود قالب لموصل جديد"""
        return f'''"""
Army81 Connector — {service}
Auto-generated by SelfBuilder
"""
import os
import requests
import logging

logger = logging.getLogger("army81.connector.{service}")


class {service.capitalize()}Connector:
    def __init__(self):
        self.api_key = os.getenv("{service.upper()}_API_KEY", "")
        self.base_url = ""

    def connect(self) -> bool:
        """اختبار الاتصال"""
        if not self.api_key:
            logger.warning("{service} API key not configured")
            return False
        return True

    def fetch(self, query: str) -> str:
        """جلب بيانات"""
        if not self.connect():
            return "غير متصل"
        # TODO: implement for {service}
        return f"{service}: not implemented yet"


def main():
    c = {service.capitalize()}Connector()
    print(c.fetch("test"))


if __name__ == "__main__":
    main()
'''

    # ══════════════════════════════════════════════════
    # نظام الموافقات
    # ══════════════════════════════════════════════════

    def _load_pending(self):
        """تحميل الطلبات المعلقة"""
        if os.path.exists(PENDING_FILE):
            try:
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    self.pending = json.load(f)
            except Exception:
                self.pending = []
        else:
            self.pending = []

    def _save_pending(self):
        """حفظ الطلبات المعلقة"""
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(self.pending, f, ensure_ascii=False, indent=2)

    def _create_approval_request(self, title: str, description: str,
                                  action_type: str, action_data: Dict = None):
        """إنشاء طلب موافقة جديد"""
        request = {
            "id": f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.pending)}",
            "title": title,
            "description": description,
            "action_type": action_type,
            "action_data": action_data or {},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        self.pending.append(request)
        self._save_pending()
        logger.info(f"Created approval request: {request['id']} — {title}")
        return request

    def approve_request(self, request_id: str) -> Dict:
        """الموافقة على طلب"""
        for req in self.pending:
            if req["id"] == request_id:
                req["status"] = "approved"
                req["approved_at"] = datetime.now().isoformat()
                self._save_pending()

                # تنفيذ الإجراء
                return self._execute_approved_action(req)

        return {"error": f"Request {request_id} not found"}

    def reject_request(self, request_id: str) -> Dict:
        """رفض طلب"""
        for req in self.pending:
            if req["id"] == request_id:
                req["status"] = "rejected"
                req["rejected_at"] = datetime.now().isoformat()
                self._save_pending()
                return {"status": "rejected", "id": request_id}
        return {"error": f"Request {request_id} not found"}

    def get_pending_requests(self) -> List[Dict]:
        """الحصول على الطلبات المعلقة"""
        return [r for r in self.pending if r["status"] == "pending"]

    def _execute_approved_action(self, request: Dict) -> Dict:
        """تنفيذ إجراء بعد الموافقة"""
        action_type = request.get("action_type")
        action_data = request.get("action_data", {})

        if action_type == "add_knowledge":
            source = action_data.get("source", "github")
            repo = action_data.get("repo", "")
            return self.add_knowledge_layer(source, repo)

        elif action_type == "add_skill":
            return self.add_skill(
                action_data.get("name", "unknown"),
                action_data.get("code", ""),
            )

        logger.info(f"Executed approved action: {action_type}")
        return {"status": "executed", "action": action_type}

    # ══════════════════════════════════════════════════
    # سجل الاكتشافات
    # ══════════════════════════════════════════════════

    def _load_discovery_log(self):
        """تحميل سجل الاكتشافات"""
        if os.path.exists(DISCOVERY_LOG):
            try:
                with open(DISCOVERY_LOG, "r", encoding="utf-8") as f:
                    self.discovery_log = json.load(f)
            except Exception:
                self.discovery_log = []
        else:
            self.discovery_log = []

    def _save_discovery_log(self, discoveries: Dict):
        """حفظ سجل الاكتشافات"""
        self.discovery_log.append(discoveries)
        # احتفظ بآخر 30 فقط
        self.discovery_log = self.discovery_log[-30:]
        with open(DISCOVERY_LOG, "w", encoding="utf-8") as f:
            json.dump(self.discovery_log, f, ensure_ascii=False, indent=2)

    def _format_assessment_report(self, report: Dict) -> str:
        """تنسيق تقرير التقييم الذاتي"""
        lines = [
            "## تقرير التحسين الذاتي الأسبوعي\n",
            f"التاريخ: {report['timestamp'][:10]}\n",
        ]

        if report["knowledge_gaps"]:
            lines.append("\n### فجوات معرفية:")
            for gap in report["knowledge_gaps"]:
                lines.append(f"  - {gap['topic']} (فشل {gap['failure_count']} مرة)")

        if report["missing_skills"]:
            lines.append("\n### مهارات مفقودة:")
            for skill in report["missing_skills"]:
                lines.append(f"  - {skill}")

        if report["useful_connectors"]:
            lines.append("\n### موصلات مفيدة:")
            for conn in report["useful_connectors"]:
                status = "متصل" if conn["configured"] else "غير متصل"
                lines.append(f"  - {conn['service']}: {conn['benefit']} [{status}]")

        if report["auto_items"]:
            lines.append(f"\n### سأضيف تلقائياً: {', '.join(report['auto_items'])}")
        if report["approval_items"]:
            lines.append(f"### يحتاج موافقتك: {', '.join(report['approval_items'])}")

        return "\n".join(lines)


# ── للاختبار المباشر ────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    builder = SelfBuilder()

    print("=== Knowledge Gaps ===")
    gaps = builder.identify_knowledge_gaps()
    for g in gaps:
        print(f"  - {g['topic']}: {g['suggestion']}")

    print("\n=== Missing Skills ===")
    skills = builder.identify_missing_skills()
    for s in skills:
        print(f"  - {s}")

    print("\n=== Useful Connectors ===")
    connectors = builder.identify_useful_connectors()
    for c in connectors:
        print(f"  - {c['service']}: {c['benefit']} ({'configured' if c['configured'] else 'missing'})")
