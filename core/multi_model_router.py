"""
Army81 — Multi-Model Router
يشغّل مهمة على عدة نماذج في آنٍ واحد
أنماط: parallel, ensemble, debate
"""
import logging
import time
import concurrent.futures
from typing import Dict, List, Optional

from core.llm_client import LLMClient, TASK_MODEL_MAP, REAL_MODELS

logger = logging.getLogger("army81.multi_model_router")


class MultiModelRouter:
    """
    يوجّه المهام لعدة نماذج بأنماط مختلفة:
    - parallel: نفس السؤال على عدة نماذج → أفضل رد
    - ensemble: draft → refine → verify
    - debate: نموذجان يختلفان ثم محكّم يوحّد
    """

    def __init__(self):
        self.queries_routed = 0
        self.models_used_stats: Dict[str, int] = {}

    # ═══════════════════════════════════════════════════
    # Single — أفضل نموذج لتخصص الوكيل
    # ═══════════════════════════════════════════════════

    def route_single(self, task: str, agent_id: str = "",
                     system_prompt: str = "") -> Dict:
        """وكيل واحد ← أفضل نموذج لتخصصه"""
        task_type = self._classify(task, agent_id)
        models = TASK_MODEL_MAP.get(task_type, ["gemini-flash"])

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": task})

        for model_alias in models:
            if model_alias not in REAL_MODELS:
                continue
            try:
                client = LLMClient(model_alias)
                result = client.chat(messages)
                content = result.get("content", "")
                if content and not content.startswith("ERROR"):
                    self._track(model_alias)
                    self.queries_routed += 1
                    return {
                        "content": content,
                        "model": model_alias,
                        "model_full": result.get("model", ""),
                        "tokens": result.get("tokens", 0),
                        "task_type": task_type,
                        "mode": "single",
                    }
            except Exception as e:
                logger.warning(f"Model {model_alias} failed: {e}")
                continue

        # Ultimate fallback
        result = LLMClient("gemini-flash").chat(messages)
        self._track("gemini-flash")
        return {"content": result.get("content", ""), "model": "gemini-flash", "mode": "fallback"}

    # ═══════════════════════════════════════════════════
    # Parallel — نفس المهمة على عدة نماذج
    # ═══════════════════════════════════════════════════

    def route_parallel(self, task: str, model_aliases: List[str],
                       system_prompt: str = "", timeout: int = 45) -> Dict:
        """
        نفس المهمة على عدة نماذج في آنٍ واحد
        يعيد: كل الردود + أفضل رد
        """
        valid_aliases = [a for a in model_aliases if a in REAL_MODELS]
        if not valid_aliases:
            valid_aliases = ["gemini-flash"]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": task})

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(valid_aliases)) as executor:
            futures = {
                executor.submit(self._run_model, messages, alias): alias
                for alias in valid_aliases
            }

            for future in concurrent.futures.as_completed(futures, timeout=timeout):
                alias = futures[future]
                try:
                    results[alias] = future.result()
                    self._track(alias)
                except Exception as e:
                    results[alias] = {"content": f"ERROR: {e}", "tokens": 0}

        best = self._select_best(results)
        self.queries_routed += 1

        return {
            "best_model": best,
            "best_response": results.get(best, {}).get("content", ""),
            "all_responses": {k: v.get("content", "")[:500] for k, v in results.items()},
            "models_used": list(results.keys()),
            "mode": "parallel",
        }

    # ═══════════════════════════════════════════════════
    # Ensemble — draft → refine → verify
    # ═══════════════════════════════════════════════════

    def route_ensemble(self, task: str, agent_id: str = "",
                       system_prompt: str = "") -> Dict:
        """
        Draft بنموذج سريع → Refine بنموذج ذكي → إجابة محسّنة
        """
        task_type = self._classify(task, agent_id)
        models = TASK_MODEL_MAP.get(task_type, ["gemini-flash", "gemini-pro"])

        draft_model = "gemini-flash"
        refine_model = models[0] if models else "gemini-pro"

        # المرحلة 1: Draft سريع
        draft_msgs = []
        if system_prompt:
            draft_msgs.append({"role": "system", "content": system_prompt + "\nأجب بسرعة وإيجاز."})
        draft_msgs.append({"role": "user", "content": task})

        draft = LLMClient(draft_model).chat(draft_msgs)
        draft_content = draft.get("content", "")
        self._track(draft_model)

        # المرحلة 2: Refine بنموذج أذكى
        refine_msgs = [
            {"role": "system", "content": "أنت خبير. راجع هذا الرد وحسّنه: أضف تفاصيل، صحح أخطاء، حسّن التنسيق."},
            {"role": "user", "content": f"المهمة الأصلية: {task}\n\nالرد الأولي:\n{draft_content}\n\nحسّن هذا الرد:"}
        ]

        refined = LLMClient(refine_model).chat(refine_msgs)
        self._track(refine_model)
        self.queries_routed += 1

        return {
            "content": refined.get("content", draft_content),
            "draft_model": draft_model,
            "refine_model": refine_model,
            "draft_tokens": draft.get("tokens", 0),
            "refine_tokens": refined.get("tokens", 0),
            "mode": "ensemble",
        }

    # ═══════════════════════════════════════════════════
    # Debate — نموذجان يناقشان ثم محكّم
    # ═══════════════════════════════════════════════════

    def route_debate(self, task: str, models: List[str] = None,
                     system_prompt: str = "") -> Dict:
        """
        نموذجان يعطيان رأيهما → محكّم يوحّد الرأيين
        مثالي للقرارات الصعبة
        """
        if not models or len(models) < 2:
            models = ["deepseek-r1", "claude-smart"]

        model_a, model_b = models[0], models[1]

        # كل نموذج يعطي رأيه
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": task})

        # بالتوازي
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_a = executor.submit(self._run_model, msgs, model_a)
            f_b = executor.submit(self._run_model, msgs, model_b)
            opinion_a = f_a.result(timeout=60).get("content", "")
            opinion_b = f_b.result(timeout=60).get("content", "")

        self._track(model_a)
        self._track(model_b)

        # محكّم يوحّد
        judge_msgs = [
            {"role": "system", "content": "أنت محكّم خبير. ادمج أفضل ما في الرأيين في إجابة واحدة متكاملة."},
            {"role": "user", "content": f"""المهمة: {task}

رأي {model_a}:
{opinion_a[:1500]}

رأي {model_b}:
{opinion_b[:1500]}

قدم إجابة موحدة تأخذ أفضل ما في الرأيين:"""}
        ]

        judge_model = "gemini-pro"
        verdict = LLMClient(judge_model).chat(judge_msgs)
        self._track(judge_model)
        self.queries_routed += 1

        return {
            "content": verdict.get("content", opinion_a),
            "opinion_a": {"model": model_a, "content": opinion_a[:500]},
            "opinion_b": {"model": model_b, "content": opinion_b[:500]},
            "judge": judge_model,
            "mode": "debate",
        }

    # ═══════════════════════════════════════════════════
    # أدوات مساعدة
    # ═══════════════════════════════════════════════════

    def _run_model(self, messages: List[Dict], alias: str) -> Dict:
        """يشغّل نموذج واحد"""
        try:
            client = LLMClient(alias)
            return client.chat(messages)
        except Exception as e:
            return {"content": f"ERROR: {e}", "tokens": 0}

    def _classify(self, task: str, agent_id: str = "") -> str:
        """يصنف نوع المهمة"""
        task_lower = task.lower()
        keywords = {
            "coding": ["كود", "برمج", "python", "function", "bug", "debug", "api", "code"],
            "medical": ["طب", "دواء", "مرض", "علاج", "مريض", "سريري"],
            "legal": ["قانون", "محكمة", "عقد", "حق", "تشريع"],
            "financial": ["مالي", "سهم", "اقتصاد", "استثمار", "عملة"],
            "arabic": ["عرب", "لغة عربية", "قرآن", "تراث"],
            "science": ["بحث", "ورقة", "دراسة", "فيزياء", "كيمياء"],
            "math": ["معادلة", "حساب", "إثبات", "رياضيات"],
            "current_events": ["أخبار", "اليوم", "الآن", "حديث", "2026"],
            "strategy": ["استراتيج", "خطة", "قرار", "رؤية"],
            "security": ["أمن", "هجوم", "ثغرة", "حماية", "تشفير"],
            "behavior": ["سلوك", "نفس", "شخصية", "دوافع"],
            "leadership": ["قيادة", "إدارة", "فريق", "مؤسسة"],
        }
        for task_type, kws in keywords.items():
            if any(k in task_lower for k in kws):
                return task_type
        return "fast_simple"

    def _select_best(self, results: Dict) -> str:
        """يختار أفضل رد من عدة نماذج"""
        best = None
        best_score = -1
        for model, result in results.items():
            content = result.get("content", "")
            if not content or content.startswith("ERROR"):
                continue
            score = 0
            score += min(len(content), 2000) * 0.1
            if any(c in content for c in ['1.', '2.', '3.', '##', '- ']):
                score += 200
            if len(content) > 200:
                score += 100
            if any(w in content for w in ['لأن', 'because', 'بسبب', 'أولاً']):
                score += 150
            if score > best_score:
                best_score = score
                best = model
        return best or list(results.keys())[0]

    def _track(self, alias: str):
        self.models_used_stats[alias] = self.models_used_stats.get(alias, 0) + 1

    def get_stats(self) -> Dict:
        return {
            "queries_routed": self.queries_routed,
            "models_available": len(REAL_MODELS),
            "models_used": self.models_used_stats,
            "task_types": list(TASK_MODEL_MAP.keys()),
        }
