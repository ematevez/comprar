"""
telegram_bot.py
Bot de Telegram interactivo para monitoreo y control remoto.

Comandos disponibles:
  /start       - Bienvenida y ayuda
  /estado      - Estado actual de los procesos
  /procesos    - Lista de procesos vigentes
  /ejecutar    - Forzar ejecución del scraping
  /reporte     - Enviar reporte por email ahora
  /logs        - Últimas líneas del log
  /emails      - Ver emails configurados para reportes
  /agregar_email - Agregar email a reportes
  /quitar_email  - Quitar email de reportes
  /help        - Ayuda

Configuración:
  TELEGRAM_BOT_TOKEN - Token del bot (de @BotFather)
  TELEGRAM_CHAT_IDS  - IDs de chat autorizados (separados por coma)
"""
import os
import json
import logging
import subprocess
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURACIÓN
# ============================================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_IDS = os.environ.get("TELEGRAM_CHAT_IDS", "")
ESTADO_FILE = "estado_procesos.json"
EXCEL_FILE = "procesos_armada.xlsx"
LOG_FILE = "logs_comprar.txt"
EMAILS_FILE = "data/emails_reporte.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_allowed_chats():
    """Retorna la lista de chat IDs autorizados."""
    if not CHAT_IDS:
        return []
    return [int(cid.strip()) for cid in CHAT_IDS.split(",") if cid.strip()]


def is_authorized(chat_id) -> bool:
    """Verifica si el chat está autorizado."""
    allowed = get_allowed_chats()
    if not allowed:
        return True  # Si no hay lista, permitir todos (¡cuidado!)
    return chat_id in allowed


# ============================================
# IMPORTACIÓN DE TELEGRAM (deferred)
# ============================================
try:
    from telegram import Update, BotCommand
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.error("❌ python-telegram-bot no está instalado. Ejecutá: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False


# ============================================
# COMANDOS
# ============================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado. Tu Chat ID: " + str(update.effective_chat.id))
        return
    
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🤖 *Dashboard de Licitaciones*\n\n"
        f"Tu Chat ID: `{chat_id}`\n\n"
        f"*Comandos disponibles:*\n"
        f"/estado - Estado de procesos\n"
        f"/procesos - Lista vigentes\n"
        f"/ejecutar - Forzar scraping\n"
        f"/reporte - Enviar reporte email\n"
        f"/logs - Últimos logs\n"
        f"/emails - Ver emails reporte\n"
        f"/agregar\\_email - Agregar email\n"
        f"/quitar\\_email - Quitar email\n"
        f"/help - Esta ayuda",
        parse_mode='Markdown'
    )


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        with open(ESTADO_FILE, "r") as f:
            estado = json.load(f)
        
        ultima = estado.get("ultima_ejecucion", "Nunca")
        num_procesos = len(estado.get("procesos", {}))
        
        tiempo_str = ""
        if ultima != "Nunca":
            try:
                ultima_dt = datetime.fromisoformat(ultima)
                diff = datetime.now() - ultima_dt
                horas = diff.total_seconds() / 3600
                if horas < 1:
                    tiempo_str = f"hace {int(diff.total_seconds()/60)} min"
                else:
                    tiempo_str = f"hace {horas:.1f} horas"
            except:
                tiempo_str = ultima
        
        msg = (
            f"📊 *Estado del Sistema*\n\n"
            f"🔄 Procesos activos: *{num_procesos}*\n"
            f"⏰ Última ejecución: {tiempo_str}\n"
            f"📅 Fecha última: {ultima[:16] if ultima != 'Nunca' else 'Nunca'}\n\n"
            f"🟢 Sistema operativo"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_procesos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text("📭 No hay datos. Esperá a la primera ejecución.")
            return
        
        df = pd.read_excel(EXCEL_FILE)
        total = len(df)
        
        msg = f"📋 *Procesos Vigentes* ({total} total)\n\n"
        
        for i, (_, row) in enumerate(df.head(10).iterrows()):
            numero = row.get('Número de proceso', 'N/A')
            organismo = str(row.get('Organismo', 'N/A'))[:30]
            estado = row.get('Estado de proceso', 'N/A')
            msg += f"*{i+1}.* `{numero}`\n   {organismo}\n   Estado: {estado}\n\n"
        
        if total > 10:
            msg += f"_... y {total - 10} más. Ver dashboard para completo._"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_ejecutar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    await update.message.reply_text("🔄 Iniciando ejecución forzada... Esto puede tardar varios minutos.")
    
    try:
        env = os.environ.copy()
        env["FORZAR_EJECUCION"] = "1"
        
        result = subprocess.run(
            ["python", "comprar.py"],
            capture_output=True, text=True, timeout=600,
            env=env, cwd="/app"
        )
        
        if result.returncode == 0:
            await update.message.reply_text("✅ Ejecución completada exitosamente.")
        else:
            stderr = result.stderr[-500:] if result.stderr else "Sin detalles"
            await update.message.reply_text(f"⚠️ Ejecución terminó con warnings.\n`{stderr}`", parse_mode='Markdown')
            
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ Timeout: la ejecución tardó más de 10 minutos.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    await update.message.reply_text("📧 Enviando reporte por email...")
    
    try:
        result = subprocess.run(
            ["python", "enviar_reporte_email.py"],
            capture_output=True, text=True, timeout=60,
            cwd="/app"
        )
        
        if result.returncode == 0:
            await update.message.reply_text("✅ Reporte enviado correctamente.")
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr[-300:]}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        ultimas = lines[-15:] if len(lines) > 15 else lines
        texto = "".join(ultimas[-10:])
        msg = f"📝 *Últimos logs:*\n\n`{texto}`"
        
        if len(msg) > 4000:
            msg = msg[:4000] + "\n... (truncado)"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error leyendo logs: {e}")


async def cmd_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        emails = []
        if os.path.exists(EMAILS_FILE):
            with open(EMAILS_FILE, "r") as f:
                data = json.load(f)
            emails = data.get("emails", [])
        
        # También mostrar los del .env
        env_emails = os.environ.get("EMAIL_TO", "")
        if env_emails:
            for e in env_emails.split(","):
                e = e.strip()
                if e and e not in emails:
                    emails.append(e)
        
        if emails:
            msg = "📧 *Emails para reportes:*\n\n"
            for i, email in enumerate(emails, 1):
                msg += f"{i}. `{email}`\n"
            msg += "\nUsá /agregar\\_email o /quitar\\_email para modificar"
        else:
            msg = "📭 No hay emails configurados.\nUsá /agregar\\_email para agregar."
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_agregar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: /agregar\\_email usuario@dominio.com", parse_mode='Markdown')
        return
    
    email = context.args[0].strip()
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(EMAILS_FILE), exist_ok=True)
    
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"emails": []}
    
    if email in data["emails"]:
        await update.message.reply_text(f"⚠️ {email} ya está en la lista.")
        return
    
    data["emails"].append(email)
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    await update.message.reply_text(f"✅ {email} agregado a reportes.")


async def cmd_quitar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_chat.id):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: /quitar\\_email usuario@dominio.com", parse_mode='Markdown')
        return
    
    email = context.args[0].strip()
    
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"emails": []}
    
    if email not in data["emails"]:
        await update.message.reply_text(f"⚠️ {email} no está en la lista.")
        return
    
    data["emails"].remove(email)
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    await update.message.reply_text(f"✅ {email} eliminado de reportes.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


# ============================================
# MAIN
# ============================================
def main():
    if not TELEGRAM_AVAILABLE:
        logger.error("No se puede iniciar el bot sin python-telegram-bot")
        return
    
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN no configurado en .env")
        return
    
    logger.info("🤖 Iniciando bot de Telegram...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Registrar comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("estado", cmd_estado))
    app.add_handler(CommandHandler("procesos", cmd_procesos))
    app.add_handler(CommandHandler("ejecutar", cmd_ejecutar))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("emails", cmd_emails))
    app.add_handler(CommandHandler("agregar_email", cmd_agregar_email))
    app.add_handler(CommandHandler("quitar_email", cmd_quitar_email))
    app.add_handler(CommandHandler("help", cmd_help))
    
    # Configurar comandos en el menú del bot
    import asyncio
    
    async def setup_commands():
        commands = [
            BotCommand("estado", "Estado del sistema"),
            BotCommand("procesos", "Lista de procesos"),
            BotCommand("ejecutar", "Forzar ejecución"),
            BotCommand("reporte", "Enviar reporte email"),
            BotCommand("logs", "Ver últimos logs"),
            BotCommand("emails", "Emails configurados"),
            BotCommand("agregar_email", "Agregar email"),
            BotCommand("quitar_email", "Quitar email"),
            BotCommand("help", "Ayuda"),
        ]
        await app.bot.set_my_commands(commands)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_commands())
    
    logger.info("✅ Bot iniciado. Esperando mensajes...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
