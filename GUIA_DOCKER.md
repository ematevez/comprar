# 🐳 Guía Completa de Dockerización

## 📋 Requisitos Previos

### 1. Instalar Docker

**Windows:**
- Descargar Docker Desktop: https://www.docker.com/products/docker-desktop/
- Instalar y reiniciar la PC
- Verificar: `docker --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

**Mac:**
- Descargar Docker Desktop: https://www.docker.com/products/docker-desktop/
- Instalar y abrir la aplicación

### 2. Verificar Instalación

```bash
docker --version
docker-compose --version
```

---

## 🚀 Instalación Rápida (Paso a Paso)

### Paso 1: Copiar Archivos Docker

```bash
cd ~/Desktop/Codigos/comprar

# Copiar todos los archivos Docker
cp public/archivos/Dockerfile .
cp public/archivos/docker-compose.yml .
cp public/archivos/entrypoint.sh .
cp public/archivos/nginx.conf .
cp public/archivos/.dockerignore .
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar el .env si no lo tenés
cp .env.example .env

# Editar el .env con tus credenciales
nano .env  # o notepad .env en Windows
```

**Variables obligatorias:**
```env
# Credenciales comprar.gob.ar
CUIT=25418019
PASSWORD=tu_password_aqui

# Email (para reportes automáticos)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_app_password
EMAIL_FROM=tu_email@gmail.com
EMAIL_TO=destinatario1@gmail.com,destinatario2@gmail.com
EMAIL_REPORT_HOUR=20

# Telegram
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_IDS=123456789,987654321

# Seguridad
ADMIN_USER=admin
ADMIN_PASS=tu_password_segura
SECRET_KEY=clave_secreta_larga
PUERTO=8765
```

### Paso 3: Crear Archivos Iniciales

```bash
# Crear archivos JSON vacíos si no existen
echo '{"notas": []}' > notas_mejoras.json
echo '{"procesos": {}}' > estado_procesos.json
echo '{"codigos": []}' > codigos_renovacion.json

# Crear directorios
mkdir -p data logs detalle_procesos
```

### Paso 4: Construir y Levantar Contenedores

```bash
# Construir la imagen (primera vez, tarda 5-10 minutos)
docker-compose build

# Levantar los contenedores
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

### Paso 5: Verificar que Funciona

```bash
# Ver estado de los contenedores
docker-compose ps

# Deberías ver:
# comprar_app      Up (healthy)
# comprar_nginx    Up
```

Abrir navegador: **http://localhost:8765**

---

## 📂 Estructura de Archivos Docker

```
comprar/
├── Dockerfile              # Define la imagen del contenedor
├── docker-compose.yml      # Orquesta los servicios
├── entrypoint.sh           # Script de inicio
├── nginx.conf              # Configuración del reverse proxy
├── .dockerignore           # Archivos a ignorar en Docker
├── .env                    # Variables de entorno (NO subir a Git)
│
├── data/                   # Datos persistentes (emails, telegram, favoritos)
├── logs/                   # Logs del sistema
├── detalle_procesos/       # PDFs descargados
│
└── (tus archivos .py)
```

---

## 🔧 Comandos Útiles de Docker

### Ver Estado

```bash
# Ver contenedores activos
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs solo de la app
docker-compose logs -f app

# Ver uso de recursos
docker stats
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo la app
docker-compose restart app

# Detener todo
docker-compose down

# Detener y eliminar volúmenes (¡cuidado!)
docker-compose down -v
```

### Ejecutar Comandos Dentro del Contenedor

```bash
# Entrar a la terminal del contenedor
docker-compose exec app bash

# Ejecutar un comando específico
docker-compose exec app python comprar.py

# Ver archivos dentro del contenedor
docker-compose exec app ls -la /app

# Copiar archivos desde/hacia el contenedor
docker cp comprar_app:/app/procesos_armada.xlsx ./backup.xlsx
docker cp ./archivo.xlsx comprar_app:/app/
```

### Actualizar Código

```bash
# Después de modificar archivos .py
docker-compose restart app

# O si cambiaste el Dockerfile/requirements.txt
docker-compose build
docker-compose up -d
```

---

## 📊 Acceso al Dashboard

### Local (misma PC)
```
http://localhost:8765
```

### Desde otra PC en la red
```
http://TU_IP:8765
```

Para saber tu IP:
- **Windows:** `ipconfig` (buscá "IPv4")
- **Linux/Mac:** `ifconfig` o `ip addr`

### Con Nginx (puerto 80)
```
http://localhost
http://TU_IP
```

---

## 🗄️ Persistencia de Datos

Los siguientes datos se mantienen aunque reinicies los contenedores:

- ✅ `procesos_armada.xlsx` - Lista de procesos
- ✅ `registro_gestion.xlsx` - Registro de decisiones
- ✅ `cronograma_procesos.xlsx` - Cronograma
- ✅ `estado_procesos.json` - Estado actual
- ✅ `notas_mejoras.json` - Notas del dashboard
- ✅ `detalle_procesos/` - PDFs descargados
- ✅ `data/` - Emails, Telegram, favoritos
- ✅ `logs/` - Logs del sistema

---

## 🐛 Troubleshooting

### Error: "Cannot connect to the Docker daemon"

**Solución:**
```bash
# Windows/Mac: Abrir Docker Desktop
# Linux:
sudo systemctl start docker
sudo systemctl enable docker
```

### Error: "Port 8765 already in use"

**Solución:**
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8766:8765"  # Cambiar 8766 por el puerto que quieras

# O matar el proceso que usa el puerto
# Windows:
netstat -ano | findstr :8765
taskkill /PID <NUMERO> /F

# Linux/Mac:
lsof -i :8765
kill -9 <PID>
```

### Error: "Permission denied" al crear archivos

**Solución:**
```bash
# Linux: Agregar usuario al grupo docker
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### El contenedor no inicia

**Solución:**
```bash
# Ver logs detallados
docker-compose logs app

# Verificar que el .env esté correcto
docker-compose exec app cat /app/.env

# Reiniciar con rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### No puedo acceder desde otra PC

**Solución:**
```bash
# Verificar que el servidor escuche en 0.0.0.0
docker-compose exec app netstat -tlnp | grep 8765

# Agregar regla en el firewall
# Windows:
netsh advfirewall firewall add rule name="Dashboard Docker" dir=in action=allow protocol=TCP localport=8765

# Linux:
sudo ufw allow 8765/tcp
```

---

## 🔄 Actualizar el Proyecto

### Si modificaste archivos .py:

```bash
# Opción 1: Reiniciar (rápido)
docker-compose restart app

# Opción 2: Rebuild (si cambiaste dependencias)
docker-compose build
docker-compose up -d
```

### Si actualizaste desde Git:

```bash
# Bajar cambios
git pull

# Reconstruir
docker-compose build
docker-compose up -d

# Ver logs
docker-compose logs -f
```

---

## 📝 Backup de Datos

### Hacer backup manual:

```bash
# Crear directorio de backup
mkdir -p backup

# Copiar archivos importantes
docker cp comprar_app:/app/procesos_armada.xlsx ./backup/
docker cp comprar_app:/app/registro_gestion.xlsx ./backup/
docker cp comprar_app:/app/data ./backup/
docker cp comprar_app:/app/detalle_procesos ./backup/
```

### Script de backup automático:

```bash
#!/bin/bash
# backup.sh

FECHA=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$FECHA"

mkdir -p $BACKUP_DIR

docker cp comprar_app:/app/procesos_armada.xlsx $BACKUP_DIR/
docker cp comprar_app:/app/registro_gestion.xlsx $BACKUP_DIR/
docker cp comprar_app:/app/cronograma_procesos.xlsx $BACKUP_DIR/
docker cp comprar_app:/app/data $BACKUP_DIR/
docker cp comprar_app:/app/notas_mejoras.json $BACKUP_DIR/

echo "✅ Backup creado: $BACKUP_DIR"
```

---

## 🎯 Resumen Rápido

### Primera vez:
```bash
cd ~/Desktop/Codigos/comprar
cp public/archivos/Dockerfile .
cp public/archivos/docker-compose.yml .
cp public/archivos/entrypoint.sh .
cp public/archivos/nginx.conf .
cp public/archivos/.dockerignore .

# Configurar .env
nano .env

# Construir y levantar
docker-compose build
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Uso diario:
```bash
# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart

# Detener
docker-compose down

# Volver a iniciar
docker-compose up -d
```

---

## 📞 Soporte

Si tenés problemas:

1. **Ver logs:** `docker-compose logs -f`
2. **Verificar .env:** `docker-compose exec app cat /app/.env`
3. **Verificar archivos:** `docker-compose exec app ls -la /app`
4. **Reiniciar:** `docker-compose restart`
5. **Rebuild completo:** `docker-compose down && docker-compose build --no-cache && docker-compose up -d`

---

## 🎉 ¡Listo!

Tu dashboard ahora está dockerizado y puede correr en cualquier sistema operativo con Docker.

**Ventajas:**
- ✅ Fácil de instalar en cualquier PC
- ✅ Aislado del sistema principal
- ✅ Fácil de actualizar
- ✅ Portable
- ✅ Producción-ready
