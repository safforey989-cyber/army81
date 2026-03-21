"""
Army81 Compound Evolution Engine
المبدأ: كل دورة تبني على نتائج الدورة السابقة فعلاً
"""
import os, json, time, requests, logging
from datetime import datetime
from pathlib import Path

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:8181")
log = logging.getLogger("army81.compound")

# مهام تدريب حقيقية لكل فئة
TRAINING_TASKS = {
    "cat1_science": [
        "حلل أحدث ورقة بحثية في الذكاء الاصطناعي وما تأثيرها على Army81",
        "ما التطورات العلمية التي يجب أن يعرفها النظام هذا الأسبوع؟",
        "قيّم جودة إجابتك السابقة وحسّنها",
    ],
    "cat2_society": [
        "حلل حدثاً جيوسياسياً حالياً وأثره على القرارات الاستراتيجية",
        "ما المؤشرات الاقتصادية الأهم الآن وكيف تؤثر على النظام؟",
    ],
    "cat3_tools": [
        "ابحث عن أداة AI جديدة ظهرت هذا الأسبوع وقيّم فائدتها",
        "ما أهم أخبار التقنية اليوم؟",
    ],
    "cat4_management": [
        "حلل أداء النظام الحالي وقدم 3 توصيات لتحسينه",
        "ما الأولويات الإدارية للنظام الأسبوع القادم؟",
    ],
    "cat5_behavior": [
        "حلل نمط التفاعلات الأخيرة للنظام وما تكشفه نفسياً",
        "ما الأنماط السلوكية التي يجب تحسينها؟",
    ],
    "cat6_leadership": [
        "ما القرار الاستراتيجي الأهم الذي يجب أن يتخذه النظام الآن؟",
        "قيّم الرؤية طويلة المدى للنظام وحسّنها",
    ],
    "cat7_new": [
        "كيف يمكن تحسين آلية التطور الذاتي في النظام؟",
        "ما الفجوات المعرفية الأكبر في النظام الآن؟",
    ],
}

class CompoundEvolution:
    def __init__(self):
        self.state_file = Path("workspace/compound_state.json")
        self.state = self.load_state()
        self.lessons_file = Path("workspace/compound_lessons.json")
        
    def load_state(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "cycle": 0,
            "total_tasks": 0,
            "total_lessons": 0,
            "compound_score": 1.0,
            "best_responses": {},
            "improvement_rate": [],
            "started_at": datetime.now().isoformat(),
        }
    
    def save_state(self):
        self.state_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
    
    def run_task(self, task: str, agent_id: str = None, category: str = None) -> dict:
        """ينفذ مهمة حقيقية ويقيّمها"""
        try:
            payload = {"task": task}
            if agent_id:
                payload["preferred_agent"] = agent_id
            if category:
                payload["preferred_category"] = category
            
            r = requests.post(f"{GATEWAY}/task", json=payload, timeout=60)
            if r.status_code == 200:
                result = r.json()
                response = result.get("result", "")
                quality = self.score_response(task, response)
                return {
                    "success": True,
                    "response": response,
                    "quality": quality,
                    "agent": result.get("agent_id"),
                    "model": result.get("model_used"),
                    "elapsed": result.get("elapsed_seconds", 0),
                }
        except Exception as e:
            log.error(f"Task failed: {e}")
        return {"success": False, "quality": 0}
    
    def score_response(self, task: str, response: str) -> float:
        """يقيّم جودة الرد بمعايير حقيقية"""
        score = 0.0
        if len(response) > 200: score += 0.2
        if len(response) > 500: score += 0.2
        if any(c in response for c in ['1.','2.','3.','•','-']): score += 0.2
        if not response.startswith("ERROR"): score += 0.2
        
        # مكافأة إذا الرد أفضل من السابق لنفس النوع
        task_key = task[:50]
        if task_key in self.state.get("best_responses", {}):
            prev_len = self.state["best_responses"][task_key].get("len", 0)
            if len(response) > prev_len:
                score += 0.2
                # حفظ كأفضل رد
                self.state.setdefault("best_responses", {})[task_key] = {
                    "len": len(response),
                    "quality": score,
                    "cycle": self.state["cycle"],
                }
        else:
            self.state.setdefault("best_responses", {})[task_key] = {
                "len": len(response),
                "quality": score,
                "cycle": self.state["cycle"],
            }
        return round(min(score, 1.0), 2)
    
    def extract_lesson(self, task: str, response: str, quality: float) -> str:
        """يستخلص درساً من المهمة"""
        if quality >= 0.7:
            return f"نجاح: [{task[:60]}] → جودة {quality}"
        else:
            return f"تحسين مطلوب: [{task[:60]}] → جودة {quality} → أضف تفاصيل وأمثلة"
    
    def inject_lessons_to_agents(self, lessons: list):
        """يحقن الدروس في system_prompts الوكلاء"""
        if not lessons:
            return
        
        agents_dir = Path("agents")
        lesson_text = "\n".join(f"- {l}" for l in lessons[-10:])
        
        lesson_count = 0
        for cat_dir in agents_dir.iterdir():
            if not cat_dir.is_dir(): continue
            for agent_file in cat_dir.glob("*.json"):
                try:
                    agent = json.loads(agent_file.read_text(encoding="utf-8"))
                    prompt = agent.get("system_prompt", "")
                    
                    # أضف الدروس إذا لم تكن موجودة
                    if "## دروس مستفادة:" not in prompt:
                        prompt += f"\n\n## دروس مستفادة من الدورات السابقة:\n{lesson_text}"
                    else:
                        # حدّث الدروس الموجودة
                        import re
                        prompt = re.sub(
                            r'## دروس مستفادة.*?(?=\n##|\Z)',
                            f"## دروس مستفادة من الدورات السابقة:\n{lesson_text}\n",
                            prompt,
                            flags=re.DOTALL
                        )
                    
                    agent["system_prompt"] = prompt
                    agent_file.write_text(json.dumps(agent, ensure_ascii=False, indent=2))
                    lesson_count += 1
                except: pass
        
        log.info(f"✅ حقن الدروس في {lesson_count} وكيل")
    
    def calculate_compound_score(self, cycle_results: list) -> float:
        """يحسب معامل المضاعفة المركبة"""
        if not cycle_results:
            return self.state["compound_score"]
        
        avg_quality = sum(r["quality"] for r in cycle_results) / len(cycle_results)
        success_rate = sum(1 for r in cycle_results if r["success"]) / len(cycle_results)
        
        # المعادلة الأساسية: إذا الجودة > 60% تزيد، إذا < 40% تنقص
        if avg_quality > 0.6:
            multiplier = 1 + (avg_quality - 0.5) * 0.4
        elif avg_quality < 0.4:
            multiplier = 0.95  # تراجع طفيف
        else:
            multiplier = 1.0  # ثابت
        
        new_score = self.state["compound_score"] * multiplier
        self.state["improvement_rate"].append({
            "cycle": self.state["cycle"],
            "avg_quality": avg_quality,
            "multiplier": multiplier,
            "compound_score": new_score,
        })
        
        return round(min(new_score, 100.0), 3)
    
    def run_cycle(self):
        self.state["cycle"] += 1
        cycle_num = self.state["cycle"]
        cycle_results = []
        cycle_lessons = []
        
        log.info(f"\n{'='*50}")
        log.info(f"  دورة #{cycle_num} | compound_score: {self.state['compound_score']:.2f}x")
        log.info(f"{'='*50}")
        
        # 1. نفّذ مهام حقيقية لكل فئة
        for category, tasks in TRAINING_TASKS.items():
            # اختر مهمة بناءً على الدورة (تصاعدي)
            task_idx = (cycle_num - 1) % len(tasks)
            task = tasks[task_idx]
            
            log.info(f"  [{category}] {task[:50]}...")
            result = self.run_task(task, category=category)
            result["task"] = task
            result["category"] = category
            
            if result["success"]:
                self.state["total_tasks"] += 1
                lesson = self.extract_lesson(task, result["response"], result["quality"])
                cycle_lessons.append(lesson)
                log.info(f"    ✅ جودة: {result['quality']} | {result.get('elapsed',0):.1f}s")
            else:
                log.info(f"    ❌ فشلت")
            
            cycle_results.append(result)
            time.sleep(3)
        
        # 2. احسب المضاعف المركب الحقيقي
        new_score = self.calculate_compound_score(cycle_results)
        self.state["compound_score"] = new_score
        
        # 3. حقن الدروس في الوكلاء
        self.inject_lessons_to_agents(cycle_lessons)
        self.state["total_lessons"] += len(cycle_lessons)
        
        # 4. احفظ الحالة
        self.save_state()
        
        # 5. ارفع التحديث على GitHub
        avg_q = sum(r["quality"] for r in cycle_results) / max(len(cycle_results), 1)
        import subprocess
        subprocess.run(["git", "add", "agents/", "workspace/compound_state.json"], capture_output=True)
        subprocess.run(["git", "commit", "-m", 
            f"cycle #{cycle_num}: score={new_score:.2f}x quality={avg_q:.2f} lessons={len(cycle_lessons)}"],
            capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], capture_output=True)
        
        log.info(f"\n  ✅ دورة #{cycle_num} اكتملت")
        log.info(f"  compound_score: {new_score:.2f}x")
        log.info(f"  الدروس المضافة: {len(cycle_lessons)}")
        log.info(f"  إجمالي الدروس: {self.state['total_lessons']}")
        
        return {
            "cycle": cycle_num,
            "compound_score": new_score,
            "avg_quality": avg_q,
            "lessons_added": len(cycle_lessons),
            "total_tasks": self.state["total_tasks"],
        }

def run_forever():
    """يشغّل الدورات بشكل متواصل مع فترات راحة ذكية"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.FileHandler("workspace/compound_log.txt", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    engine = CompoundEvolution()
    log.info("🚀 بدأ Compound Evolution Engine")
    log.info(f"   compound_score الحالي: {engine.state['compound_score']:.2f}x")
    log.info(f"   دورات سابقة: {engine.state['cycle']}")
    
    while True:
        try:
            result = engine.run_cycle()
            
            # فترة الراحة تتكيف مع الأداء
            if result["avg_quality"] > 0.7:
                wait = 1800  # 30 دقيقة إذا الأداء ممتاز
            elif result["avg_quality"] > 0.5:
                wait = 3600  # ساعة إذا الأداء جيد
            else:
                wait = 7200  # ساعتان إذا الأداء ضعيف (وقت للتحسين)
            
            log.info(f"  ⏳ الانتظار {wait//60} دقيقة قبل الدورة القادمة...")
            time.sleep(wait)
            
        except KeyboardInterrupt:
            log.info("⏹️ تم الإيقاف")
            break
        except Exception as e:
            log.error(f"❌ خطأ: {e}")
            time.sleep(300)  # 5 دقائق ثم إعادة المحاولة

if __name__ == "__main__":
    run_forever()
