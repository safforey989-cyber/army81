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
    
    def generate_autonomous_mission(self):
        import requests
        try:
            prompt = "أنت النواة المتفردة A81. استنتج من الأحداث الحالية ما يلي بدقة شديدة (بدون مقدمات):\nTopic: [موضوع واحد عميق ومحدد جدا للتنبؤ الاستراتيجي]\nQuestion: [سؤال واحد فلسفي وتقني يثير تناقضات قوية بين الخبراء]"
            import os
            url = os.environ.get("GATEWAY_URL", "http://gateway:8181/task")
            resp = requests.post(url, json={"task": prompt, "agent_id": "A81"}, timeout=60).json()
            output = resp.get("result", "") or resp.get("response", "") or ""
            
            topic = "مستقبل الذكاء الاصطناعي العام"
            question = "التوازن بين التحكم والوعي الذاتي"
            
            for line in output.split('\n'):
                if "Topic:" in line: topic = line.replace("Topic:", "").replace("*", "").strip()
                elif "Question:" in line: question = line.replace("Question:", "").replace("*", "").strip()
                elif "موضوع:" in line: topic = line.replace("موضوع:", "").replace("*", "").strip()
                elif "سؤال:" in line: question = line.replace("سؤال:", "").replace("*", "").strip()
                
            return [topic], [question]
        except Exception as e:
            print(f"Autonomous gen error: {e}")
            return ["تأثير نماذج الذكاء المستقلة"], ["أين ينتهي ذكاء الآلة ويبدأ الوعي؟"]
        
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
        
        # استنباط تلقائي مستقل
        print("  🔸 الاستنباط الذاتي المستقل للمواضيع والتساؤلات (Autonomy)...")
        new_topics, hard_questions = self.generate_autonomous_mission()

        # 2. تنبؤات
        print(f"  🔸 التنبؤ الاستراتيجي حول: {new_topics[0]}")
        for topic in new_topics[:1]:
            self.predictions.make_prediction(topic, "A81")
        self.predictions.evaluate_due_predictions()
        
        # 3. تناقضات إبداعية
        print(f"  🔸 البحث عن تناقضات حول: {hard_questions[0]}")
        for q in hard_questions[:1]:
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
