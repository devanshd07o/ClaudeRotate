@echo off
cd /d "%~dp0"
title ClaudeRotate — Create Desktop Shortcut

set "VBS=%~dp0silent.vbs"
set "WSCRIPT=C:\Windows\System32\wscript.exe"
set "PS1=%TEMP%\claude_shortcut.ps1"

set "ICON=%~dp0claude.ico"
if not exist "%ICON%" set "ICON=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%ICON%" set "ICON=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

(
echo $desktop  = [Environment]::GetFolderPath('Desktop'^)
echo $lnk      = Join-Path $desktop 'Claude.lnk'
echo $vbs      = '%VBS%'
echo $ws       = New-Object -ComObject WScript.Shell
echo $s        = $ws.CreateShortcut($lnk^)
echo $s.TargetPath       = '%WSCRIPT%'
echo $s.Arguments        = "`"$vbs`""
echo $s.WorkingDirectory = Split-Path $vbs
echo $s.WindowStyle      = 1
echo $s.Description      = 'ClaudeRotate'
echo $s.IconLocation     = '%ICON%, 0'
echo $s.Save(^)
echo if (Test-Path $lnk^) { Write-Host "SUCCESS:$lnk" } else { Write-Host "FAIL" }
) > "%PS1%"

for /f "tokens=*" %%O in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"') do set "RESULT=%%O"

echo %RESULT% | findstr /C:"SUCCESS" >nul
if %errorlevel% == 0 (
    echo.
    echo   Shortcut created! Location: %RESULT:SUCCESS:=%
    echo   Double-click "Claude" on your Desktop to launch.
) else (
    echo.
    echo   ERROR: Could not create shortcut.
    echo   Try: Right-click - Run as Administrator
)

del "%PS1%" >nul 2>&1
echo.
pause