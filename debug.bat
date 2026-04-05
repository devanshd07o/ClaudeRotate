@echo off
cd /d "%~dp0"
title ClaudeRotate — Debug Mode
color 0E

echo.
echo  ============================================
echo    ClaudeRotate - Debug Mode
echo  ============================================
echo.

echo  [CHECK 1] Python...
python --version
if %errorlevel% neq 0 (
    echo  FAIL: Python not found. Run install.bat first.
) else (
    echo  OK
)

echo.
echo  [CHECK 2] chrome_accounts.json...
if exist "%~dp0claude_accounts.json" (
    echo  OK: Found
) else (
    echo  FAIL: Missing. Run setup_profiles.py first.
)

echo.
echo  [CHECK 3] Chrome executable...
python -c "import json,os; d=json.load(open('claude_accounts.json')); print('  Path: '+d.get('chrome_exe','')); print('  Exists: '+str(os.path.exists(d.get('chrome_exe',''))))"
if %errorlevel% neq 0 echo  FAIL: Could not read chrome_exe from json.

echo.
echo  [CHECK 4] Running claude_switch.py with full output...
echo  ─────────────────────────────────────────────
python claude_switch.py
echo  ─────────────────────────────────────────────

echo.
echo  [CHECK 5] switch_state.json...
if exist "%~dp0switch_state.json" (
    type switch_state.json
) else (
    echo  Missing (will be created on first run^)
)

echo.
pause