@echo off
cd /d "%~dp0"

REM ── Step 1: Auto-Detect Python Executable Path ──
set "PYTHON_EXE=python"
where python >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    ) else if exist "%LocalAppData%\Programs\Python\Python314\python.exe" (
        set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python314\python.exe"
    ) else if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
    ) else if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
        set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
    ) else if exist "C:\Python312\python.exe" (
        set "PYTHON_EXE=C:\Python312\python.exe"
    )
)

set "PYTHONW_EXE=pythonw"
where pythonw >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LocalAppData%\Programs\Python\Python311\pythonw.exe" (
        set "PYTHONW_EXE=%LocalAppData%\Programs\Python\Python311\pythonw.exe"
    ) else if exist "%LocalAppData%\Programs\Python\Python314\pythonw.exe" (
        set "PYTHONW_EXE=%LocalAppData%\Programs\Python\Python314\pythonw.exe"
    ) else if exist "%LocalAppData%\Programs\Python\Python312\pythonw.exe" (
        set "PYTHONW_EXE=%LocalAppData%\Programs\Python\Python312\pythonw.exe"
    ) else if exist "%LocalAppData%\Programs\Python\Python310\pythonw.exe" (
        set "PYTHONW_EXE=%LocalAppData%\Programs\Python\Python310\pythonw.exe"
    ) else if exist "C:\Python312\pythonw.exe" (
        set "PYTHONW_EXE=C:\Python312\pythonw.exe"
    )
)

REM ── Step 2: Start background handover server if not running ──
curl -s --max-time 1 http://127.0.0.1:5757/ping >nul 2>&1
if errorlevel 1 (
    start "" /B "%PYTHONW_EXE%" "%~dp0handover_server.py"
)

REM ── Step 3: Launch Profile Switcher ──
"%PYTHON_EXE%" "%~dp0profile_switcher.py"