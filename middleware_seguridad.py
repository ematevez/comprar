"""
middleware_seguridad.py
Middleware de seguridad para el servidor dashboard.
Incluye: autenticación, rate limiting, bloqueo de IPs, logs de seguridad.
"""
import hashlib
import time
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
SESSION_DURATION = 3600 * 8  # 8 horas
SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esta-clave-secreta-larga")
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutos

# Almacenamiento en memoria (para producción usar Redis)
login_attempts = {}
sessions = {}
blocked_ips = {}


def verificar_ip_permitida(ip):
    """Verifica si la IP está en la lista de IPs permitidas."""
    allowed = os.environ.get("ALLOWED_IPS", "")
    if not allowed:
        return True  # Si no hay lista, permitir todas
    allowed_list = [ip.strip() for ip in allowed.split(",")]
    return ip in allowed_list


def verificar_rate_limit(ip):
    """Rate limiting por IP para prevenir fuerza bruta."""
    ahora = time.time()
    
    # Limpiar bloqueos expirados
    if ip in blocked_ips:
        if ahora - blocked_ips[ip] > LOCKOUT_DURATION:
            del blocked_ips[ip]
        else:
            return False, "IP bloqueada temporalmente. Intentá más tarde."
    
    # Verificar intentos
    if ip not in login_attempts:
        login_attempts[ip] = []
    
    # Limpiar intentos viejos (últimos 15 min)
    login_attempts[ip] = [t for t in login_attempts[ip] if ahora - t < LOCKOUT_DURATION]
    
    if len(login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
        blocked_ips[ip] = ahora
        return False, f"Demasiados intentos. IP bloqueada por {LOCKOUT_DURATION//60} min."
    
    return True, None


def registrar_intento_login(ip, exitoso=False):
    """Registra un intento de login."""
    ahora = time.time()
    if ip not in login_attempts:
        login_attempts[ip] = []
    login_attempts[ip].append(ahora)


def crear_token(username):
    """Crea un token de sesión."""
    timestamp = str(time.time())
    data = f"{username}:{timestamp}:{SECRET_KEY}"
    token = hashlib.sha256(data.encode()).hexdigest()
    sessions[token] = {
        "username": username,
        "created": time.time(),
        "expires": time.time() + SESSION_DURATION
    }
    return token


def verificar_token(token):
    """Verifica si un token es válido."""
    if token not in sessions:
        return False
    if time.time() > sessions[token]["expires"]:
        del sessions[token]
        return False
    return True


def verificar_credenciales(username, password):
    """Verifica credenciales del admin."""
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "")
    
    if not admin_pass:
        return False, "No hay password de admin configurada"
    
    if username == admin_user and password == admin_pass:
        return True, None
    return False, "Credenciales inválidas"


# ============================================
# LOG DE SEGURIDAD
# ============================================
def log_seguridad(evento, ip=None, detalle=None):
    """Registra eventos de seguridad."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"[SEGURIDAD] {timestamp} | {evento}"
    if ip:
        msg += f" | IP: {ip}"
    if detalle:
        msg += f" | {detalle}"
    print(msg)
    
    # También escribir a archivo
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/seguridad.log", "a") as f:
            f.write(msg + "\n")
    except:
        pass
