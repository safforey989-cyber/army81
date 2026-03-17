"""
Army81 Daily Updater - وكيل الاستخبارات والتحديث الذاتي
يعمل يومياً في الساعة 2 صباحاً لجمع التحديثات وتطبيقها
"""
import json
import os
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger("army81.updater")


class DailyUpdater:
    """
    وكيل التحديث اليومي
    - يجمع التحديثات من GitHub Trending, HuggingFace, arXiv
    - يحلل ما هو مفيد للنظام
    - يقترح تحسينات (أو يطبقها تلقائياً إذا مُفعّل)
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.updates_dir = self.base_dir / "updates"
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.updates_dir / "update_log.jsonl"

    def run_daily_update(self) -> Dict:
        """تشغيل التحديث اليومي الكامل"""
        logger.info("Starting daily update cycle...")
        timestamp = datetime.now().isoformat()
        results = {
            "timestamp": timestamp,
            "github_trending": [],
            "new_models": [],
            "arxiv_papers": [],
            "recommendations": [],
            "applied": [],
        }

        # 1. جمع GitHub Trending
        try:
            results["github_trending"] = self._fetch_github_trending()
        except Exception as e:
            logger.error(f"GitHub trending fetch failed: {e}")

        # 2. فحص نماذج Ollama الجديدة
        try:
            results["new_models"] = self._check_new_models()
        except Exception as e:
            logger.error(f"Model check failed: {e}")

        # 3. توليد التوصيات
        results["recommendations"] = self._generate_recommendations(results)

        # 4. حفظ السجل
        self._save_log(results)

        logger.info(f"Daily update complete: {len(results['recommendations'])} recommendations")
        return results

    def _fetch_github_trending(self) -> List[Dict]:
        """جمع المشاريع الرائجة على GitHub في مجال AI/Agents"""
        import requests
        trending = []
        # GitHub API search for recently updated AI agent repos
        queries = [
            "ai agent framework",
            "llm agent",
            "multi agent system",
            "self improving ai",
        ]
        headers = {}
        gh_token = os.getenv("GITHUB_TOKEN", "")
        if gh_token:
            headers["Authorization"] = f"token {gh_token}"

        for query in queries:
            try:
                resp = requests.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"{query} pushed:>{datetime.now().strftime('%Y-%m-%d')}",
                        "sort": "stars",
                        "per_page": 5,
                    },
                    headers=headers,
                    timeout=15,
                )
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        trending.append({
                            "name": item["full_name"],
                            "stars": item["stargazers_count"],
                            "description": item.get("description", ""),
                            "url": item["html_url"],
                            "language": item.get("language", ""),
                            "updated": item.get("pushed_at", ""),
                        })
            except Exception as e:
                logger.warning(f"GitHub search failed for '{query}': {e}")

        # إزالة التكرار
        seen = set()
        unique = []
        for item in trending:
            if item["name"] not in seen:
                seen.add(item["name"])
                unique.append(item)
        return unique

    def _check_new_models(self) -> List[Dict]:
        """فحص النماذج المتاحة في Ollama"""
        models = []
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[1:]:
                    parts = line.split()
                    if parts:
                        models.append({
                            "name": parts[0],
                            "size": parts[2] if len(parts) > 2 else "unknown",
                        })
        except FileNotFoundError:
            logger.info("Ollama not found locally, checking remote...")
        except Exception as e:
            logger.warning(f"Ollama check failed: {e}")
        return models

    def _generate_recommendations(self, data: Dict) -> List[Dict]:
        """توليد توصيات بناءً على البيانات المجمعة"""
        recommendations = []

        # توصيات من GitHub Trending
        for repo in data.get("github_trending", []):
            if repo.get("stars", 0) > 1000:
                recommendations.append({
                    "type": "new_tool",
                    "priority": "medium",
                    "title": f"مشروع جديد رائج: {repo['name']}",
                    "description": repo.get("description", ""),
                    "action": f"فحص واستنساخ {repo['url']}",
                    "auto_apply": False,
                })

        return recommendations

    def _save_log(self, results: Dict):
        """حفظ سجل التحديث"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(results, ensure_ascii=False) + "\n")

        # حفظ تقرير يومي
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_file = self.updates_dir / f"report_{date_str}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def get_latest_report(self) -> Dict:
        """الحصول على آخر تقرير تحديث"""
        reports = sorted(self.updates_dir.glob("report_*.json"), reverse=True)
        if reports:
            with open(reports[0], "r", encoding="utf-8") as f:
                return json.load(f)
        return {"message": "No reports yet"}

    def get_update_history(self, days: int = 7) -> List[Dict]:
        """تاريخ التحديثات"""
        history = []
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        history.append(json.loads(line))
        return history[-days:]


class SelfImprover:
    """
    محرك التحسين الذاتي
    مستوحى من: Hermes Agent + AutoResearch + OUROBOROS
    """

    def __init__(self, agents_dir: str = "agents", memory_system=None):
        self.agents_dir = Path(agents_dir)
        self.memory = memory_system
        self.improvement_log: List[Dict] = []

    def evaluate_agent(self, agent_id: str, episodes: List[Dict]) -> Dict:
        """تقييم أداء وكيل بناءً على سجل المهام"""
        if not episodes:
            return {"agent_id": agent_id, "score": 0, "issues": ["لا توجد بيانات كافية"]}

        total = len(episodes)
        successes = sum(1 for e in episodes if e.get("success"))
        success_rate = successes / total if total > 0 else 0

        issues = []
        if success_rate < 0.7:
            issues.append(f"معدل النجاح منخفض: {success_rate:.0%}")
        if success_rate < 0.5:
            issues.append("يحتاج تحسين عاجل في System Prompt")

        # تحليل أنماط الفشل
        failures = [e for e in episodes if not e.get("success")]
        if failures:
            error_patterns = {}
            for f in failures:
                result = f.get("result", "")
                if "ERROR" in result:
                    error_type = result.split("ERROR")[1][:50] if "ERROR" in result else "unknown"
                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
            if error_patterns:
                most_common = max(error_patterns, key=error_patterns.get)
                issues.append(f"خطأ متكرر: {most_common}")

        return {
            "agent_id": agent_id,
            "total_tasks": total,
            "successes": successes,
            "success_rate": round(success_rate, 2),
            "score": round(success_rate * 100),
            "issues": issues,
        }

    def suggest_improvement(self, evaluation: Dict) -> Dict:
        """اقتراح تحسين بناءً على التقييم"""
        suggestions = []

        if evaluation["success_rate"] < 0.7:
            suggestions.append({
                "type": "prompt_refinement",
                "description": "تحسين System Prompt بإضافة أمثلة وتوضيحات",
                "priority": "high",
            })

        if evaluation["success_rate"] < 0.5:
            suggestions.append({
                "type": "model_upgrade",
                "description": "ترقية النموذج لنموذج أقوى",
                "priority": "critical",
            })

        if any("خطأ متكرر" in i for i in evaluation.get("issues", [])):
            suggestions.append({
                "type": "error_handling",
                "description": "إضافة معالجة أخطاء محسنة في System Prompt",
                "priority": "high",
            })

        return {
            "agent_id": evaluation["agent_id"],
            "evaluation": evaluation,
            "suggestions": suggestions,
        }

    def apply_prompt_improvement(self, agent_id: str, new_prompt_section: str) -> bool:
        """تطبيق تحسين على System Prompt لوكيل"""
        # البحث عن ملف الوكيل
        for json_file in self.agents_dir.rglob(f"{agent_id.lower()}.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # إضافة التحسين
                old_prompt = data["system_prompt"]
                data["system_prompt"] = old_prompt + f"\n\n## تحسين مُطبق ({datetime.now().strftime('%Y-%m-%d')}):\n{new_prompt_section}"
                data["metadata"]["last_updated"] = datetime.now().isoformat()
                data["metadata"]["version"] = data["metadata"].get("version", 1) + 1

                # حفظ نسخة احتياطية
                backup_path = json_file.with_suffix(f".v{data['metadata']['version']-1}.json.bak")
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump({"system_prompt": old_prompt}, f, ensure_ascii=False)

                # حفظ التحسين
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.improvement_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "agent_id": agent_id,
                    "action": "prompt_improvement",
                    "new_version": data["metadata"]["version"],
                })

                logger.info(f"Applied prompt improvement to {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to improve {agent_id}: {e}")
                return False

        return False
