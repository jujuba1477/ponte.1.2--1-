@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set BASE_PYTHON_CMD=py -3
) else (
  set BASE_PYTHON_CMD=python
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual Python do projeto...
  %BASE_PYTHON_CMD% -m venv .venv
  if errorlevel 1 (
    echo Nao foi possivel criar o ambiente virtual.
    pause
    exit /b 1
  )
)

set "PYTHON_CMD=%CD%\.venv\Scripts\python.exe"

"%PYTHON_CMD%" -m pip install -r requirements.txt
"%PYTHON_CMD%" testar_mysql.py
pause
