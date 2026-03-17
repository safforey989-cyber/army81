FROM python:3.11-slim

WORKDIR /app

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء مجلد السجلات
RUN mkdir -p logs

EXPOSE 8181

CMD ["python", "gateway/app.py"]
