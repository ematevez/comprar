"""
enviar_reporte_email.py
Envía un reporte diario por email con el estado de los procesos.
Se ejecuta automáticamente vía cron a la hora configurada.
"""
import os
import json
import smtplib
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURACIÓN
# ============================================
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")  # Separado por comas

EXCEL_PROCESOS = "procesos_armada.xlsx"
EXCEL_GESTION = "registro_gestion.xlsx"
ESTADO_PROCESOS = "estado_procesos.json"
LOG_FILE = "logs_comprar.txt"
EMAILS_FILE = "data/emails_reporte.json"


def cargar_destinatarios():
    """Carga la lista de destinatarios: combina .env + archivo JSON."""
    destinatarios = set()
    
    # Desde variable de entorno
    if EMAIL_TO:
        for email in EMAIL_TO.split(","):
            email = email.strip()
            if email:
                destinatarios.add(email)
    
    # Desde archivo JSON (agregados dinámicamente)
    if os.path.exists(EMAILS_FILE):
        try:
            with open(EMAILS_FILE, "r") as f:
                data = json.load(f)
            for email in data.get("emails", []):
                destinatarios.add(email.strip())
        except:
            pass
    
    return list(destinatarios)


def generar_reporte_html():
    """Genera el contenido HTML del reporte."""
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    procesos_activos = 0
    try:
        with open(ESTADO_PROCESOS, "r") as f:
            estado = json.load(f)
        procesos_activos = len(estado.get("procesos", {}))
        ultima = estado.get("ultima_ejecucion", "Nunca")
    except:
        ultima = "Error al cargar"
    
    tabla_html = ""
    total_registros = 0
    if os.path.exists(EXCEL_PROCESOS):
        try:
            df = pd.read_excel(EXCEL_PROCESOS)
            total_registros = len(df)
            
            df_preview = df.head(20)
            tabla_html = "<table style='border-collapse:collapse;width:100%;font-size:12px'>"
            tabla_html += "<tr style='background:#1a365d;color:white'>"
            for col in df_preview.columns[:6]:
                tabla_html += f"<th style='padding:8px;border:1px solid #ddd;text-align:left'>{col}</th>"
            tabla_html += "</tr>"
            
            for _, row in df_preview.iterrows():
                tabla_html += "<tr style='background:#f8f9fa'>"
                for col in df_preview.columns[:6]:
                    valor = str(row.get(col, ""))[:40]
                    tabla_html += f"<td style='padding:6px;border:1px solid #ddd'>{valor}</td>"
                tabla_html += "</tr>"
            
            tabla_html += "</table>"
            if len(df) > 20:
                tabla_html += f"<p style='color:#666;font-size:11px'>Mostrando 20 de {len(df)} procesos</p>"
        except Exception as e:
            tabla_html = f"<p>Error leyendo Excel: {e}</p>"
    
    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px">
        <div style="background:linear-gradient(135deg,#1a365d,#2d3748);padding:20px;border-radius:10px;color:white;margin-bottom:20px">
            <h1 style="margin:0;font-size:22px">📊 Reporte Diario de Licitaciones</h1>
            <p style="margin:5px 0 0;opacity:0.8">Generado: {hoy}</p>
        </div>
        
        <div style="display:flex;gap:15px;margin-bottom:20px">
            <div style="flex:1;background:#e6fffa;padding:15px;border-radius:8px;text-align:center">
                <div style="font-size:28px;font-weight:bold;color:#234e52">{procesos_activos}</div>
                <div style="font-size:12px;color:#2c7a7b">Procesos Activos</div>
            </div>
            <div style="flex:1;background:#ebf8ff;padding:15px;border-radius:8px;text-align:center">
                <div style="font-size:28px;font-weight:bold;color:#2a4365">{total_registros}</div>
                <div style="font-size:12px;color:#2b6cb0">En Excel</div>
            </div>
            <div style="flex:1;background:#faf5ff;padding:15px;border-radius:8px;text-align:center">
                <div style="font-size:14px;font-weight:bold;color:#553c9a;margin-top:8px">{ultima[:16] if ultima != 'Nunca' else 'Nunca'}</div>
                <div style="font-size:12px;color:#6b46c1">Última Ejecución</div>
            </div>
        </div>
        
        <h2 style="color:#1a365d;font-size:16px">📋 Procesos Vigentes</h2>
        {tabla_html if tabla_html else "<p>No hay datos disponibles.</p>"}
        
        <hr style="margin:20px 0;border:none;border-top:1px solid #eee">
        <p style="font-size:11px;color:#999;text-align:center">
            Dashboard de Licitaciones - Reporte automático<br>
            Servidor Docker - {hoy}
        </p>
    </body>
    </html>
    """
    return html


def enviar_email(destinatarios_override=None):
    """Envía el reporte por email."""
    destinatarios = destinatarios_override or cargar_destinatarios()
    
    if not destinatarios:
        print("❌ No hay destinatarios configurados (EMAIL_TO o data/emails_reporte.json)")
        return False
    
    if not SMTP_USER or not SMTP_PASS:
        print("❌ No hay credenciales SMTP configuradas (SMTP_USER / SMTP_PASS)")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM or SMTP_USER
        msg['To'] = ', '.join(destinatarios)
        msg['Subject'] = f"📊 Reporte Licitaciones - {datetime.now().strftime('%d/%m/%Y')}"
        
        html = generar_reporte_html()
        msg.attach(MIMEText(html, 'html'))
        
        # Adjuntar Excel si existe
        if os.path.exists(EXCEL_PROCESOS):
            with open(EXCEL_PROCESOS, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=EXCEL_PROCESOS)
                msg.attach(part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Reporte enviado a {len(destinatarios)} destinatarios: {', '.join(destinatarios)}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False


if __name__ == "__main__":
    print(f"📧 Enviando reporte diario - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    enviar_email()
