@echo off
cd /d "%~dp0"

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

"%PYTHONW_EXE%" "%~dp0handover_server.py"
