@echo off
REM ============================================================
REM  Iniciar Dashboard de Licitaciones (Windows)
REM  Doble click para arrancar todo. Toda la logica real vive en
REM  iniciar_dashboard.py, que es igual en Windows/Mac/Linux.
REM ============================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No encontre Python instalado en esta PC.
    echo Instala Python desde https://www.python.org/downloads/ y volve a intentar.
    pause
    exit /b 1
)

python iniciar_dashboard.py
pause
