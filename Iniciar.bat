@echo off
setlocal
cd /d "%~dp0"
node --version >nul 2>&1
if errorlevel 1 (
    echo Instale o Node.js LTS em https://nodejs.org/ e abra este arquivo novamente.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto erro
exit /b 0
:erro
echo.
echo Nao foi possivel iniciar. Confira a mensagem acima e se o Python esta instalado.
pause
exit /b 1
