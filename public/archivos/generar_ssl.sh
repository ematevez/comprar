#!/bin/bash
# ============================================
# generar_ssl.sh - Generar certificado SSL
# ============================================

# Opción 1: Certificado autofirmado (para testing)
echo "🔐 Generando certificado SSL autofirmado..."
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=AR/ST=BA/L=BuenosAires/O=Licitaciones/CN=localhost"

echo "✅ Certificados generados en ./ssl/"
echo ""
echo "Para producción, usar Let's Encrypt:"
echo "  certbot --nginx -d tu_dominio.com"

# Opción 2: Let's Encrypt (producción)
# ============================================
# Descomentar las siguientes líneas si tenés un dominio:
# 
# apt-get install certbot python3-certbot-nginx
# certbot --nginx -d tu-dominio.com
# 
# Renovación automática:
# certbot renew --dry-run
