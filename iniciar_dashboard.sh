#!/bin/bash
# ============================================================
#  Iniciar Dashboard de Licitaciones (Mac / Linux)
<<<<<<< HEAD
#  Ejecutar: bash iniciar_dashboard.sh
#  O hacerlo ejecutable: chmod +x iniciar_dashboard.sh
#        y luego: ./iniciar_dashboard.sh
# ============================================================

# Cambiar al directorio donde está este script
cd "$(dirname "$0")"

echo "============================================================"
echo "  Dashboard de Licitaciones - $(uname -s)"
echo "============================================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] No se encontró Python 3 instalado."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "En macOS, instalá Python con:"
        echo "  brew install python3"
        echo "O descargalo desde https://www.python.org/downloads/"
    else
        echo "En Linux, instalá Python con:"
        echo "  sudo apt install python3 python3-venv python3-pip"
        echo "  o"
        echo "  sudo dnf install python3 python3-pip"
    fi
    echo ""
    exit 1
fi

# Mostrar versión de Python
echo "[INFO] Python encontrado:"
python3 --version
echo ""

# Verificar si existe el archivo iniciar_dashboard.py
if [ ! -f "iniciar_dashboard.py" ]; then
    echo "[ERROR] No se encontró iniciar_dashboard.py"
    echo "Verificá que todos los archivos estén en esta carpeta."
    exit 1
fi

# Ejecutar el lanzador
python3 iniciar_dashboard.py

echo ""
echo "============================================================"
echo "  Servidor detenido"
echo "============================================================"
=======
#  Doble click (o "bash iniciar_dashboard.sh" en la terminal) para
#  arrancar todo. Toda la lógica real vive en iniciar_dashboard.py,
#  que es igual en Windows/Mac/Linux.
# ============================================================
cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] No encontré python3 instalado en esta máquina."
    echo "Instalalo desde https://www.python.org/downloads/ (o con tu gestor de paquetes: brew, apt, etc.) y volvé a intentar."
    read -p "Presioná ENTER para cerrar..."
    exit 1
fi

python3 iniciar_dashboard.py

read -p "Presioná ENTER para cerrar..."
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
