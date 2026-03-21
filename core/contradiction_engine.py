import concurrent.futures
import os
import requests

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")

class ContradictionEngine:
    """
    يجد التناقضات بين آراء الوكلاء
    ويصنع رؤى جديدة لا يمكن لوكيل واحد اكتشافها
    """
    
    def query_agent(self, agent_id: str, prompt: str) -> str:
        try:
            r = requests.post(f"{GATEWAY}/task", json={"task": prompt, "agent_id": agent_id, "preferred_agent": agent_id}, timeout=60)
            if r.status_code == 200:
                return r.json().get("result", "")
        except Exception as e:
            print(f"Error querying {agent_id}: {e}")
        return ""

    def find_and_resolve(self, question: str) -> dict:
        """
        1. يسأل 3 وكلاء من تخصصات مختلفة
        2. يجد نقاط الاختلاف بينهم
        3. يرسلها لـ A81 للتركيب في رؤية أعلى
        """
        agents = self.select_diverse_agents(question)
        
        opinions = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futures = {ex.submit(self.query_agent, a, question): a for a in agents}
            for f in concurrent.futures.as_completed(futures, timeout=60):
                a = futures[f]
                opinions[a] = f.result()
        
        contradictions = self.find_contradictions(opinions)
        
        if contradictions:
            synthesis_prompt = f"""
            السؤال: {question}
            
            ثلاثة خبراء اختلفوا:
            {chr(10).join(f"{k}: {v[:200]}" for k,v in opinions.items())}
            
            نقاط الاختلاف الجوهرية:
            {contradictions}
            
            مهمتك: لا تختر رأياً — اصنع رؤية جديدة تفسر لماذا كل منهم صحيح
            في سياقه، وما الذي يعنيه الاختلاف نفسه.
            """
            synthesis = self.query_agent("A81", synthesis_prompt)
        else:
            synthesis = "الآراء متسقة — لا توجد تناقضات مثيرة للاهتمام"
        
        return {
            "question": question,
            "opinions": opinions,
            "contradictions": contradictions,
            "synthesis": synthesis,
            "insight_level": "HIGH" if contradictions else "NORMAL",
        }
    
    def find_contradictions(self, opinions: dict) -> str:
        """يستخلص نقاط الاختلاف الجوهرية"""
        prompt = "حدد نقاط الاختلاف الجوهرية والتناقضات الواضحة بين هذه الآراء:\n" + "\n".join(f"{k}: {v}" for k,v in opinions.items())
        res = self.query_agent("A81", prompt)
        if len(res) > 50:
            return res
        return ""
    
    def select_diverse_agents(self, question: str) -> list:
        """يختار وكلاء من أكثر التخصصات اختلافاً للسؤال"""
        return ["A04", "A23", "A37"]
