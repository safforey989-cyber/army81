import json
from pathlib import Path

class EpistemicMap:
    """
    كل وكيل يعرف بدقة:
    - ما يعلمه بيقين (certainty > 80%)
    - ما يعلمه بشك (certainty 40-80%)
    - ما لا يعلمه (certainty < 40%)
    - ما لا يعلم أنه لا يعلمه (unknown unknowns)
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        Path("workspace/epistemic").mkdir(parents=True, exist_ok=True)
        self.map_file = Path(f"workspace/epistemic/{agent_id}_map.json")
        self.map = self.load()
        
    def load(self):
        if self.map_file.exists():
            return json.loads(self.map_file.read_text(encoding="utf-8"))
        return {"certain": [], "uncertain": [], "unknown": []}
        
    def save(self):
        self.map_file.write_text(json.dumps(self.map, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def query_with_honesty(self, question: str, agent_response: str) -> str:
        """
        بعد كل إجابة، يقيّم الوكيل مستوى يقينه
        """
        evaluation_prompt = f"""
        السؤال: {question}
        إجابتك: {agent_response[:500]}
        
        الآن كن صادقاً تماماً:
        1. ما درجة يقينك في هذه الإجابة؟ (0-100%)
        2. ما الأجزاء التي أنت غير متأكد منها؟
        3. ما الذي تحتاج أن تعرفه لتكون أكثر يقيناً؟
        4. هل هناك سؤال آخر يجب أن يُسأل أولاً؟
        
        أجب بـ JSON فقط: {{"certainty": 0-100, "uncertain_parts": [], "needed_info": [], "better_question": ""}}
        """
        return evaluation_prompt
    
    def update_map(self, question: str, certainty: int, category: str):
        """يبني خريطة تراكمية للمعرفة"""
        if certainty > 80:
            self.map["certain"].append({"q": question, "cat": category})
        elif certainty > 40:
            self.map["uncertain"].append({"q": question, "cat": category})
        else:
            self.map["unknown"].append({"q": question, "cat": category})
        self.save()
    
    def get_weaknesses(self) -> list:
        """ما نقاط ضعف هذا الوكيل المعرفية؟"""
        return [item["q"] for item in self.map.get("unknown", [])]
