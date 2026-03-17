FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs memory/episodes skills updates

EXPOSE 8181

CMD ["python", "gateway.py"]
