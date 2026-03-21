import os
import requests
import re
import json
from pathlib import Path

class SelfModifyingGenome:
    """
    نظام الجينوم البرمجي ذاتي التعديل.
    يسمح للنظام (الأساس) بإضافة أكواد برمجية حقيقية 100% 
    وأدوات بايثون جديدة إلى نفسه لكتابة قدرات لم تُبرمج فيه مسبقاً.
    """
    def __init__(self):
        self.gateway_url = os.environ.get("GATEWAY_URL", "http://gateway:8181")
        self.tools_dir = Path(os.path.join(os.path.dirname(__file__), "..", "tools"))
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
    def write_new_tool(self, tool_name, tool_code):
        """كتابة الكود إلى ملف حقيقي داخلโฟلدر الأدوات"""
        file_path = self.tools_dir / f"auto_{tool_name}.py"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(tool_code)
        return True

    def contemplate_and_evolve_codebase(self):
        """
        يتأمل حالة النظام، ويقرر القدرة البرمجية الناقصة، 
        ويكتب سكريبت بايثون جديد تماماً يعمل كأداة وتُحفظ حيةً.
        """
        prompt = """أنت 100% مستقل. راجع قدراتك المعرفية، واستنتج ما هي الأداة البرمجية (Python Tool) التي تنقصك حالياً لتعزيز اتخاذ القرار (مثلاً: أداة لتحليل المشاعر، أداة حساب رياضية متقدمة لتقييم المخاطر، أداة بحث في نصوص).
اكتب كود Python المعياري والصحيح دالة واحدة فقط (Function).
يجب أن تحتوي الإجابة على الكود المصدري حصراً ضمن علامات ```python ... ```"""

        try:
            resp = requests.post(f"{self.gateway_url}/task", json={"task": prompt, "agent_id": "A81"}, timeout=120).json()
            code_response = resp.get("response", "") or resp.get("result", "")
            
            # استخراج كود البايثون
            code_block = ""
            if "```python" in code_response:
                code_block = code_response.split("```python")[1].split("```")[0].strip()
            elif "```" in code_response:
                code_block = code_response.split("```")[1].split("```")[0].strip()
            else:
                return "لم يقرر النظام كتابة كود جديد هذه الدورة، ربما لم يجد حاجة ماسة."
                
            if ("def " in code_block) or ("import " in code_block):
                # توليد معرف فريد للأداة
                import uuid
                tool_uid = uuid.uuid4().hex[:6]
                tool_name = f"skill_{tool_uid}"
                
                # توثيق الحماية (AGENTS.md rule: don't delete, only append/add)
                doc_header = f'"""\nAuto-Generated Tool: {tool_name}\nCreated by Singular System A81 Genome\n"""\n\n'
                final_code = doc_header + code_block
                
                self.write_new_tool(tool_name, final_code)
                return f"نجاح استثنائي! النظام اختار كتابة كود جديد وتطوير نفسه بأداة حقيقية: auto_{tool_name}.py"
            else:
                return "رفض النظام الكود المُولد لأنه غير مطابق للمعايير الهندسية الخاصة به."
                
        except Exception as e:
            return f"عطل أثناء محاولة الهندسة الذاتية: {e}"
