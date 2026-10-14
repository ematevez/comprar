"""
iniciar_dashboard.py
Lanzador multiplataforma (Windows / Mac / Linux). Hace lo mismo que antes
hacía el .bat, pero en Python puro -- así el mismo código sirve para
cualquier sistema operativo, sin duplicar lógica en .bat y .sh por separado.

Uso: python3 iniciar_dashboard.py
(en Windows también podés seguir usando iniciar_dashboard.bat con doble
click, y en Mac/Linux iniciar_dashboard.sh -- los dos solo llaman a este
archivo).
"""
import os
import sys
import time
import platform
import subprocess
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "env_1")
ES_WINDOWS = platform.system() == "Windows"
PUERTO = 8765

LIBRERIAS_NECESARIAS = ["playwright", "pandas", "openpyxl", "pypdf"]


def ruta_python_venv() -> str:
    """Ruta al Python DENTRO del entorno virtual -- cambia de estructura según el SO."""
    if ES_WINDOWS:
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python3")


def crear_venv_si_falta():
    if os.path.exists(ruta_python_venv()):
        return
    print(f"[SETUP] No encontré el entorno virtual en {VENV_DIR} -- creando uno nuevo...")
    try:
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] No pude crear el entorno virtual. ¿Python está bien instalado?")
        sys.exit(1)


def instalar_dependencias_si_faltan():
    py = ruta_python_venv()
    chequeo = subprocess.run(
        [py, "-c", f"import {', '.join(LIBRERIAS_NECESARIAS)}"],
        capture_output=True
    )
    if chequeo.returncode == 0:
        return

    print("[SETUP] Faltan librerías -- instalando por primera vez, puede tardar unos minutos...")
    try:
        subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([py, "-m", "pip", "install"] + LIBRERIAS_NECESARIAS, check=True)
        print("[SETUP] Instalando el navegador Chromium para Playwright...")
        subprocess.run([py, "-m", "playwright", "install", "chromium"], check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Falló la instalación. Revisá tu conexión a internet.")
        sys.exit(1)


def main():
    os.chdir(BASE_DIR)
    print("=" * 60)
    print(f"Sistema detectado: {platform.system()}")
    print("=" * 60)

    crear_venv_si_falta()
    instalar_dependencias_si_faltan()

    py = ruta_python_venv()
    ruta_servidor = os.path.join(BASE_DIR, "servidor_dashboard.py")

    print("[OK] Entorno listo. Arrancando el servidor...")
    proceso = subprocess.Popen([py, ruta_servidor])

    time.sleep(3)
    webbrowser.open(f"http://localhost:{PUERTO}")

    try:
        proceso.wait()
    except KeyboardInterrupt:
        print("\n👋 Cerrando el servidor...")
        proceso.terminate()


if __name__ == "__main__":
    main()
