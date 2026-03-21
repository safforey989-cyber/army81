import os
import json
import uuid
import requests
from datetime import datetime, timedelta
from pathlib import Path

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")

class PredictionTracker:
    """
    النظام يتنبأ ويتتبع تنبؤاته ويتعلم من الخطأ
    هذا ما يفعله كبار المحللين الاستراتيجيين
    لا أحد فعله في AI بعد
    """
    
    def __init__(self):
        Path("workspace/predictions").mkdir(parents=True, exist_ok=True)
        self.predictions_file = Path("workspace/predictions/tracker.json")
        self.predictions = self.load_predictions()

    def load_predictions(self):
        if self.predictions_file.exists():
            return json.loads(self.predictions_file.read_text(encoding="utf-8"))
        return {"predictions": [], "lessons": []}
        
    def save_predictions_state(self):
        self.predictions_file.write_text(json.dumps(self.predictions, ensure_ascii=False, indent=2), encoding="utf-8")

    def query_agent(self, agent_id: str, prompt: str) -> str:
        try:
            r = requests.post(f"{GATEWAY}/task", json={"task": prompt, "agent_id": agent_id, "preferred_agent": agent_id}, timeout=60)
            if r.status_code == 200:
                return r.json().get("result", "")
        except Exception as e:
            print(f"Error querying {agent_id}: {e}")
        return ""

    def make_prediction(self, topic: str, agent_id: str) -> dict:
        """يطلب من الوكيل تنبؤاً مع مستوى ثقة وإطار زمني"""
        prompt = f"""
        حول: {topic}
        
        قدم تنبؤاً محدداً وقابلاً للاختبار:
        1. ما الذي ستتوقع حدوثه؟ (محدد وقابل للقياس)
        2. خلال أي إطار زمني بالايام؟ (مثال: 7)
        3. ما مستوى ثقتك؟ (0-100%)
        4. ما الذي سيجعلك مخطئاً؟ (falsification criteria)
        
        أجب بـ JSON المنسق هكذا: {{"prediction": "...", "timeframe_days": 7, "confidence": 80, "falsification": "..."}}
        """
        
        response = self.query_agent(agent_id, prompt)
        
        prediction_text = response
        timeframe = 7
        confidence = 50
        falsification = ""
        try:
            import re
            m = re.search(r'\{.*\}', response, re.DOTALL)
            if m:
                d = json.loads(m.group(0))
                prediction_text = d.get("prediction", response)
                timeframe = d.get("timeframe_days", 7)
                confidence = d.get("confidence", 50)
                falsification = d.get("falsification", "")
        except:
            pass
        
        prediction = {
            "id": str(uuid.uuid4()),
            "agent": agent_id,
            "topic": topic,
            "made_at": datetime.now().isoformat(),
            "due_at": (datetime.now() + timedelta(days=timeframe)).isoformat(),
            "prediction": prediction_text,
            "confidence": confidence,
            "falsification": falsification,
            "outcome": None,
            "accuracy": None,
        }
        
        self.predictions["predictions"].append(prediction)
        self.save_predictions_state()
        return prediction
    
    def get_due_predictions(self):
        now = datetime.now()
        return [p for p in self.predictions["predictions"] if p["outcome"] is None and datetime.fromisoformat(p["due_at"]) <= now]

    def update_prediction(self, pred_id, evaluation):
        for p in self.predictions["predictions"]:
            if p["id"] == pred_id:
                p["outcome"] = evaluation
                if "صحيح تماماً" in evaluation: p["accuracy"] = 1.0
                elif "جزئياً" in evaluation: p["accuracy"] = 0.5
                elif "خاطئ" in evaluation: p["accuracy"] = 0.0
                self.save_predictions_state()
                break

    def save_lesson(self, agent_id, evaluation):
        self.predictions["lessons"].append({"agent": agent_id, "lesson": evaluation, "time": datetime.now().isoformat()})
        self.save_predictions_state()

    def evaluate_due_predictions(self):
        """
        يُشغَّل يومياً — يقيّم التنبؤات التي حان موعدها
        """
        due = self.get_due_predictions()
        for pred in due:
            days_ago = (datetime.now() - datetime.fromisoformat(pred['made_at'])).days
            eval_prompt = f"""
            قبل {days_ago} يوم، تنبأت بـ: {pred['prediction']}
            
            الآن: هل حدث هذا؟ قيّم:
            1. صحيح تماماً / صحيح جزئياً / خاطئ / لا يمكن تقييمه بعد
            2. إذا كنت مخطئاً: لماذا؟ ما الذي فاتك؟
            3. ما الذي تعلمته للمرة القادمة؟
            """
            evaluation = self.query_agent(pred["agent"], eval_prompt)
            self.update_prediction(pred["id"], evaluation)
            
            if "خاطئ" in evaluation:
                self.save_lesson(pred["agent"], evaluation)
    
    def get_accuracy(self) -> float:
        accuracies = [p["accuracy"] for p in self.predictions["predictions"] if p.get("accuracy") is not None]
        if accuracies:
            return sum(accuracies) / len(accuracies)
        return 0.5
        
    def get_accuracy_report(self) -> dict:
        """تقرير دقة كل وكيل في التنبؤات"""
        return {"overall": self.get_accuracy()}
