#!/usr/bin/env python3
"""
email_test.py
Terminal interactiva para probar la configuración de email.
"""
import os
import sys
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Colores para la terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  📧 TERMINAL DE PRUEBA - EMAIL")
    print("=" * 70)
    print(f"{Colors.ENDC}")

def print_menu():
    print(f"\n{Colors.OKCYAN}MENÚ DE OPCIONES:{Colors.ENDC}")
    print("1. Ver configuración SMTP actual")
    print("2. Probar conexión con servidor SMTP")
    print("3. Ver lista de destinatarios")
    print("4. Agregar destinatario")
    print("5. Eliminar destinatario")
    print("6. Enviar email de prueba")
    print("7. Enviar reporte completo")
    print("8. Salir")
    print()

def get_smtp_config():
    """Carga la configuración SMTP."""
    return {
        'host': os.environ.get('SMTP_HOST', ''),
        'port': os.environ.get('SMTP_PORT', '587'),
        'user': os.environ.get('SMTP_USER', ''),
        'password': os.environ.get('SMTP_PASS', ''),
        'from_email': os.environ.get('EMAIL_FROM', '')
    }

def get_emails():
    """Carga la lista de emails."""
    config_file = "data/emails_reporte.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            data = json.load(f)
            return data.get('emails', [])
    return []

def save_emails(emails):
    """Guarda la lista de emails."""
    config_file = "data/emails_reporte.json"
    os.makedirs('data', exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump({'emails': emails}, f, indent=2)

def test_smtp_connection(config):
    """Prueba la conexión con el servidor SMTP."""
    print(f"\n{Colors.OKBLUE}Probando conexión con {config['host']}:{config['port']}...{Colors.ENDC}")
    
    try:
        server = smtplib.SMTP(config['host'], int(config['port']), timeout=10)
        server.starttls()
        server.login(config['user'], config['password'])
        print(f"{Colors.OKGREEN}✅ Conexión exitosa!{Colors.ENDC}")
        print(f"   Servidor: {config['host']}")
        print(f"   Puerto: {config['port']}")
        print(f"   Usuario: {config['user']}")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"{Colors.FAIL}❌ Error de autenticación: {e}{Colors.ENDC}")
        print(f"   Verificá que el usuario y contraseña sean correctos")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        return False

def show_emails():
    """Muestra la lista de emails configurados."""
    emails = get_emails()
    
    print(f"\n{Colors.OKCYAN}DESTINATARIOS CONFIGURADOS:{Colors.ENDC}\n")
    
    if not emails:
        print(f"{Colors.WARNING}⚠️  No hay destinatarios configurados{Colors.ENDC}")
        print("   Usá la opción 4 para agregar uno")
        return
    
    for i, email in enumerate(emails, 1):
        print(f"   {i}. {email}")
    
    print(f"\n   Total: {len(emails)} destinatario(s)")

def add_email():
    """Agrega un nuevo destinatario."""
    email = input(f"\n{Colors.BOLD}Ingresá el email: {Colors.ENDC}").strip()
    
    if not email or '@' not in email:
        print(f"{Colors.FAIL}❌ Email inválido{Colors.ENDC}")
        return
    
    emails = get_emails()
    
    if email in emails:
        print(f"{Colors.WARNING}⚠️  Ese email ya está en la lista{Colors.ENDC}")
        return
    
    emails.append(email)
    save_emails(emails)
    print(f"{Colors.OKGREEN}✅ Email agregado: {email}{Colors.ENDC}")

def remove_email():
    """Elimina un destinatario."""
    emails = get_emails()
    
    if not emails:
        print(f"{Colors.WARNING}⚠️  No hay destinatarios para eliminar{Colors.ENDC}")
        return
    
    show_emails()
    
    try:
        opcion = int(input(f"\n{Colors.BOLD}Número del email a eliminar (0 para cancelar): {Colors.ENDC}"))
        
        if opcion == 0:
            return
        
        if opcion < 1 or opcion > len(emails):
            print(f"{Colors.FAIL}❌ Número inválido{Colors.ENDC}")
            return
        
        removed = emails.pop(opcion - 1)
        save_emails(emails)
        print(f"{Colors.OKGREEN}✅ Email eliminado: {removed}{Colors.ENDC}")
    
    except ValueError:
        print(f"{Colors.FAIL}❌ Debe ser un número{Colors.ENDC}")

def send_test_email(config, destinatario=None):
    """Envía un email de prueba."""
    if not destinatario:
        destinatario = input(f"\n{Colors.BOLD}Ingresá el email destino: {Colors.ENDC}").strip()
    
    if not destinatario or '@' not in destinatario:
        print(f"{Colors.FAIL}❌ Email inválido{Colors.ENDC}")
        return
    
    print(f"\n{Colors.OKBLUE}Enviando email de prueba a {destinatario}...{Colors.ENDC}")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config['from_email'] or config['user']
        msg['To'] = destinatario
        msg['Subject'] = f"📧 Email de prueba - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">Dashboard de Licitaciones</h2>
            <p>Este es un email de prueba enviado desde la terminal.</p>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>Destinatario:</strong> {destinatario}</p>
            <hr style="border: 1px solid #e0e0e0; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                Si recibiste este email, la configuración SMTP es correcta.
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(config['host'], int(config['port']))
        server.starttls()
        server.login(config['user'], config['password'])
        server.send_message(msg)
        server.quit()
        
        print(f"{Colors.OKGREEN}✅ Email enviado exitosamente{Colors.ENDC}")
        return True
    
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        return False

def send_report(config):
    """Envía un reporte completo a todos los destinatarios."""
    emails = get_emails()
    
    if not emails:
        print(f"{Colors.WARNING}⚠️  No hay destinatarios configurados{Colors.ENDC}")
        return
    
    print(f"\n{Colors.OKBLUE}Generando y enviando reporte a {len(emails)} destinatario(s)...{Colors.ENDC}")
    
    # Cargar datos de procesos
    try:
        import pandas as pd
        df = pd.read_excel('procesos_armada.xlsx')
        procesos = df.to_dict('records')
    except:
        procesos = []
    
    enviados = 0
    for email in emails:
        try:
            msg = MIMEMultipart()
            msg['From'] = config['from_email'] or config['user']
            msg['To'] = email
            msg['Subject'] = f"📊 Reporte de Licitaciones - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #667eea;">Reporte de Licitaciones</h2>
                <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <hr style="border: 1px solid #e0e0e0; margin: 20px 0;">
                
                <h3>Estadísticas</h3>
                <ul>
                    <li>Total de procesos: {len(procesos)}</li>
                    <li>Activos: {len([p for p in procesos if p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA'])}</li>
                    <li>Descartados: {len([p for p in procesos if p.get('Estado gestión') == 'DESCARTADA'])}</li>
                </ul>
                
                <h3>Próximos 5 procesos</h3>
                <ol>
            """
            
            for proc in procesos[:5]:
                numero = proc.get('Número de proceso', 'N/A')
                objeto = proc.get('Nombre de proceso', 'Sin descripción')
                body += f"<li><strong>{numero}</strong>: {objeto}</li>"
            
            body += """
                </ol>
                <hr style="border: 1px solid #e0e0e0; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    Dashboard de Licitaciones - Reporte automático
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(config['host'], int(config['port']))
            server.starttls()
            server.login(config['user'], config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"{Colors.OKGREEN}✅ Email enviado a {email}{Colors.ENDC}")
            enviados += 1
        
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error enviando a {email}: {e}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}✅ {enviados} email(s) enviado(s) de {len(emails)}{Colors.ENDC}")

def main():
    while True:
        clear_screen()
        print_header()
        
        config = get_smtp_config()
        emails = get_emails()
        
        print(f"{Colors.OKCYAN}CONFIGURACIÓN ACTUAL:{Colors.ENDC}")
        print(f"   Servidor: {config['host'] or 'No configurado'}")
        print(f"   Puerto: {config['port'] or 'No configurado'}")
        print(f"   Usuario: {config['user'] or 'No configurado'}")
        print(f"   Destinatarios: {len(emails)}")
        
        print_menu()
        
        try:
            opcion = input(f"{Colors.BOLD}Seleccioná una opción (1-8): {Colors.ENDC}").strip()
            
            if opcion == '1':
                clear_screen()
                print_header()
                print(f"\n{Colors.OKCYAN}CONFIGURACIÓN SMTP DETALLADA:{Colors.ENDC}\n")
                print(f"   SMTP_HOST: {config['host']}")
                print(f"   SMTP_PORT: {config['port']}")
                print(f"   SMTP_USER: {config['user']}")
                print(f"   SMTP_PASS: {'*' * len(config['password']) if config['password'] else 'No configurado'}")
                print(f"   EMAIL_FROM: {config['from_email']}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '2':
                clear_screen()
                print_header()
                if config['host'] and config['user'] and config['password']:
                    test_smtp_connection(config)
                else:
                    print(f"{Colors.FAIL}❌ Configuración SMTP incompleta{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '3':
                clear_screen()
                print_header()
                show_emails()
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '4':
                clear_screen()
                print_header()
                add_email()
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '5':
                clear_screen()
                print_header()
                remove_email()
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '6':
                clear_screen()
                print_header()
                if config['host'] and config['user'] and config['password']:
                    send_test_email(config)
                else:
                    print(f"{Colors.FAIL}❌ Configuración SMTP incompleta{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '7':
                clear_screen()
                print_header()
                if config['host'] and config['user'] and config['password']:
                    send_report(config)
                else:
                    print(f"{Colors.FAIL}❌ Configuración SMTP incompleta{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '8':
                print(f"\n{Colors.OKGREEN}¡Hasta luego!{Colors.ENDC}\n")
                break
            
            else:
                print(f"{Colors.FAIL}❌ Opción inválida{Colors.ENDC}")
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.OKGREEN}¡Hasta luego!{Colors.ENDC}\n")
            break
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")

if __name__ == "__main__":
    main()
