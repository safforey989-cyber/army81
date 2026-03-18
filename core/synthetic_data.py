"""
Army81 — Synthetic Data Generator + Self-Play Engine
توليد بيانات اصطناعية + تدريب عبر اللعب الذاتي
"""
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("army81.synthetic_data")

WORKSPACE = Path("workspace")
SYNTH_DIR = WORKSPACE / "synthetic_data"
SELFPLAY_DIR = WORKSPACE / "self_play"


class SyntheticDataGenerator:
    """
    توليد سيناريوهات ومشاكل معقدة يومياً
    وكلاء العلم (Cat1) يولدون — وكلاء آخرون يحلون
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.generated_count = 0
        self.solved_count = 0
        SYNTH_DIR.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════
    # مولدات السيناريوهات حسب المجال
    # ═══════════════════════════════════════════════════

    SCENARIO_TEMPLATES = {
        "medical": [
            "مريض عمره {age} سنة يعاني من {symptoms}. التاريخ المرضي: {history}. ما التشخيص التفريقي وخطة العلاج؟",
            "حالة طوارئ: {emergency_type} في مستشفى ريفي. الموارد محدودة. ما خطة التعامل؟",
            "بحث سريري: تصميم تجربة عشوائية لاختبار {drug} على {condition}. ما المنهجية المثلى؟",
        ],
        "financial": [
            "محفظة استثمارية بقيمة {amount}. الأسواق تشير لـ {trend}. ما استراتيجية التحوط المثلى؟",
            "شركة ناشئة تحتاج تمويل {funding}. المنافسون: {competitors}. ما التقييم العادل؟",
            "أزمة مالية في {country}. التضخم {inflation}%. ما السياسة النقدية المناسبة؟",
        ],
        "code": [
            "صمم نظام {system_type} يتحمل {load} طلب/ثانية. القيود: {constraints}. أعطِ الكود كاملاً.",
            "أصلح هذا الخطأ: {bug_description}. الكود الأصلي: {code_snippet}. أعطِ الحل مع الشرح.",
            "حسّن أداء هذه الخوارزمية من O({old_complexity}) إلى O({new_complexity}): {algorithm}",
        ],
        "strategy": [
            "دولة {country} تواجه {crisis}. الموارد: {resources}. ما الخطة الاستراتيجية؟",
            "شركة تقنية تدخل سوق {market}. المنافس الرئيسي: {competitor}. ما استراتيجية الدخول؟",
            "نزاع جيوسياسي بين {party_a} و{party_b} حول {issue}. ما سيناريوهات الحل؟",
        ],
        "research": [
            "اكتب ملخصاً لورقة بحثية عن {topic} مع نقد منهجي لـ 3 نقاط ضعف.",
            "قارن بين {method_a} و{method_b} في معالجة {problem}. أيهما أفضل ولماذا؟",
            "صمم تجربة لاختبار فرضية: {hypothesis}. ما المتغيرات والضوابط؟",
        ],
    }

    FILL_DATA = {
        "age": lambda: random.randint(5, 90),
        "symptoms": lambda: random.choice(["صداع شديد وحمى", "ألم صدري وضيق تنفس",
                                            "تنميل في الأطراف", "نزيف هضمي"]),
        "history": lambda: random.choice(["سكري نوع 2", "ضغط مرتفع", "بدون أمراض سابقة"]),
        "emergency_type": lambda: random.choice(["حادث سير جماعي", "تسمم غذائي جماعي"]),
        "drug": lambda: random.choice(["دواء جديد للسكري", "لقاح تجريبي"]),
        "condition": lambda: random.choice(["السكري نوع 2", "ارتفاع الكوليسترول"]),
        "amount": lambda: random.choice(["$100K", "$1M", "$10M"]),
        "trend": lambda: random.choice(["ركود قادم", "فقاعة تقنية", "نمو مستدام"]),
        "funding": lambda: random.choice(["$500K seed", "$5M Series A"]),
        "competitors": lambda: random.choice(["3 شركات كبرى", "سوق مزدحم"]),
        "country": lambda: random.choice(["مصر", "السعودية", "الإمارات", "الأردن"]),
        "inflation": lambda: random.randint(3, 25),
        "system_type": lambda: random.choice(["chat bot", "e-commerce", "real-time analytics"]),
        "load": lambda: random.choice(["1000", "10000", "100000"]),
        "constraints": lambda: random.choice(["ميزانية محدودة", "وقت أسبوع", "فريق شخصين"]),
        "bug_description": lambda: random.choice(["memory leak", "race condition", "deadlock"]),
        "code_snippet": lambda: "def process(data): return data.transform()",
        "old_complexity": lambda: random.choice(["n²", "n³", "2^n"]),
        "new_complexity": lambda: random.choice(["n log n", "n", "log n"]),
        "algorithm": lambda: "bubble_sort",
        "crisis": lambda: random.choice(["جفاف حاد", "أزمة اقتصادية", "وباء"]),
        "resources": lambda: random.choice(["محدودة", "متوسطة", "وفيرة"]),
        "market": lambda: random.choice(["الشرق الأوسط", "أفريقيا", "جنوب آسيا"]),
        "competitor": lambda: random.choice(["Google", "Microsoft", "Amazon"]),
        "party_a": lambda: random.choice(["دولة A", "مجموعة A"]),
        "party_b": lambda: random.choice(["دولة B", "مجموعة B"]),
        "issue": lambda: random.choice(["الموارد المائية", "الحدود", "التجارة"]),
        "topic": lambda: random.choice(["LLM agents", "quantum ML", "protein folding"]),
        "method_a": lambda: random.choice(["Transformer", "GNN", "RL"]),
        "method_b": lambda: random.choice(["LSTM", "CNN", "Bayesian"]),
        "problem": lambda: random.choice(["NLP", "computer vision", "time series"]),
        "hypothesis": lambda: "النماذج الصغيرة المُقطَّرة تتفوق على الكبيرة في المهام المتخصصة",
    }

    def generate_scenario(self, domain: str = None) -> Dict:
        """يولد سيناريو واحد"""
        if domain is None:
            domain = random.choice(list(self.SCENARIO_TEMPLATES.keys()))

        templates = self.SCENARIO_TEMPLATES.get(domain, self.SCENARIO_TEMPLATES["research"])
        template = random.choice(templates)

        # ملء القالب
        scenario_text = template
        for key, gen_fn in self.FILL_DATA.items():
            placeholder = "{" + key + "}"
            if placeholder in scenario_text:
                scenario_text = scenario_text.replace(placeholder, str(gen_fn()))

        scenario = {
            "id": f"SYN-{self.generated_count:06d}",
            "domain": domain,
            "scenario": scenario_text,
            "difficulty": random.choice(["easy", "medium", "hard", "expert"]),
            "created_at": datetime.now().isoformat(),
            "solved": False,
            "solution": None,
            "solver_agent": None,
            "quality_score": None,
        }
        self.generated_count += 1
        return scenario

    def generate_batch(self, count: int = 50) -> List[Dict]:
        """توليد دفعة من السيناريوهات"""
        scenarios = []
        for _ in range(count):
            domain = random.choice(list(self.SCENARIO_TEMPLATES.keys()))
            scenarios.append(self.generate_scenario(domain))

        # حفظ
        batch_file = SYNTH_DIR / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        batch_file.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"📊 تم توليد {count} سيناريو")
        return scenarios

    def solve_scenario(self, scenario: Dict, agent_run_fn=None) -> Dict:
        """حل سيناريو باستخدام وكيل"""
        if agent_run_fn:
            try:
                result = agent_run_fn(scenario["scenario"])
                scenario["solved"] = True
                scenario["solution"] = result.get("result", "")[:2000]
                scenario["solver_agent"] = result.get("agent_id", "unknown")
                scenario["quality_score"] = self._evaluate_solution(scenario)
                self.solved_count += 1
            except Exception as e:
                scenario["solved"] = False
                scenario["solution"] = f"Error: {e}"
        return scenario

    def _evaluate_solution(self, scenario: Dict) -> float:
        """تقييم بسيط لجودة الحل"""
        solution = scenario.get("solution", "")
        score = 0.0

        # طول كافٍ
        if len(solution) > 100:
            score += 30
        if len(solution) > 300:
            score += 20

        # يحتوي على بنية
        if any(marker in solution for marker in ["1.", "أولاً", "##", "- "]):
            score += 20

        # يحتوي على تحليل
        if any(word in solution for word in ["لأن", "بسبب", "نتيجة", "therefore", "because"]):
            score += 15

        # لا يحتوي على أخطاء واضحة
        if "خطأ" not in solution and "Error" not in solution:
            score += 15

        return min(score, 100.0)

    def daily_generation_cycle(self, agent_run_fn=None) -> Dict:
        """الدورة اليومية لتوليد البيانات"""
        logger.info("📊 بدء دورة توليد البيانات الاصطناعية")

        scenarios = self.generate_batch(50)
        solved = 0

        if agent_run_fn:
            for scenario in scenarios[:20]:  # حل 20 فقط لتوفير الموارد
                self.solve_scenario(scenario, agent_run_fn)
                if scenario["solved"]:
                    solved += 1
                time.sleep(1)

        return {
            "generated": len(scenarios),
            "solved": solved,
            "avg_quality": sum(
                s.get("quality_score", 0) for s in scenarios if s.get("solved")
            ) / max(solved, 1)
        }

    def get_stats(self) -> Dict:
        return {
            "total_generated": self.generated_count,
            "total_solved": self.solved_count,
            "domains": list(self.SCENARIO_TEMPLATES.keys()),
        }


class SelfPlayEngine:
    """
    التعلم المعزز باللعب الذاتي
    Red Team vs Blue Team
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.rounds_played = 0
        self.red_wins = 0
        self.blue_wins = 0
        SELFPLAY_DIR.mkdir(parents=True, exist_ok=True)

    def create_challenge(self, domain: str) -> Dict:
        """Red Team يخلق تحدياً"""
        challenges = {
            "security": {
                "challenge": "اكتشف ثغرة في هذا الكود واشرح كيف يمكن استغلالها",
                "code": "app.get('/user', (req) => db.query(`SELECT * FROM users WHERE id=${req.params.id}`))",
                "difficulty": "medium"
            },
            "logic": {
                "challenge": "هذا الحل يدعي أنه O(n) لكنه في الحقيقة O(n²). اكتشف الخطأ المنطقي.",
                "code": "def find_dup(arr): seen=set(); return [x for x in arr if x in seen or seen.add(x)]",
                "difficulty": "hard"
            },
            "strategy": {
                "challenge": "هذه الخطة الاستراتيجية فيها 3 ثغرات خطيرة. اكتشفها.",
                "plan": "ندخل السوق بسعر منخفض → نرفع بعد سنة → نوسع عالمياً",
                "difficulty": "medium"
            },
            "factual": {
                "challenge": "هذه الإجابة تحتوي معلومة خاطئة واحدة. اكتشفها وصححها.",
                "answer": "الـ Transformer اخترعته Google عام 2015 في ورقة Attention is All You Need",
                "difficulty": "easy"
            },
        }
        return challenges.get(domain, challenges["logic"])

    def play_round(self, red_agent_fn=None, blue_agent_fn=None) -> Dict:
        """جولة واحدة Red vs Blue"""
        domain = random.choice(["security", "logic", "strategy", "factual"])
        challenge = self.create_challenge(domain)

        round_result = {
            "round": self.rounds_played + 1,
            "domain": domain,
            "challenge": challenge,
            "red_attack": None,
            "blue_defense": None,
            "winner": None,
            "timestamp": datetime.now().isoformat()
        }

        # Red Team يهاجم
        if red_agent_fn:
            try:
                red_task = f"أنت Red Team. {challenge['challenge']}\n{json.dumps(challenge, ensure_ascii=False)}"
                red_result = red_agent_fn(red_task)
                round_result["red_attack"] = red_result.get("result", "")[:1000]
            except Exception:
                round_result["red_attack"] = "فشل الهجوم"

        # Blue Team يدافع
        if blue_agent_fn:
            try:
                blue_task = f"أنت Blue Team. دافع عن هذا النظام وأصلح الثغرات:\n{round_result['red_attack']}"
                blue_result = blue_agent_fn(blue_task)
                round_result["blue_defense"] = blue_result.get("result", "")[:1000]
            except Exception:
                round_result["blue_defense"] = "فشل الدفاع"

        # تقييم الفائز
        red_score = len(round_result.get("red_attack", "")) if round_result.get("red_attack") else 0
        blue_score = len(round_result.get("blue_defense", "")) if round_result.get("blue_defense") else 0

        if red_score > blue_score:
            round_result["winner"] = "red"
            self.red_wins += 1
        else:
            round_result["winner"] = "blue"
            self.blue_wins += 1

        self.rounds_played += 1

        # حفظ
        log_file = SELFPLAY_DIR / f"round_{self.rounds_played:04d}.json"
        log_file.write_text(json.dumps(round_result, ensure_ascii=False, indent=2), encoding="utf-8")

        return round_result

    def daily_tournament(self, red_fn=None, blue_fn=None, rounds: int = 10) -> Dict:
        """بطولة يومية"""
        logger.info(f"⚔️ بدء بطولة Self-Play — {rounds} جولات")
        results = []
        for i in range(rounds):
            r = self.play_round(red_fn, blue_fn)
            results.append(r)
            time.sleep(1)

        return {
            "rounds": rounds,
            "red_wins": sum(1 for r in results if r["winner"] == "red"),
            "blue_wins": sum(1 for r in results if r["winner"] == "blue"),
        }

    def get_stats(self) -> Dict:
        return {
            "rounds_played": self.rounds_played,
            "red_wins": self.red_wins,
            "blue_wins": self.blue_wins,
            "red_rate": self.red_wins / max(self.rounds_played, 1),
        }
