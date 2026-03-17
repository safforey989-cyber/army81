#!/bin/bash
echo "============================================"
echo "  Army81 - Setup Script"
echo "  81 AI Agents System"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
    exit 1
fi
echo "[OK] Python found: $(python3 --version)"

# Create virtual environment
echo "[INFO] Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt

# Create directories
echo "[INFO] Creating directories..."
mkdir -p logs memory/episodes skills updates

# Check Ollama
if command -v ollama &> /dev/null; then
    echo "[OK] Ollama found"
    echo "[INFO] Pulling recommended models..."
    ollama pull qwen3:8b
    ollama pull qwen2.5-coder:14b
else
    echo "[WARNING] Ollama not found. Install from https://ollama.com"
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "  Quick Start:"
echo "    python cli.py status    - System status"
echo "    python cli.py list      - List all agents"
echo "    python cli.py chat      - Interactive chat"
echo "    python cli.py serve     - Start API server"
echo ""
