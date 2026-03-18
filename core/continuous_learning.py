"""
Army81 — Continuous Learning Engine
محرك التعلم المستمر 24/7 — يعمل بدون توقف
"""
import json, time, logging, random, os, threading
from datetime import datetime
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger("army81.continuous_learning")
WORKSPACE = Path("workspace")
LEARNING_DIR = WORKSPACE / "learning"
BENCHMARKS_DIR = WORKSPACE / "benchmarks"

class ContinuousLearning:
    """
    حلقة التعلم المستمرة — تعمل 24/7
    - تدريب ذاتي عبر سيناريوهات
    - تقييم مستمر لكل وكيل
    - تحسين تلقائي للضعفاء
    - مشاركة المعرفة بين الوكلاء
    """

    BENCHMARK_TASKS = {
        "medical": [
            {"task": "مريض 45 سنة يعاني من ألم صدري وضيق تنفس. التاريخ: سكري. ما التشخيص التفريقي؟", "min_score": 60},
            {"task": "صمم بروتوكول علاج لمريض ضغط مرتفع مع فشل كلوي مزمن", "min_score": 65},
            {"task": "ما الفرق بين التهاب الكبد A وB وC من حيث الآلية والعلاج؟", "min_score": 70},
        ],
        "coding": [
            {"task": "اكتب دالة Python لحساب أقصر مسار في رسم بياني (Dijkstra) مع شرح التعقيد", "min_score": 70},
            {"task": "صمم REST API بـ FastAPI لنظام إدارة مهام مع authentication", "min_score": 65},
            {"task": "اكتب كود يقرأ CSV كبير (1GB) بكفاءة مع معالجة الأخطاء", "min_score": 60},
        ],
        "strategy": [
            {"task": "ضع خطة استراتيجية لشركة AI ناشئة تدخل السوق العربي", "min_score": 60},
            {"task": "حلل SWOT لتوسع شركة تقنية من الخليج إلى أفريقيا", "min_score": 55},
            {"task": "صمم خطة إدارة أزمة لشركة تواجه خرق بيانات ضخم", "min_score": 65},
        ],
        "financial": [
            {"task": "حلل جدوى استثمار $500K في مشروع blockchain في الشرق الأوسط", "min_score": 60},
            {"task": "قارن بين 3 استراتيجيات تحوط ضد التضخم في 2026", "min_score": 55},
        ],
        "research": [
            {"task": "لخص أهم 5 تطورات في LLM agents خلال 2025-2026 مع مراجع", "min_score": 60},
            {"task": "قارن بين RAG و Fine-tuning: متى نستخدم كل واحد؟", "min_score": 65},
        ],
        "security": [
            {"task": "حلل أمنياً تطبيق ويب يستخدم JWT + OAuth2. ما الثغرات المحتملة؟", "min_score": 65},
            {"task": "صمم خطة استجابة لحادث اختراق بيانات 100K مستخدم", "min_score": 60},
        ],
        "arabic": [
            {"task": "اكتب مقالاً تحليلياً عن مستقبل الذكاء الاصطناعي في التعليم العربي", "min_score": 55},
            {"task": "ترجم هذا المفهوم التقني بدقة مع شرح مبسط: Retrieval Augmented Generation", "min_score": 60},
        ],
    }

    AGENT_SPECIALTIES = {
        "A01": "strategy", "A02": "research", "A03": "strategy",
        "A05": "coding", "A06": "research", "A07": "medical",
        "A08": "financial", "A09": "security", "A10": "research",
        "A11": "arabic", "A12": "arabic", "A13": "strategy",
        "A14": "strategy", "A15": "research", "A16": "strategy",
        "A28": "strategy", "A29": "strategy", "A31": "security",
        "A34": "financial", "A38": "research", "A41": "financial",
        "A42": "financial", "A47": "arabic", "A48": "research",
        "A51": "coding", "A52": "medical", "A57": "coding",
    }

    def __init__(self):
        self.scores: Dict[str, List[Dict]] = {}
        self.training_rounds = 0
        self.improvements_found = 0
        self.running = False
        LEARNING_DIR.mkdir(parents=True, exist_ok=True)
        BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_scores()

    def _load_scores(self):
        score_file = LEARNING_DIR / "agent_scores.json"
        if score_file.exists():
            try:
                self.scores = json.loads(score_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_scores(self):
        score_file = LEARNING_DIR / "agent_scores.json"
        score_file.write_text(json.dumps(self.scores, ensure_ascii=False, indent=2), encoding="utf-8")

    def evaluate_agent(self, agent_id: str, run_fn=None) -> Dict:
        specialty = self.AGENT_SPECIALTIES.get(agent_id, "research")
        tasks = self.BENCHMARK_TASKS.get(specialty, self.BENCHMARK_TASKS["research"])

        results = []
        for bench in tasks[:3]:
            score = 50.0
            if run_fn:
                try:
                    result = run_fn(agent_id, bench["task"])
                    result_text = result.get("result", "") if isinstance(result, dict) else str(result)
                    score = self._score_response(result_text, bench.get("min_score", 50))
                except Exception:
                    score = 10.0
            results.append({"task": bench["task"][:80], "score": score})
            time.sleep(1)

        avg_score = sum(r["score"] for r in results) / max(len(results), 1)

        if agent_id not in self.scores:
            self.scores[agent_id] = []
        self.scores[agent_id].append({
            "score": avg_score,
            "tasks_tested": len(results),
            "details": results,
            "timestamp": datetime.now().isoformat(),
        })
        self.scores[agent_id] = self.scores[agent_id][-20:]
        self._save_scores()

        return {"agent_id": agent_id, "score": avg_score, "specialty": specialty, "details": results}

    def _score_response(self, text: str, min_score: float = 50) -> float:
        if not text: return 0.0
        score = 0.0
        if len(text) > 50: score += 10
        if len(text) > 200: score += 15
        if len(text) > 500: score += 10
        if any(m in text for m in ["1.", "2.", "3.", "##", "- "]): score += 15
        if any(w in text for w in ["لأن", "بسبب", "نتيجة", "because"]): score += 10
        if "```" in text: score += 10
        if any(w in text for w in ["أولاً", "ثانياً", "أخيراً", "first", "second"]): score += 10
        if len(text) > 100 and "خطأ" not in text.lower(): score += 10
        if any(w in text for w in ["تحليل", "استنتاج", "توصية", "conclusion"]): score += 10
        return min(score, 100.0)

    def identify_weak_agents(self, threshold: float = 50.0) -> List[Dict]:
        weak = []
        for agent_id, history in self.scores.items():
            if history:
                latest = history[-1]["score"]
                if latest < threshold:
                    weak.append({
                        "agent_id": agent_id,
                        "score": latest,
                        "specialty": self.AGENT_SPECIALTIES.get(agent_id, "unknown"),
                        "trend": "declining" if len(history) > 1 and history[-1]["score"] < history[-2]["score"] else "stable",
                    })
        return sorted(weak, key=lambda x: x["score"])

    def train_agent(self, agent_id: str, run_fn=None) -> Dict:
        specialty = self.AGENT_SPECIALTIES.get(agent_id, "research")
        tasks = self.BENCHMARK_TASKS.get(specialty, self.BENCHMARK_TASKS["research"])

        logger.info(f"Training {agent_id} on {specialty}")

        results = []
        for bench in tasks:
            if run_fn:
                try:
                    enhanced_task = f"""هذه مهمة تدريبية. أجب بأفضل ما يمكنك مع:
1. تحليل عميق ومنظم
2. أمثلة واقعية
3. مراجع إن أمكن
4. خلاصة واضحة

المهمة: {bench['task']}"""
                    result = run_fn(agent_id, enhanced_task)
                    result_text = result.get("result", "") if isinstance(result, dict) else str(result)
                    score = self._score_response(result_text)
                    results.append({"score": score, "improved": score > bench.get("min_score", 50)})
                except Exception as e:
                    results.append({"score": 0, "error": str(e)[:100]})
            time.sleep(2)

        self.training_rounds += 1
        improved = sum(1 for r in results if r.get("improved", False))
        if improved > 0:
            self.improvements_found += 1

        return {
            "agent_id": agent_id,
            "tasks_trained": len(results),
            "improved": improved,
            "training_round": self.training_rounds,
        }

    def knowledge_sharing_round(self, agents: List[str], run_fn=None) -> Dict:
        """جولة مشاركة معرفة بين الوكلاء"""
        if len(agents) < 2:
            return {"error": "need at least 2 agents"}

        teacher = agents[0]
        students = agents[1:]
        specialty = self.AGENT_SPECIALTIES.get(teacher, "research")

        teacher_knowledge = ""
        if run_fn:
            try:
                result = run_fn(teacher, f"أنت الخبير. شارك أهم 5 دروس تعلمتها في مجال {specialty}. كن محدداً.")
                teacher_knowledge = result.get("result", "") if isinstance(result, dict) else str(result)
            except Exception:
                pass

        student_results = []
        for student in students[:3]:
            if run_fn and teacher_knowledge:
                try:
                    result = run_fn(student, f"تعلم من هذه الدروس وطبقها على تخصصك:\n{teacher_knowledge[:500]}")
                    student_results.append({"student": student, "learned": True})
                except Exception:
                    student_results.append({"student": student, "learned": False})
            time.sleep(1)

        return {
            "teacher": teacher,
            "students": students,
            "knowledge_shared": len(teacher_knowledge),
            "students_learned": sum(1 for s in student_results if s.get("learned")),
        }

    def run_training_cycle(self, run_fn=None, max_agents: int = 10) -> Dict:
        logger.info("Starting training cycle")
        cycle_results = {
            "evaluated": 0, "trained": 0, "improved": 0,
            "knowledge_shared": 0, "timestamp": datetime.now().isoformat(),
        }

        # 1. Evaluate sample
        agent_ids = list(self.AGENT_SPECIALTIES.keys())
        sample = random.sample(agent_ids, min(max_agents, len(agent_ids)))

        for aid in sample:
            self.evaluate_agent(aid, run_fn)
            cycle_results["evaluated"] += 1
            time.sleep(1)

        # 2. Train weak agents
        weak = self.identify_weak_agents(50.0)
        for w in weak[:3]:
            self.train_agent(w["agent_id"], run_fn)
            cycle_results["trained"] += 1

        # 3. Knowledge sharing
        if len(sample) >= 4:
            top = sorted(sample, key=lambda a: (self.scores.get(a, [{}])[-1:] or [{"score":0}])[0].get("score",0), reverse=True)
            self.knowledge_sharing_round(top[:4], run_fn)
            cycle_results["knowledge_shared"] += 1

        # Save results
        cycle_file = LEARNING_DIR / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        cycle_file.write_text(json.dumps(cycle_results, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info(f"Cycle done: {cycle_results}")
        return cycle_results

    def get_leaderboard(self) -> List[Dict]:
        board = []
        for agent_id, history in self.scores.items():
            if history:
                latest = history[-1]
                board.append({
                    "agent_id": agent_id,
                    "score": latest["score"],
                    "specialty": self.AGENT_SPECIALTIES.get(agent_id, "unknown"),
                    "evaluations": len(history),
                    "trend": "up" if len(history)>1 and history[-1]["score"]>history[-2]["score"] else "stable",
                })
        return sorted(board, key=lambda x: x["score"], reverse=True)

    def get_stats(self) -> Dict:
        return {
            "training_rounds": self.training_rounds,
            "improvements_found": self.improvements_found,
            "agents_tracked": len(self.scores),
            "total_evaluations": sum(len(h) for h in self.scores.values()),
        }
