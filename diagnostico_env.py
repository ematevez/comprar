#!/usr/bin/env python3
"""
diagnostico_env.py
Diagnostica problemas con el archivo .env y las credenciales SMTP.
"""
import os
import sys
from dotenv import load_dotenv

print("=" * 70)
print("  🔍 DIAGNÓSTICO DEL ARCHIVO .env")
print("=" * 70)
print()

# 1. Verificar si existe el archivo .env
print("📁 Verificando archivo .env...")
if os.path.exists('.env'):
    print("   ✅ Archivo .env encontrado")
    print(f"   Ubicación: {os.path.abspath('.env')}")
else:
    print("   ❌ Archivo .env NO encontrado")
    print("   💡 Solución: Copiá .env.example a .env y editá las credenciales")
    print("      cp .env.example .env")
    print("      notepad .env")
    sys.exit(1)

print()

# 2. Mostrar contenido del .env (ocultando passwords)
print("📄 Contenido del archivo .env:")
print("-" * 70)
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            print(f"   {line}")
        else:
            # Ocultar valores sensibles
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if any(sensitive in key.upper() for sensitive in ['PASS', 'SECRET', 'TOKEN', 'KEY']):
                    if value:
                        print(f"   {key}={'*' * min(len(value), 20)}")
                    else:
                        print(f"   {key}=")
                else:
                    print(f"   {key}={value}")
            else:
                print(f"   {line}")
print("-" * 70)
print()

# 3. Cargar el .env y verificar variables
print("🔧 Cargando variables de entorno...")
load_dotenv()

variables_requeridas = [
    'SMTP_HOST',
    'SMTP_PORT',
    'SMTP_USER',
    'SMTP_PASS',
    'EMAIL_FROM',
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_CHAT_IDS'
]

print()
print("📋 Variables de entorno cargadas:")
print("-" * 70)
todas_ok = True
for var in variables_requeridas:
    value = os.environ.get(var, '')
    if value:
        # Ocultar valores sensibles
        if any(sensitive in var.upper() for sensitive in ['PASS', 'SECRET', 'TOKEN', 'KEY']):
            print(f"   ✅ {var}={'*' * min(len(value), 20)}")
        else:
            print(f"   ✅ {var}={value}")
    else:
        print(f"   ❌ {var} NO CONFIGURADA")
        todas_ok = False
print("-" * 70)
print()

# 4. Diagnóstico específico
if not todas_ok:
    print("❌ PROBLEMAS DETECTADOS:")
    print()
    
    if not os.environ.get('SMTP_HOST'):
        print("   • SMTP_HOST no está configurado")
        print("     💡 Agregá en .env: SMTP_HOST=smtp.gmail.com")
    
    if not os.environ.get('SMTP_USER'):
        print("   • SMTP_USER no está configurado")
        print("     💡 Agregá en .env: SMTP_USER=tu_email@gmail.com")
    
    if not os.environ.get('SMTP_PASS'):
        print("   • SMTP_PASS no está configurado")
        print("     💡 Agregá en .env: SMTP_PASS=tu_app_password")
        print("     💡 Para Gmail, usá una App Password:")
        print("        https://myaccount.google.com/apppasswords")
    
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        print("   • TELEGRAM_BOT_TOKEN no está configurado")
        print("     💡 Agregá en .env: TELEGRAM_BOT_TOKEN=tu_token")
    
    print()
    print("💡 POSIBLES CAUSAS:")
    print("   1. El archivo .env tiene espacios alrededor del '='")
    print("      ❌ INCORRECTO: SMTP_HOST = smtp.gmail.com")
    print("      ✅ CORRECTO:   SMTP_HOST=smtp.gmail.com")
    print()
    print("   2. El archivo .env tiene comillas en los valores")
    print("      ❌ INCORRECTO: SMTP_HOST=\"smtp.gmail.com\"")
    print("      ✅ CORRECTO:   SMTP_HOST=smtp.gmail.com")
    print()
    print("   3. Hay comentarios en la misma línea que los valores")
    print("      ❌ INCORRECTO: SMTP_HOST=smtp.gmail.com # comentario")
    print("      ✅ CORRECTO:   SMTP_HOST=smtp.gmail.com")
    print()
else:
    print("✅ TODAS LAS VARIABLES ESTÁN CONFIGURADAS")
    print()
    
    # 5. Probar conexión SMTP
    print("📧 Probando conexión SMTP...")
    try:
        import smtplib
        host = os.environ.get('SMTP_HOST')
        port = int(os.environ.get('SMTP_PORT', '587'))
        user = os.environ.get('SMTP_USER')
        password = os.environ.get('SMTP_PASS')
        
        print(f"   Conectando a {host}:{port}...")
        server = smtplib.SMTP(host, port, timeout=10)
        server.starttls()
        server.login(user, password)
        print("   ✅ Conexión SMTP exitosa!")
        server.quit()
    except Exception as e:
        print(f"   ❌ Error de conexión SMTP: {e}")
        print()
        print("   💡 POSIBLES SOLUCIONES:")
        if 'Authentication' in str(e):
            print("      • Verificá que el usuario y contraseña sean correctos")
            print("      • Para Gmail, usá una App Password (no tu password normal)")
        elif 'Connection' in str(e) or 'Timeout' in str(e):
            print("      • Verificá tu conexión a internet")
            print("      • Verificá que el puerto sea correcto (587 para TLS)")
        else:
            print(f"      • Error: {e}")

print()
print("=" * 70)
