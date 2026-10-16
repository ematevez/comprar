@echo off
REM ============================================================
REM  Iniciar Dashboard de Licitaciones (Windows)
REM  Doble click para arrancar todo. Toda la logica real vive en
REM  iniciar_dashboard.py, que es igual en Windows/Mac/Linux.
REM ============================================================
cd /d "%~dp0"

<<<<<<< HEAD
echo ============================================================
echo   Dashboard de Licitaciones - Windows
echo ============================================================
echo.

REM Verificar si Python está instalado
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python instalado en esta PC.
    echo Instala Python desde https://www.python.org/downloads/
    echo y volve a intentar.
    echo.
=======
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No encontre Python instalado en esta PC.
    echo Instala Python desde https://www.python.org/downloads/ y volve a intentar.
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
    pause
    exit /b 1
)

<<<<<<< HEAD
REM Mostrar versión de Python
echo [INFO] Python encontrado:
python --version
echo.

REM Verificar si existe el archivo iniciar_dashboard.py
if not exist "iniciar_dashboard.py" (
    echo [ERROR] No se encontro iniciar_dashboard.py
    echo Verifica que todos los archivos esten en esta carpeta.
    pause
    exit /b 1
)

REM Ejecutar el lanzador
python iniciar_dashboard.py

echo.
echo ============================================================
echo   Servidor detenido
echo ============================================================
=======
python iniciar_dashboard.py
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
pause
