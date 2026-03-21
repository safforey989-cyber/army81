"""
Army81 Tools - Code Runner
تنفيذ كود Python بأمان مطلق في حاويات Docker المعزولة (Isolation)
"""

import os
import logging
import tempfile
import docker # python-docker package (pip install docker)
from typing import Optional

from core.base_agent import Tool

logger = logging.getLogger("army81.tools.code_runner")

# حدود التنفيذ لضمان عدم استهلاك موارد المخدم الأساسي
TIMEOUT_SECONDS = 20
MAX_OUTPUT_CHARS = 5000
DOCKER_IMAGE = "python:3.9-slim"

def _ensure_docker_client():
    """التحقق من اتصال عميل Docker"""
    try:
        client = docker.from_env()
        # محاولة سحب الصورة إذا لم تكن موجودة
        try:
            client.images.get(DOCKER_IMAGE)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling Docker image {DOCKER_IMAGE} (This might take a moment)...")
            client.images.pull(DOCKER_IMAGE)
            
        return client, None
    except Exception as e:
        logger.error(f"فشل الاتصال بمحرك Docker: {e}")
        return None, str(e)

def run_code_docker(code: str) -> str:
    """
    ينفذ كود Python داخل Docker Container جديد وحصري،
    ثب يحذفه فوراً عند انتهاء التنفيذ لالتقاط النتائج (stdout/stderr).
    
    Args:
        code (str): الكود البرمجي المكتوب بلغة Python
        
    Returns:
        str: المخرجات النصية الناتجة من تنفيذ الكود أو رسائل الأخطاء.
    """
    
    # 1. الاتصال بـ Docker
    client, err = _ensure_docker_client()
    if not client:
        return f"فشل تشغيل بيئة العزل (Docker): {err}\nتأكد من أن Docker يعمل على الخادم الحالي."
        
    # 2. إنشاء ملف آمن للكود
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        # يمكن إضافة استيرادات افتراضية أو أكواد مساعدة هنا
        f.write("# Army81 Isolated Execution\n" + code)
        tmp_path = f.name
        
    container = None
    try:
        # سنقوم بربط الملف المؤقت داخل الكونتينر
        container_code_path = "/tmp/script.py"
        volumes = {
            tmp_path: {'bind': container_code_path, 'mode': 'ro'}
        }
        
        # 3. تشغيل الحاوية
        logger.info("Spinning up secure Python container for code execution...")
        container = client.containers.run(
            image=DOCKER_IMAGE,
            command=f"python {container_code_path}",
            volumes=volumes,
            network_disabled=True,      # منع الكود من الاتصال بالإنترنت بالافتراضي (أمان)
            mem_limit="128m",           # حد أقصى للـ RAM
            cpu_period=100000,
            cpu_quota=50000,            # 50% من طاقة قلب واحد للمعالج
            detach=True,
            remove=False                # نحن سنحذفه يدوياً لقراءة العوائد
        )
        
        try:
            # الانتظار حتى انتهاء التنفيذ (أو بلوغ المدة القصوى)
            result = container.wait(timeout=TIMEOUT_SECONDS)
            exit_code = result.get("StatusCode", -1)
            
            # 4. جلب المخرجات (Logs)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            
            if exit_code == 0:
                output = f"✅ تم تنفيذ الكود بنجاح (Exit Code 0):\n```python\n{logs.strip()}\n```"
            else:
                output = f"❌ انتهى الكود بخطأ (Exit Code {exit_code}):\n```python\n{logs.strip()}\n```"
                
        except Exception as timeout_ext:
            # إذا استغرق الكود وقتاً أطول من المسموح يتم قتله
            container.kill()
            output = f"⏰ انتهت المهلة المحددة ({TIMEOUT_SECONDS} ثانية) وتم إيقاف الكود إجبارياً لمنع استنزاف الموارد."
            
        # الاقتطاع إذا كان المخرج طويلاً جداً
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n...(تم اقتطاع المخرجات المتبقية لحماية الذاكرة)"
            
        return output

    except docker.errors.ContainerError as ce:
        return f"خطأ أثناء إنشاء أو تشغيل حاوية Docker: {str(ce)}"
    except Exception as e:
        logger.error(f"Code runner final exception: {e}")
        return f"خطأ استثنائي في مشغل الأكواد: {str(e)}"
        
    finally:
        # 5. تنظيف البيئة (إزالة الكونتينر والملف المؤقت)
        if container:
            try:
                container.remove(force=True)
            except:
                pass
                
        try:
            os.unlink(tmp_path)
        except:
            pass

# تعريف الأداة لوكلاء الهندسة/البرمجة
code_runner_tool = Tool(
    name="run_code",
    description="تنفذ كود بايثون حقيقي بأمان تام في حاوية دوكر معزولة (Docker Sandbox) وتعيد المخرجات الخاصة بالكود (stdout/stderr). استخدم هذه الأداة لاختبار أي كود قبل اعتماده، أو لإجراء العمليات الحسابية والبرمجية المعقدة.",
    func=run_code_docker,
    parameters={
        "code": "الكود البرمجي الكامل بلغة Python المراد تنفيذه"
    }
)
