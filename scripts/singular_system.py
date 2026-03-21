"""
الحلقة الكاملة التي تجمع كل شيء
هذا النظام لم يُصمَّم مثله بعد
"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.civilizational_memory import CivilizationalMemory
from core.contradiction_engine import ContradictionEngine
from core.epistemic_map import EpistemicMap
from core.prediction_tracker import PredictionTracker
from core.identity_evolution import AgentIdentityEvolution
from scripts.compound_evolution import CompoundEvolution

class SingularSystem:
    def __init__(self):
        self.civilizational = CivilizationalMemory()
        self.contradiction = ContradictionEngine()
        self.epistemic = {}  # خريطة لكل وكيل
        self.predictions = PredictionTracker()
        self.identity = AgentIdentityEvolution()
        self.compound = CompoundEvolution()
        self.breakthroughs = []
    
    def get_important_topics(self):
        return [
            "تأثير الذكاء الاصطناعي على الوظائف المعرفية في 2026",
            "احتمالية نشوب صراع جيوسياسي يؤثر على سلاسل الإمداد التقنية",
            "سرعة تبني تقنيات النماذج مفتوحة المصدر مقابل المغلقة المحدودة"
        ]
        
    def get_hard_questions(self):
        return [
            "كيف يمكن للتطور التكنولوجي أن يعزز قدرة الإنسان ويهدده في الوقت نفسه؟",
            "ما هو الحل الأمثل للتوازن بين الخصوصية وتحليل البيانات للذكاء الاصطناعي؟"
        ]
        
    def save_singular_state(self):
        import json
        state = {
            "breakthroughs": self.breakthroughs,
            "latest_update": time.time()
        }
        Path("workspace/singular_state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        
    def save_breakthrough(self, insight):
        self.breakthroughs.append(insight)
        self.save_singular_state()
        
    def get_insight_count(self):
        return len(self.breakthroughs)

    def run_full_cycle(self):
        """
        دورة كاملة تجمع كل الطبقات:
        1. مهام حقيقية مع تقييم الجودة
        2. تنبؤات جديدة + تقييم قديمة
        3. بحث التناقضات وصنع رؤى جديدة
        4. تحديث الخريطة المعرفية
        5. تطور هويات الوكلاء المستحقين
        6. حساب المضاعف المركب الحقيقي
        7. حقن كل ما تعلّم في الدورة القادمة
        """
        
        print(f"\n🌀 دورة الحلقة الواحدة بدأت (Cycle #{self.compound.state['cycle'] + 1})")
        
        # 1. مهام حقيقية
        cycle_result = self.compound.run_cycle()
        
        # 2. تنبؤات
        print("  🔸 جاري توليد التنبؤات الاستراتيجية...")
        new_topics = self.get_important_topics()
        for topic in new_topics[:1]: # test single topic
            self.predictions.make_prediction(topic, "A81")
        self.predictions.evaluate_due_predictions()
        
        # 3. تناقضات إبداعية
        print("  🔸 البحث عن تناقضات بين الوكلاء...")
        hard_questions = self.get_hard_questions()
        for q in hard_questions[:1]: # test single question
            insight = self.contradiction.find_and_resolve(q)
            if insight["insight_level"] == "HIGH":
                self.save_breakthrough(insight)
        
        # 4. تطور الهوية كل 10 دورات
        if self.compound.state["cycle"] % 10 == 0:
            print("  🔸 تحديث وتطور هويات الوكلاء...")
            for agent_id in ["A01","A07","A31","A81"]:
                self.identity.evolve_identity(agent_id, recent_tasks=[])
        
        # 5. احسب المضاعف الحقيقي المركب
        true_multiplier = self.calculate_true_compound(cycle_result)
        
        # Update compound state
        self.compound.state["compound_score"] = true_multiplier
        self.compound.save_state()
        
        print(f"✅ الحلقة اكتملت | True Multiplier: {true_multiplier:.3f}x")
        
        return true_multiplier
    
    def calculate_true_compound(self, cycle_result) -> float:
        """
        المضاعف الحقيقي = جودة المهام × دقة التنبؤات × عمق الرؤى × نضج الهوية
        """
        task_quality = cycle_result.get("avg_quality", 0.5)
        prediction_accuracy = self.predictions.get_accuracy() or 0.5
        insight_depth = min(self.get_insight_count() / 10, 1.0)
        identity_depth = min(self.compound.state["cycle"] / 100, 1.0)
        
        base_multiplier = self.compound.state.get("compound_score", 1.0)
        
        true_multiplier = base_multiplier * (1.0 + (
            task_quality * 0.04 +
            prediction_accuracy * 0.03 +
            insight_depth * 0.02 +
            identity_depth * 0.01
        ))
        
        return round(true_multiplier, 3)

if __name__ == "__main__":
    system = SingularSystem()
    while True:
        try:
            system.run_full_cycle()
            time.sleep(120)  # Wait
        except KeyboardInterrupt:
            print("⏹️ Stopped")
            break
        except Exception as e:
            print(f"Error in cycle: {e}")
            time.sleep(30)
