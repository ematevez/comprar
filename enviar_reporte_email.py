"""
enviar_reporte_email.py
Envía reportes por email a los destinatarios configurados.
"""
import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Configuración SMTP desde .env
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")


def enviar_reporte(destinatarios, asunto="Reporte de Licitaciones", html_email=None):
    """
    Envía un email de prueba o reporte a los destinatarios.
    Si html_email es proporcionado, usa ese HTML personalizado.
    Retorna el número de emails enviados exitosamente.
    """
    if not SMTP_USER or not SMTP_PASS:
        print("❌ Credenciales SMTP no configuradas en .env")
        return 0
    
    enviados = 0
    for email in destinatarios:
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM or SMTP_USER
            msg['To'] = email
            msg['Subject'] = f"📧 {asunto} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            # Usar HTML personalizado si se proporciona, sino usar el de prueba
            if html_email:
                body = html_email
            else:
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #667eea;">Dashboard de Licitaciones</h2>
                    <p>Este es un email de prueba enviado desde el dashboard.</p>
                    <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>Destinatario:</strong> {email}</p>
                    <hr style="border: 1px solid #e0e0e0; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        Si recibiste este email, la configuración SMTP es correcta.
                    </p>
                </body>
                </html>
                """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email enviado a {email}")
            enviados += 1
            
        except Exception as e:
            print(f"❌ Error enviando a {email}: {e}")
    
    return enviados


if __name__ == "__main__":
    # Si se ejecuta directamente, enviar a todos los emails configurados
    from api_emails import cargar_emails
    emails = cargar_emails().get('emails', [])
    
    if not emails:
        print("❌ No hay emails configurados")
    else:
        print(f"📧 Enviando email de prueba a {len(emails)} destinatarios...")
        enviados = enviar_reporte(emails)
        print(f"✅ {enviados} emails enviados exitosamente")
