# Army81 Architecture Guide

## System Overview
Army81 is a self-evolving multi-agent system with 81 specialized AI agents connected as a neural network.

## Core Components

### 1. Gateway (`gateway/app.py`)
- FastAPI server on port 8181
- Routes tasks to specialized agents
- 30+ REST endpoints

### 2. Agents (`agents/`)
- 81 agents across 7 categories
- Each has: system_prompt, model, tools, category
- Connected via neural network graph

### 3. Neural Network (`core/neural_network.py`)
- A00 (hub) connects to 7 category leaders
- 12 cross-links between categories
- Hebbian learning strengthens used connections

### 4. Memory System
| Level | Type | Storage | Purpose |
|-------|------|---------|---------|
| L1 | Working | RAM | Current conversation |
| L2 | Episodic | SQLite | Task history + ratings |
| L3 | Semantic | Chroma | Vector search |
| L4 | Compressed | Files | Weekly summaries |

### 5. Evolution Engine (`core/exponential_evolution.py`)
6 phases per cycle:
1. Research & Clone
2. Deep Distillation
3. Experiments
4. Invention
5. Battle (Red vs Blue)
6. Memory Crystallization

### 6. LLM Client (`core/llm_client.py`)
- 28+ models via OpenRouter
- Auto-retry with exponential backoff
- Smart fallback chain: gemini-flash -> deepseek -> qwen-free -> llama-free

## API Endpoints

### Core
- `GET /health` - System health
- `GET /status` - Full status with agent counts
- `GET /agents` - List all 81 agents
- `POST /task` - Send task to best agent

### Memory
- `GET /memory/stats` - Memory statistics
- `GET /memory/swarm/stats` - Swarm memory stats

### Evolution
- `POST /evolution/exponential/start` - Start evolution
- `GET /evolution/stats` - Evolution statistics
- `POST /training/cycle` - Run training cycle

### Swarm
- `POST /swarm/start` - Start swarm session
- `POST /swarm/stop` - Stop swarm
- `GET /swarm/status` - Swarm status
- `GET /swarm/events` - Event feed

### Voice
- `POST /voice/speak` - Text to speech
- `POST /voice/ask` - Ask agent with voice reply
- `POST /voice/morning-report` - Daily voice report

## Running the System

```bash
# Single command to start everything:
cd C:\Users\saffo\army81
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 5
Start-Process python -ArgumentList "gateway/app.py"
Start-Sleep 10
Start-Process python -ArgumentList "scripts/evolution_runner.py"
Start-Process python -ArgumentList "integrations/telegram_bot.py"
```

## Models Used
| Alias | Model | Use Case |
|-------|-------|----------|
| gemini-flash | google/gemini-2.0-flash | Fast general tasks |
| claude-smart | anthropic/claude-sonnet-4.6 | Complex reasoning |
| deepseek-r1 | deepseek/deepseek-r1 | Deep thinking, math |
| qwen-coder | qwen/qwen-2.5-coder-32b | Code generation |
| o3-mini | openai/o3-mini | Math, science |
| perplexity | perplexity/sonar-pro | Web search |
