@echo off
echo ============================================
echo   Army81 - Setup Script for Windows
echo   81 AI Agents System
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python found

REM Create virtual environment
echo [INFO] Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt

REM Create directories
echo [INFO] Creating directories...
mkdir logs 2>nul
mkdir memory 2>nul
mkdir memory\episodes 2>nul
mkdir skills 2>nul
mkdir updates 2>nul

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not found. Install from https://ollama.com
    echo [INFO] You can still use cloud providers (OpenAI, Anthropic, Perplexity)
) else (
    echo [OK] Ollama found
    echo [INFO] Pulling recommended models...
    ollama pull qwen3:8b
    ollama pull qwen2.5-coder:14b
    echo [INFO] Models ready
)

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   Quick Start:
echo     python cli.py status    - System status
echo     python cli.py list      - List all agents
echo     python cli.py chat      - Interactive chat
echo     python cli.py serve     - Start API server
echo     python cli.py task "your task here"
echo.
echo ============================================
pause
