# Dashboard de Licitaciones - Servidor Seguro

## ⚠️ IMPORTANTE: Credenciales Expuestas

Si este repo es público y tenías credenciales hardcodeadas en `comprar.py`, **cambiá la contraseña en comprar.gob.ar AHORA MISMO**.

## 📁 Archivos Incluidos

### Archivos Python Modificados
- `comprar.py` - Versión segura (credenciales desde .env)
- `servidor_dashboard.py` - Servidor con integraciones de seguridad, email y telegram
- `enviar_reporte_email.py` - Reporte diario por email
- `telegram_bot.py` - Bot de Telegram interactivo
- `middleware_seguridad.py` - Autenticación y rate limiting
- `api_emails.py` - Gestión de emails para reportes

### Configuración
- `requirements.txt` - Dependencias Python
- `.env.example` - Plantilla de variables de entorno
- `.gitignore` - Ignorar archivos sensibles
- `Dockerfile` - Imagen del contenedor
- `docker-compose.yml` - Orquestación de servicios
- `nginx.conf` - Reverse proxy con seguridad
- `entrypoint.sh` - Script de inicio del contenedor

### Scripts de Seguridad
- `firewall.sh` - Configuración de firewall UFW
- `generar_ssl.sh` - Generar certificados SSL
- `limpiar_credenciales.sh` - Limpiar credenciales del repo

## 🚀 Instalación Rápida

### 1. Clonar el repo
```bash
git clone https://github.com/tu-usuario/comprar.git
cd comprar
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
nano .env
# Completar con tus credenciales reales
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Ejecutar (sin Docker)
```bash
python servidor_dashboard.py
```

### 5. Ejecutar (con Docker)
```bash
docker compose up -d
```

## 🔐 Seguridad

### Credenciales
- **NUNCA** subas `.env` a Git
- Las credenciales están en variables de entorno
- Cambiá la contraseña en comprar.gob.ar si estaba expuesta

### Acceso desde la red
- El servidor escucha en `0.0.0.0:8765` (accesible desde la red)
- Usá el firewall para restringir IPs
- Configurá HTTPS con Nginx para producción

### Autenticación
- Login con usuario/password (configurar en .env)
- Tokens de sesión con expiración
- Rate limiting para prevenir fuerza bruta

## 📧 Reportes por Email

### Configuración Gmail
1. Ir a https://myaccount.google.com/apppasswords
2. Activar verificación en 2 pasos
3. Generar "App Password" (16 caracteres)
4. Ponerla en `SMTP_PASS` del .env

### Enviar reporte manual
```bash
python enviar_reporte_email.py
```

### Reporte automático
Se ejecuta vía cron a la hora configurada en `EMAIL_REPORT_HOUR`

## 🤖 Bot de Telegram

### Crear el bot
1. Abrir Telegram y buscar @BotFather
2. Enviar `/newbot`
3. Copiar el token
4. Ponerlo en `TELEGRAM_BOT_TOKEN` del .env

### Obtener Chat ID
1. Enviar `/start` a tu bot
2. Visitar: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Copiar tu `chat.id`
4. Ponerlo en `TELEGRAM_CHAT_IDS` del .env

### Comandos del bot
- `/estado` - Estado del sistema
- `/procesos` - Lista de procesos
- `/ejecutar` - Forzar ejecución
- `/reporte` - Enviar reporte email
- `/logs` - Ver últimos logs
- `/emails` - Ver emails configurados
- `/agregar_email` - Agregar email
- `/quitar_email` - Quitar email

## 🐳 Docker

### Construir y ejecutar
```bash
docker compose up -d
```

### Ver logs
```bash
docker compose logs -f
```

### Detener
```bash
docker compose down
```

## 📊 Acceso al Dashboard

- Local: http://localhost:8765
- Red local: http://TU_IP:8765
- Con Nginx: http://TU_DOMINIO (puerto 80)

## 🔧 Troubleshooting

### Error de credenciales
```
❌ ERROR: Faltan variables de entorno CUIT y/o PASSWORD
```
**Solución:** Crear archivo `.env` con las credenciales

### Error de SMTP
```
❌ No hay credenciales SMTP configuradas
```
**Solución:** Configurar `SMTP_USER` y `SMTP_PASS` en .env

### Error de Telegram
```
❌ TELEGRAM_BOT_TOKEN no configurado
```
**Solución:** Configurar `TELEGRAM_BOT_TOKEN` en .env

## 📝 Notas

- El proyecto original usa `http.server` de Python (no Django)
- Las credenciales ahora están seguras en variables de entorno
- El bot de Telegram corre en background junto con el servidor
- Los reportes por email se envían automáticamente vía cron
- Todo está dockerizado para fácil despliegue

## 🆘 Soporte

Si tenés problemas:
1. Revisá los logs: `docker compose logs -f`
2. Verificá que el `.env` esté correcto
3. Asegurate de que las credenciales de comprar.gob.ar funcionen
4. Probá ejecutar manualmente: `python comprar.py`
