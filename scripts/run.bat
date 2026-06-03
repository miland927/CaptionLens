@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\.."
title Teams Caption Translator Launcher

set "APP_ROOT=%CD%"
set "VENV_DIR=%APP_ROOT%\.venv"
set "LOG_DIR=%APP_ROOT%\logs"
set "RUN_LOG=%LOG_DIR%\launcher.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul
echo [%DATE% %TIME%] Launcher started > "%RUN_LOG%"

echo.
echo Teams Caption Translator
echo ========================
echo Project: %APP_ROOT%
echo Log: %RUN_LOG%
echo.

set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PYW=%VENV_DIR%\Scripts\pythonw.exe"

if not exist "%VENV_PY%" (
  echo Creating dedicated .venv for this project...
  echo Creating venv >> "%RUN_LOG%"
  call :find_python
  if "!BASE_PY!"=="" (
    echo Python 3.10+ was not found. Please install Python and run again.
    echo Python 3.10+ not found >> "%RUN_LOG%"
    pause
    exit /b 1
  )
  echo Base Python: !BASE_PY!
  echo Base Python: !BASE_PY! >> "%RUN_LOG%"
  "!BASE_PY!" -m venv "%VENV_DIR%" >> "%RUN_LOG%" 2>&1
  if errorlevel 1 (
    echo Failed to create .venv. See log:
    echo %RUN_LOG%
    pause
    exit /b 1
  )
)

echo Checking runtime...
set "PYTHONUTF8=1"
set "PYTHONPATH=%APP_ROOT%\src"
"%VENV_PY%" "%APP_ROOT%\scripts\check_runtime.py" >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
  if "%TCT_SKIP_INSTALL%"=="1" (
    echo Runtime check failed and auto install is disabled. See log:
    echo %RUN_LOG%
    pause
    exit /b 1
  )
  echo Installing or repairing dependencies. First run may take a few minutes...
  "%VENV_PY%" -m pip install --upgrade pip >> "%RUN_LOG%" 2>&1
  "%VENV_PY%" -m pip install -r "%APP_ROOT%\requirements.txt" >> "%RUN_LOG%" 2>&1
  if errorlevel 1 (
    echo Dependency install failed. See log:
    echo %RUN_LOG%
    echo.
    echo Manual command:
    echo "%VENV_PY%" -m pip install -r "%APP_ROOT%\requirements.txt"
    pause
    exit /b 1
  )
  "%VENV_PY%" "%APP_ROOT%\scripts\check_runtime.py" >> "%RUN_LOG%" 2>&1
  if errorlevel 1 (
    echo Runtime check still failed after install. See log:
    echo %RUN_LOG%
    pause
    exit /b 1
  )
)

if not exist "%VENV_PYW%" set "VENV_PYW=%VENV_PY%"

echo Launching UI...
echo Launching UI with %VENV_PYW% >> "%RUN_LOG%"
start "Teams Caption Translator" "%VENV_PYW%" "%APP_ROOT%\scripts\launch_app.py"
exit /b 0

:find_python
set "BASE_PY="
if "%BASE_PY%"=="" if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "BASE_PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if "%BASE_PY%"=="" if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "BASE_PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if "%BASE_PY%"=="" if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set "BASE_PY=%LocalAppData%\Programs\Python\Python310\python.exe"
if "%BASE_PY%"=="" if exist "%LocalAppData%\AstrBot\backend\python\python.exe" set "BASE_PY=%LocalAppData%\AstrBot\backend\python\python.exe"
if "%BASE_PY%"=="" if exist "C:\Users\35538\AppData\Local\AstrBot\backend\python\python.exe" set "BASE_PY=C:\Users\35538\AppData\Local\AstrBot\backend\python\python.exe"
if not "%BASE_PY%"=="" exit /b 0
for /f "delims=" %%P in ('where py 2^>nul') do (
  if "!BASE_PY!"=="" set "BASE_PY=py"
)
if not "%BASE_PY%"=="" exit /b 0
for /f "delims=" %%P in ('where python 2^>nul') do (
  if "!BASE_PY!"=="" set "BASE_PY=%%P"
)
exit /b 0
