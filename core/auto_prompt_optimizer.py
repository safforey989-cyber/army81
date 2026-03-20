"""
Army81 - Auto Prompt Optimizer
تحسين system prompts تلقائياً بناءً على الأداء
المرحلة 4: التطور الذاتي
مكمّل لـ prompt_optimizer.py الموجود (DSPy-style)
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger("army81.auto_prompt_optimizer")


class AutoPromptOptimizer:
    """
    يحلل أداء الوكلاء ويقترح تحسينات على system prompts تلقائياً
    المنهجية:
    1. تحليل المهام الناجحة vs الفاشلة
    2. استخراج أنماط النجاح
    3. توليد تحسينات مقترحة
    4. تطبيق التحسينات بعد الموافقة
    """

    def __init__(self, agents_dir: str = None, data_dir: str = None):
        self.agents_dir = agents_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "agents"
        )
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "workspace", "auto_prompt_optimizer"
        )
        os.makedirs(self.data_dir, exist_ok=True)

        self._optimization_history: List[Dict] = []
        self._pending_suggestions: Dict[str, List[Dict]] = defaultdict(list)
        self._load_history()

    def analyze_agent(self, agent_id: str, task_history: List[Dict]) -> Dict:
        """
        تحليل أداء وكيل وتوليد اقتراحات تحسين
        task_history: قائمة من {task, result, success, quality_score}
        """
        if not task_history:
            return {"agent_id": agent_id, "status": "no_data"}

        successes = [t for t in task_history if t.get("success")]
        failures = [t for t in task_history if not t.get("success")]
        success_rate = len(successes) / len(task_history)

        failure_patterns = self._extract_failure_patterns(failures)
        success_patterns = self._extract_success_patterns(successes)

        current_prompt = self._load_agent_prompt(agent_id)

        suggestions = self._generate_suggestions(
            agent_id, current_prompt, success_rate,
            failure_patterns, success_patterns
        )

        analysis = {
            "agent_id": agent_id,
            "tasks_analyzed": len(task_history),
            "success_rate": round(success_rate, 3),
            "failure_patterns": failure_patterns,
            "success_patterns": success_patterns,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat(),
        }

        self._pending_suggestions[agent_id] = suggestions
        return analysis

    def get_suggestions(self, agent_id: str) -> List[Dict]:
        """استرجاع اقتراحات التحسين المعلقة"""
        return self._pending_suggestions.get(agent_id, [])

    def apply_suggestion(self, agent_id: str, suggestion_idx: int = 0,
                         auto_backup: bool = True) -> str:
        """تطبيق اقتراح تحسين على system prompt"""
        suggestions = self._pending_suggestions.get(agent_id, [])
        if not suggestions or suggestion_idx >= len(suggestions):
            return f"لا يوجد اقتراح رقم {suggestion_idx} للوكيل {agent_id}"

        suggestion = suggestions[suggestion_idx]
        json_path = self._find_agent_json(agent_id)
        if not json_path:
            return f"لم يتم العثور على ملف JSON للوكيل {agent_id}"

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                agent_data = json.load(f)

            old_prompt = agent_data.get("system_prompt", "")

            if auto_backup:
                backup_dir = os.path.join(self.data_dir, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(
                    backup_dir,
                    f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(agent_data, f, ensure_ascii=False, indent=2)

            new_prompt = self._apply_prompt_change(old_prompt, suggestion)
            agent_data["system_prompt"] = new_prompt

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)

            self._optimization_history.append({
                "agent_id": agent_id,
                "suggestion": suggestion,
                "old_prompt_length": len(old_prompt),
                "new_prompt_length": len(new_prompt),
                "applied_at": datetime.now().isoformat(),
            })
            self._save_history()

            return f"تم تطبيق التحسين على {agent_id}: {suggestion['type']}"

        except Exception as e:
            logger.error(f"Apply suggestion error for {agent_id}: {e}")
            return f"خطأ في تطبيق التحسين: {e}"

    def batch_analyze(self, monitor_data: Dict) -> Dict:
        """تحليل دفعي لكل الوكلاء"""
        results = {}
        candidates = []

        for agent_id, records in monitor_data.items():
            analysis = self.analyze_agent(agent_id, records)
            results[agent_id] = analysis
            if analysis.get("suggestions"):
                candidates.append(agent_id)

        return {
            "agents_analyzed": len(results),
            "agents_needing_optimization": len(candidates),
            "optimization_candidates": candidates,
            "analyses": results,
            "timestamp": datetime.now().isoformat(),
        }

    def get_history(self, agent_id: str = "", limit: int = 20) -> List[Dict]:
        """سجل التحسينات"""
        if agent_id:
            return [h for h in self._optimization_history
                   if h["agent_id"] == agent_id][-limit:]
        return self._optimization_history[-limit:]

    # ── Private ──────────────────────────────────────────────────

    def _extract_failure_patterns(self, failures: List[Dict]) -> List[str]:
        patterns = []
        if not failures:
            return patterns

        error_keywords = defaultdict(int)
        for f in failures:
            result = f.get("result", "").lower()
            if "timeout" in result or "انتهت المهلة" in result:
                error_keywords["timeout"] += 1
            if "خطأ" in result or "error" in result:
                error_keywords["general_error"] += 1
            if "لا أعلم" in result or "لا أستطيع" in result:
                error_keywords["knowledge_gap"] += 1
            if "api" in result or "connection" in result:
                error_keywords["api_error"] += 1

        for error_type, count in sorted(error_keywords.items(), key=lambda x: -x[1]):
            if count >= 2:
                patterns.append(f"{error_type}: {count} مرة")

        long_tasks = [f for f in failures if len(f.get("task", "")) > 200]
        if len(long_tasks) > len(failures) * 0.5:
            patterns.append("أغلب الفشل في المهام الطويلة — قد يحتاج تقسيم")

        return patterns

    def _extract_success_patterns(self, successes: List[Dict]) -> List[str]:
        patterns = []
        if not successes:
            return patterns

        avg_len = sum(len(s.get("result", "")) for s in successes) / len(successes)
        if avg_len > 500:
            patterns.append("الإجابات الناجحة تفصيلية")
        elif avg_len < 100:
            patterns.append("الإجابات الناجحة مختصرة")

        return patterns

    def _generate_suggestions(self, agent_id: str, current_prompt: str,
                              success_rate: float, failure_patterns: List[str],
                              success_patterns: List[str]) -> List[Dict]:
        suggestions = []

        if success_rate < 0.7:
            suggestions.append({
                "type": "add_examples",
                "description": "إضافة أمثلة few-shot",
                "priority": "high",
                "change": "\n\n## أمثلة:\nمثال 1: [مهمة] → [إجابة مختصرة]\nمثال 2: [مهمة] → [إجابة مع مصادر]\n",
            })

        if any("knowledge_gap" in p for p in failure_patterns):
            suggestions.append({
                "type": "add_boundaries",
                "description": "إضافة حدود المعرفة",
                "priority": "medium",
                "change": "\n\n## حدود معرفتي:\n- عند عدم المعرفة: أقول ذلك بصراحة\n",
            })

        if any("timeout" in p for p in failure_patterns):
            suggestions.append({
                "type": "simplify_prompt",
                "description": "تبسيط لتسريع الاستجابة",
                "priority": "high",
                "change": "simplify",
            })

        if len(current_prompt) > 2000:
            suggestions.append({
                "type": "compress_prompt",
                "description": f"ضغط prompt ({len(current_prompt)} حرف)",
                "priority": "low",
                "change": "compress",
            })

        if success_rate >= 0.9 and not suggestions:
            suggestions.append({
                "type": "enhance_quality",
                "description": "أداء ممتاز — تحسينات طفيفة",
                "priority": "low",
                "change": "\n## تحسين: أضف مصادر واستخدم Markdown واضح\n",
            })

        return suggestions

    def _apply_prompt_change(self, old_prompt: str, suggestion: Dict) -> str:
        change = suggestion.get("change", "")

        if suggestion["type"] == "compress_prompt":
            lines = old_prompt.split("\n")
            compressed = []
            prev_empty = False
            for line in lines:
                is_empty = not line.strip()
                if is_empty and prev_empty:
                    continue
                compressed.append(line)
                prev_empty = is_empty
            return "\n".join(compressed)

        if suggestion["type"] == "simplify_prompt":
            if len(old_prompt) > 1500:
                return old_prompt[:1500] + "\n\n[تم تبسيط التعليمات]"
            return old_prompt

        if change and change not in ("simplify", "compress"):
            return old_prompt + change

        return old_prompt

    def _load_agent_prompt(self, agent_id: str) -> str:
        json_path = self._find_agent_json(agent_id)
        if not json_path:
            return ""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f).get("system_prompt", "")
        except Exception:
            return ""

    def _find_agent_json(self, agent_id: str) -> Optional[str]:
        for root, dirs, files in os.walk(self.agents_dir):
            for fname in files:
                if fname.endswith(".json") and agent_id in fname:
                    return os.path.join(root, fname)
        return None

    def _save_history(self) -> None:
        filepath = os.path.join(self.data_dir, "auto_optimization_history.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._optimization_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save history error: {e}")

    def _load_history(self) -> None:
        filepath = os.path.join(self.data_dir, "auto_optimization_history.json")
        if not os.path.exists(filepath):
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._optimization_history = json.load(f)
        except Exception as e:
            logger.error(f"Load history error: {e}")


# ── Singleton ──────────────────────────────────────────────────
_instance = None


def get_auto_optimizer() -> AutoPromptOptimizer:
    global _instance
    if _instance is None:
        _instance = AutoPromptOptimizer()
    return _instance
