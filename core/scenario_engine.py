"""
Army81 v7 — Scenario Engine
يولّد ويقيّم سيناريوهات تدريب حقيقية لكل وكيل
170 سيناريو فردي + 10 سيناريوهات متعددة الوكلاء
"""
import os
import json
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.scenario_engine")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_FILE = os.path.join(BASE_DIR, "tests", "training_scenarios.json")
RESULTS_DIR = os.path.join(BASE_DIR, "workspace", "training_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Agent → Category mapping
AGENT_CATEGORY = {
    "cat1_science": [f"A{str(i).zfill(2)}" for i in [1,2,3,4,5,6,7,8,9]],
    "cat2_society": [f"A{str(i).zfill(2)}" for i in range(10,25)],
    "cat3_tools": [f"A{str(i).zfill(2)}" for i in range(25,35)],
    "cat4_management": [f"A{str(i).zfill(2)}" for i in range(35,43)],
    "cat5_behavior": [f"A{str(i).zfill(2)}" for i in range(43,56)],
    "cat6_leadership": [f"A{str(i).zfill(2)}" for i in range(56,72)],
    "cat7_new": [f"A{str(i).zfill(2)}" for i in range(72,82)],
}


class ScenarioEngine:
    """يولّد ويقيّم سيناريوهات التدريب"""

    def __init__(self):
        self.scenarios = self._load_scenarios()
        self._results_today = []

    def _load_scenarios(self) -> Dict:
        if os.path.exists(SCENARIOS_FILE):
            with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"categories": {}, "multi_agent_scenarios": []}

    def get_scenario(self, category: str, difficulty: str = "medium") -> Optional[Dict]:
        """يختار سيناريو عشوائي لفئة ومستوى"""
        cat_key = category
        # تحويل cat1_science → cat1_science
        cats = self.scenarios.get("categories", {})
        if cat_key not in cats:
            return None
        level_scenarios = cats[cat_key].get(difficulty, [])
        if not level_scenarios:
            return None
        return random.choice(level_scenarios)

    def get_scenario_for_agent(self, agent_id: str, level: int = 5) -> Optional[Dict]:
        """يختار سيناريو مناسب لمستوى الوكيل"""
        cat = self._agent_to_category(agent_id)
        if not cat:
            return None
        if level <= 3:
            diff = "easy"
        elif level <= 7:
            diff = "medium"
        else:
            diff = "hard"
        return self.get_scenario(cat, diff)

    def get_multi_agent_scenario(self) -> Optional[Dict]:
        """يختار سيناريو متعدد الوكلاء"""
        multi = self.scenarios.get("multi_agent_scenarios", [])
        if not multi:
            return None
        return random.choice(multi)

    def evaluate_response(self, task: str, response: str,
                          criteria: List[str] = None,
                          min_words: int = 50) -> Dict:
        """
        تقييم حقيقي متعدد الأبعاد — بدون LLM (سريع)
        """
        criteria = criteria or ["quality"]
        words = response.split()
        word_count = len(words)

        scores = {}

        # 1. الطول — هل يلبي الحد الأدنى؟
        length_score = min(10, (word_count / max(min_words, 1)) * 10)
        scores["length"] = round(length_score, 1)

        # 2. عمق — هل يحتوي فقرات وأقسام؟
        paragraphs = response.count("\n\n") + 1
        sections = response.count("#") + response.count("**")
        depth_score = min(10, paragraphs * 1.5 + sections * 0.5)
        scores["depth"] = round(depth_score, 1)

        # 3. دقة — هل يذكر مصطلحات متعلقة بالمهمة؟
        task_words = set(task.lower().split())
        response_lower = response.lower()
        relevance = sum(1 for w in task_words if len(w) > 3 and w in response_lower)
        accuracy_score = min(10, relevance * 2)
        scores["accuracy"] = round(accuracy_score, 1)

        # 4. إبداع — هل يقدم أفكاراً متنوعة؟
        unique_words = len(set(words))
        diversity = unique_words / max(word_count, 1)
        creativity_score = min(10, diversity * 20)
        scores["creativity"] = round(creativity_score, 1)

        # 5. هيكلة — هل منظم؟
        has_bullets = "•" in response or "-" in response or "1." in response
        has_headers = "#" in response or "**" in response
        structure_score = 5
        if has_bullets: structure_score += 2.5
        if has_headers: structure_score += 2.5
        scores["structure"] = round(min(10, structure_score), 1)

        # 6. لا أخطاء — هل يحتوي "خطأ" أو "ERROR"?
        has_error = "خطأ" in response or "ERROR" in response or "error" in response.lower()
        scores["no_errors"] = 0 if has_error else 10

        # المتوسط المرجّح
        total = sum(scores.values()) / len(scores)

        return {
            "scores": scores,
            "total": round(total, 1),
            "word_count": word_count,
            "passed": total >= 5.0 and not has_error,
            "grade": self._grade(total),
        }

    def evaluate_with_llm(self, task: str, response: str,
                          evaluator_agent=None) -> Dict:
        """
        تقييم عميق باستخدام LLM (أبطأ لكن أدق)
        يستخدم وكيل التقييم A74 أو A81
        """
        if not evaluator_agent:
            return self.evaluate_response(task, response)

        eval_prompt = (
            f"قيّم هذا الرد على مقياس 1-10 في 5 أبعاد:\n"
            f"المهمة: {task[:300]}\n"
            f"الرد: {response[:1500]}\n\n"
            f"أعطِ تقييماً بتنسيق JSON:\n"
            f'{{"accuracy": X, "depth": X, "creativity": X, "structure": X, "usefulness": X, "comment": "..."}}'
        )

        try:
            result = evaluator_agent.run(eval_prompt)
            text = result.result if hasattr(result, "result") else str(result)
            # حاول تحليل JSON
            import re
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                data = json.loads(json_match.group())
                total = sum(v for v in data.values() if isinstance(v, (int, float))) / 5
                return {
                    "scores": data,
                    "total": round(total, 1),
                    "passed": total >= 5.0,
                    "grade": self._grade(total),
                    "evaluator": "llm",
                }
        except Exception as e:
            logger.debug(f"LLM eval failed: {e}")

        return self.evaluate_response(task, response)

    def record_result(self, agent_id: str, scenario_id: str,
                      evaluation: Dict, elapsed: float):
        """يسجل نتيجة التدريب"""
        result = {
            "agent_id": agent_id,
            "scenario_id": scenario_id,
            "evaluation": evaluation,
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now().isoformat(),
        }
        self._results_today.append(result)

        # حفظ كل 10 نتائج
        if len(self._results_today) % 10 == 0:
            self._save_results()

    def get_leaderboard(self) -> List[Dict]:
        """ترتيب الوكلاء بالأداء"""
        agent_scores = {}
        for r in self._results_today:
            aid = r["agent_id"]
            score = r["evaluation"].get("total", 0)
            if aid not in agent_scores:
                agent_scores[aid] = {"scores": [], "tasks": 0}
            agent_scores[aid]["scores"].append(score)
            agent_scores[aid]["tasks"] += 1

        leaderboard = []
        for aid, data in agent_scores.items():
            avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            leaderboard.append({
                "agent_id": aid,
                "avg_score": round(avg, 1),
                "tasks_completed": data["tasks"],
                "grade": self._grade(avg),
            })

        leaderboard.sort(key=lambda x: x["avg_score"], reverse=True)
        return leaderboard

    def status(self) -> Dict:
        cats = self.scenarios.get("categories", {})
        total = sum(
            len(cats[c].get("easy", [])) + len(cats[c].get("medium", [])) + len(cats[c].get("hard", []))
            for c in cats
        )
        multi = len(self.scenarios.get("multi_agent_scenarios", []))
        return {
            "total_scenarios": total,
            "multi_agent_scenarios": multi,
            "results_today": len(self._results_today),
            "leaderboard_size": len(set(r["agent_id"] for r in self._results_today)),
            "categories": list(cats.keys()),
        }

    # ── Internal ──────────────────────────────

    def _agent_to_category(self, agent_id: str) -> Optional[str]:
        for cat, agents in AGENT_CATEGORY.items():
            if agent_id in agents:
                return cat
        return None

    def _grade(self, score: float) -> str:
        if score >= 9: return "A+"
        if score >= 8: return "A"
        if score >= 7: return "B+"
        if score >= 6: return "B"
        if score >= 5: return "C"
        if score >= 4: return "D"
        return "F"

    def _save_results(self):
        date = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(RESULTS_DIR, f"training_{date}.json")

        existing = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass

        existing.extend(self._results_today)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        self._results_today = []


# Singleton
_engine: Optional[ScenarioEngine] = None

def get_scenario_engine() -> ScenarioEngine:
    global _engine
    if _engine is None:
        _engine = ScenarioEngine()
    return _engine
