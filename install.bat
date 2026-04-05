@echo off
cd /d "%~dp0"
title ClaudeRotate — First Time Setup
color 0A

echo.
echo  =============================================
echo    ClaudeRotate — Auto Setup
echo    by Devansh Dubey (github.com/devanshd07o)
echo  =============================================
echo.

REM ── STEP 1: Check Python ──────────────────────────────────────
echo  [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo        Python found!
    goto :check_pip
)

echo        Python NOT found. Downloading installer...
echo.

REM Download Python installer using PowerShell
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"

if not exist "%TEMP%\python_installer.exe" (
    echo  ERROR: Could not download Python.
    echo  Please install manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo        Installing Python (this takes ~1 min)...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1

REM Refresh PATH for current session
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python install failed.
    echo  Please install manually from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during install!
    pause
    exit /b 1
)
echo        Python installed successfully!

:check_pip
REM ── STEP 2: Check pip ────────────────────────────────────────
echo.
echo  [2/4] Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo        Installing pip...
    python -m ensurepip --upgrade >nul 2>&1
)
echo        pip ready!

REM ── STEP 3: Check Chrome ─────────────────────────────────────
echo.
echo  [3/4] Checking Chrome...
set CHROME1=C:\Program Files\Google\Chrome\Application\chrome.exe
set CHROME2=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
set CHROME3=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe

if exist "%CHROME1%" ( echo        Chrome found! & goto :setup )
if exist "%CHROME2%" ( echo        Chrome found! & goto :setup )
if exist "%CHROME3%" ( echo        Chrome found! & goto :setup )

echo        Chrome NOT found!
echo        Please install Chrome from: https://www.google.com/chrome/
echo        Then re-run this file.
pause
exit /b 1

:setup
REM ── STEP 4: Run setup_profiles.py ────────────────────────────
echo.
echo  [4/4] Launching Profile Setup...
echo.
echo  ─────────────────────────────────────────────
echo   Follow the on-screen instructions to map
echo   your Chrome profiles to Claude accounts.
echo  ─────────────────────────────────────────────
echo.
pause

python setup_profiles.py

echo.
echo  =============================================
echo   Setup Complete!
echo   Now double-click: Claude.bat to launch
echo   Or run: create_shortcut.bat for desktop icon
echo  =============================================
echo.
pause