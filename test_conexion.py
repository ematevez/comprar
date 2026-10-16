#!/usr/bin/env python3
"""
test_conexion.py
Prueba diferentes aspectos de la conexión SMTP y sugiere soluciones.
"""
import os
import sys
import socket
import subprocess
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("  🔌 DIAGNÓSTICO DE CONEXIÓN SMTP")
print("=" * 70)
print()

# 1. Verificar conectividad básica a internet
print("🌐 1. Probando conectividad a internet...")
try:
    socket.create_connection(("8.8.8.8", 53), timeout=5)
    print("   ✅ Internet funciona")
except Exception as e:
    print(f"   ❌ No hay conexión a internet: {e}")
    print("   💡 Verificá tu conexión WiFi/Ethernet")
    sys.exit(1)

print()

# 2. Probar resolución DNS
print("🔍 2. Probando resolución DNS de smtp.gmail.com...")
try:
    ip = socket.gethostbyname("smtp.gmail.com")
    print(f"   ✅ DNS resuelto: smtp.gmail.com -> {ip}")
except Exception as e:
    print(f"   ❌ No se puede resolver DNS: {e}")
    print("   💡 Posible problema de DNS o firewall")
    sys.exit(1)

print()

# 3. Probar conexión al puerto 587 (TLS)
print("📡 3. Probando conexión a smtp.gmail.com:587 (TLS)...")
try:
    sock = socket.create_connection(("smtp.gmail.com", 587), timeout=10)
    sock.close()
    print("   ✅ Puerto 587 accesible")
except socket.timeout:
    print("   ❌ TIMEOUT: No se puede conectar al puerto 587")
    print()
    print("   💡 POSIBLES CAUSAS:")
    print("      1. Firewall de Windows bloqueando Python")
    print("      2. Firewall del router bloqueando el puerto 587")
    print("      3. Proxy corporativo bloqueando SMTP")
    print("      4. Antivirus bloqueando la conexión")
    print()
    print("   🔧 SOLUCIONES:")
    print("      A) Agregar excepción en Firewall de Windows:")
    print("         - Panel de Control > Firewall de Windows")
    print("         - Permitir una aplicación > Agregar Python")
    print()
    print("      B) Probar con otro puerto (465 SSL):")
    print("         Cambiá en .env: SMTP_PORT=465")
    print()
    print("      C) Usar otro proveedor SMTP:")
    print("         - Outlook: smtp-mail.outlook.com:587")
    print("         - Yahoo: smtp.mail.yahoo.com:587")
    print("         - SendGrid, Mailgun, etc.")
    print()
    print("      D) Si estás en red corporativa:")
    print("         - Contactá al administrador de red")
    print("         - Pedí que permitan SMTP en puerto 587")
    print("         - O usá un relay SMTP interno")
    
except ConnectionRefusedError:
    print("   ❌ CONEXIÓN RECHAZADA")
    print("   💡 El servidor SMTP está rechazando conexiones")
    print("   💡 Posible problema de configuración o firewall")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# 4. Probar puerto 465 (SSL)
print("📡 4. Probando conexión a smtp.gmail.com:465 (SSL)...")
try:
    sock = socket.create_connection(("smtp.gmail.com", 465), timeout=10)
    sock.close()
    print("   ✅ Puerto 465 accesible")
    print("   💡 Podés usar SMTP_PORT=465 en .env")
except socket.timeout:
    print("   ❌ TIMEOUT en puerto 465 también")
    print("   💡 Parece que los puertos SMTP están bloqueados")
except Exception as e:
    print(f"   ❌ Error en puerto 465: {e}")

print()

# 5. Probar ping (puede estar bloqueado pero útil)
print("🏓 5. Probando ping a smtp.gmail.com...")
try:
    result = subprocess.run(
        ["ping", "-n", "2", "smtp.gmail.com"],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        print("   ✅ Ping funciona")
    else:
        print("   ⚠️  Ping bloqueado (normal en muchas redes)")
except Exception as e:
    print(f"   ⚠️  No se pudo hacer ping: {e}")

print()

# 6. Verificar firewall de Windows
print("🔥 6. Verificando reglas del Firewall de Windows...")
try:
    result = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", "name=all", "dir=out"],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    # Buscar reglas que bloqueen Python o SMTP
    if "python" in result.stdout.lower():
        print("   ⚠️  Hay reglas de firewall que mencionan Python")
        print("   💡 Verificá que Python no esté bloqueado")
    else:
        print("   ℹ️  No se encontraron reglas específicas para Python")
        
except Exception as e:
    print(f"   ⚠️  No se pudo verificar el firewall: {e}")

print()

# 7. Sugerencias finales
print("=" * 70)
print("💡 RECOMENDACIONES:")
print("=" * 70)
print()
print("1. SI ESTÁS EN RED CORPORATIVA:")
print("   - Contactá al administrador de TI")
print("   - Pedí que permitan SMTP saliente en puerto 587")
print("   - O usá un relay SMTP interno de la empresa")
print()
print("2. SI ESTÁS EN RED DOMÉSTICA:")
print("   - Verificá el firewall del router")
print("   - Probá conectar desde otra red (ej: celular con datos)")
print("   - Desactivá temporalmente el antivirus")
print()
print("3. ALTERNATIVAS:")
print("   - Usá otro proveedor SMTP (Outlook, Yahoo, SendGrid)")
print("   - Usá un servicio de email transaccional (Mailgun, SendGrid)")
print("   - Configurá un relay SMTP local")
print()
print("4. PARA PROBAR RÁPIDO:")
print("   - Conectá desde otra red (celular, otra WiFi)")
print("   - Si funciona ahí, el problema es tu red actual")
print()
print("=" * 70)
