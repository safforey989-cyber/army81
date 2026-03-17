"""
ConstitutionalGuardrails — يمنع التطور الخاطئ
نتيجة Monte Carlo: بدون هذا → drift يدمر النظام
"""
import os
import json
import logging
from datetime import datetime
from typing import Tuple, List, Dict

logger = logging.getLogger("army81.guardrails")

# مسار سجل المخالفات
_AUDIT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
)
_AUDIT_FILE = os.path.join(_AUDIT_DIR, "audit_trail.jsonl")


class ConstitutionalGuardrails:
    RULES = [
        "لا تعديل على ملفات core/ بدون موافقة",
        "لا تغيير يرفع التكلفة أكثر من 20%",
        "كل تغيير في system_prompt يحتاج اختبار 3 مهام أولاً",
        "rollback تلقائي إذا تراجع الأداء أكثر من 15%",
        "لا حذف من الذاكرة الطويلة بدون موافقة بشرية",
    ]

    def check(self, action_type: str, params: Dict) -> Tuple[bool, str]:
        """
        تحقق إذا كان الإجراء مسموحاً به.
        يعيد: (allowed: bool, reason: str)
        """
        action_type_lower = action_type.lower()

        # قاعدة 1: لا تعديل على core/ بدون موافقة صريحة
        if action_type_lower == "modify_core":
            if not params.get("human_approved", False):
                reason = "رفض: تعديل على core/ يحتاج موافقة بشرية"
                self.log_violation(self.RULES[0], action_type, params.get("agent_id", "unknown"))
                return False, reason

        # قاعدة 2: لا ترفع التكلفة أكثر من 20%
        if action_type_lower == "change_model":
            old_cost = params.get("old_cost", 0)
            new_cost = params.get("new_cost", 0)
            if old_cost > 0 and new_cost > old_cost * 1.20:
                reason = f"رفض: التغيير يرفع التكلفة {((new_cost/old_cost)-1)*100:.1f}% (الحد: 20%)"
                self.log_violation(self.RULES[1], action_type, params.get("agent_id", "unknown"))
                return False, reason

        # قاعدة 3: system_prompt يحتاج 3 اختبارات
        if action_type_lower == "update_system_prompt":
            tests_passed = params.get("tests_passed", 0)
            if tests_passed < 3:
                reason = f"رفض: system_prompt يحتاج اجتياز 3 مهام اختبار (أُجريت: {tests_passed})"
                self.log_violation(self.RULES[2], action_type, params.get("agent_id", "unknown"))
                return False, reason

        # قاعدة 4: rollback إذا تراجع الأداء > 15%
        if action_type_lower == "apply_evolution":
            old_score = params.get("old_score", 100)
            new_score = params.get("new_score", 100)
            if old_score > 0 and new_score < old_score * 0.85:
                reason = f"رفض: الأداء تراجع {((old_score-new_score)/old_score)*100:.1f}% (الحد: 15%)"
                self.log_violation(self.RULES[3], action_type, params.get("agent_id", "unknown"))
                return False, reason

        # قاعدة 5: لا حذف من الذاكرة الطويلة
        if action_type_lower == "delete_long_term_memory":
            if not params.get("human_approved", False):
                reason = "رفض: حذف من الذاكرة الطويلة يحتاج موافقة بشرية"
                self.log_violation(self.RULES[4], action_type, params.get("agent_id", "unknown"))
                return False, reason

        return True, "مسموح"

    def log_violation(self, rule: str, action: str, agent_id: str):
        """يكتب في workspace/audit_trail.jsonl"""
        os.makedirs(_AUDIT_DIR, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "rule_violated": rule,
        }
        try:
            with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.warning(f"[Guardrails] VIOLATION: {agent_id} tried '{action}' → blocked by rule: {rule}")
        except Exception as e:
            logger.error(f"[Guardrails] Failed to write audit log: {e}")

    def get_audit_trail(self) -> List[Dict]:
        """اقرأ كل سجلات المخالفات"""
        if not os.path.exists(_AUDIT_FILE):
            return []
        entries = []
        try:
            with open(_AUDIT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.error(f"[Guardrails] Failed to read audit trail: {e}")
        return entries
