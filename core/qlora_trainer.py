"""
Army81 QLoRA Trainer — تدريب حقيقي لـ Qwen3:8b على RTX 4050
يبني طبقات LoRA فوق النموذج الأساسي بدون تعديل الأوزان الأصلية
"""
import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("army81.qlora_trainer")

DISTILL_DIR = Path("workspace/brain_nucleus/distillation_data")
ADAPTER_DIR = Path("workspace/brain_nucleus/adapters")
TRAINING_LOG = Path("workspace/brain_nucleus/training_log.json")

# تأكد من وجود المجلدات
ADAPTER_DIR.mkdir(parents=True, exist_ok=True)


class QLoRATrainer:
    """
    مدرّب QLoRA حقيقي — يبني طبقات LoRA فوق Qwen3:8b
    يعمل على RTX 4050 (6GB VRAM)
    """

    def __init__(self):
        self.model_name = "Qwen/Qwen3-8B"
        self.adapter_dir = ADAPTER_DIR
        self.training_log = []
        self.total_trained = 0
        self._load_log()

    def _load_log(self):
        """تحميل سجل التدريب"""
        if TRAINING_LOG.exists():
            try:
                self.training_log = json.loads(TRAINING_LOG.read_text(encoding="utf-8"))
                self.total_trained = len(self.training_log)
            except:
                self.training_log = []

    def _save_log(self, entry: dict):
        """حفظ سجل التدريب"""
        self.training_log.append(entry)
        self.total_trained = len(self.training_log)
        TRAINING_LOG.write_text(
            json.dumps(self.training_log, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def prepare_dataset(self, domain: str = None) -> Dict:
        """تحضير بيانات التدريب من ملفات التقطير"""
        all_examples = []

        for jsonl_file in DISTILL_DIR.glob("*.jsonl"):
            if domain and domain not in jsonl_file.stem:
                continue
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        ex = json.loads(line.strip())
                        if ex.get("output") and len(ex["output"]) > 50:
                            all_examples.append({
                                "instruction": ex.get("instruction", ""),
                                "input": ex.get("input", ""),
                                "output": ex["output"],
                                "domain": ex.get("domain", "general"),
                            })
                    except:
                        continue

        logger.info(f"📊 Prepared {len(all_examples)} training examples"
                    f"{f' for domain {domain}' if domain else ''}")

        return {
            "examples": all_examples,
            "count": len(all_examples),
            "domains": list(set(ex["domain"] for ex in all_examples)),
        }

    def train(self, domain: str = None, epochs: int = 3,
              learning_rate: float = 2e-4, batch_size: int = 1) -> Dict:
        """
        تدريب QLoRA حقيقي على GPU
        RTX 4050 (6GB) → batch_size=1, gradient_accumulation=4
        """
        start_time = time.time()
        result = {
            "success": False,
            "domain": domain or "all",
            "started_at": datetime.now().isoformat(),
        }

        # 1. تحضير البيانات
        dataset_info = self.prepare_dataset(domain)
        if dataset_info["count"] < 3:
            result["error"] = f"Not enough data: {dataset_info['count']} examples (need 3+)"
            logger.warning(f"❌ {result['error']}")
            return result

        try:
            import torch
            if not torch.cuda.is_available():
                # Fallback: CPU training (بطيء لكن يعمل)
                logger.warning("⚠️ No CUDA — training on CPU (slow)")
                device = "cpu"
            else:
                device = "cuda"
                gpu_name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_mem / 1024**3
                logger.info(f"🔥 GPU: {gpu_name} ({vram:.1f}GB VRAM)")

            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                TrainingArguments,
            )
            from peft import LoraConfig, get_peft_model, TaskType
            from trl import SFTTrainer
            from datasets import Dataset

            # 2. تحميل النموذج مع quantization
            logger.info(f"📥 Loading {self.model_name}...")

            # تحميل tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                padding_side="right"
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # تحميل النموذج بـ 4-bit quantization لتوفير VRAM
            if device == "cuda":
                try:
                    from transformers import BitsAndBytesConfig
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                    )
                    model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        quantization_config=bnb_config,
                        device_map="auto",
                        trust_remote_code=True,
                    )
                except Exception as e:
                    logger.warning(f"4-bit failed: {e}, trying float16")
                    model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True,
                    )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                )

            # 3. إعداد LoRA
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=16,                    # rank — 16 مثالي لـ 6GB
                lora_alpha=32,
                lora_dropout=0.05,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                               "gate_proj", "up_proj", "down_proj"],
                bias="none",
            )

            model = get_peft_model(model, lora_config)
            trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in model.parameters())
            logger.info(f"🎯 LoRA: {trainable:,} trainable / {total:,} total "
                       f"({trainable/total*100:.2f}%)")

            # 4. تحضير Dataset
            def format_example(ex):
                return f"### Instruction:\n{ex['instruction']}\n\n### Response:\n{ex['output']}"

            formatted = [{"text": format_example(ex)} for ex in dataset_info["examples"]]
            train_dataset = Dataset.from_list(formatted)

            # 5. إعدادات التدريب (محسّنة لـ RTX 4050 6GB)
            output_dir = str(ADAPTER_DIR / f"qlora_{domain or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M')}")

            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=4,
                learning_rate=learning_rate,
                weight_decay=0.01,
                warmup_steps=5,
                logging_steps=1,
                save_strategy="epoch",
                fp16=(device == "cuda"),
                optim="adamw_torch",
                max_grad_norm=0.3,
                report_to="none",
            )

            # 6. التدريب!
            logger.info(f"🚀 Starting QLoRA training — {dataset_info['count']} examples, "
                       f"{epochs} epochs, lr={learning_rate}")

            trainer = SFTTrainer(
                model=model,
                train_dataset=train_dataset,
                args=training_args,
                processing_class=tokenizer,
                max_seq_length=512,
            )

            train_result = trainer.train()

            # 7. حفظ الـ adapter
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

            elapsed = time.time() - start_time
            loss = train_result.training_loss if hasattr(train_result, 'training_loss') else 0

            result.update({
                "success": True,
                "output_dir": output_dir,
                "examples_trained": dataset_info["count"],
                "domains": dataset_info["domains"],
                "epochs": epochs,
                "final_loss": round(loss, 4),
                "trainable_params": trainable,
                "total_params": total,
                "lora_percent": round(trainable / total * 100, 2),
                "elapsed_seconds": round(elapsed, 1),
                "device": device,
            })

            self._save_log(result)

            logger.info(
                f"✅ QLoRA training complete! "
                f"Loss: {loss:.4f} | "
                f"Examples: {dataset_info['count']} | "
                f"Time: {elapsed:.0f}s | "
                f"Adapter: {output_dir}"
            )

            # تنظيف GPU
            if device == "cuda":
                del model, trainer
                torch.cuda.empty_cache()

            return result

        except ImportError as e:
            missing = str(e).split("'")[-2] if "'" in str(e) else str(e)
            result["error"] = f"Missing library: {missing}. Run: pip install {missing}"
            logger.error(f"❌ {result['error']}")
            return result

        except Exception as e:
            result["error"] = str(e)[:500]
            logger.error(f"❌ Training failed: {e}")
            return result

    def get_status(self) -> Dict:
        """حالة المدرّب"""
        adapters = list(ADAPTER_DIR.glob("qlora_*"))
        dataset = self.prepare_dataset()

        return {
            "model": self.model_name,
            "total_trained": self.total_trained,
            "adapters_saved": len(adapters),
            "adapter_dirs": [a.name for a in adapters],
            "available_examples": dataset["count"],
            "available_domains": dataset["domains"],
            "training_log": self.training_log[-5:],
        }


# Singleton
_trainer = None
def get_trainer() -> QLoRATrainer:
    global _trainer
    if _trainer is None:
        _trainer = QLoRATrainer()
    return _trainer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    trainer = get_trainer()
    print("📊 Status:", json.dumps(trainer.get_status(), ensure_ascii=False, indent=2))

    print("\n🚀 Starting training...")
    result = trainer.train(epochs=1)
    print(f"\n{'✅' if result['success'] else '❌'} Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
