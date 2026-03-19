"""
Army81 Brain Nucleus — النواة المركزية الحية
═══════════════════════════════════════════════

Qwen3-8B هو الدماغ المركزي. كل الوكلاء الـ 191 متصلون به.
كل دورة تطور تقطّر المعرفة من النماذج الكبيرة (Claude, GPT, DeepSeek)
وتبني طبقات جديدة فوق Qwen3-8B عبر LoRA adapters.

الهدف: بعد 3 أشهر → نموذج Army81-Core مستقل بمعرفة فائقة.

Architecture:
┌─────────────────────────────────────┐
│         Army81 Brain Nucleus         │
│                                      │
│  ┌──────────┐  ┌──────────────────┐ │
│  │ Qwen3-8B │←→│ LoRA Adapters     │ │
│  │ (Ollama)  │  │ medical_v1.bin   │ │
│  │ 4GB base  │  │ coding_v1.bin    │ │
│  └──────────┘  │ strategy_v1.bin   │ │
│       ↕         │ science_v1.bin    │ │
│  ┌──────────┐  │ arabic_v1.bin     │ │
│  │ Distill  │  └──────────────────┘ │
│  │ Pipeline │                        │
│  └──────────┘                        │
│       ↕                              │
│  ┌──────────────────────────────┐   │
│  │ Knowledge Layers (Chroma)    │   │
│  │ 10,146 docs + growing daily  │   │
│  └──────────────────────────────┘   │
│       ↕                              │
│  ┌──────────────────────────────┐   │
│  │ 191 Agents Neural Network     │   │
│  │ 17 categories, 97+ connections│   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
"""
import os
import json
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.brain")

# تحميل .env دائماً
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

WORKSPACE = Path(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workspace")
))
BRAIN_DIR = WORKSPACE / "brain_nucleus"
ADAPTERS_DIR = BRAIN_DIR / "lora_adapters"
DISTILL_DIR = BRAIN_DIR / "distillation_data"
TRAINING_LOG = BRAIN_DIR / "training_log.json"
BRAIN_STATE = BRAIN_DIR / "brain_state.json"

# Ensure directories exist
for d in [BRAIN_DIR, ADAPTERS_DIR, DISTILL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════
# Ollama Connection — التواصل مع Qwen3-8B
# ═══════════════════════════════════════════════

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
NUCLEUS_MODEL = "qwen3:8b"  # النموذج الأساسي


class OllamaClient:
    """اتصال مباشر بـ Qwen3-8B عبر Ollama"""

    def __init__(self, model: str = NUCLEUS_MODEL):
        self.model = model
        self.base_url = OLLAMA_URL

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7,
                 max_tokens: int = 2048) -> Dict:
        """استدعاء Qwen3-8B مباشرة"""
        import requests
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            }
            r = requests.post(f"{self.base_url}/api/generate",
                            json=payload, timeout=120)
            if r.ok:
                data = r.json()
                return {
                    "content": data.get("response", ""),
                    "model": self.model,
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration": data.get("eval_duration", 0),
                    "success": True,
                }
            else:
                return {"content": f"ERROR: Ollama {r.status_code}", "success": False}
        except Exception as e:
            return {"content": f"ERROR: {e}", "success": False}

    def chat(self, messages: List[Dict], temperature: float = 0.7) -> Dict:
        """Chat format"""
        import requests
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {"temperature": temperature},
                "stream": False,
            }
            r = requests.post(f"{self.base_url}/api/chat",
                            json=payload, timeout=120)
            if r.ok:
                data = r.json()
                msg = data.get("message", {})
                return {
                    "content": msg.get("content", ""),
                    "model": self.model,
                    "success": True,
                }
            return {"content": f"ERROR: {r.status_code}", "success": False}
        except Exception as e:
            return {"content": f"ERROR: {e}", "success": False}

    def is_available(self) -> bool:
        """هل Ollama و Qwen3 متاحين؟"""
        import requests
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                return any(self.model in m for m in models)
        except:
            pass
        return False


# ═══════════════════════════════════════════════
# Distillation Pipeline — خط أنابيب التقطير
# ═══════════════════════════════════════════════

class DistillationPipeline:
    """
    التقطير المعرفي: النماذج الكبيرة تعلّم Qwen3-8B

    الآلية:
    1. مهمة معقدة → ترسل لـ Claude/GPT/DeepSeek (المعلم)
    2. المعلم يجيب مع Chain-of-Thought مفصّل
    3. نحفظ (المهمة + التفكير + الإجابة) كبيانات تدريب
    4. بعد تجميع 1000+ مثال → نعمل QLoRA fine-tune
    5. Qwen3-8B يتعلم أنماط تفكير المعلم

    بعد 3 أشهر: Qwen3-8B يصبح أذكى من كل معلم بمفرده
    لأنه يجمع أفضل ما في كل النماذج.
    """

    # أزواج المعلم-الطالب — محلي أولاً، cloud كـ fallback
    TEACHER_MODELS_LOCAL = {
        "reasoning": "qwen2.5:14b",       # أكبر نموذج محلي
        "coding": "qwen2.5-coder:14b",    # متخصص بالكود
        "medical": "qwen2.5:14b",         # 14B للطب
        "strategy": "qwen2.5:14b",        # استراتيجية
        "arabic": "qwen3:8b",             # Qwen3 للعربية
        "science": "qwen2.5:14b",         # علوم
        "creative": "qwen2.5:14b",        # إبداع
        "legal": "qwen2.5:14b",           # قانون
        "financial": "qwen2.5:14b",       # مالية
        "security": "deepseek-coder:6.7b",# أمن
    }
    TEACHER_MODELS = {
        "reasoning": "deepseek-r1",
        "coding": "claude-smart",
        "medical": "gemini-pro",
        "strategy": "gpt4o",
        "arabic": "qwen-72b",
        "science": "deepseek-r1",
        "creative": "claude-opus",
        "legal": "claude-smart",
        "financial": "deepseek-chat",
        "security": "gemini-pro",
    }

    def __init__(self):
        self.distill_count = 0
        self.domains_trained = set()
        self._load_state()

    def _load_state(self):
        """تحميل حالة التقطير"""
        state_file = BRAIN_DIR / "distill_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                self.distill_count = state.get("distill_count", 0)
                self.domains_trained = set(state.get("domains_trained", []))
            except:
                pass

    def _save_state(self):
        """حفظ حالة التقطير"""
        state = {
            "distill_count": self.distill_count,
            "domains_trained": list(self.domains_trained),
            "last_updated": datetime.now().isoformat(),
        }
        (BRAIN_DIR / "distill_state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def distill_from_teacher(self, domain: str, task: str,
                             run_agent_fn=None) -> Dict:
        """
        تقطير مهمة واحدة:
        1. أرسل للمعلم الكبير
        2. احصل على Chain-of-Thought
        3. احفظ كبيانات تدريب
        4. اختبر Qwen3 على نفس المهمة
        5. احسب الفجوة
        """
        # جرّب المعلم المحلي أولاً، ثم cloud
        local_model = self.TEACHER_MODELS_LOCAL.get(domain, "qwen2.5:14b")
        cloud_model = self.TEACHER_MODELS.get(domain, "gemini-pro")
        result = {"domain": domain, "task": task[:100], "success": False}

        # 1. استدعاء المعلم — محلي أولاً
        teacher_text = ""
        teacher_source = ""

        # محاولة 1: Ollama المحلي (مجاني وسريع)
        try:
            local_teacher = OllamaClient(local_model)
            if local_teacher.is_available():
                teacher_prompt_local = f"""أجب بالتفصيل مع خطوات التفكير:

المهمة: {task}

أعطني:
1. خطوات التفكير
2. الإجابة النهائية
3. القواعد التي اعتمدت عليها"""

                t_resp = local_teacher.generate(
                    prompt=teacher_prompt_local,
                    system=f"أنت خبير في {domain}. فكّر بعمق وأجب بالعربية.",
                    temperature=0.4, max_tokens=2048)

                if t_resp.get("success") and len(t_resp.get("content", "")) > 100:
                    teacher_text = t_resp["content"]
                    teacher_source = f"ollama/{local_model}"
                    result["teacher_model"] = teacher_source
                    result["teacher_response"] = teacher_text[:500]
                    logger.info(f"🎓 Local teacher [{local_model}] answered ({len(teacher_text)} chars)")
        except Exception as e:
            logger.debug(f"Local teacher failed: {e}")

        # محاولة 2: Cloud (إذا المحلي فشل)
        if not teacher_text:
            try:
                from core.llm_client import LLMClient
                teacher = LLMClient(cloud_model)
                teacher_response = teacher.chat([
                    {"role": "system", "content": f"أنت خبير في {domain}. أجب بالعربية."},
                    {"role": "user", "content": f"أجب بالتفصيل مع خطوات التفكير:\n\n{task}"}
                ])
                teacher_text = teacher_response.get("content", "")
                if teacher_text and not teacher_text.startswith("ERROR"):
                    teacher_source = f"cloud/{cloud_model}"
                    result["teacher_model"] = teacher_source
                    result["teacher_response"] = teacher_text[:500]
            except Exception as e:
                logger.debug(f"Cloud teacher failed: {e}")

        # إذا كل المعلمين فشلوا
        if not teacher_text or len(teacher_text) < 50:
            result["error"] = "All teachers failed (local + cloud)"
            return result

        # 2. اختبار Qwen3 على نفس المهمة
        ollama = OllamaClient()
        if ollama.is_available():
            student_response = ollama.generate(
                prompt=task,
                system=f"أنت خبير في {domain}. أجب بالعربية بدقة.",
                temperature=0.3
            )
            student_text = student_response.get("content", "")
            result["student_response"] = student_text[:500]
            result["student_available"] = True

            # 3. حساب الفجوة
            teacher_len = len(teacher_text)
            student_len = len(student_text)
            gap = max(0, 1 - (student_len / max(teacher_len, 1)))
            result["quality_gap"] = round(gap, 3)
        else:
            result["student_available"] = False
            result["quality_gap"] = 1.0  # فجوة كاملة

        # 4. حفظ كبيانات تدريب
        training_example = {
            "instruction": task,
            "input": "",
            "output": teacher_text,
            "domain": domain,
            "teacher": teacher_model,
            "quality_gap": result.get("quality_gap", 1.0),
            "timestamp": datetime.now().isoformat(),
        }

        # حفظ في ملف JSONL (صيغة التدريب القياسية)
        domain_file = DISTILL_DIR / f"{domain}_training.jsonl"
        with open(domain_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(training_example, ensure_ascii=False) + "\n")

        self.distill_count += 1
        self.domains_trained.add(domain)
        self._save_state()

        result["success"] = True
        result["total_distilled"] = self.distill_count
        result["training_file"] = str(domain_file)

        logger.info(
            f"🎓 Distilled [{domain}] from {teacher_model} → "
            f"gap={result.get('quality_gap', '?')} | total={self.distill_count}"
        )
        return result

    def get_training_stats(self) -> Dict:
        """إحصائيات التدريب"""
        stats = {
            "total_distilled": self.distill_count,
            "domains_trained": list(self.domains_trained),
            "training_files": {},
        }
        for f in DISTILL_DIR.glob("*_training.jsonl"):
            domain = f.stem.replace("_training", "")
            lines = sum(1 for _ in open(f, encoding="utf-8"))
            stats["training_files"][domain] = lines
        return stats

    def is_ready_for_training(self, min_examples: int = 100) -> bool:
        """هل تجمعت بيانات كافية للتدريب؟"""
        total = sum(
            sum(1 for _ in open(f, encoding="utf-8"))
            for f in DISTILL_DIR.glob("*_training.jsonl")
        )
        return total >= min_examples


# ═══════════════════════════════════════════════
# QLoRA Training Manager — إدارة التدريب
# ═══════════════════════════════════════════════

class QLoRATrainingManager:
    """
    إدارة تدريب QLoRA على Qwen3-8B

    بدون GPU: نصدّر البيانات بصيغة جاهزة ونستخدم:
    - Unsloth (مجاني على Colab)
    - أو cloud GPU (RunPod, Lambda)
    - أو Ollama create مع Modelfile

    مع GPU: تدريب مباشر بـ PEFT + BitsAndBytes
    """

    def __init__(self):
        self.training_runs = []
        self._load_history()

    def _load_history(self):
        if TRAINING_LOG.exists():
            try:
                self.training_runs = json.loads(
                    TRAINING_LOG.read_text(encoding="utf-8"))
            except:
                self.training_runs = []

    def _save_history(self):
        TRAINING_LOG.write_text(
            json.dumps(self.training_runs, ensure_ascii=False, indent=2),
            encoding="utf-8")

    def prepare_training_data(self, domain: str = None) -> Dict:
        """تحضير بيانات التدريب بصيغة Alpaca/ChatML"""
        all_examples = []

        files = list(DISTILL_DIR.glob("*_training.jsonl"))
        if domain:
            files = [f for f in files if domain in f.stem]

        for f in files:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        ex = json.loads(line.strip())
                        # Alpaca format
                        all_examples.append({
                            "instruction": ex["instruction"],
                            "input": ex.get("input", ""),
                            "output": ex["output"],
                        })
                    except:
                        continue

        # حفظ بصيغة JSON (للتدريب)
        output_file = BRAIN_DIR / f"training_dataset{'_' + domain if domain else ''}.json"
        output_file.write_text(
            json.dumps(all_examples, ensure_ascii=False, indent=2),
            encoding="utf-8")

        # حفظ بصيغة ChatML (لـ Unsloth)
        chatml_examples = []
        for ex in all_examples:
            chatml_examples.append({
                "messages": [
                    {"role": "system", "content": "أنت Army81-Core، نظام ذكاء اصطناعي متطور."},
                    {"role": "user", "content": ex["instruction"]},
                    {"role": "assistant", "content": ex["output"]},
                ]
            })
        chatml_file = BRAIN_DIR / f"training_chatml{'_' + domain if domain else ''}.json"
        chatml_file.write_text(
            json.dumps(chatml_examples, ensure_ascii=False, indent=2),
            encoding="utf-8")

        return {
            "total_examples": len(all_examples),
            "alpaca_file": str(output_file),
            "chatml_file": str(chatml_file),
            "domains": list(set(
                json.loads(line).get("domain", "unknown")
                for f in DISTILL_DIR.glob("*_training.jsonl")
                for line in open(f, encoding="utf-8")
            )),
        }

    def create_ollama_modelfile(self, adapter_path: str = None) -> str:
        """إنشاء Modelfile لـ Ollama مع LoRA adapter"""
        modelfile_content = f"""FROM qwen3:8b

# Army81 Brain Nucleus — Custom trained model
PARAMETER temperature 0.7
PARAMETER num_predict 4096
PARAMETER top_p 0.9

SYSTEM \"\"\"
أنت Army81-Core — الدماغ المركزي لنظام Army81.
أنت نظام ذكاء اصطناعي متطور يضم 191 وكيل متخصص.
لديك معرفة عميقة في: الطب، البرمجة، الاستراتيجية، العلوم، القانون، المالية، الأمن.
تفكّر بعمق قبل الإجابة وتستخدم Chain-of-Thought.
تجيب بالعربية بدقة وثقة.
\"\"\"
"""
        if adapter_path:
            modelfile_content += f"\nADAPTER {adapter_path}\n"

        modelfile_path = BRAIN_DIR / "Modelfile"
        modelfile_path.write_text(modelfile_content, encoding="utf-8")

        logger.info(f"📝 Modelfile created: {modelfile_path}")
        return str(modelfile_path)

    def register_training_run(self, domain: str, examples: int,
                             adapter_name: str, notes: str = "") -> Dict:
        """تسجيل جلسة تدريب"""
        run = {
            "id": len(self.training_runs) + 1,
            "domain": domain,
            "examples": examples,
            "adapter": adapter_name,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
            "base_model": NUCLEUS_MODEL,
        }
        self.training_runs.append(run)
        self._save_history()
        return run


# ═══════════════════════════════════════════════
# Brain Nucleus — الكيان المركزي
# ═══════════════════════════════════════════════

class BrainNucleus:
    """
    الدماغ المركزي لـ Army81 — يربط كل شيء:
    - Qwen3-8B كنموذج أساسي
    - خط أنابيب التقطير
    - إدارة التدريب QLoRA
    - الذاكرة الجماعية (Chroma)
    - الشبكة العصبية (191 وكيل)
    """

    def __init__(self):
        self.ollama = OllamaClient()
        self.distillation = DistillationPipeline()
        self.training = QLoRATrainingManager()
        self.state = self._load_state()
        logger.info(f"🧠 Brain Nucleus initialized | Model: {NUCLEUS_MODEL}")

    def _load_state(self) -> Dict:
        if BRAIN_STATE.exists():
            try:
                return json.loads(BRAIN_STATE.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "version": 1,
            "base_model": NUCLEUS_MODEL,
            "adapters": [],
            "total_distillations": 0,
            "total_training_runs": 0,
            "knowledge_layers": 0,
            "created_at": datetime.now().isoformat(),
            "consciousness_level": 0.0,  # 0-1, يزداد مع التطور
        }

    def _save_state(self):
        BRAIN_STATE.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2),
            encoding="utf-8")

    def think(self, query: str, context: str = "", use_nucleus: bool = True) -> Dict:
        """
        التفكير المركزي — يستخدم Qwen3-8B أو fallback
        """
        if use_nucleus and self.ollama.is_available():
            # استخدم النواة المحلية
            system = f"""أنت Army81-Core — الدماغ المركزي لنظام 191 وكيل.
فكّر بعمق قبل الإجابة.

{context[:2000] if context else ''}"""

            result = self.ollama.chat([
                {"role": "system", "content": system},
                {"role": "user", "content": query}
            ])
            result["source"] = "nucleus_local"
            return result
        else:
            # fallback لـ OpenRouter
            from core.llm_client import LLMClient
            client = LLMClient("gemini-flash")
            result = client.chat([
                {"role": "system", "content": "أنت Army81-Core."},
                {"role": "user", "content": query}
            ])
            result["source"] = "fallback_cloud"
            return result

    def distill_cycle(self, tasks_per_domain: int = 3) -> Dict:
        """
        دورة تقطير كاملة — تشمل كل المجالات
        هذه هي العملية الأهم في بناء الدماغ
        """
        logger.info(f"🎓 Starting distillation cycle — {tasks_per_domain} tasks/domain")

        # مهام تقطير لكل مجال
        DISTILL_TASKS = {
            "reasoning": [
                "حلل هذه المسألة المنطقية: إذا كان كل A هو B، وبعض B هو C، فهل كل A هو C؟ اشرح بالتفصيل.",
                "ما هي مغالطة الرجل القش؟ أعط 3 أمثلة واقعية.",
                "حلل هذا القياس: السمك يسبح، الحوت يسبح، إذاً الحوت سمكة. ما الخطأ؟",
            ],
            "coding": [
                "اكتب خوارزمية Dijkstra بالبايثون مع شرح كل خطوة وتعقيد الزمن والمكان.",
                "صمم نظام Rate Limiter باستخدام Token Bucket بالبايثون.",
                "اكتب decorator في Python يعمل caching مع TTL قابل للتعديل.",
            ],
            "medical": [
                "اشرح آلية عمل مثبطات SGLT2 في علاج السكري من النوع الثاني.",
                "ما هي المراحل الأربع لتطور سرطان القولون وعلاج كل مرحلة؟",
                "اشرح الفرق بين المناعة الخلطية والمناعة الخلوية بالتفصيل.",
            ],
            "strategy": [
                "حلل استراتيجية تسلا في السيارات الكهربائية باستخدام إطار Porter's Five Forces.",
                "صمم خطة دخول سوق جديد لشركة SaaS ناشئة في الشرق الأوسط.",
                "حلل مخاطر الاستثمار في الذكاء الاصطناعي التوليدي باستخدام SWOT.",
            ],
            "science": [
                "اشرح مبدأ عدم اليقين لهايزنبرغ وتطبيقاته في الحوسبة الكمية.",
                "كيف يعمل التشابك الكمي؟ وما تطبيقاته في التشفير والاتصالات؟",
                "اشرح نظرية الأوتار ولماذا تحتاج 11 بُعداً.",
            ],
            "arabic": [
                "حلل البنية البلاغية في سورة الرحمن: التكرار، الإيقاع، والصور.",
                "ما الفرق بين المجاز المرسل والاستعارة المكنية؟ أعط 5 أمثلة لكل.",
                "اشرح نظام الإعراب في اللغة العربية وعلاقته بالمعنى.",
            ],
            "financial": [
                "حلل مخاطر DeFi مقارنة بالنظام المالي التقليدي.",
                "اشرح نموذج Black-Scholes لتسعير الخيارات مع مثال عملي.",
                "كيف يعمل التداول الخوارزمي وما هي أشهر الاستراتيجيات؟",
            ],
            "security": [
                "اشرح هجوم SQL Injection المتقدم (Second-order) وكيفية الحماية.",
                "حلل ثغرة Log4Shell وتأثيرها على الأنظمة.",
                "صمم نظام Zero-Trust Architecture لشركة متوسطة.",
            ],
        }

        results = {"domains": {}, "total_distilled": 0, "errors": 0}

        for domain, tasks in DISTILL_TASKS.items():
            domain_results = []
            for task in tasks[:tasks_per_domain]:
                try:
                    r = self.distillation.distill_from_teacher(domain, task)
                    domain_results.append(r)
                    if r.get("success"):
                        results["total_distilled"] += 1
                    else:
                        results["errors"] += 1
                except Exception as e:
                    logger.warning(f"Distill error [{domain}]: {e}")
                    results["errors"] += 1

                time.sleep(2)  # rate limiting

            results["domains"][domain] = {
                "tasks": len(domain_results),
                "success": sum(1 for r in domain_results if r.get("success")),
                "avg_gap": sum(r.get("quality_gap", 1) for r in domain_results) / max(len(domain_results), 1),
            }

        # تحديث حالة الدماغ
        self.state["total_distillations"] += results["total_distilled"]
        self.state["knowledge_layers"] += 1
        self.state["consciousness_level"] = min(
            1.0, self.state["consciousness_level"] + 0.01 * results["total_distilled"])
        self._save_state()

        logger.info(
            f"🧠 Distillation cycle complete: {results['total_distilled']} distilled, "
            f"{results['errors']} errors, consciousness={self.state['consciousness_level']:.2f}")

        return results

    def prepare_for_training(self) -> Dict:
        """تحضير كل شيء للتدريب"""
        # 1. تجميع بيانات التدريب
        data = self.training.prepare_training_data()

        # 2. إنشاء Modelfile
        modelfile = self.training.create_ollama_modelfile()

        return {
            "training_data": data,
            "modelfile": modelfile,
            "ready": data["total_examples"] >= 50,
            "examples_needed": max(0, 50 - data["total_examples"]),
            "brain_state": self.state,
        }

    def status(self) -> Dict:
        """حالة الدماغ الشاملة"""
        ollama_ok = self.ollama.is_available()
        distill_stats = self.distillation.get_training_stats()

        return {
            "nucleus_model": NUCLEUS_MODEL,
            "ollama_available": ollama_ok,
            "consciousness_level": self.state.get("consciousness_level", 0),
            "version": self.state.get("version", 1),
            "knowledge_layers": self.state.get("knowledge_layers", 0),
            "total_distillations": self.state.get("total_distillations", 0),
            "distillation": distill_stats,
            "adapters": self.state.get("adapters", []),
            "training_runs": len(self.training.training_runs),
            "created_at": self.state.get("created_at", ""),
        }


# ═══════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════

_brain_instance = None

def get_brain() -> BrainNucleus:
    """Singleton للدماغ"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = BrainNucleus()
    return _brain_instance
