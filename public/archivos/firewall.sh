#!/bin/bash
# ============================================
# firewall.sh - Configuración de firewall
# Ejecutar como root en el servidor host
# ============================================

echo "🔒 Configurando firewall..."

# Instalar UFW si no está
apt-get install -y ufw

# Resetear reglas
ufw --force reset

# Configurar defaults
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH (¡IMPORTANTE! Hacer antes de bloquear todo)
ufw allow 22/tcp comment 'SSH'

# Permitir HTTP/HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Permitir el puerto del dashboard SOLO desde red local (opcional)
# ufw allow from 192.168.1.0/24 to any port 8765 comment 'Dashboard LAN'

# NO exponer el puerto 8765 directamente (va por nginx)
# ufw deny 8765/tcp

# Activar firewall
ufw --force enable

echo "✅ Firewall configurado"
echo "📋 Estado:"
ufw status verbose
