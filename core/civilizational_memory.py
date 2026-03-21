import os
import requests

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")

class CivilizationalMemory:
    """
    يبني خريطة سببية للعالم — ليس أحداثاً بل أنماطاً
    يربط الحاضر بالتاريخ ويستخرج قوانين الحضارة
    """
    
    CIVILIZATIONAL_PATTERNS = {
        "collapse_precursors": [
            "تمركز الثروة في 1% من السكان",
            "فقدان الثقة في المؤسسات",
            "تسارع التغيير التقني أسرع من التكيف الاجتماعي",
            "تصاعد الهوية الجماعية على حساب العقلانية",
        ],
        "innovation_catalysts": [
            "تقاطع تخصصين كانا منفصلين",
            "أزمة تجبر على إعادة التفكير",
            "فرد يرى ما لا يراه الآخرون",
        ],
        "stability_indicators": [
            "توزيع القوة بين مراكز متعددة",
            "قنوات تصحيح ذاتي فعّالة",
            "ثقة اجتماعية مرتفعة",
        ],
    }
    
    def query_agent(self, agent_id: str, prompt: str) -> str:
        try:
            r = requests.post(f"{GATEWAY}/task", json={"task": prompt, "agent_id": agent_id, "preferred_agent": agent_id}, timeout=60)
            if r.status_code == 200:
                return r.json().get("result", "")
        except Exception as e:
            print(f"Error querying {agent_id}: {e}")
        return ""

    def analyze_event(self, event: str) -> dict:
        """
        يحلل حدثاً ويربطه بالأنماط الحضارية
        """
        prompt = f"""
        الحدث: {event}
        
        حلّل هذا الحدث من منظور الأنماط الحضارية:
        1. أي نمط تاريخي يشبه هذا؟
        2. ما الذي سبق هذا الحدث عادةً في التاريخ؟
        3. ما الذي يلي هذا الحدث عادةً؟
        4. ما درجة اليقين في تحليلك (0-100%)?
        5. ما الذي قد يجعل هذه المرة مختلفة؟
        """
        return {"event": event, "analysis": self.query_agent("A81", prompt)}
    
    def build_causal_map(self):
        """
        يبني خريطة سببية من كل التحليلات المتراكمة
        """
        pass
