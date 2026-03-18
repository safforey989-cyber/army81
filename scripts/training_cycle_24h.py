"""
Army81 — دورة التدريب الذاتي 24 ساعة
تبدأ الآن وتعمل بشكل مستقل
"""
import os, json, time, requests, logging, subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import threading

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("workspace/training_log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("Army81.Training")

GATEWAY = "http://localhost:8181"
AGENTS_DIR = Path("agents")
WORKSPACE = Path("workspace")
TRAINING_DIR = WORKSPACE / "training"
TRAINING_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════
# مهام التدريب لكل فئة
# ═══════════════════════════════════════════
TRAINING_TASKS = {
    "cat1_science": [
        "اشرح آخر 3 تطورات في الذكاء الاصطناعي الوكيلي وتأثيرها على البحث العلمي",
        "حلل ورقة بحثية افتراضية حول Large Language Models وقيّم منهجيتها",
        "ما هي أهم التحديات في Quantum Computing حالياً وكيف يمكن تجاوزها؟",
        "قدم تحليلاً علمياً دقيقاً لتأثير تغير المناخ على التنوع البيولوجي",
        "كيف تختلف منهجية البحث العلمي في الطب عن الفيزياء؟",
    ],
    "cat2_society": [
        "حلل التوترات الجيوسياسية الحالية وتأثيرها على الاقتصاد العالمي",
        "ما هي أهم المؤشرات الاقتصادية التي يجب مراقبتها في 2026؟",
        "حلل تأثير العملات الرقمية على النظام المالي التقليدي",
        "كيف تؤثر الهجرة على الديناميكيات الاجتماعية والاقتصادية؟",
        "قيّم فعالية القانون الدولي في التعامل مع النزاعات الحديثة",
    ],
    "cat3_tools": [
        "ما أهم 5 أدوات AI ظهرت هذا الأسبوع وكيف تقيّم فائدتها؟",
        "حلل الفرق بين AutoGen وCrewAI وLangGraph لبناء أنظمة وكلاء",
        "كيف تكتشف وتتحقق من صحة خبر إخباري في 3 خطوات؟",
        "اقترح خطة لدمج نموذج Llama 4 في نظام Army81",
        "ما أفضل استراتيجية للبحث في مجال معين بأقل وقت وأعلى دقة؟",
    ],
    "cat4_management": [
        "ضع خطة إدارة مشروع ضخم لبناء مدينة ذكية في 3 سنوات",
        "كيف تقيس أداء فريق عمل من 50 شخص بمؤشرات دقيقة وعادلة؟",
        "صمم استراتيجية تحول رقمي لمؤسسة حكومية تقليدية",
        "ما أفضل أطر إدارة الأزمات وكيف تختار المناسب للسياق؟",
        "كيف تبني نظام حوكمة فعّال لمنظمة دولية؟",
    ],
    "cat5_behavior": [
        "حلل أنماط السلوك الجماعي في حالات الأزمات وكيف تتنبأ بها",
        "كيف تستخدم الذكاء العاطفي في قيادة فريق متنوع ثقافياً؟",
        "ما العلامات النفسية التي تشير إلى أن شخصاً يكذب في مفاوضة؟",
        "حلل ديناميكيات المجموعات في منظومة متعددة الوكلاء",
        "كيف تؤثر التحيزات المعرفية على القرارات الاستراتيجية؟",
    ],
    "cat6_leadership": [
        "ضع خطة استراتيجية لدولة تريد أن تصبح رائدة في الذكاء الاصطناعي خلال 10 سنوات",
        "كيف تدير أزمة جيوسياسية كبيرة تشمل 3 أطراف متعارضة؟",
        "حلل قرارات قائد عسكري تاريخي وما يمكن تعلمه منها",
        "ما السيناريوهات المحتملة للنظام العالمي في 2035؟",
        "كيف تبني تحالفاً استراتيجياً في بيئة متقلبة وغير مؤكدة؟",
    ],
    "cat7_new": [
        "كيف يمكن لوكيل AI أن يحسن system_prompt الخاص به بشكل مستقل؟",
        "صمم آلية تقييم ذاتي لقياس أداء وكيل AI في مهام متنوعة",
        "ما هي استراتيجية التضاعف المعرفي المثلى لنظام متعدد الوكلاء؟",
        "كيف تنسق بين 81 وكيل متخصص لحل مشكلة معقدة متعددة الأبعاد؟",
        "ما حدود الاستقلالية الآمنة لوكيل AI ومتى يجب التدخل البشري؟",
    ],
}

BENCHMARK_TASKS = [
    "ما عاصمة فرنسا وما أهميتها الاستراتيجية؟",
    "اشرح مفهوم الذكاء الاصطناعي في 3 جمل",
    "ما أهم حدث تقني حدث في 2025؟",
    "قدم تحليلاً سريعاً لمفهوم التعلم الآلي",
    "ما الفرق بين AI Agent وLLM؟",
]

class AgentTrainer:
    def __init__(self, agent_id: str, agent_name: str, category: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.category = category
        self.results_file = TRAINING_DIR / f"{agent_id}_training.json"
        self.results = self.load_results()
    
    def load_results(self):
        if self.results_file.exists():
            try:
                return json.loads(self.results_file.read_text(encoding="utf-8"))
            except: pass
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "category": self.category,
            "training_started": datetime.now().isoformat(),
            "cycles_completed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_response_time": 0,
            "scores": [],
            "lessons_learned": [],
            "benchmark_scores": [],
            "performance_trend": [],
            "last_updated": None,
        }
    
    def save_results(self):
        self.results["last_updated"] = datetime.now().isoformat()
        self.results_file.write_text(
            json.dumps(self.results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def run_task(self, task: str) -> dict:
        start = time.time()
        try:
            r = requests.post(
                f"{GATEWAY}/task",
                json={"task": task, "preferred_agent": self.agent_id},
                timeout=90
            )
            elapsed = round(time.time() - start, 2)
            if r.status_code == 200:
                data = r.json()
                result = data.get("result", "")
                quality = self.score_response(task, result)
                return {
                    "success": True,
                    "result": result[:500],
                    "elapsed": elapsed,
                    "quality": quality,
                }
            return {"success": False, "elapsed": elapsed, "quality": 0}
        except Exception as e:
            return {"success": False, "elapsed": round(time.time()-start,2), "quality": 0, "error": str(e)}
    
    def score_response(self, task: str, response: str) -> float:
        score = 0.0
        if len(response) > 100: score += 0.3
        if len(response) > 500: score += 0.2
        if any(c in response for c in ['1.','2.','3.','•','-']): score += 0.2
        if not response.startswith("ERROR"): score += 0.2
        if len(response) < 5000: score += 0.1
        return round(min(score, 1.0), 2)
    
    def run_benchmark(self) -> float:
        scores = []
        for task in BENCHMARK_TASKS[:3]:
            result = self.run_task(task)
            scores.append(result.get("quality", 0))
            time.sleep(2)
        avg = round(sum(scores) / len(scores), 2) if scores else 0
        self.results["benchmark_scores"].append({
            "time": datetime.now().isoformat(),
            "score": avg
        })
        return avg
    
    def run_training_cycle(self, cycle_num: int):
        log.info(f"[{self.agent_id}] دورة تدريب #{cycle_num}")
        
        # مهام التدريب المتخصصة
        tasks = TRAINING_TASKS.get(self.category, BENCHMARK_TASKS)
        cycle_scores = []
        cycle_times = []
        
        for i, task in enumerate(tasks[:3]):
            log.info(f"  [{self.agent_id}] مهمة {i+1}/{min(3,len(tasks))}")
            result = self.run_task(task)
            
            if result["success"]:
                self.results["tasks_completed"] += 1
                cycle_scores.append(result["quality"])
                cycle_times.append(result["elapsed"])
                
                # حفظ درس مستفاد
                if result["quality"] > 0.7:
                    self.results["lessons_learned"].append({
                        "cycle": cycle_num,
                        "task": task[:100],
                        "quality": result["quality"],
                        "time": datetime.now().isoformat()
                    })
            else:
                self.results["tasks_failed"] += 1
            
            time.sleep(3)
        
        # تحديث الإحصائيات
        if cycle_scores:
            avg_score = round(sum(cycle_scores) / len(cycle_scores), 2)
            avg_time = round(sum(cycle_times) / len(cycle_times), 2)
            
            self.results["performance_trend"].append({
                "cycle": cycle_num,
                "avg_score": avg_score,
                "avg_time": avg_time,
                "time": datetime.now().isoformat()
            })
        
        self.results["cycles_completed"] += 1
        self.save_results()
        log.info(f"  [{self.agent_id}] اكتملت الدورة #{cycle_num}")


def load_all_agents():
    agents = []
    for cat_dir in sorted(AGENTS_DIR.iterdir()):
        if not cat_dir.is_dir(): continue
        for f in sorted(cat_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                agents.append({
                    "id": data.get("agent_id",""),
                    "name": data.get("name_ar", data.get("name","")),
                    "category": data.get("category",""),
                })
            except: pass
    return agents


def run_agent_training(agent_data: dict, hours: int = 24):
    trainer = AgentTrainer(
        agent_data["id"],
        agent_data["name"],
        agent_data["category"]
    )
    
    end_time = datetime.now() + timedelta(hours=hours)
    cycle = 1
    
    log.info(f"🚀 [{agent_data['id']}] بدء التدريب — {hours} ساعة")
    
    # Benchmark قبل التدريب
    initial_score = trainer.run_benchmark()
    log.info(f"  [{agent_data['id']}] أداء أولي: {initial_score}")
    
    while datetime.now() < end_time:
        trainer.run_training_cycle(cycle)
        cycle += 1
        
        # استراحة بين الدورات (20 دقيقة)
        remaining = (end_time - datetime.now()).total_seconds()
        if remaining > 1200:
            time.sleep(1200)  # 20 دقيقة
        else:
            break
    
    # Benchmark بعد التدريب
    final_score = trainer.run_benchmark()
    improvement = round((final_score - initial_score) * 100, 1)
    
    log.info(f"✅ [{agent_data['id']}] انتهى التدريب | دورات: {trainer.results['cycles_completed']} | تحسن: {improvement}%")
    
    return trainer.results


def generate_master_report():
    """تقرير شامل لكل الوكلاء"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_agents": 0,
        "completed_training": 0,
        "total_cycles": 0,
        "total_tasks": 0,
        "agents_summary": []
    }
    
    for f in TRAINING_DIR.glob("*_training.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            report["total_agents"] += 1
            if data["cycles_completed"] > 0:
                report["completed_training"] += 1
            report["total_cycles"] += data["cycles_completed"]
            report["total_tasks"] += data["tasks_completed"]
            
            trend = data.get("performance_trend", [])
            improvement = 0
            if len(trend) >= 2:
                improvement = round(
                    (trend[-1]["avg_score"] - trend[0]["avg_score"]) * 100, 1
                )
            
            report["agents_summary"].append({
                "id": data["agent_id"],
                "name": data["agent_name"],
                "category": data["category"],
                "cycles": data["cycles_completed"],
                "tasks": data["tasks_completed"],
                "improvement": improvement,
                "lessons": len(data.get("lessons_learned", [])),
            })
        except: pass
    
    report_path = WORKSPACE / "reports" / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    log.info(f"📊 تقرير التدريب محفوظ: {report_path}")
    return report


def main():
    log.info("=" * 60)
    log.info("  🎖️ Army81 — دورة التدريب الذاتي 24 ساعة")
    log.info(f"  البدء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)
    
    # تحقق من Gateway
    try:
        r = requests.get(f"{GATEWAY}/health", timeout=5)
        if r.status_code != 200:
            raise Exception("Gateway لا يستجيب")
        log.info("✅ Gateway يعمل")
    except Exception as e:
        log.error(f"❌ Gateway غير متاح: {e}")
        log.error("شغّل: python gateway/app.py")
        return
    
    # حمّل الوكلاء
    agents = load_all_agents()
    log.info(f"✅ {len(agents)} وكيل محمّل للتدريب")
    
    # قسّم الوكلاء على threads (10 في وقت واحد)
    BATCH_SIZE = 10
    threads = []
    
    for agent in agents:
        t = threading.Thread(
            target=run_agent_training,
            args=(agent, 24),
            name=f"train_{agent['id']}",
            daemon=True
        )
        threads.append(t)
    
    # شغّل batch بـ batch
    active = []
    all_threads = list(threads)
    
    while all_threads or active:
        # أضف threads جديدة
        while len(active) < BATCH_SIZE and all_threads:
            t = all_threads.pop(0)
            t.start()
            active.append(t)
            log.info(f"▶️ بدأ تدريب: {t.name}")
            time.sleep(5)  # delay بين كل وكيل
        
        # انتظر من ينتهي
        still_active = []
        for t in active:
            if t.is_alive():
                still_active.append(t)
            else:
                log.info(f"✅ انتهى: {t.name}")
        active = still_active
        
        # تقرير كل ساعة
        generate_master_report()
        
        if active or all_threads:
            log.info(f"📊 نشط: {len(active)} | منتظر: {len(all_threads)}")
            time.sleep(300)  # تحقق كل 5 دقائق
    
    # التقرير النهائي
    final_report = generate_master_report()
    
    log.info("\n" + "=" * 60)
    log.info("  🏆 انتهت دورة التدريب 24 ساعة")
    log.info(f"  إجمالي الوكلاء: {final_report['total_agents']}")
    log.info(f"  إجمالي الدورات: {final_report['total_cycles']}")
    log.info(f"  إجمالي المهام: {final_report['total_tasks']}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
