# ============================================
# Dockerfile
# Imagen para el servidor de licitaciones
# ============================================
FROM python:3.11-slim

# Instalar dependencias del sistema para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero (cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright con Chromium
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar el resto del código
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/data /app/logs /app/detalle_procesos

# Exponer puerto del dashboard
EXPOSE 8765

# Script de entrada
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
