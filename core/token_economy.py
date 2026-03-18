"""
Army81 — Token Economy + Cell Division + Adaptive Guardrails
الاقتصاد الداخلي + التكاثر الخلوي + الحماية التكيفية
"""
import json
import time
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.token_economy")

WORKSPACE = Path("workspace")
ECONOMY_FILE = WORKSPACE / "token_economy.json"
AGENTS_DIR = Path("agents")


class TokenEconomy:
    """
    الاقتصاد الداخلي للرموز
    كل وكيل = ميزانية يومية — الكفاءة تُكافأ
    """

    DEFAULT_DAILY_BUDGET = 50000  # tokens per agent per day

    def __init__(self):
        self.budgets: Dict[str, Dict] = {}
        self.transactions: List[Dict] = []
        self._load()

    def _load(self):
        if ECONOMY_FILE.exists():
            try:
                data = json.loads(ECONOMY_FILE.read_text(encoding="utf-8"))
                self.budgets = data.get("budgets", {})
                self.transactions = data.get("transactions", [])[-1000:]
            except Exception:
                pass

    def _save(self):
        ECONOMY_FILE.write_text(json.dumps({
            "budgets": self.budgets,
            "transactions": self.transactions[-1000:],
            "updated_at": datetime.now().isoformat(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    def initialize_agent(self, agent_id: str):
        """تهيئة ميزانية وكيل"""
        if agent_id not in self.budgets:
            self.budgets[agent_id] = {
                "daily_budget": self.DEFAULT_DAILY_BUDGET,
                "remaining": self.DEFAULT_DAILY_BUDGET,
                "total_spent": 0,
                "tasks_completed": 0,
                "efficiency_score": 50.0,
                "last_reset": datetime.now().isoformat(),
            }

    def spend(self, agent_id: str, tokens: int, task: str = "") -> bool:
        """إنفاق tokens — يرفض إذا انتهت الميزانية"""
        self.initialize_agent(agent_id)
        budget = self.budgets[agent_id]

        if budget["remaining"] < tokens:
            logger.warning(f"💰 {agent_id}: ميزانية غير كافية ({budget['remaining']}/{tokens})")
            return False

        budget["remaining"] -= tokens
        budget["total_spent"] += tokens
        budget["tasks_completed"] += 1

        # تسجيل المعاملة
        self.transactions.append({
            "agent_id": agent_id,
            "tokens": tokens,
            "task": task[:100],
            "remaining": budget["remaining"],
            "timestamp": datetime.now().isoformat(),
        })

        # تحديث الكفاءة
        if budget["tasks_completed"] > 0:
            avg_tokens = budget["total_spent"] / budget["tasks_completed"]
            budget["efficiency_score"] = max(0, 100 - (avg_tokens / 1000))

        self._save()
        return True

    def reset_daily_budgets(self):
        """إعادة تعيين الميزانيات اليومية"""
        for agent_id, budget in self.budgets.items():
            # الوكلاء الكفوءين يحصلون على ميزانية أكبر
            efficiency = budget.get("efficiency_score", 50)
            multiplier = 1.0 + (efficiency / 200)  # max 1.5x
            budget["daily_budget"] = int(self.DEFAULT_DAILY_BUDGET * multiplier)
            budget["remaining"] = budget["daily_budget"]
            budget["last_reset"] = datetime.now().isoformat()

        self._save()
        logger.info(f"💰 تم إعادة تعيين ميزانيات {len(self.budgets)} وكيل")

    def get_leaderboard(self) -> List[Dict]:
        """ترتيب الوكلاء حسب الكفاءة"""
        board = []
        for agent_id, budget in self.budgets.items():
            board.append({
                "agent_id": agent_id,
                "efficiency": budget.get("efficiency_score", 0),
                "tasks": budget.get("tasks_completed", 0),
                "total_spent": budget.get("total_spent", 0),
            })
        return sorted(board, key=lambda x: x["efficiency"], reverse=True)

    def get_stats(self) -> Dict:
        total_spent = sum(b.get("total_spent", 0) for b in self.budgets.values())
        return {
            "agents_tracked": len(self.budgets),
            "total_tokens_spent": total_spent,
            "transactions_today": len([
                t for t in self.transactions
                if t.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))
            ]),
        }


class CellDivision:
    """
    التكاثر الخلوي للوكلاء
    إذا وكيل مثقل → ينقسم إلى وكيلين متخصصين
    """

    def __init__(self):
        self.divisions_done = 0

    def check_overload(self, agent_stats: Dict) -> bool:
        """هل الوكيل مثقل؟"""
        tasks = agent_stats.get("tasks_done", 0)
        failed = agent_stats.get("tasks_failed", 0)
        # مثقل إذا: أكثر من 50 مهمة/يوم أو نسبة فشل > 30%
        if tasks > 50:
            return True
        if tasks > 10 and failed / max(tasks, 1) > 0.3:
            return True
        return False

    def propose_division(self, agent_id: str, agent_data: Dict) -> Optional[Dict]:
        """اقتراح انقسام"""
        name = agent_data.get("name", "Agent")
        category = agent_data.get("category", "cat1_science")
        description = agent_data.get("description", "")

        # اقتراح تخصصات فرعية
        specializations = {
            "A38": [("A38a", "الفيزياء الكمية", "quantum physics"),
                    ("A38b", "الفيزياء الفلكية", "astrophysics")],
            "A05": [("A05a", "تطوير Backend", "backend development"),
                    ("A05b", "تطوير Frontend", "frontend development")],
            "A02": [("A02a", "البحث الطبي", "medical research"),
                    ("A02b", "البحث التقني", "technical research")],
        }

        specs = specializations.get(agent_id)
        if not specs:
            # تقسيم عام
            specs = [
                (f"{agent_id}a", f"{name} — تحليل", "analysis"),
                (f"{agent_id}b", f"{name} — تنفيذ", "execution"),
            ]

        return {
            "parent": agent_id,
            "children": [
                {"id": s[0], "name": s[1], "specialty": s[2]}
                for s in specs
            ],
            "reason": "overloaded",
            "proposed_at": datetime.now().isoformat(),
        }

    def execute_division(self, agent_id: str, agent_file: str,
                          proposal: Dict) -> Dict:
        """تنفيذ الانقسام — ينسخ ملف JSON ويعدله"""
        results = {"created": [], "errors": []}

        try:
            parent_path = Path(agent_file)
            if not parent_path.exists():
                return {"error": "ملف الوكيل غير موجود"}

            parent_data = json.loads(parent_path.read_text(encoding="utf-8"))

            for child in proposal.get("children", []):
                child_data = parent_data.copy()
                child_data["id"] = child["id"]
                child_data["name"] = child["name"]
                child_data["description"] = f"تخصص فرعي: {child['specialty']}"
                child_data["system_prompt"] = (
                    parent_data.get("system_prompt", "") +
                    f"\n\nتخصصك الدقيق: {child['specialty']}"
                )

                child_file = parent_path.parent / f"{child['id']}.json"
                child_file.write_text(
                    json.dumps(child_data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                results["created"].append(child["id"])

            self.divisions_done += 1
            logger.info(f"🧬 انقسام {agent_id} → {[c['id'] for c in proposal['children']]}")

        except Exception as e:
            results["errors"].append(str(e))

        return results

    def get_stats(self) -> Dict:
        return {"divisions_done": self.divisions_done}


class AdaptiveGuardrails:
    """
    حواجز الحماية التكيفية — جهاز مناعي
    يختبر كل تحديث في sandbox قبل التطبيق
    """

    CRITICAL_FILES = [
        "core/base_agent.py",
        "core/llm_client.py",
        "gateway/app.py",
        "router/smart_router.py",
    ]

    RESOURCE_LIMITS = {
        "max_tokens_per_day": 5_000_000,
        "max_api_cost_per_day": 10.0,  # $
        "max_memory_mb": 2048,
        "max_agents": 200,
        "max_concurrent_tasks": 50,
    }

    def __init__(self):
        self.checks_done = 0
        self.blocks = 0
        self.violations: List[Dict] = []

    def check_code_safety(self, file_path: str, new_code: str) -> Dict:
        """فحص أمان كود جديد"""
        result = {"safe": True, "warnings": [], "blocked": False}

        # 1. ملفات حرجة
        if any(cf in file_path for cf in self.CRITICAL_FILES):
            result["warnings"].append(f"⚠️ تعديل ملف حرج: {file_path}")

        # 2. أنماط خطيرة
        dangerous_patterns = [
            ("os.system", "تنفيذ أوامر نظام"),
            ("subprocess.call", "تنفيذ أوامر خارجية"),
            ("eval(", "تنفيذ كود ديناميكي"),
            ("exec(", "تنفيذ كود ديناميكي"),
            ("shutil.rmtree", "حذف مجلدات"),
            ("os.remove", "حذف ملفات"),
            ("DROP TABLE", "حذف جداول"),
            ("DELETE FROM", "حذف بيانات"),
            ("__import__", "استيراد ديناميكي"),
        ]

        for pattern, desc in dangerous_patterns:
            if pattern in new_code:
                result["warnings"].append(f"🔴 {desc}: {pattern}")
                result["safe"] = False

        # 3. حجم الكود
        if len(new_code) > 50000:
            result["warnings"].append("⚠️ كود كبير جداً (>50KB)")

        self.checks_done += 1
        if not result["safe"]:
            self.blocks += 1
            result["blocked"] = True
            self._log_violation(file_path, result["warnings"])

        return result

    def check_resource_usage(self, metrics: Dict) -> Dict:
        """فحص استهلاك الموارد"""
        result = {"within_limits": True, "violations": []}

        for key, limit in self.RESOURCE_LIMITS.items():
            current = metrics.get(key, 0)
            if current > limit:
                result["within_limits"] = False
                result["violations"].append(f"{key}: {current} > {limit}")

        return result

    def check_prompt_change(self, agent_id: str, old_prompt: str,
                            new_prompt: str) -> Dict:
        """فحص تغيير prompt"""
        result = {"approved": True, "reason": ""}

        # لا تحذف أكثر من 50% من المحتوى
        if len(new_prompt) < len(old_prompt) * 0.5:
            result["approved"] = False
            result["reason"] = "حذف أكثر من 50% من المحتوى"

        # لا تزيد أكثر من 3x
        if len(new_prompt) > len(old_prompt) * 3:
            result["approved"] = False
            result["reason"] = "زيادة أكثر من 3 أضعاف"

        return result

    def simulate_change(self, change_type: str, change_data: Dict) -> Dict:
        """محاكاة تغيير قبل التطبيق"""
        simulation = {
            "change_type": change_type,
            "simulated": True,
            "passed": True,
            "issues": [],
            "timestamp": datetime.now().isoformat(),
        }

        if change_type == "code":
            safety = self.check_code_safety(
                change_data.get("file", ""),
                change_data.get("code", "")
            )
            if not safety["safe"]:
                simulation["passed"] = False
                simulation["issues"] = safety["warnings"]

        elif change_type == "prompt":
            check = self.check_prompt_change(
                change_data.get("agent_id", ""),
                change_data.get("old", ""),
                change_data.get("new", "")
            )
            if not check["approved"]:
                simulation["passed"] = False
                simulation["issues"].append(check["reason"])

        return simulation

    def _log_violation(self, target: str, warnings: List[str]):
        self.violations.append({
            "target": target,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat(),
        })

    def get_stats(self) -> Dict:
        return {
            "checks_done": self.checks_done,
            "blocks": self.blocks,
            "violations": len(self.violations),
        }
