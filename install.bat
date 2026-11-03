@echo off
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo [ERROR] Python 3.10+ no encontrado. Instalalo desde https://www.python.org/downloads/
  pause
  exit /b 1
)
%PY% -m venv .venv
if errorlevel 1 ( echo [ERROR] No se pudo crear el entorno virtual & pause & exit /b 1 )
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] Fallo la instalacion de dependencias & pause & exit /b 1 )
echo Instalacion completa.
pause
