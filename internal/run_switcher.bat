@echo off
cd /d "%~dp0"

REM ── Step 1: Start extractor server in background if not already running ──
curl -s --max-time 1 http://127.0.0.1:5757/ping >nul 2>&1
if errorlevel 1 (
    start "" /B pythonw "%~dp0handover_server.py"
)

REM ── Step 2: Switch to next Claude account ──
python "%~dp0profile_switcher.py"