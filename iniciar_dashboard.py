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

# Librerías necesarias (actualizado con las nuevas funcionalidades)
LIBRERIAS_NECESARIAS = [
    "playwright",
    "pandas",
    "openpyxl",
    "pypdf",
    "telegram",      # Bot de Telegram
    "dotenv",        # Variables de entorno
    "requests"       # HTTP requests
]


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
    
    # Verificar cada librería por separado (telegram se importa como 'telegram')
    librerias_faltantes = []
    for lib in LIBRERIAS_NECESARIAS:
        try:
            __import__(lib)
        except ImportError:
            librerias_faltantes.append(lib)
    
    if not librerias_faltantes:
        return

    print(f"[SETUP] Faltan librerías: {', '.join(librerias_faltantes)}")
    print("[SETUP] Instalando dependencias, puede tardar unos minutos...")
    
    try:
        subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Mapear nombres de import a nombres de paquetes pip
        paquete_map = {
            "telegram": "python-telegram-bot",
            "dotenv": "python-dotenv",
            "playwright": "playwright",
            "pandas": "pandas",
            "openpyxl": "openpyxl",
            "pypdf": "pypdf",
            "requests": "requests"
        }
        
        paquetes_a_instalar = [paquete_map.get(lib, lib) for lib in librerias_faltantes]
        subprocess.run([py, "-m", "pip", "install"] + paquetes_a_instalar, check=True)
        
        if "playwright" in librerias_faltantes:
            print("[SETUP] Instalando el navegador Chromium para Playwright...")
            subprocess.run([py, "-m", "playwright", "install", "chromium"], check=True)
            
    except subprocess.CalledProcessError:
        print("[ERROR] Falló la instalación. Revisá tu conexión a internet.")
        sys.exit(1)


def verificar_archivos_esenciales():
    """Verifica que existan los archivos esenciales."""
    archivos_esenciales = [
        "servidor_dashboard.py",
        "generar_dashboard.py",
        "comprar.py",
        "detalle_proceso.py"
    ]
    
    faltantes = []
    for archivo in archivos_esenciales:
        if not os.path.exists(os.path.join(BASE_DIR, archivo)):
            faltantes.append(archivo)
    
    if faltantes:
        print(f"[ERROR] Faltan archivos esenciales: {', '.join(faltantes)}")
        print("[ERROR] Verificá que todos los archivos estén en la carpeta del proyecto.")
        sys.exit(1)


def verificar_env():
    """Verifica que exista el archivo .env."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        print("[ADVERTENCIA] No se encontró el archivo .env")
        print("[ADVERTENCIA] Copiá .env.example a .env y configurá las credenciales")
        respuesta = input("¿Querés continuar sin .env? (s/n): ")
        if respuesta.lower() != 's':
            sys.exit(0)


def main():
    os.chdir(BASE_DIR)
    print("=" * 60)
    print(f"  🚀 Dashboard de Licitaciones")
    print(f"  Sistema detectado: {platform.system()}")
    print("=" * 60)

    verificar_archivos_esenciales()
    verificar_env()
    
    crear_venv_si_falta()
    instalar_dependencias_si_faltan()

    py = ruta_python_venv()
    ruta_servidor = os.path.join(BASE_DIR, "servidor_dashboard.py")

    print("\n[OK] Entorno listo. Arrancando el servidor...")
    print(f"[OK] Puerto: {PUERTO}")
    print(f"[OK] URL: http://localhost:{PUERTO}")
    print("=" * 60)
    
    proceso = subprocess.Popen([py, ruta_servidor])

    time.sleep(3)
    print("\n[OK] Abriendo el navegador...")
    webbrowser.open(f"http://localhost:{PUERTO}")

    try:
        proceso.wait()
    except KeyboardInterrupt:
        print("\n\n👋 Cerrando el servidor...")
        proceso.terminate()
        print("✅ Servidor detenido")


if __name__ == "__main__":
    main()
