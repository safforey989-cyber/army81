FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p workspace/reports workspace/compressed workspace/knowledge \
    workspace/experiments workspace/training_data workspace/agent_memories \
    workspace/exponential_evolution workspace/cloned_skills \
    workspace/hyper_evolution workspace/network_intelligence logs

EXPOSE 8181 8501

CMD ["python", "gateway/app.py"]
