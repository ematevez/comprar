#!/usr/bin/env python3
"""
telegram_test.py
Terminal interactiva para probar el bot de Telegram y ver mensajes recibidos.
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
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
    print("  🤖 TERMINAL DE PRUEBA - BOT DE TELEGRAM")
    print("=" * 70)
    print(f"{Colors.ENDC}")

def print_menu():
    print(f"\n{Colors.OKCYAN}MENÚ DE OPCIONES:{Colors.ENDC}")
    print("1. Ver configuración actual")
    print("2. Probar conexión con Telegram API")
    print("3. Ver mensajes recibidos (últimos updates)")
    print("4. Enviar mensaje de prueba")
    print("5. Enviar reporte completo")
    print("6. Monitorear mensajes en tiempo real (Ctrl+C para salir)")
    print("7. Salir")
    print()

def get_config():
    """Carga la configuración de Telegram."""
    config_file = "data/telegram_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Si no existe, usar variables de entorno
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_ids_str = os.environ.get("TELEGRAM_CHAT_IDS", "")
    chat_ids = [int(cid.strip()) for cid in chat_ids_str.split(",") if cid.strip()]
    
    return {
        "bot_token": token,
        "chat_ids": chat_ids,
        "activo": bool(token and chat_ids)
    }

def test_connection(token):
    """Prueba la conexión con la API de Telegram."""
    print(f"\n{Colors.OKBLUE}Probando conexión con Telegram API...{Colors.ENDC}")
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"{Colors.OKGREEN}✅ Conexión exitosa!{Colors.ENDC}")
            print(f"   Nombre: {bot_info.get('first_name', 'N/A')}")
            print(f"   Username: @{bot_info.get('username', 'N/A')}")
            print(f"   ID: {bot_info.get('id', 'N/A')}")
            return True
        else:
            print(f"{Colors.FAIL}❌ Error: {data.get('description', 'Error desconocido')}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error de conexión: {e}{Colors.ENDC}")
        return False

def get_updates(token, offset=None):
    """Obtiene los últimos updates del bot."""
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        params = {'timeout': 1}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            return data.get('result', [])
        return []
    except Exception as e:
        print(f"{Colors.FAIL}Error obteniendo updates: {e}{Colors.ENDC}")
        return []

def show_updates(token):
    """Muestra los últimos mensajes recibidos."""
    print(f"\n{Colors.OKBLUE}Obteniendo últimos mensajes...{Colors.ENDC}")
    updates = get_updates(token)
    
    if not updates:
        print(f"{Colors.WARNING}⚠️  No hay mensajes recientes{Colors.ENDC}")
        print("   Enviá un mensaje al bot en Telegram y volvé a intentar")
        return
    
    print(f"\n{Colors.OKGREEN}📬 Mensajes recibidos ({len(updates)}):{Colors.ENDC}\n")
    
    for update in updates[-10:]:  # Mostrar últimos 10
        if 'message' in update:
            msg = update['message']
            chat = msg.get('chat', {})
            from_user = msg.get('from', {})
            text = msg.get('text', '[Sin texto]')
            date = datetime.fromtimestamp(msg.get('date', 0))
            
            print(f"{Colors.BOLD}De:{Colors.ENDC} {from_user.get('first_name', 'N/A')} @{from_user.get('username', 'N/A')}")
            print(f"{Colors.BOLD}Chat ID:{Colors.ENDC} {chat.get('id', 'N/A')}")
            print(f"{Colors.BOLD}Fecha:{Colors.ENDC} {date.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"{Colors.BOLD}Mensaje:{Colors.ENDC} {text}")
            print("-" * 70)

def send_test_message(token, chat_ids):
    """Envía un mensaje de prueba."""
    if not chat_ids:
        print(f"{Colors.FAIL}❌ No hay chat IDs configurados{Colors.ENDC}")
        return
    
    print(f"\n{Colors.OKBLUE}Enviando mensaje de prueba...{Colors.ENDC}")
    
    mensaje = f"""✅ *Bot de Telegram funcionando correctamente*

🕐 Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
📊 Dashboard: Activo
📧 Emails configurados: {len(os.environ.get('EMAIL_TO', '').split(','))}

Comandos disponibles:
/estado - Ver estado del sistema
/procesos - Lista de procesos
/ejecutar - Forzar ejecución
/reporte - Enviar reporte
/logs - Ver últimos logs
/help - Ayuda"""
    
    enviados = 0
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': mensaje,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)
            if response.json().get('ok'):
                enviados += 1
                print(f"{Colors.OKGREEN}✅ Mensaje enviado a {chat_id}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Error enviando a {chat_id}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}✅ {enviados} mensaje(s) enviado(s){Colors.ENDC}")

def send_report(token, chat_ids):
    """Envía un reporte completo."""
    if not chat_ids:
        print(f"{Colors.FAIL}❌ No hay chat IDs configurados{Colors.ENDC}")
        return
    
    print(f"\n{Colors.OKBLUE}Generando y enviando reporte...{Colors.ENDC}")
    
    # Cargar datos de procesos
    try:
        import pandas as pd
        df = pd.read_excel('procesos_armada.xlsx')
        procesos = df.to_dict('records')
    except:
        procesos = []
    
    if not procesos:
        print(f"{Colors.WARNING}⚠️  No hay procesos para reportar{Colors.ENDC}")
        return
    
    # Generar mensaje
    urgentes = [p for p in procesos if p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA']
    
    mensaje = f"""📊 *Reporte de Licitaciones*
🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}

📈 *Estadísticas:*
• Total: {len(procesos)} procesos
• Activos: {len([p for p in procesos if p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA'])}
• Descartados: {len([p for p in procesos if p.get('Estado gestión') == 'DESCARTADA'])}

📋 *Próximos 5 procesos:*
"""
    
    for i, proc in enumerate(procesos[:5], 1):
        numero = proc.get('Número de proceso', 'N/A')
        objeto = proc.get('Nombre de proceso', 'Sin descripción')[:50]
        mensaje += f"{i}. `{numero}`\n   _{objeto}_\n"
    
    enviados = 0
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': mensaje,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)
            if response.json().get('ok'):
                enviados += 1
        except Exception as e:
            print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
    
    print(f"{Colors.OKGREEN}✅ Reporte enviado a {enviados} chat(s){Colors.ENDC}")

def monitor_updates(token):
    """Monitorea mensajes en tiempo real."""
    print(f"\n{Colors.OKBLUE}Monitoreando mensajes en tiempo real...{Colors.ENDC}")
    print(f"{Colors.WARNING}Presioná Ctrl+C para salir{Colors.ENDC}\n")
    
    last_update_id = None
    
    try:
        while True:
            updates = get_updates(token, offset=last_update_id)
            
            for update in updates:
                if 'message' in update:
                    msg = update['message']
                    from_user = msg.get('from', {})
                    text = msg.get('text', '[Sin texto]')
                    date = datetime.fromtimestamp(msg.get('date', 0))
                    
                    print(f"{Colors.OKGREEN}[{date.strftime('%H:%M:%S')}]{Colors.ENDC} ", end='')
                    print(f"{Colors.BOLD}{from_user.get('first_name', 'N/A')}:{Colors.ENDC} {text}")
                    
                    last_update_id = update['update_id'] + 1
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.OKBLUE}Monitoreo detenido{Colors.ENDC}")

def main():
    while True:
        clear_screen()
        print_header()
        
        config = get_config()
        
        print(f"{Colors.OKCYAN}CONFIGURACIÓN ACTUAL:{Colors.ENDC}")
        print(f"   Token: {config['bot_token'][:20]}...{Colors.ENDC}" if config['bot_token'] else f"   Token: {Colors.FAIL}No configurado{Colors.ENDC}")
        print(f"   Chat IDs: {config['chat_ids'] if config['chat_ids'] else 'No configurados'}")
        print(f"   Estado: {Colors.OKGREEN}Activo{Colors.ENDC}" if config['activo'] else f"   Estado: {Colors.FAIL}Inactivo{Colors.ENDC}")
        
        print_menu()
        
        try:
            opcion = input(f"{Colors.BOLD}Seleccioná una opción (1-7): {Colors.ENDC}").strip()
            
            if opcion == '1':
                clear_screen()
                print_header()
                print(f"\n{Colors.OKCYAN}CONFIGURACIÓN DETALLADA:{Colors.ENDC}\n")
                print(json.dumps(config, indent=2, ensure_ascii=False))
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '2':
                clear_screen()
                print_header()
                if config['bot_token']:
                    test_connection(config['bot_token'])
                else:
                    print(f"{Colors.FAIL}❌ No hay token configurado{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '3':
                clear_screen()
                print_header()
                if config['bot_token']:
                    show_updates(config['bot_token'])
                else:
                    print(f"{Colors.FAIL}❌ No hay token configurado{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '4':
                clear_screen()
                print_header()
                if config['activo']:
                    send_test_message(config['bot_token'], config['chat_ids'])
                else:
                    print(f"{Colors.FAIL}❌ Bot no configurado correctamente{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '5':
                clear_screen()
                print_header()
                if config['activo']:
                    send_report(config['bot_token'], config['chat_ids'])
                else:
                    print(f"{Colors.FAIL}❌ Bot no configurado correctamente{Colors.ENDC}")
                input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '6':
                clear_screen()
                print_header()
                if config['bot_token']:
                    monitor_updates(config['bot_token'])
                else:
                    print(f"{Colors.FAIL}❌ No hay token configurado{Colors.ENDC}")
                    input(f"\n{Colors.WARNING}Presioná Enter para continuar...{Colors.ENDC}")
            
            elif opcion == '7':
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
