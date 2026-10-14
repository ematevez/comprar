#!/bin/bash
# ============================================================
#  Iniciar Dashboard de Licitaciones (Mac / Linux)
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
