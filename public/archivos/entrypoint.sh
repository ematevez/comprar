#!/bin/bash
# ============================================
# entrypoint.sh
# Script de inicio del contenedor
# ============================================
set -e

echo "============================================"
echo "🚀 Iniciando Dashboard de Licitaciones"
echo "============================================"

# Crear directorios necesarios
mkdir -p /app/data /app/logs

# Configurar cron para reporte diario
if [ -n "$EMAIL_REPORT_HOUR" ]; then
    echo "0 $EMAIL_REPORT_HOUR * * * cd /app && python enviar_reporte_email.py >> /app/logs/cron_email.log 2>&1" > /etc/cron.d/email_report
    chmod 0644 /etc/cron.d/email_report
    crontab /etc/cron.d/email_report
    cron
    echo "✅ Cron configurado: reporte email a las ${EMAIL_REPORT_HOUR}:00"
fi

# Iniciar bot de Telegram en background
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✅ Iniciando bot de Telegram..."
    python telegram_bot.py &
fi

# Iniciar servidor principal
echo "📍 Dashboard disponible en http://0.0.0.0:8765"
exec python servidor_dashboard.py
