@echo off
cd /d "%~dp0"
title ClaudeRotate — Profile Setup
color 0A

echo.
echo  =============================================
echo    ClaudeRotate - Profile Setup
echo    by Devansh Dubey (github.com/devanshd07o)
echo  =============================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python not found!
    echo  Run install.bat first.
    echo.
    pause
    exit /b 1
)

python setup_profiles.py

echo.
pause