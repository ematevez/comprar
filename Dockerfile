# ============================================
# Dockerfile
# Imagen para el servidor de licitaciones
# ============================================
# Usamos imagen oficial de Playwright que YA incluye Chromium
# Esto evita tener que descargarlo (tu firewall lo bloquea)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Instalar dependencias adicionales del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero (cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright y Chromium ya vienen instalados en la imagen base
# No necesitamos ejecutar playwright install

# Copiar el resto del código
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/data /app/logs /app/detalle_procesos

# Exponer puerto del dashboard
EXPOSE 8765

# Script de entrada (se copia al final para no invalidar la caché de COPY . .)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
