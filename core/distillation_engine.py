"""
Army81 — Knowledge Distillation + Model Merger
التقطير المعرفي — Flash يتعلم من Pro
دمج النماذج المفتوحة لإنشاء Army81-Core
"""
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.distillation_engine")

WORKSPACE = Path("workspace")
DISTILL_DIR = WORKSPACE / "distillation"
MERGE_DIR = WORKSPACE / "model_merges"


class DistillationEngine:
    """
    CoT-Guided Knowledge Distillation
    النماذج الكبيرة تعلم الصغيرة عبر خطوات التفكير
    """

    TEACHER_STUDENT_PAIRS = [
        {"teacher": "gemini-pro",    "student": "gemini-flash",  "domain": "general"},
        {"teacher": "claude-smart",  "student": "claude-fast",   "domain": "critical"},
        {"teacher": "deepseek-r1",   "student": "deepseek-chat", "domain": "reasoning"},
        {"teacher": "claude-smart",  "student": "qwen-free",     "domain": "arabic"},
        {"teacher": "gemini-pro",    "student": "llama-free",    "domain": "simple"},
    ]

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.gap_measurements = {}
        DISTILL_DIR.mkdir(parents=True, exist_ok=True)
        # عدّ الأمثلة الموجودة فعلاً على القرص
        self.examples_stored = len(list(DISTILL_DIR.glob("*.json")))

    def record_teacher_solution(self, task_type: str, task: str,
                                 solution: str, model: str,
                                 cot_steps: str = "") -> Dict:
        """
        يسجل حل المعلم مع خطوات التفكير
        """
        record = {
            "id": f"DIST-{self.examples_stored:06d}",
            "task_type": task_type,
            "task": task[:500],
            "solution": solution[:2000],
            "cot_steps": cot_steps[:1500],
            "teacher_model": model,
            "quality_score": self._score_solution(solution),
            "created_at": datetime.now().isoformat(),
        }

        # حفظ في ملف
        type_dir = DISTILL_DIR / task_type
        type_dir.mkdir(exist_ok=True)
        record_file = type_dir / f"{record['id']}.json"
        record_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        self.examples_stored += 1
        logger.info(f"📝 تسجيل مثال تعليمي: {task_type} — {model}")
        return record

    def get_examples_for_student(self, task_type: str, student_model: str,
                                  k: int = 5) -> str:
        """
        يجلب أفضل k أمثلة من المعلم لنفس نوع المهمة
        """
        type_dir = DISTILL_DIR / task_type
        if not type_dir.exists():
            return ""

        examples = []
        for f in sorted(type_dir.glob("*.json"), reverse=True)[:k*2]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("quality_score", 0) > 60:
                    examples.append(data)
            except Exception:
                continue

        if not examples:
            return ""

        # أفضل k
        examples.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        examples = examples[:k]

        # تنسيق
        ctx = "## أمثلة ناجحة من نماذج خبيرة:\n"
        for i, ex in enumerate(examples, 1):
            ctx += f"\n### مثال {i} ({ex['teacher_model']}):\n"
            ctx += f"المهمة: {ex['task'][:200]}\n"
            if ex.get("cot_steps"):
                ctx += f"خطوات التفكير: {ex['cot_steps'][:300]}\n"
            ctx += f"الحل: {ex['solution'][:300]}\n"

        return ctx[:2000]

    def measure_gap(self, task_type: str, task: str,
                     teacher_fn=None, student_fn=None) -> Dict:
        """
        يقيس الفجوة بين المعلم والطالب
        إذا < 10% → استخدم الطالب دائماً (أرخص)
        """
        result = {"task_type": task_type, "gap_percent": 50.0}

        if teacher_fn and student_fn:
            try:
                t_start = time.time()
                teacher_result = teacher_fn(task)
                t_time = time.time() - t_start

                s_start = time.time()
                student_result = student_fn(task)
                s_time = time.time() - s_start

                t_score = self._score_solution(teacher_result.get("result", ""))
                s_score = self._score_solution(student_result.get("result", ""))

                gap = abs(t_score - s_score)
                result["teacher_score"] = t_score
                result["student_score"] = s_score
                result["gap_percent"] = gap
                result["teacher_time"] = t_time
                result["student_time"] = s_time
                result["use_student"] = gap < 10  # إذا الفرق أقل من 10%

                # سجل الفجوة
                if task_type not in self.gap_measurements:
                    self.gap_measurements[task_type] = []
                self.gap_measurements[task_type].append(result)

            except Exception as e:
                logger.error(f"خطأ في قياس الفجوة: {e}")

        return result

    def daily_distillation(self, get_agent_fn=None, *, max_pairs: Optional[int] = None, sleep_s: float = 0.25) -> Dict:
        """
        الدورة اليومية — الساعة 2 صباحاً
        لكل نوع مهمة → إذا teacher حلّها أمس → سجّل مثالاً للطالب
        """
        logger.info("📚 بدء دورة التقطير اليومية")
        results = {"pairs_processed": 0, "examples_added": 0, "gaps_measured": 0}

        test_tasks = {
            "general": "لخص أهم 3 تطورات في الذكاء الاصطناعي هذا الأسبوع",
            "critical": "حلل مخاطر الاستثمار في شركة AI ناشئة",
            "reasoning": "إذا كان A > B و B > C و C > D، وكان D = 10، ما أقل قيمة ممكنة لـ A؟",
            "arabic": "اكتب مقالاً عن مستقبل التعليم في العالم العربي",
            "simple": "ما هو الفرق بين Python و JavaScript؟",
        }

        pairs = self.TEACHER_STUDENT_PAIRS
        if isinstance(max_pairs, int) and max_pairs > 0:
            pairs = pairs[:max_pairs]

        for pair in pairs:
            domain = pair["domain"]
            task = test_tasks.get(domain, test_tasks["general"])

            if get_agent_fn:
                try:
                    # المعلم يحل
                    teacher_result = get_agent_fn(task, model=pair["teacher"])
                    if teacher_result:
                        # سجل كمثال
                        self.record_teacher_solution(
                            task_type=domain,
                            task=task,
                            solution=teacher_result.get("result", ""),
                            model=pair["teacher"],
                            cot_steps=teacher_result.get("reasoning", "")
                        )
                        results["examples_added"] += 1
                except Exception as e:
                    logger.warning(f"فشل التقطير لـ {domain}: {e}")

            results["pairs_processed"] += 1
            if sleep_s and sleep_s > 0:
                time.sleep(sleep_s)

        logger.info(f"📚 انتهى التقطير: {results['examples_added']} أمثلة جديدة")
        return results

    def _score_solution(self, solution: str) -> float:
        """تقييم جودة الحل"""
        if not solution:
            return 0.0
        score = 0.0
        if len(solution) > 50: score += 20
        if len(solution) > 200: score += 20
        if len(solution) > 500: score += 10
        if any(m in solution for m in ["1.", "أولاً", "##"]): score += 15
        if any(w in solution for w in ["لأن", "because", "بسبب"]): score += 15
        if "```" in solution: score += 10  # كود
        if "خطأ" not in solution.lower(): score += 10
        return min(score, 100.0)

    def get_stats(self) -> Dict:
        return {
            "examples_stored": self.examples_stored,
            "pairs": len(self.TEACHER_STUDENT_PAIRS),
            "gap_measurements": {k: len(v) for k, v in self.gap_measurements.items()},
        }


class ModelMerger:
    """
    Evolutionary Model Merging
    دمج أفضل النماذج المفتوحة لإنشاء Army81-Core
    (MergeKit-style — يحتاج HuggingFace + GPU)
    """

    def __init__(self):
        self.merge_history: List[Dict] = []
        self.current_best = None
        MERGE_DIR.mkdir(parents=True, exist_ok=True)

    def discover_models(self) -> List[Dict]:
        """اكتشاف أفضل النماذج من HuggingFace"""
        candidates = [
            {"name": "Qwen/Qwen2.5-7B-Instruct", "size": "7B", "lang": "multilingual", "score": 85},
            {"name": "mistralai/Mistral-Small-24B", "size": "24B", "lang": "en", "score": 88},
            {"name": "meta-llama/Llama-3.2-3B-Instruct", "size": "3B", "lang": "en", "score": 75},
            {"name": "microsoft/phi-4-mini", "size": "3.8B", "lang": "en", "score": 82},
            {"name": "deepseek-ai/DeepSeek-V3", "size": "685B", "lang": "multilingual", "score": 95},
        ]
        return candidates

    def propose_merge(self, models: List[str], strategy: str = "slerp") -> Dict:
        """اقتراح دمج نماذج"""
        proposal = {
            "id": f"MERGE-{len(self.merge_history)+1:04d}",
            "models": models,
            "strategy": strategy,  # slerp, ties, dare, linear
            "status": "proposed",
            "expected_improvement": "10-15%",
            "created_at": datetime.now().isoformat(),
            "mergekit_config": {
                "merge_method": strategy,
                "slices": [{"sources": [{"model": m, "layer_range": [0, 32]} for m in models]}],
                "parameters": {"weight": [0.5] * len(models)},
            }
        }
        self.merge_history.append(proposal)

        config_file = MERGE_DIR / f"{proposal['id']}_config.yaml"
        config_file.write_text(json.dumps(proposal["mergekit_config"], indent=2), encoding="utf-8")

        logger.info(f"🔀 اقتراح دمج: {models} بطريقة {strategy}")
        return proposal

    def weekly_merge_cycle(self) -> Dict:
        """الدورة الأسبوعية لدمج النماذج"""
        logger.info("🔀 بدء دورة دمج النماذج الأسبوعية")

        # 1. اكتشاف النماذج
        candidates = self.discover_models()

        # 2. اختيار أفضل زوج للدمج
        top_2 = sorted(candidates, key=lambda x: x["score"], reverse=True)[:2]

        # 3. اقتراح الدمج
        proposal = self.propose_merge(
            [m["name"] for m in top_2],
            strategy="slerp"
        )

        return {
            "candidates_found": len(candidates),
            "merge_proposed": proposal["id"],
            "models": [m["name"] for m in top_2],
        }

    def get_stats(self) -> Dict:
        return {
            "merges_proposed": len(self.merge_history),
            "current_best": self.current_best,
        }
