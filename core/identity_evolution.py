import os
import json
import requests
from pathlib import Path

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")

class AgentIdentityEvolution:
    """
    كل وكيل لديه هوية تتطور عبر الوقت
    ليس system_prompt ثابت — بل شخصية تتعمق
    """
    
    def query_agent(self, agent_id: str, prompt: str) -> str:
        try:
            r = requests.post(f"{GATEWAY}/task", json={"task": prompt, "agent_id": agent_id, "preferred_agent": agent_id}, timeout=60)
            if r.status_code == 200:
                return r.json().get("result", "")
        except Exception as e:
            print(f"Error querying {agent_id}: {e}")
        return ""

    def update_agent_identity(self, agent_id: str, reflection: str):
        agents_dir = Path("agents")
        for cat_dir in agents_dir.iterdir():
            if not cat_dir.is_dir(): continue
            agent_file = cat_dir / f"{agent_id}.json"
            if agent_file.exists():
                try:
                    data = json.loads(agent_file.read_text(encoding="utf-8"))
                    prompt = data.get("system_prompt", "")
                    if "## تطور الهوية:" not in prompt:
                        prompt += f"\n\n## تطور الهوية:\n{reflection}"
                    else:
                        prompt += f"\n- {reflection}"
                    data["system_prompt"] = prompt
                    agent_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                except:
                    pass
                break

    def evolve_identity(self, agent_id: str, recent_tasks: list):
        """
        بعد كل 100 مهمة، يطرح الوكيل على نفسه:
        "ماذا تعلمت؟ كيف تغيرت نظرتي؟ ما الذي صار أكثر وضوحاً؟"
        """
        if not recent_tasks:
            recent_tasks = ["مهام عامة في التخصص", "مهندسو Army81 يقومون بترقيتك"]
            
        reflection_prompt = f"""
        أنت {agent_id}. أنهيت مهام جديدة.
        
        من بين مهامك الأخيرة:
        {chr(10).join(f"- {t[:80]}" for t in recent_tasks[-10:])}
        
        أجب بصدق تام:
        1. ما الذي صار أكثر وضوحاً في تخصصك؟
        2. ما الذي تفاجأت أنك لا تعرفه؟
        3. ما القناعة التي تغيرت لديك؟
        4. كيف تصف نفسك اليوم مقارنة بقبل هذه المهام؟
        5. ما الأسلوب الأفضل الذي اكتشفته للإجابة؟
        
        اكتب بضمير المتكلم وبصدق — هذا سيصبح جزءاً من هويتك.
        """
        reflection = self.query_agent(agent_id, reflection_prompt)
        
        self.update_agent_identity(agent_id, reflection)
        
        return reflection
