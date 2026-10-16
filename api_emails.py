"""
api_emails.py
Endpoints para gestionar la lista de emails de reporte.
Permite agregar, eliminar y enviar emails de prueba.
"""
import json
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

EMAILS_FILE = "data/emails_reporte.json"


def cargar_emails():
    """Carga la lista de emails configurados."""
    os.makedirs(os.path.dirname(EMAILS_FILE), exist_ok=True)
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            return json.load(f)
    return {"emails": [], "updated": None}


def guardar_emails(data):
    """Guarda la lista de emails."""
    os.makedirs(os.path.dirname(EMAILS_FILE), exist_ok=True)
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def agregar_email(email):
    """Agrega un email a la lista."""
    if not email or "@" not in email:
        return {"ok": False, "error": "Email inválido"}
    
    data = cargar_emails()
    if email in data["emails"]:
        return {"ok": False, "error": "Email ya existe"}
    
    data["emails"].append(email)
    guardar_emails(data)
    return {"ok": True, "mensaje": f"Email {email} agregado", "emails": data["emails"]}


def eliminar_email(email):
    """Elimina un email de la lista."""
    data = cargar_emails()
    if email not in data["emails"]:
        return {"ok": False, "error": "Email no encontrado"}
    
    data["emails"].remove(email)
    guardar_emails(data)
    return {"ok": True, "mensaje": f"Email {email} eliminado", "emails": data["emails"]}


def enviar_test(email):
    """Envía un email de prueba."""
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
    
    if not SMTP_USER or not SMTP_PASS:
        return {"ok": False, "error": "Credenciales SMTP no configuradas"}
    
    try:
        msg = MIMEText(
            f"✅ Email de prueba enviado correctamente.\n\n"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"Si recibís este email, la configuración SMTP es correcta.\n"
            f"Los reportes diarios se enviarán a esta dirección."
        )
        msg['Subject'] = '📧 Test - Dashboard Licitaciones'
        msg['From'] = EMAIL_FROM or SMTP_USER
        msg['To'] = email
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return {"ok": True, "mensaje": f"Email de prueba enviado a {email}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
