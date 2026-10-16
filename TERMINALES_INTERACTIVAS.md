# Terminales Interactivas de Prueba

Estas terminales te permiten probar y monitorear el bot de Telegram y el sistema de emails en tiempo real.

## 🤖 Terminal de Telegram

### Ejecutar:
```bash
python telegram_test.py
```

### Opciones disponibles:
1. **Ver configuración actual** - Muestra el token y chat IDs configurados
2. **Probar conexión con Telegram API** - Verifica que el bot esté activo
3. **Ver mensajes recibidos** - Muestra los últimos mensajes que recibió el bot
4. **Enviar mensaje de prueba** - Envía un mensaje simple a los chat IDs
5. **Enviar reporte completo** - Envía un reporte con estadísticas y procesos
6. **Monitorear mensajes en tiempo real** - Muestra mensajes a medida que llegan (Ctrl+C para salir)

### Ejemplo de uso:
```bash
# Ver si alguien te escribió al bot
python telegram_test.py
# Opción 3: Ver mensajes recibidos

# Monitorear en tiempo real
python telegram_test.py
# Opción 6: Monitorear mensajes en tiempo real
```

## 📧 Terminal de Email

### Ejecutar:
```bash
python email_test.py
```

### Opciones disponibles:
1. **Ver configuración SMTP actual** - Muestra los datos del servidor SMTP
2. **Probar conexión con servidor SMTP** - Verifica que puedas conectarte
3. **Ver lista de destinatarios** - Muestra los emails configurados
4. **Agregar destinatario** - Agrega un nuevo email a la lista
5. **Eliminar destinatario** - Elimina un email de la lista
6. **Enviar email de prueba** - Envía un email simple a un destinatario
7. **Enviar reporte completo** - Envía un reporte con estadísticas y procesos

### Ejemplo de uso:
```bash
# Probar que el SMTP funciona
python email_test.py
# Opción 2: Probar conexión SMTP

# Ver si te llegó algo
python email_test.py
# Opción 6: Enviar email de prueba
```

## 🔧 Requisitos

### Para Telegram:
- Token del bot configurado en `.env` o `data/telegram_config.json`
- Al menos un chat ID configurado
- Conexión a internet

### Para Email:
- Configuración SMTP completa en `.env`:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USER`
  - `SMTP_PASS`
  - `EMAIL_FROM`
- Lista de destinatarios en `data/emails_reporte.json`

## 📋 Solución de problemas

### Telegram no recibe mensajes:
1. Verificá que el token sea correcto (opción 2)
2. Asegurate de haber enviado `/start` al bot en Telegram
3. Usá la opción 6 para monitorear en tiempo real

### Email no envía:
1. Verificá la configuración SMTP (opción 2)
2. Para Gmail, usá una "App Password" (no tu password normal)
3. Verificá que el puerto sea correcto (587 para TLS)

### No hay destinatarios:
1. Usá la opción 4 para agregar emails
2. O editá directamente `data/emails_reporte.json`

## 🎯 Uso recomendado

### Para verificar que todo funciona:
```bash
# 1. Probar Telegram
python telegram_test.py
# Opción 2: Probar conexión
# Opción 4: Enviar mensaje de prueba

# 2. Probar Email
python email_test.py
# Opción 2: Probar conexión SMTP
# Opción 6: Enviar email de prueba
```

### Para monitoreo continuo:
```bash
# En una terminal: Monitorear Telegram
python telegram_test.py
# Opción 6: Monitorear mensajes en tiempo real

# En otra terminal: Ver dashboard
python servidor_dashboard.py
```

## 📝 Notas

- Las terminales usan colores para mejor legibilidad
- Presioná Ctrl+C en cualquier momento para salir
- Los mensajes de Telegram se muestran con formato Markdown
- Los emails se envían en formato HTML
