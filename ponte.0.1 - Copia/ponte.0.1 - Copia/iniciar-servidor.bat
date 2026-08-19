@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set BASE_PYTHON_CMD=py -3
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set BASE_PYTHON_CMD=python
  ) else (
    echo Python nao foi encontrado.
    echo Instale o Python 3 em https://www.python.org/downloads/ e marque "Add Python to PATH".
    pause
    exit /b 1
  )
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

echo Instalando dependencias Python, se necessario...
"%PYTHON_CMD%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Nao foi possivel instalar as dependencias.
  pause
  exit /b 1
)

set "NEEDS_MYSQL_CONFIG="
if not exist ".env" (
  set "NEEDS_MYSQL_CONFIG=1"
) else (
  findstr /R /I "^MYSQL_HOST=." ".env" >nul || set "NEEDS_MYSQL_CONFIG=1"
  findstr /R /I "^MYSQL_PORT=." ".env" >nul || set "NEEDS_MYSQL_CONFIG=1"
  findstr /R /I "^MYSQL_USER=." ".env" >nul || set "NEEDS_MYSQL_CONFIG=1"
  findstr /R /I "^MYSQL_DATABASE=." ".env" >nul || set "NEEDS_MYSQL_CONFIG=1"
)

if defined NEEDS_MYSQL_CONFIG (
  echo.
  echo A configuracao do MySQL ainda nao esta completa no arquivo .env.
  echo Informe agora os mesmos dados que voce usa no MySQL Workbench.
  call configurar-mysql.bat
  if errorlevel 1 (
    echo Nao foi possivel configurar o MySQL.
    pause
    exit /b 1
  )
)

set OPEN_BROWSER=1
echo Iniciando backend Python + MySQL...
"%PYTHON_CMD%" server.py
