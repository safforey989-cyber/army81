"""
Army81 — Prompt Optimizer + Memory Crystallizer
تحسين خوارزمي للأوامر (DSPy-style) + تبلور تكراري للذاكرة
"""
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.prompt_optimizer")

WORKSPACE = Path("workspace")
PROMPT_DIR = WORKSPACE / "prompt_versions"
CRYSTAL_DIR = WORKSPACE / "compressed"
AGENTS_DIR = Path("agents")


class PromptOptimizer:
    """
    التحسين الخوارزمي للأوامر — DSPy-style
    يعدل system_prompt رياضياً وجيربه آلاف المرات
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.optimizations_done = 0
        self.prompts_improved = 0
        PROMPT_DIR.mkdir(parents=True, exist_ok=True)

    def evaluate_prompt(self, agent_id: str, system_prompt: str,
                        test_tasks: List[str], run_fn=None) -> float:
        """تقييم prompt عبر مجموعة مهام"""
        if not run_fn or not test_tasks:
            return 50.0

        scores = []
        for task in test_tasks[:5]:
            try:
                result = run_fn(task, system_prompt=system_prompt)
                score = self._score_result(result)
                scores.append(score)
            except Exception:
                scores.append(0.0)
            time.sleep(1)

        return sum(scores) / max(len(scores), 1)

    def _score_result(self, result) -> float:
        """تقييم نتيجة"""
        if not result:
            return 0.0
        text = result.get("result", "") if isinstance(result, dict) else str(result)
        score = 0.0
        if len(text) > 50: score += 20
        if len(text) > 200: score += 20
        if any(m in text for m in ["1.", "##", "- "]): score += 20
        if any(w in text for w in ["لأن", "because", "بسبب"]): score += 20
        if "خطأ" not in text.lower() and "error" not in text.lower(): score += 20
        return min(score, 100.0)

    def generate_variants(self, original_prompt: str, count: int = 5) -> List[str]:
        """توليد متغيرات من prompt"""
        mutations = [
            # إضافة تعليمات بنيوية
            lambda p: p + "\n\nقاعدة: استخدم عناوين وتنسيق واضح في كل إجابة.",
            # إضافة CoT
            lambda p: p + "\n\nقاعدة: فكر خطوة بخطوة قبل الإجابة.",
            # إضافة نقد ذاتي
            lambda p: p + "\n\nقاعدة: راجع إجابتك قبل إرسالها وصحح أي خطأ.",
            # إضافة أمثلة
            lambda p: p + "\n\nقاعدة: أعطِ أمثلة واقعية دائماً.",
            # تقصير
            lambda p: p[:len(p)//2] + "\n\nكن مختصراً ودقيقاً.",
            # إضافة سياق الشبكة
            lambda p: p + "\n\nتذكر: أنت جزء من شبكة 81 وكيل. تعاون مع الآخرين عند الحاجة.",
            # إضافة معايير جودة
            lambda p: p + "\n\nمعايير الجودة: دقة > 90%، شمولية، وضوح، قابلية تطبيق.",
        ]

        variants = [original_prompt]  # الأصلي دائماً
        chosen = random.sample(mutations, min(count, len(mutations)))
        for mutation_fn in chosen:
            try:
                variant = mutation_fn(original_prompt)
                variants.append(variant)
            except Exception:
                pass

        return variants

    def optimize_agent(self, agent_id: str, current_prompt: str,
                       test_tasks: List[str], run_fn=None) -> Dict:
        """
        تحسين prompt لوكيل واحد:
        1. قياس الأداء الحالي
        2. توليد متغيرات
        3. اختبار كل متغير
        4. اختيار الأفضل
        """
        logger.info(f"🔧 تحسين prompt لـ {agent_id}")
        self.optimizations_done += 1

        # 1. Baseline
        baseline_score = self.evaluate_prompt(agent_id, current_prompt, test_tasks, run_fn)

        # 2. متغيرات
        variants = self.generate_variants(current_prompt, 5)

        # 3. اختبار
        best_score = baseline_score
        best_prompt = current_prompt
        results = [{"variant": "original", "score": baseline_score}]

        for i, variant in enumerate(variants[1:], 1):
            score = self.evaluate_prompt(agent_id, variant, test_tasks, run_fn)
            results.append({"variant": f"v{i}", "score": score})

            if score > best_score:
                best_score = score
                best_prompt = variant

        # 4. اعتماد إذا تحسّن > 10%
        improvement = (best_score - baseline_score) / max(baseline_score, 1) * 100
        improved = improvement > 10

        if improved:
            self.prompts_improved += 1
            # حفظ النسخة القديمة
            backup = PROMPT_DIR / f"{agent_id}_v{self.optimizations_done}.txt"
            backup.write_text(current_prompt, encoding="utf-8")

        result = {
            "agent_id": agent_id,
            "baseline_score": baseline_score,
            "best_score": best_score,
            "improvement": improvement,
            "improved": improved,
            "best_prompt": best_prompt if improved else None,
            "variants_tested": len(variants),
        }

        logger.info(f"{'✅' if improved else '❌'} {agent_id}: {improvement:.1f}% تغيير")
        return result

    def daily_optimization(self, agents_data: List[Dict] = None,
                           run_fn=None) -> Dict:
        """الدورة اليومية لتحسين الـ prompts"""
        logger.info("🔧 بدء دورة تحسين الأوامر")
        results = {"optimized": 0, "improved": 0, "total": 0}

        test_tasks = [
            "لخص موضوع الذكاء الاصطناعي في 100 كلمة",
            "ما هي أهم 3 تحديات في مجالك؟",
            "اكتب خطة عمل لمشروع صغير",
        ]

        if agents_data:
            # اختر 5 وكلاء عشوائياً
            sample = random.sample(agents_data, min(5, len(agents_data)))
            for agent in sample:
                result = self.optimize_agent(
                    agent.get("id", ""),
                    agent.get("system_prompt", ""),
                    test_tasks, run_fn
                )
                results["total"] += 1
                results["optimized"] += 1
                if result["improved"]:
                    results["improved"] += 1

        return results

    def get_stats(self) -> Dict:
        return {
            "optimizations_done": self.optimizations_done,
            "prompts_improved": self.prompts_improved,
        }


class MemoryCrystallizer:
    """
    التبلور التكراري للذاكرة
    كل 24 ساعة — ضغط المحادثات إلى قواعد ذهبية
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.crystalizations = 0
        CRYSTAL_DIR.mkdir(parents=True, exist_ok=True)

    def crystallize_agent(self, agent_id: str, episodes: List[Dict] = None) -> str:
        """
        ضغط حلقات وكيل إلى قواعد ذهبية
        """
        if not episodes:
            return ""

        # تحليل الحلقات
        successes = [e for e in episodes if e.get("success")]
        failures = [e for e in episodes if not e.get("success")]

        crystal = f"## ملخص خبرة {agent_id}\n"
        crystal += f"📊 إجمالي: {len(episodes)} مهمة — {len(successes)} نجاح — {len(failures)} فشل\n\n"

        # دروس النجاح
        if successes:
            crystal += "### ✅ قواعد النجاح:\n"
            for s in successes[-5:]:
                task_short = s.get("task", "")[:100]
                crystal += f"- عند '{task_short}' → نجحت بـ: {s.get('model', 'unknown')}\n"

        # دروس الفشل
        if failures:
            crystal += "\n### ❌ أخطاء يجب تجنبها:\n"
            for f in failures[-5:]:
                task_short = f.get("task", "")[:100]
                crystal += f"- فشلت في '{task_short}' — السبب: {f.get('error', 'غير معروف')[:100]}\n"

        # قواعد ذهبية
        crystal += "\n### 💎 القواعد الذهبية:\n"
        if len(successes) > len(failures):
            crystal += "- أدائي جيد عموماً — أحافظ على نفس المنهج\n"
        else:
            crystal += "- أحتاج تحسين — أركز على التفكير قبل الإجابة\n"

        if any("code" in str(e.get("task", "")).lower() for e in successes):
            crystal += "- أجيد البرمجة — أستخدم أمثلة كود دائماً\n"
        if any("تحليل" in str(e.get("task", "")) for e in successes):
            crystal += "- أجيد التحليل — أستخدم بيانات ومراجع\n"

        # حفظ
        crystal_file = CRYSTAL_DIR / f"{agent_id}_crystal.md"
        crystal_file.write_text(crystal, encoding="utf-8")

        self.crystalizations += 1
        return crystal[:2000]

    def crystallize_all(self, agents_episodes: Dict[str, List[Dict]] = None) -> Dict:
        """ضغط ذاكرة كل الوكلاء"""
        logger.info("💎 بدء تبلور الذاكرة")
        results = {"agents_processed": 0, "crystals_created": 0}

        if agents_episodes:
            for agent_id, episodes in agents_episodes.items():
                crystal = self.crystallize_agent(agent_id, episodes)
                if crystal:
                    results["crystals_created"] += 1
                results["agents_processed"] += 1

        logger.info(f"💎 انتهى التبلور: {results['crystals_created']} بلورة")
        return results

    def inject_crystal(self, agent_id: str) -> str:
        """يحقن البلورة في بداية system_prompt"""
        crystal_file = CRYSTAL_DIR / f"{agent_id}_crystal.md"
        if crystal_file.exists():
            return crystal_file.read_text(encoding="utf-8")[:1000]
        return ""

    def daily_crystallization(self) -> Dict:
        """الدورة اليومية — 4 صباحاً"""
        logger.info("💎 تبلور الذاكرة اليومي")

        # قراءة الحلقات من الملفات
        episodes_dir = WORKSPACE / "episodes"
        agents_episodes = {}

        if episodes_dir.exists():
            for f in episodes_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    agent_id = f.stem
                    agents_episodes[agent_id] = data if isinstance(data, list) else [data]
                except Exception:
                    continue

        return self.crystallize_all(agents_episodes)

    def get_stats(self) -> Dict:
        crystals = list(CRYSTAL_DIR.glob("*_crystal.md"))
        return {
            "crystalizations": self.crystalizations,
            "crystals_on_disk": len(crystals),
        }
