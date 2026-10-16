@echo off
setlocal
if "%~1"=="" goto interactive
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply.ps1" %*
exit /b %errorlevel%
:interactive
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply.ps1"
set "patch_result=%errorlevel%"
pause
exit /b %patch_result%
