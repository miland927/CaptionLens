@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
title Teams Caption Translator Launcher

set "APP_ROOT=%CD%"
set "LOG_DIR=%APP_ROOT%\logs"
set "RUN_LOG=%LOG_DIR%\launcher.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul

echo Starting launcher > "%RUN_LOG%"
echo.
echo Teams Caption Translator
echo ========================
echo Checking runtime...
echo.

set "PY="
if exist "%LocalAppData%\AstrBot\backend\python\python.exe" set "PY=%LocalAppData%\AstrBot\backend\python\python.exe"
if "%PY%"=="" if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if "%PY%"=="" for /f "delims=" %%P in ('where python 2^>nul') do if "%PY%"=="" set "PY=%%P"
if "%PY%"=="" for /f "delims=" %%P in ('where py 2^>nul') do if "%PY%"=="" set "PY=%%P"
if "%PY%"=="" set "PY=C:\Users\35538\AppData\Local\AstrBot\backend\python\python.exe"

if "%PY%"=="" (
  echo Python was not found.
  echo Please install Python 3.10 or newer, then run this file again.
  echo Python not found >> "%RUN_LOG%"
  pause
  exit /b 1
)

echo Python: %PY%
echo Python: %PY% >> "%RUN_LOG%"

set "PYTHONPATH=%APP_ROOT%\src;%PYTHONPATH%"
"%PY%" "%APP_ROOT%\scripts\check_runtime.py" >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
  echo.
  if "%TCT_SKIP_INSTALL%"=="1" (
    echo Runtime check failed and install is disabled for this run.
    echo See log:
    echo %RUN_LOG%
    exit /b 1
  )
  echo Required packages are missing. Installing now...
  echo This may take a few minutes on first run.
  echo.
  "%PY%" -m pip install -r "%APP_ROOT%\requirements.txt" >> "%RUN_LOG%" 2>&1
  if errorlevel 1 (
    echo.
    echo Automatic install failed. See log:
    echo %RUN_LOG%
    echo.
    echo Manual command:
    echo "%PY%" -m pip install -r "%APP_ROOT%\requirements.txt"
    pause
    exit /b 1
  )
)

set "PYW="
for %%I in ("%PY%") do if exist "%%~dpIpythonw.exe" set "PYW=%%~dpIpythonw.exe"
if "%PYW%"=="" set "PYW=%PY%"

echo Launching UI...
echo Launching UI with %PYW% >> "%RUN_LOG%"
start "Teams Caption Translator" "%PYW%" "%APP_ROOT%\scripts\launch_app.py"
exit /b 0
