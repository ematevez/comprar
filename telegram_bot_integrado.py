"""
telegram_bot_integrado.py
Bot de Telegram integrado en el servidor con menú interactivo.
"""
import os
import json
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# Configuración
TELEGRAM_CONFIG_FILE = "data/telegram_config.json"

def cargar_telegram_config():
    """Carga la configuración de Telegram."""
    if os.path.exists(TELEGRAM_CONFIG_FILE):
        with open(TELEGRAM_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"bot_token": "", "chat_ids": [], "activo": False}

def cargar_procesos():
    """Carga los procesos del Excel."""
    try:
        df = pd.read_excel('procesos_armada.xlsx')
        return df.to_dict('records')
    except:
        return []

def calcular_dias(proc):
    """Calcula días hasta la apertura."""
    fecha_str = proc.get('Fecha acto de apertura', '')
    if not fecha_str or pd.isna(fecha_str):
        return None
    try:
        for fmt in ('%d/%m/%Y %H:%M Hrs.', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
            try:
                fecha = datetime.strptime(str(fecha_str).strip(), fmt)
                return (fecha - datetime.now()).days
            except:
                continue
    except:
        return None

def get_clase(proc):
    """Determina la clase/urgencia del proceso."""
    dias = calcular_dias(proc)
    estado = proc.get('Estado gestión', 'ACTIVA')
    
    if estado == 'DESCARTADA':
        return 'descartada', 'DESCARTADA'
    elif dias is None:
        return 'sin-fecha', 'Sin fecha'
    elif dias <= 0:
        return 'vencido', 'VENCIDO'
    elif dias <= 3:
        return 'urgente', f'🔴 {dias} días'
    elif dias <= 14:
        return 'seguimiento', f'🟡 {dias} días'
    else:
        return 'lejana', f'🟢 {dias} días'


def detectar_palabras_clave(proc):
    """Detecta palabras clave importantes en un proceso."""
    palabras_clave = []
    
    if proc.get('PDF - FONDEF'):
        palabras_clave.append('FONDEF')
    if proc.get('PDF - Menciona 6.8.7') == 'Sí':
        palabras_clave.append('6.8.7')
    if proc.get('PDF - Menciona 6.8.2') == 'Sí':
        palabras_clave.append('6.8.2')
    
    return palabras_clave

# ============================================
# COMANDOS DEL BOT
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú principal del bot."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Estadísticas", callback_data='stats'),
            InlineKeyboardButton("📋 Ver Procesos", callback_data='listar')
        ],
        [
            InlineKeyboardButton("⭐ Favoritos", callback_data='favoritos'),
            InlineKeyboardButton("🔴 Urgentes", callback_data='urgentes')
        ],
        [
            InlineKeyboardButton("🟡 Seguimiento", callback_data='seguimiento'),
            InlineKeyboardButton("🟢 Lejanos", callback_data='lejanos')
        ],
        [
            InlineKeyboardButton("⚫ Vencidos", callback_data='vencidos'),
            InlineKeyboardButton("🗑️ Limpiar", callback_data='limpiar')
        ],
        [
            InlineKeyboardButton("🔄 Actualizar", callback_data='refresh'),
            InlineKeyboardButton("❓ Ayuda", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *Dashboard de Licitaciones*\n\n"
        "Seleccioná una opción:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los clicks en los botones inline."""
    query = update.callback_query
    await query.answer()
    
    procesos = cargar_procesos()
    
    if query.data == 'stats':
        await mostrar_estadisticas(query, procesos)
    elif query.data == 'listar':
        await listar_procesos(query, procesos, 'todos')
    elif query.data == 'urgentes':
        await listar_procesos(query, procesos, 'urgente')
    elif query.data == 'seguimiento':
        await listar_procesos(query, procesos, 'seguimiento')
    elif query.data == 'lejanos':
        await listar_procesos(query, procesos, 'lejana')
    elif query.data == 'vencidos':
        await listar_procesos(query, procesos, 'vencido')
    elif query.data == 'refresh':
        await query.edit_message_text("✅ Dashboard actualizado\n\nSeleccioná una opción:")
        await start(update, context)
    elif query.data == 'help':
        await mostrar_ayuda(query)
    elif query.data == 'limpiar':
        await limpiar_vencidos(query)
    elif query.data == 'favoritos':
        await mostrar_favoritos(query, procesos)
    elif query.data.startswith('detalle_'):
        numero = query.data.replace('detalle_', '')
        await mostrar_detalle(query, procesos, numero)
    elif query.data.startswith('seguimiento_'):
        numero = query.data.replace('seguimiento_', '')
        await marcar_seguimiento_telegram(query, numero)
    elif query.data.startswith('descartar_'):
        numero = query.data.replace('descartar_', '')
        await descartar_telegram(query, numero)
    elif query.data.startswith('favorito_'):
        numero = query.data.replace('favorito_', '')
        await toggle_favorito_telegram(query, numero)

async def mostrar_estadisticas(query, procesos):
    """Muestra estadísticas generales."""
    total = len(procesos)
    urgentes = len([p for p in procesos if get_clase(p)[0] == 'urgente'])
    seguimiento = len([p for p in procesos if get_clase(p)[0] == 'seguimiento'])
    lejanos = len([p for p in procesos if get_clase(p)[0] == 'lejana'])
    vencidos = len([p for p in procesos if get_clase(p)[0] == 'vencido'])
    descartados = len([p for p in procesos if p.get('Estado gestión') == 'DESCARTADA'])
    
    keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        f"📊 *Estadísticas de Procesos*\n\n"
        f"📈 *Total:* {total} procesos\n\n"
        f"🔴 *Urgentes (≤3 días):* {urgentes}\n"
        f"🟡 *Seguimiento (4-14 días):* {seguimiento}\n"
        f"🟢 *Lejanos (>14 días):* {lejanos}\n"
        f"⚫ *Vencidos:* {vencidos}\n"
        f"⚪ *Descartados:* {descartados}\n\n"
        f"🕐 *Actualizado:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    
    await query.edit_message_text(texto, parse_mode='Markdown', reply_markup=reply_markup)

async def listar_procesos(query, procesos, filtro):
    """Lista los procesos según el filtro."""
    # Filtrar procesos
    if filtro == 'todos':
        filtrados = [p for p in procesos if p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA']
        titulo = "📋 Todos los Procesos"
    elif filtro == 'urgente':
        filtrados = [p for p in procesos if get_clase(p)[0] == 'urgente']
        titulo = "🔴 Procesos Urgentes"
    elif filtro == 'seguimiento':
        filtrados = [p for p in procesos if get_clase(p)[0] == 'seguimiento']
        titulo = "🟡 Procesos en Seguimiento"
    elif filtro == 'lejanos':
        filtrados = [p for p in procesos if get_clase(p)[0] == 'lejana']
        titulo = "🟢 Procesos Lejanos"
    elif filtro == 'vencido':
        filtrados = [p for p in procesos if get_clase(p)[0] == 'vencido']
        titulo = "⚫ Procesos Vencidos"
    else:
        filtrados = procesos
        titulo = "📋 Procesos"
    
    if not filtrados:
        texto = f"{titulo}\n\nNo hay procesos en esta categoría."
        keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(texto, reply_markup=reply_markup)
        return
    
    # Mostrar primeros 10 procesos
    texto = f"{titulo}\n\n"
    
    for i, proc in enumerate(filtrados[:10], 1):
        numero = proc.get('Número de proceso', 'N/A')
        objeto = proc.get('Nombre de proceso', 'Sin descripción')[:60]
        fecha = proc.get('Fecha acto de apertura', 'Sin fecha')
        clase, etiqueta = get_clase(proc)
        
        texto += f"*{i}.* `{numero}` {etiqueta}\n"
        texto += f"   📝 {objeto}\n"
        texto += f"   📅 {fecha}\n\n"
    
    if len(filtrados) > 10:
        texto += f"_... y {len(filtrados) - 10} más_\n\n"
    
    # Botones de navegación
    keyboard = []
    
    # Botones para ver detalles de cada proceso
    for proc in filtrados[:5]:
        numero = proc.get('Número de proceso', 'N/A')
        keyboard.append([InlineKeyboardButton(
            f"🔍 Ver {numero[:20]}",
            callback_data=f'detalle_{numero}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(texto, parse_mode='Markdown', reply_markup=reply_markup)

async def mostrar_detalle(query, procesos, numero):
    """Muestra el detalle completo de un proceso."""
    proc = next((p for p in procesos if p.get('Número de proceso') == numero), None)
    
    if not proc:
        await query.edit_message_text("❌ Proceso no encontrado")
        return
    
    clase, etiqueta = get_clase(proc)
    palabras_clave = detectar_palabras_clave(proc)
    
    texto = f"📋 *Detalle del Proceso*\n\n"
    texto += f"*Número:* `{numero}`\n"
    texto += f"*Estado:* {etiqueta}\n\n"
    
    # Mostrar palabras clave destacadas si existen
    if palabras_clave:
        texto += f"⭐ *PALABRAS CLAVE DESTACADAS:*\n"
        for pc in palabras_clave:
            texto += f"   🔸 *{pc}*\n"
        texto += "\n"
    
    texto += f"*📝 Objeto:*\n"
    texto += f"{proc.get('Nombre de proceso', 'Sin descripción')}\n\n"
    
    texto += f"*📅 Fechas:*\n"
    texto += f"• Publicación: {proc.get('Fecha publicación portal', 'N/A')}\n"
    texto += f"• Apertura: {proc.get('Fecha acto de apertura', 'N/A')}\n\n"
    
    texto += f"*🏢 Organismo:*\n"
    texto += f"{proc.get('Organismo', 'N/A')}\n\n"
    
    if proc.get('Unidad Ejecutora'):
        texto += f"*📍 Unidad:*\n"
        texto += f"{proc.get('Unidad Ejecutora')}\n\n"
    
    dias = calcular_dias(proc)
    if dias is not None:
        if dias > 0:
            texto += f"⏳ *Días restantes:* {dias}\n"
        else:
            texto += f"⚠️ *VENCIDO* hace {abs(dias)} días\n"
    
    # Botones de acción
    keyboard = [
        [
            InlineKeyboardButton("⭐ Favorito", callback_data=f'favorito_{numero}'),
            InlineKeyboardButton("📌 Seguimiento", callback_data=f'seguimiento_{numero}')
        ],
        [
            InlineKeyboardButton("❌ Descartar", callback_data=f'descartar_{numero}')
        ],
        [InlineKeyboardButton("🔙 Volver a la lista", callback_data='listar')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(texto, parse_mode='Markdown', reply_markup=reply_markup)

async def mostrar_ayuda(query):
    """Muestra la ayuda del bot."""
    texto = (
        "❓ *Ayuda del Bot*\n\n"
        "*Comandos disponibles:*\n"
        "/start - Menú principal\n"
        "/stats - Estadísticas\n"
        "/listar - Ver todos los procesos\n"
        "/urgentes - Solo urgentes\n"
        "/seguimiento - Solo seguimiento\n"
        "/lejanos - Solo lejanos\n"
        "/vencidos - Solo vencidos\n\n"
        "*Botones interactivos:*\n"
        "• Usá los botones para navegar\n"
        "• Tocá un proceso para ver detalles\n"
        "• 📌 Marcar Seguimiento - Marcar para seguimiento\n"
        "• ❌ Descartar - Descartar proceso\n"
        "• 🗑️ Limpiar Vencidos - Borrar carpetas >15 días\n"
        "• Volvé al menú en cualquier momento\n\n"
        "🕐 Los datos se actualizan automáticamente cada 24hs\n"
        "🗑️ Las carpetas de vencidos se borran automáticamente después de 15 días"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Limpiar Vencidos", callback_data='limpiar')],
        [InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(texto, parse_mode='Markdown', reply_markup=reply_markup)


async def marcar_seguimiento_telegram(query, numero):
    """Marca un proceso como en seguimiento desde Telegram."""
    from generar_dashboard import marcar_seguimiento
    
    resultado = marcar_seguimiento(numero, "Marcado desde Telegram")
    
    if resultado.get('ok'):
        await query.edit_message_text(
            f"✅ Proceso `{numero}` marcado como EN SEGUIMIENTO\n\n"
            f"📅 Fecha: {resultado.get('fecha_seguimiento', 'N/A')}\n\n"
            f"La carpeta se mantiene intacta para seguimiento.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )
    else:
        await query.edit_message_text(
            f"❌ Error: {resultado.get('error', 'Error desconocido')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )


async def descartar_telegram(query, numero):
    """Descarta un proceso desde Telegram."""
    from generar_dashboard import descartar_proceso
    
    resultado = descartar_proceso(numero, "Descartado desde Telegram")
    
    if resultado.get('ok'):
        carpeta_msg = "✅ Carpeta eliminada" if resultado.get('carpeta_borrada') else "ℹ️ No había carpeta"
        await query.edit_message_text(
            f"❌ Proceso `{numero}` DESCARTADO\n\n"
            f"{carpeta_msg}\n"
            f"📅 Fecha: {resultado.get('fecha_descarte', 'N/A')}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )
    else:
        await query.edit_message_text(
            f"❌ Error: {resultado.get('error', 'Error desconocido')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )


async def toggle_favorito_telegram(query, numero):
    """Agrega o quita un proceso de favoritos desde Telegram."""
    from generar_dashboard import agregar_favorito, quitar_favorito, cargar_favoritos
    
    favoritos = cargar_favoritos().get('favoritos', [])
    
    if numero in favoritos:
        # Quitar de favoritos
        resultado = quitar_favorito(numero)
        if resultado.get('ok'):
            await query.edit_message_text(
                f"☆ Proceso `{numero}` quitado de favoritos",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
            )
        else:
            await query.edit_message_text(f"❌ Error: {resultado.get('error', 'Error desconocido')}")
    else:
        # Agregar a favoritos
        resultado = agregar_favorito(numero)
        if resultado.get('ok'):
            await query.edit_message_text(
                f"⭐ Proceso `{numero}` agregado a favoritos",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
            )
        else:
            await query.edit_message_text(f"❌ Error: {resultado.get('error', 'Error desconocido')}")


async def mostrar_favoritos(query, procesos):
    """Muestra la lista de procesos favoritos."""
    from generar_dashboard import cargar_favoritos
    
    favoritos_nums = cargar_favoritos().get('favoritos', [])
    
    if not favoritos_nums:
        await query.edit_message_text(
            "⭐ *No hay procesos favoritos*\n\n"
            "Marcá procesos como favoritos desde el detalle de cada proceso.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )
        return
    
    # Filtrar procesos favoritos
    favoritos = [p for p in procesos if p.get('Número de proceso') in favoritos_nums]
    
    texto = f"⭐ *Procesos Favoritos* ({len(favoritos)})\n\n"
    
    for proc in favoritos[:10]:
        numero = proc.get('Número de proceso', 'N/A')
        objeto = proc.get('Nombre de proceso', 'Sin descripción')[:50]
        palabras_clave = detectar_palabras_clave(proc)
        dias = calcular_dias(proc)
        
        texto += f"⭐ `{numero}`\n"
        texto += f"   📝 {objeto}\n"
        
        if palabras_clave:
            texto += f"   🏷️ Palabras clave: *{', '.join(palabras_clave)}*\n"
        
        if dias is not None:
            if dias > 0:
                texto += f"   ⏳ {dias} días restantes\n"
            else:
                texto += f"   ⚠️ VENCIDO hace {abs(dias)} días\n"
        
        texto += "\n"
    
    if len(favoritos) > 10:
        texto += f"_... y {len(favoritos) - 10} más_\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(texto, parse_mode='Markdown', reply_markup=reply_markup)


async def limpiar_vencidos(query):
    """Limpia carpetas de procesos vencidos hace más de 15 días."""
    from generar_dashboard import limpiar_procesos_vencidos
    
    await query.edit_message_text("🗑️ Limpiando carpetas de procesos vencidos (>15 días)...")
    
    resultado = limpiar_procesos_vencidos(15)
    
    if resultado.get('ok'):
        limpiados = resultado.get('limpiados', 0)
        numeros = resultado.get('numeros', [])
        
        if limpiados > 0:
            texto = f"✅ *Limpieza completada*\n\n"
            texto += f"🗑️ {limpiados} carpeta(s) eliminada(s):\n\n"
            for num in numeros[:10]:
                texto += f"• `{num}`\n"
            if len(numeros) > 10:
                texto += f"\n_... y {len(numeros) - 10} más_"
        else:
            texto = "✅ No hay carpetas para limpiar\n\nNo hay procesos vencidos hace más de 15 días."
        
        await query.edit_message_text(
            texto,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )
    else:
        await query.edit_message_text(
            f"❌ Error en limpieza: {resultado.get('error', 'Error desconocido')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver al menú", callback_data='menu')]])
        )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vuelve al menú principal."""
    query = update.callback_query
    await query.answer()
    await start(update, context)

# ============================================
# COMANDOS DIRECTOS
# ============================================

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats directo."""
    procesos = cargar_procesos()
    total = len(procesos)
    urgentes = len([p for p in procesos if get_clase(p)[0] == 'urgente'])
    
    await update.message.reply_text(
        f"📊 *Estadísticas*\n\n"
        f"Total: {total} procesos\n"
        f"🔴 Urgentes: {urgentes}\n\n"
        f"Usá /start para el menú completo",
        parse_mode='Markdown'
    )

async def cmd_listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /listar directo."""
    procesos = cargar_procesos()
    texto = "📋 *Próximos 10 procesos:*\n\n"
    
    for i, proc in enumerate(procesos[:10], 1):
        numero = proc.get('Número de proceso', 'N/A')
        objeto = proc.get('Nombre de proceso', 'Sin descripción')[:50]
        fecha = proc.get('Fecha acto de apertura', 'Sin fecha')
        clase, etiqueta = get_clase(proc)
        
        texto += f"{i}. `{numero}` {etiqueta}\n"
        texto += f"   {objeto}\n"
        texto += f"   📅 {fecha}\n\n"
    
    await update.message.reply_text(texto, parse_mode='Markdown')

async def cmd_urgentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /urgentes directo."""
    procesos = cargar_procesos()
    urgentes = [p for p in procesos if get_clase(p)[0] == 'urgente']
    
    if not urgentes:
        await update.message.reply_text("✅ No hay procesos urgentes")
        return
    
    texto = "🔴 *Procesos Urgentes:*\n\n"
    for proc in urgentes[:10]:
        numero = proc.get('Número de proceso', 'N/A')
        dias = calcular_dias(proc)
        objeto = proc.get('Nombre de proceso', 'Sin descripción')[:50]
        
        texto += f"• `{numero}` - {dias} días\n"
        texto += f"  _{objeto}_\n\n"
    
    await update.message.reply_text(texto, parse_mode='Markdown')

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def iniciar_bot():
    """Inicia el bot de Telegram."""
    import asyncio
    
    config = cargar_telegram_config()
    
    if not config.get('bot_token'):
        print("⚠️  Bot de Telegram no configurado")
        return None
    
    try:
        # Crear un nuevo event loop para este thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        app = Application.builder().token(config['bot_token']).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stats", cmd_stats))
        app.add_handler(CommandHandler("listar", cmd_listar))
        app.add_handler(CommandHandler("urgentes", cmd_urgentes))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(CallbackQueryHandler(menu_callback, pattern='^menu$'))
        
        print("✅ Bot de Telegram iniciado")
        print("   Enviá /start al bot para ver el menú")
        
        # Iniciar polling con el event loop
        async def run_bot():
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            # Mantener el bot corriendo
            while True:
                await asyncio.sleep(3600)
        
        loop.run_until_complete(run_bot())
        
    except Exception as e:
        print(f"❌ Error iniciando bot: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    iniciar_bot()
