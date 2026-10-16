# run_comprar.py SIN usar discord.py

import subprocess
import os
from datetime import datetime
import requests

# CONFIG
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1387230168090939412/ID0uEmm59Luj4mCgJHyykkP0cLxVYyMS2nncLmQDgRkc6tM83Pk5_fApLuf9yHVRCmZa"

archivo_base = "procesos_"
fecha_hoy = datetime.now().strftime("%Y%m%d")
nombre_excel = f"{archivo_base}{fecha_hoy}.xlsx"

def enviar_archivo_webhook():
    if not os.path.exists(nombre_excel):
        print("❌ El archivo Excel no fue generado. Revisá el script.")
        requests.post(DISCORD_WEBHOOK, json={"content": "❌ El archivo Excel no fue generado. Revisá el script."})
        return

    try:
        with open(nombre_excel, "rb") as f:
            files = {"file": (nombre_excel, f)}
            data = {"content": f"📁 Proceso completado para el día {fecha_hoy}"}
            response = requests.post(DISCORD_WEBHOOK, data=data, files=files)

        if response.status_code == 204:
            print("✅ Archivo enviado correctamente.")
        else:
            print(f"❌ Error al enviar a Discord: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Error general al enviar archivo: {e}")

def ejecutar_comprar():
    env = os.environ.copy()
    env["NOMBRE_EXCEL"] = nombre_excel
    try:
        subprocess.run(["python", "comprar.py"], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar comprar.py:", e)

if __name__ == "__main__":
    ejecutar_comprar()
    enviar_archivo_webhook()
