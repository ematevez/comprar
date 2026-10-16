"""
servidor_dashboard.py - VERSIÓN COMPATIBLE
Funciona con o sin licencia.py
Incluye: seguridades + Email + Telegram
"""
import json
import os
import sys
import time
import threading
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# ============================================
# IMPORTS - Funciones de generar_dashboard
# ============================================
from generar_dashboard import (
    generar_dashboard, 
    descartar_proceso, 
    reactivar_proceso,
    cargar_cronograma,
    ejecutar_script,
    estado_ejecucion,
    cargar_notas,
    agregar_nota,
    marcar_nota,
    eliminar_nota,
    marcar_seguimiento,
    limpiar_procesos_vencidos,
    registrar_impresion,
    resetear_datos,
    buscar_expediente_en_pdfs,
    cargar_favoritos,
    agregar_favorito,
    quitar_favorito,
    EXCEL_GESTION
)

# ============================================
# IMPORTS - Middleware de seguridad
# ============================================
from middleware_seguridad import (
    verificar_ip_permitida,
    verificar_rate_limit,
    registrar_intento_login,
    crear_token,
    verificar_token,
    verificar_credenciales,
    log_seguridad
)

# ============================================
# IMPORTS - API de emails
# ============================================
from api_emails import cargar_emails, agregar_email, eliminar_email

# ============================================
# IMPORTS - Licencia (OPCIONAL - si existe)
# ============================================
try:
    from licencia import verificar_licencia, renovar_licencia
    LICENCIA_DISPONIBLE = True
except ImportError:
    LICENCIA_DISPONIBLE = False
    # Funciones dummy si no hay licencia
    def verificar_licencia():
        return {'ok': True, 'motivo': 'Sistema sin licencia (modo libre)'}
    
    def renovar_licencia(clave):
        return {'ok': False, 'error': 'Sistema sin módulo de licencia'}

# ============================================
# Telegram config
# ============================================
TELEGRAM_CONFIG_FILE = "data/telegram_config.json"

def cargar_telegram_config():
    os.makedirs(os.path.dirname(TELEGRAM_CONFIG_FILE), exist_ok=True)
    if os.path.exists(TELEGRAM_CONFIG_FILE):
        with open(TELEGRAM_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"bot_token": "", "chat_ids": [], "activo": False}

def guardar_telegram_config(config):
    os.makedirs(os.path.dirname(TELEGRAM_CONFIG_FILE), exist_ok=True)
    config["updated"] = datetime.now().isoformat()
    with open(TELEGRAM_CONFIG_FILE, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def actualizar_telegram(token, chat_ids):
    config = {
        "bot_token": token,
        "chat_ids": [int(cid.strip()) for cid in chat_ids.split(",") if cid.strip()],
        "activo": bool(token),
    }
    guardar_telegram_config(config)
    print(f"✅ Configuración de Telegram actualizada")
    return {"ok": True, "mensaje": "Configuración de Telegram guardada"}


# Cada cuánto se FIJA si toca correr algo (en minutos)
INTERVALO_CHEQUEO_MINUTOS = 60


def scheduler_automatico():
    print(f"⏱️  Scheduler automático activo: revisa cada {INTERVALO_CHEQUEO_MINUTOS} min")
    while True:
        try:
            r1 = ejecutar_script('comprar')
            if r1.get('ok'):
                # Esperar a que termine comprar.py
                for _ in range(600):
                    time.sleep(1)
                    if not estado_ejecucion('comprar')['corriendo']:
                        break
                
                # Ejecutar detalle_proceso.py
                ejecutar_script('detalle')
                
                # Esperar a que termine detalle_proceso.py
                for _ in range(600):
                    time.sleep(1)
                    if not estado_ejecucion('detalle')['corriendo']:
                        break
                
                # Enviar notificaciones automáticas
                print("📧 Enviando notificaciones automáticas...")
                try:
                    enviar_notificaciones_automaticas()
                except Exception as e:
                    print(f"⚠️ Error enviando notificaciones: {e}")
                
                # Limpieza automática de procesos vencidos (>15 días)
                print("🗑️ Ejecutando limpieza automática de procesos vencidos...")
                try:
                    resultado_limpieza = limpiar_procesos_vencidos(15)
                    if resultado_limpieza.get('limpiados', 0) > 0:
                        print(f"✅ Limpieza completada: {resultado_limpieza['limpiados']} carpetas eliminadas")
                    else:
                        print("✅ No hay carpetas para limpiar")
                except Exception as e:
                    print(f"⚠️ Error en limpieza automática: {e}")
                    
        except Exception as e:
            print(f"⚠️ Error en el scheduler automático: {e}")
        time.sleep(INTERVALO_CHEQUEO_MINUTOS * 60)


def enviar_notificaciones_automaticas():
    """Envía email y telegram con todas las cards del dashboard después de ejecutar los scripts."""
    import pandas as pd
    from generar_dashboard import cargar_emails, cargar_telegram_config
    
    # Cargar datos de procesos
    try:
        df = pd.read_excel('procesos_armada.xlsx')
        procesos = df.to_dict('records')
    except:
        procesos = []
    
    if not procesos:
        print("⚠️ No hay procesos para enviar")
        return
    
    # Generar HTML para email
    html_email = generar_html_reporte(procesos)
    
    # Enviar email
    try:
        from enviar_reporte_email import enviar_reporte
        emails = cargar_emails().get('emails', [])
        if emails:
            enviados = enviar_reporte(emails, html_email=html_email)
            print(f"✅ Email enviado a {enviados} destinatarios")
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
    
    # Enviar telegram
    try:
        config = cargar_telegram_config()
        if config.get('activo') and config.get('bot_token') and config.get('chat_ids'):
            mensaje = generar_mensaje_telegram(procesos)
            enviados = enviar_telegram(config['bot_token'], config['chat_ids'], mensaje)
            print(f"✅ Telegram enviado a {enviados} chats")
    except Exception as e:
        print(f"❌ Error enviando telegram: {e}")


def detectar_palabras_clave(proc):
    """Detecta palabras clave importantes en el proceso."""
    palabras_clave = []
    
    # Buscar en todos los campos del proceso
    texto_completo = str(proc).lower()
    
    if 'fondef' in texto_completo:
        palabras_clave.append('FONDEF')
    if '6.8.7' in texto_completo or '6,8,7' in texto_completo:
        palabras_clave.append('6.8.7')
    if '6.8.2' in texto_completo or '6,8,2' in texto_completo:
        palabras_clave.append('6.8.2')
    
    # También verificar campos específicos
    if proc.get('PDF - FONDEF'):
        palabras_clave.append('FONDEF')
    if proc.get('PDF - Menciona 6.8.7') == 'Sí':
        palabras_clave.append('6.8.7')
    if proc.get('PDF - Menciona 6.8.2') == 'Sí':
        palabras_clave.append('6.8.2')
    
    return list(set(palabras_clave))  # Eliminar duplicados


def generar_html_reporte(procesos):
    """Genera HTML con las cards de procesos para email (igual al dashboard)."""
    from datetime import datetime
    
    # Detectar palabras clave en cada proceso
    for proc in procesos:
        proc['_palabras_clave'] = detectar_palabras_clave(proc)
    
    # Separar procesos destacados
    destacados = [p for p in procesos if p.get('_palabras_clave') and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA']
    normales = [p for p in procesos if not p.get('_palabras_clave') and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA']
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #F4F6F9; padding: 20px; color: #1F2A3C; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            h1 {{ color: #14213D; font-size: 24px; font-weight: 800; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
            h2 {{ color: #14213D; font-size: 18px; margin-top: 30px; margin-bottom: 15px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat {{ background: #F8F9FA; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #E4E8EF; }}
            .stat-value {{ font-size: 32px; font-weight: 800; color: #667eea; }}
            .stat-label {{ color: #5B6B82; font-size: 12px; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; margin-top: 20px; }}
            .card {{ border-radius: 12px; padding: 18px; border-left: 6px solid; background: white; box-shadow: 0 2px 6px rgba(20,33,61,0.06); }}
            .card.destacado {{ border-left-color: #FFD700; background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 2px solid #FFD700; box-shadow: 0 4px 12px rgba(255,215,0,0.3); }}
            .card.urgente {{ border-left-color: #DC2626; background: #FFF1F1; }}
            .card.seguimiento {{ border-left-color: #D97706; background: #FFFAEF; }}
            .card.lejana {{ border-left-color: #059669; background: #F0FDF7; }}
            .card.vencido {{ border-left-color: #44403C; background: #FAFAF9; }}
            .card.descartada {{ border-left-color: #64748B; opacity: 0.65; background: #F4F6F9; }}
            .card-num {{ font-weight: 800; font-size: 15px; color: #14213D; font-family: 'Consolas', monospace; }}
            .card-obj {{ color: #5B6B82; font-size: 12.5px; margin: 8px 0; line-height: 1.4; }}
            .card-meta {{ display: flex; justify-content: space-between; align-items: flex-start; margin-top: 10px; }}
            .card-dias {{ font-size: 22px; font-weight: 800; color: #1F2A3C; text-align: right; }}
            .card-dias small {{ display: block; font-size: 10px; font-weight: 600; color: #8A97AB; text-transform: uppercase; }}
            .badge {{ display: inline-block; padding: 5px 14px; border-radius: 20px; font-size: 10.5px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }}
            .badge.urgente {{ background: #FEE2E2; color: #991B1B; }}
            .badge.seguimiento {{ background: #FEF3C7; color: #92400E; }}
            .badge.lejana {{ background: #D1FAE5; color: #065F46; }}
            .badge.vencido {{ background: #E7E5E4; color: #44403C; }}
            .badge.descartada {{ background: #E2E8F0; color: #475569; }}
            .hallazgos {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0; }}
            .hallazgo {{ background: #EFF6FF; color: #1E40AF; padding: 4px 11px; border-radius: 20px; font-size: 11px; font-weight: 700; }}
            .hallazgo.destacado {{ background: #FFD700; color: #14213D; border: 2px solid #FFA500; }}
            .fecha-info {{ font-size: 11px; color: #8A97AB; margin-top: 8px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #E4E8EF; color: #5B6B82; font-size: 11px; text-align: center; }}
            .alert-destacados {{ background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin: 20px 0; }}
            .alert-destacados h3 {{ color: #14213D; margin: 0 0 10px 0; font-size: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Reporte de Licitaciones</h1>
            <p style="color: #5B6B82; font-size: 13px;">Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(procesos)}</div>
                    <div class="stat-label">Total Procesos</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len([p for p in procesos if calcular_dias(p) is not None and calcular_dias(p) <= 3 and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA'])}</div>
                    <div class="stat-label">Urgentes (≤3 días)</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(destacados)}</div>
                    <div class="stat-label">⭐ Destacados (FONDEF/6.8.7/6.8.2)</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len([p for p in procesos if p.get('Estado gestión') == 'DESCARTADA'])}</div>
                    <div class="stat-label">Descartados</div>
                </div>
            </div>
            
            {f'<div class="alert-destacados"><h3>⭐ Procesos Destacados ({len(destacados)})</h3><p style="margin:0;color:#5B6B82;font-size:13px;">Procesos con palabras clave importantes: FONDEF, 6.8.7, 6.8.2</p></div>' if destacados else ''}
    """
    
    # Generar cards de procesos destacados primero
    if destacados:
        html += '<h2>⭐ Procesos Destacados</h2><div class="grid">'
        for proc in destacados[:30]:
            html += generar_card_html(proc, destacado=True)
        html += '</div>'
    
    # Luego los procesos normales
    html += '<h2>📋 Otros Procesos</h2><div class="grid">'
    for proc in normales[:50]:
        html += generar_card_html(proc, destacado=False)
    html += '</div>'
    
    html += """
            <div class="footer">
                <p><strong>Dashboard de Licitaciones - Armada Argentina</strong></p>
                <p>Reporte automático generado después de la ejecución de los scripts.</p>
                <p style="margin-top:10px;font-size:10px;">⭐ Procesos destacados: Contienen palabras clave importantes (FONDEF, 6.8.7, 6.8.2)</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generar_card_html(proc, destacado=False):
    """Genera el HTML de una card individual."""
    dias = calcular_dias(proc)
    estado = proc.get('Estado gestión', 'ACTIVA')
    palabras_clave = proc.get('_palabras_clave', [])
    
    # Determinar clase y etiqueta
    if estado == 'DESCARTADA':
        clase = 'descartada'
        etiqueta = 'DESCARTADA'
    elif estado == 'EN SEGUIMIENTO':
        clase = 'seguimiento'
        etiqueta = 'EN SEGUIMIENTO'
    elif dias is None:
        clase = ''
        etiqueta = 'Sin fecha'
    elif dias <= 0:
        clase = 'vencido'
        etiqueta = 'VENCIDO'
    elif dias <= 3:
        clase = 'urgente'
        etiqueta = f'{dias} días'
    elif dias <= 14:
        clase = 'seguimiento'
        etiqueta = f'{dias} días'
    else:
        clase = 'lejana'
        etiqueta = f'{dias} días'
    
    # Si tiene palabras clave, agregar clase destacado
    if destacado and palabras_clave:
        clase_card = 'destacado'
    else:
        clase_card = clase
    
    numero = proc.get('Número de proceso', 'N/A')
    objeto = proc.get('Nombre de proceso', 'Sin descripción')[:80]
    fecha_apertura = proc.get('Fecha acto de apertura', '—')
    fecha_publicacion = proc.get('Fecha publicación portal', '—')
    
    # Generar hallazgos
    hallazgos_html = ''
    hallazgos = []
    
    # Agregar palabras clave destacadas
    for pc in palabras_clave:
        hallazgos.append(f'<span class="hallazgo destacado">⭐ {pc}</span>')
    
    # Agregar otros hallazgos del proceso original
    if proc.get('PDF - Pago adelantado'):
        hallazgos.append('<span class="hallazgo">Pago adelantado</span>')
    if proc.get('Objeto del gasto (detalle)'):
        detalle = str(proc.get('Objeto del gasto (detalle)'))[:40]
        hallazgos.append(f'<span class="hallazgo">Objeto: {detalle}</span>')
    
    if hallazgos:
        hallazgos_html = f'<div class="hallazgos">{"".join(hallazgos)}</div>'
    
    # Días para mostrar
    dias_label = f'{dias} días' if dias is not None and dias > 0 else etiqueta
    
    html = f"""
            <div class="card {clase_card}">
                <div class="card-meta">
                    <div class="card-num">{numero}</div>
                    <div class="card-dias">{dias_label}<small>para apertura</small></div>
                </div>
                <div class="card-obj">{objeto}</div>
                {hallazgos_html}
                <div class="fecha-info">
                    📅 Apertura: {fecha_apertura}<br>
                    📢 Publicación: {fecha_publicacion}
                </div>
            </div>
    """
    
    return html


def calcular_dias(proc):
    """Calcula días hasta la apertura."""
    from datetime import datetime
    fecha_str = proc.get('Fecha acto de apertura', '')
    if not fecha_str:
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


def generar_mensaje_telegram(procesos):
    """Genera mensaje de Telegram completo con toda la info del dashboard."""
    from datetime import datetime
    
    # Detectar palabras clave en cada proceso
    for proc in procesos:
        proc['_palabras_clave'] = detectar_palabras_clave(proc)
    
    # Separar por categorías
    destacados = [p for p in procesos if p.get('_palabras_clave') and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA']
    urgentes = [p for p in procesos if calcular_dias(p) is not None and calcular_dias(p) <= 3 and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA' and not p.get('_palabras_clave')]
    seguimiento = [p for p in procesos if calcular_dias(p) is not None and 3 < calcular_dias(p) <= 14 and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA' and not p.get('_palabras_clave')]
    lejanos = [p for p in procesos if calcular_dias(p) is not None and calcular_dias(p) > 14 and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA' and not p.get('_palabras_clave')]
    vencidos = [p for p in procesos if calcular_dias(p) is not None and calcular_dias(p) <= 0 and p.get('Estado gestión', 'ACTIVA') != 'DESCARTADA']
    descartados = [p for p in procesos if p.get('Estado gestión') == 'DESCARTADA']
    
    mensaje = f"📊 *Reporte de Licitaciones*\n"
    mensaje += f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    # Estadísticas
    mensaje += f"📈 *ESTADÍSTICAS:*\n"
    mensaje += f"├ Total: {len(procesos)} procesos\n"
    mensaje += f"├ ⭐ Destacados: {len(destacados)}\n"
    mensaje += f"├ 🔴 Urgentes: {len(urgentes)}\n"
    mensaje += f"├ 🟡 Seguimiento: {len(seguimiento)}\n"
    mensaje += f"├ 🟢 Lejanos: {len(lejanos)}\n"
    mensaje += f"├ ⚫ Vencidos: {len(vencidos)}\n"
    mensaje += f"└ ⚪ Descartados: {len(descartados)}\n\n"
    
    # Procesos destacados (FONDEF, 6.8.7, 6.8.2)
    if destacados:
        mensaje += f"⭐ *PROCESOS DESTACADOS* ⭐\n"
        mensaje += f"_(Contienen: FONDEF, 6.8.7 o 6.8.2)_\n\n"
        for p in destacados[:10]:
            dias = calcular_dias(p)
            numero = p.get('Número de proceso', 'N/A')
            objeto = p.get('Nombre de proceso', 'Sin descripción')[:60]
            palabras = ', '.join(p.get('_palabras_clave', []))
            fecha = p.get('Fecha acto de apertura', '—')
            
            dias_texto = f"{dias} días" if dias and dias > 0 else "VENCIDO"
            
            mensaje += f"🔸 `{numero}`\n"
            mensaje += f"   📝 {objeto}\n"
            mensaje += f"   🏷️ Palabras clave: *{palabras}*\n"
            mensaje += f"   📅 Apertura: {fecha}\n"
            mensaje += f"   ⏳ {dias_texto}\n\n"
        
        if len(destacados) > 10:
            mensaje += f"_... y {len(destacados) - 10} más_\n\n"
    
    # Procesos urgentes
    if urgentes:
        mensaje += f"🔴 *URGENTES* (≤3 días)\n"
        for p in urgentes[:5]:
            dias = calcular_dias(p)
            numero = p.get('Número de proceso', 'N/A')
            objeto = p.get('Nombre de proceso', 'Sin descripción')[:50]
            mensaje += f"• `{numero}` - *{dias} días*\n"
            mensaje += f"  _{objeto}_\n"
        if len(urgentes) > 5:
            mensaje += f"_... y {len(urgentes) - 5} más_\n"
        mensaje += "\n"
    
    # Procesos en seguimiento
    if seguimiento:
        mensaje += f"🟡 *SEGUIMIENTO* (4-14 días)\n"
        for p in seguimiento[:5]:
            dias = calcular_dias(p)
            numero = p.get('Número de proceso', 'N/A')
            mensaje += f"• `{numero}` - {dias} días\n"
        if len(seguimiento) > 5:
            mensaje += f"_... y {len(seguimiento) - 5} más_\n"
        mensaje += "\n"
    
    # Procesos lejanos
    if lejanos:
        mensaje += f"🟢 *LEJANOS* (>14 días)\n"
        for p in lejanos[:3]:
            dias = calcular_dias(p)
            numero = p.get('Número de proceso', 'N/A')
            mensaje += f"• `{numero}` - {dias} días\n"
        if len(lejanos) > 3:
            mensaje += f"_... y {len(lejanos) - 3} más_\n"
        mensaje += "\n"
    
    # Procesos vencidos
    if vencidos:
        mensaje += f"⚫ *VENCIDOS*\n"
        for p in vencidos[:3]:
            dias = calcular_dias(p)
            numero = p.get('Número de proceso', 'N/A')
            mensaje += f"• `{numero}` - Vencido hace {abs(dias)} días\n"
        if len(vencidos) > 3:
            mensaje += f"_... y {len(vencidos) - 3} más_\n"
        mensaje += "\n"
    
    mensaje += "✅ Ejecución completada exitosamente\n"
    mensaje += "📧 Email con reporte completo enviado"
    
    return mensaje


def enviar_telegram(token, chat_ids, mensaje):
    """Envía mensaje a Telegram."""
    import requests
    
    enviados = 0
    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': mensaje,
                'parse_mode': 'Markdown'
            }
            resp = requests.post(url, data=data, timeout=10)
            if resp.status_code == 200:
                enviados += 1
        except Exception as e:
            print(f"Error enviando a {chat_id}: {e}")
    
    return enviados


class DashboardHandler(SimpleHTTPRequestHandler):
    
    def _get_client_ip(self):
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0]
    
    def _check_auth(self):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return verificar_token(token)
        cookie = self.headers.get('Cookie', '')
        if 'session=' in cookie:
            token = cookie.split('session=')[1].split(';')[0]
            return verificar_token(token)
        return False
    
    def do_GET(self):
        client_ip = self._get_client_ip()
        
        # Verificar IP permitida
        if not verificar_ip_permitida(client_ip):
            log_seguridad("ACCESO_DENEGADO_IP", client_ip)
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error": "IP no autorizada"}')
            return
        
        if self.path == '/' or self.path == '/dashboard.html':
            lic = verificar_licencia()
            if not lic['ok']:
                self._servir_pantalla_licencia(lic)
                return
            generar_dashboard()
            self.path = '/dashboard.html'
            return super().do_GET()
        
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/estado':
            qs = parse_qs(parsed.query)
            script_name = qs.get('script', [''])[0]
            resultado = estado_ejecucion(script_name)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())
            return

        if self.path == '/api/notas':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'notas': cargar_notas()}, ensure_ascii=False).encode())
            return

        if self.path == '/api/gestion':
            if os.path.exists(EXCEL_GESTION):
                df = pd.read_excel(EXCEL_GESTION)
                rows = df.to_dict(orient='records')
            else:
                rows = []
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'rows': rows}, ensure_ascii=False).encode())
            return
        
        if self.path == '/api/emails':
            emails = cargar_emails()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(emails, ensure_ascii=False).encode())
            return
        
        if self.path == '/api/telegram/status':
            from generar_dashboard import cargar_telegram_config
            config = cargar_telegram_config()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'config': config}, ensure_ascii=False).encode())
            return
        
        if self.path == '/api/telegram/status':
            config = cargar_telegram_config()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'config': config}, ensure_ascii=False).encode())
            return
        
        if self.path == '/api/favoritos':
            favoritos = cargar_favoritos()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'favoritos': favoritos.get('favoritos', [])}, ensure_ascii=False).encode())
            return
        
        return super().do_GET()

    def _servir_pantalla_licencia(self, lic):
        html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Licencia</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Arial, sans-serif; background: #F4F6F9;
         display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
  .box {{ background: white; border: 1px solid #E4E8EF; border-radius: 12px; padding: 32px;
          max-width: 420px; box-shadow: 0 8px 24px rgba(20,33,61,0.12); }}
  h1 {{ color: #14213D; font-size: 18px; margin: 0 0 12px; }}
  p {{ color: #5B6B82; font-size: 13.5px; line-height: 1.5; margin: 0 0 18px; }}
  input {{ width: 100%; padding: 10px 12px; border: 1px solid #E4E8EF; border-radius: 6px;
           font-size: 13px; margin-bottom: 12px; box-sizing: border-box; }}
  button {{ width: 100%; padding: 10px; border: 0; border-radius: 6px; background: #14213D;
            color: white; font-weight: 700; font-size: 13px; cursor: pointer; }}
  #msg {{ margin-top: 12px; font-size: 12.5px; }}
</style></head>
<body>
  <div class="box">
    <h1>Dashboard de Licitaciones</h1>
    <p>{lic['motivo']}</p>
    <input type='password' id='clave' placeholder='Clave o código de renovación'>
    <button onclick='renovar()'>Renovar</button>
    <div id="msg"></div>
  </div>
  <script>
    async function renovar() {{
      const clave = document.getElementById('clave').value;
      const resp = await fetch('/api/licencia/renovar', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{clave}})
      }});
      const data = await resp.json();
      const msg = document.getElementById('msg');
      if (data.ok) {{
        msg.style.color = '#059669';
        msg.textContent = data.mensaje + ' Recargando...';
        setTimeout(() => location.reload(), 1200);
      }} else {{
        msg.style.color = '#DC2626';
        msg.textContent = data.error;
      }}
    }}
  </script>
</body></html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        client_ip = self._get_client_ip()
        
        # Verificar IP permitida
        if not verificar_ip_permitida(client_ip):
            log_seguridad("ACCESO_DENEGADO_IP", client_ip)
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'IP no autorizada'}).encode())
            return
        
        # Rate limiting
        allowed, msg = verificar_rate_limit(client_ip)
        if not allowed:
            log_seguridad("RATE_LIMIT_EXCEDIDO", client_ip, msg)
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': msg}).encode())
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length else {}

        # LOGIN
        if self.path == '/api/login':
            username = body.get('username', '')
            password = body.get('password', '')
            valido, error = verificar_credenciales(username, password)
            if valido:
                registrar_intento_login(client_ip, exitoso=True)
                token = crear_token(username)
                log_seguridad("LOGIN_EXITOSO", client_ip, f"Usuario: {username}")
                resultado = {'ok': True, 'token': token}
            else:
                registrar_intento_login(client_ip, exitoso=False)
                log_seguridad("LOGIN_FALLIDO", client_ip, error)
                resultado = {'ok': False, 'error': error}
        
        # ENDPOINTS ORIGINALES
        elif self.path == '/api/descartar':
            resultado = descartar_proceso(body.get('numero', ''), body.get('motivo', ''))
        elif self.path == '/api/seguimiento':
            resultado = marcar_seguimiento(body.get('numero', ''), body.get('motivo', ''))
        elif self.path == '/api/limpiar':
            dias = body.get('dias', 15)
            resultado = limpiar_procesos_vencidos(dias)
        elif self.path == '/api/favoritos':
            resultado = {'ok': True, 'favoritos': cargar_favoritos().get('favoritos', [])}
        elif self.path == '/api/favoritos/agregar':
            resultado = agregar_favorito(body.get('numero', ''))
        elif self.path == '/api/favoritos/quitar':
            resultado = quitar_favorito(body.get('numero', ''))
        elif self.path == '/api/reactivar':
            resultado = reactivar_proceso(body.get('numero', ''))
        elif self.path == '/api/ejecutar':
            resultado = ejecutar_script(body.get('script', ''), forzar=bool(body.get('forzar', False)))
        elif self.path == '/api/notas/agregar':
            resultado = agregar_nota(body.get('texto', ''))
        elif self.path == '/api/notas/marcar':
            resultado = marcar_nota(body.get('id'), body.get('hecha', True))
        elif self.path == '/api/notas/eliminar':
            resultado = eliminar_nota(body.get('id'))
        elif self.path == '/api/registrar_impresion':
            resultado = registrar_impresion(body.get('numero', ''))
        elif self.path == '/api/resetear':
            resultado = resetear_datos()
        elif self.path == '/api/expediente':
            resultado = buscar_expediente_en_pdfs(body.get('numero', ''))
        elif self.path == '/api/licencia/renovar':
            resultado = renovar_licencia(body.get('clave', ''))
        
        # EMAILS
        elif self.path == '/api/emails/agregar':
            resultado = agregar_email(body.get('email', ''))
        elif self.path == '/api/emails/eliminar':
            resultado = eliminar_email(body.get('email', ''))
        elif self.path == '/api/emails/test':
            # Enviar email de prueba a todos los configurados
            emails = cargar_emails().get('emails', [])
            if not emails:
                resultado = {'ok': False, 'error': 'No hay emails configurados'}
            else:
                try:
                    from enviar_reporte_email import enviar_reporte
                    enviados = enviar_reporte(emails, "Email de prueba desde el dashboard")
                    if enviados > 0:
                        resultado = {'ok': True, 'mensaje': f'✅ Email enviado a {enviados} destinatario(s)'}
                    else:
                        resultado = {'ok': False, 'error': 'No se pudo enviar. Verificá la configuración SMTP en .env'}
                except Exception as e:
                    resultado = {'ok': False, 'error': f'Error: {str(e)}'}
        
        # TELEGRAM
        elif self.path == '/api/telegram/config':
            token = body.get('token', '')
            chats = body.get('chats', '')
            resultado = actualizar_telegram(token, chats)
        elif self.path == '/api/telegram/status':
            from generar_dashboard import cargar_telegram_config
            config = cargar_telegram_config()
            resultado = {'ok': True, 'config': config}
        elif self.path == '/api/telegram/test':
            # Enviar mensaje de prueba al bot
            from generar_dashboard import cargar_telegram_config
            import requests
            config = cargar_telegram_config()
            token = config.get('bot_token', '')
            chat_ids = config.get('chat_ids', [])
            
            if not token:
                resultado = {'ok': False, 'error': 'No hay token configurado'}
            elif not chat_ids:
                resultado = {'ok': False, 'error': 'No hay chat IDs configurados'}
            else:
                try:
                    mensaje = "✅ *Bot de Telegram funcionando correctamente*\n\n"
                    mensaje += f"🕐 Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                    mensaje += f"📊 Dashboard: Activo\n"
                    mensaje += f"📧 Emails configurados: {len(cargar_emails().get('emails', []))}\n"
                    
                    enviados = 0
                    for chat_id in chat_ids:
                        try:
                            url = f"https://api.telegram.org/bot{token}/sendMessage"
                            data = {
                                'chat_id': chat_id,
                                'text': mensaje,
                                'parse_mode': 'Markdown'
                            }
                            resp = requests.post(url, data=data, timeout=10)
                            if resp.status_code == 200:
                                enviados += 1
                        except Exception as e:
                            print(f"Error enviando a {chat_id}: {e}")
                    
                    if enviados > 0:
                        resultado = {'ok': True, 'mensaje': f'✅ Mensaje enviado a {enviados} chat(s)'}
                    else:
                        resultado = {'ok': False, 'error': 'No se pudo enviar el mensaje. Verificá el token y los chat IDs'}
                except Exception as e:
                    resultado = {'ok': False, 'error': f'Error: {str(e)}'}
        
        # NOTIFICACIONES FORZADAS
        elif self.path == '/api/notificaciones/forzar':
            try:
                enviar_notificaciones_automaticas()
                resultado = {'ok': True, 'mensaje': '✅ Notificaciones enviadas correctamente'}
            except Exception as e:
                resultado = {'ok': False, 'error': f'Error: {str(e)}'}
        
        else:
            resultado = {'ok': False, 'error': 'Endpoint desconocido'}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass


def main():
    puerto = int(os.environ.get("PUERTO", "8765"))
    print("="*60)
    print("🚀 Dashboard de Licitaciones")
    print("="*60)

    lic = verificar_licencia()
    if lic['ok']:
        print(f"🔑 Licencia: {lic['motivo']}")
    else:
        print(f"🔒 Licencia BLOQUEADA: {lic['motivo']}")
    
    print(f"🔐 Seguridad: Activa (rate limiting + IP filter)")
    
    # Verificar configuración de email
    smtp_user = os.environ.get("SMTP_USER", "")
    if smtp_user:
        print(f"📧 Email: Configurado ({smtp_user})")
    else:
        print(f"📧 Email: No configurado (editá el .env)")
    
    # Verificar configuración de Telegram
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if telegram_token:
        print(f"🤖 Telegram: Configurado")
    else:
        print(f"🤖 Telegram: No configurado (editá el .env)")
    
    print("="*60)
    print(f"📍 Accedé a: http://localhost:{puerto}")
    print(f"📍 Desde la red: http://TU_IP:{puerto}")
    print("📁 Archivos:")
    print("   - cronograma_procesos.xlsx")
    print("   - registro_gestion.xlsx")
    print("   - notas_mejoras.json")
    print("   - detalle_procesos/")
    print(f"⏱️  Scheduler automático: revisa cada {INTERVALO_CHEQUEO_MINUTOS} min")
    print("="*60)
    print("Presioná Ctrl+C para detener el servidor")
    print("="*60)
    
    generar_dashboard()
    threading.Thread(target=scheduler_automatico, daemon=True).start()
    
    # Iniciar bot de Telegram en un thread separado
    if telegram_token:
        print("\n🤖 Iniciando bot de Telegram...")
        def run_telegram_bot():
            try:
                from telegram_bot_integrado import iniciar_bot
                iniciar_bot()
            except Exception as e:
                print(f"⚠️  Error iniciando bot de Telegram: {e}")
        
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
        print("✅ Bot de Telegram corriendo en background")
        print("   Enviá /start al bot desde tu teléfono")
    else:
        print("\n⚠️  Bot de Telegram no iniciado (falta TELEGRAM_BOT_TOKEN)")

    # Escuchar en 0.0.0.0 para acceso desde la red
    server = HTTPServer(('0.0.0.0', puerto), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
        server.shutdown()


if __name__ == "__main__":
    main()

# Importar funciones del generador
from generar_dashboard import (
    generar_dashboard, 
    descartar_proceso, 
    reactivar_proceso,
    cargar_cronograma,
    ejecutar_script,
    estado_ejecucion,
    cargar_notas,
    agregar_nota,
    marcar_nota,
    eliminar_nota,
    registrar_impresion,
    resetear_datos,
    buscar_expediente_en_pdfs,
    EXCEL_GESTION
)
from urllib.parse import urlparse, parse_qs
from licencia import verificar_licencia, renovar_licencia

# Cada cuánto se FIJA si toca correr algo (en minutos). No es la frecuencia real
# de scraping -- comprar.py y detalle_proceso.py se autolimitan solos a una vez
# por día (ver INTERVALO_MINIMO_HORAS en cada uno), así que acá alcanza con
# chequear seguido y dejar que cada script decida si le toca o no.
INTERVALO_CHEQUEO_MINUTOS = 60


def scheduler_automatico():
    print(f"⏱️  Scheduler automático activo: revisa cada {INTERVALO_CHEQUEO_MINUTOS} min "
          f"si toca correr comprar.py / detalle_proceso.py (cada uno se autolimita a 1 vez por día).")
    while True:
        try:
            r1 = ejecutar_script('comprar')
            if r1.get('ok'):
                # Esperamos a que termine comprar.py antes de lanzar detalle_proceso.py
                # (que depende del Excel que comprar.py acaba de actualizar).
                for _ in range(600):  # hasta 10 min de espera activa
                    time.sleep(1)
                    if not estado_ejecucion('comprar')['corriendo']:
                        break
                ejecutar_script('detalle')
        except Exception as e:
            print(f"⚠️ Error en el scheduler automático: {e}")
        time.sleep(INTERVALO_CHEQUEO_MINUTOS * 60)


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard.html':
            lic = verificar_licencia()
            if not lic['ok']:
                self._servir_pantalla_licencia(lic)
                return
            # Regenerar dashboard antes de servir
            generar_dashboard()
            self.path = '/dashboard.html'
            return super().do_GET()
        
        parsed = urlparse(self.path)
        if parsed.path == '/api/estado':
            qs = parse_qs(parsed.query)
            script_name = qs.get('script', [''])[0]
            resultado = estado_ejecucion(script_name)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())
            return

        if self.path == '/api/notas':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'notas': cargar_notas()}, ensure_ascii=False).encode())
            return

        if self.path == '/api/gestion':
            if os.path.exists(EXCEL_GESTION):
                df = pd.read_excel(EXCEL_GESTION)
                rows = df.to_dict(orient='records')
            else:
                rows = []
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'rows': rows}, ensure_ascii=False).encode())
            return
        
        return super().do_GET()

    def _servir_pantalla_licencia(self, lic):
        """Pantalla simple de bloqueo/renovación cuando la licencia no está ok."""
        mostrar_form = True  # la misma clave sirve para renovar o para autorizar una máquina nueva
        html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Licencia</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Arial, sans-serif; background: #F4F6F9;
         display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
  .box {{ background: white; border: 1px solid #E4E8EF; border-radius: 12px; padding: 32px;
          max-width: 420px; box-shadow: 0 8px 24px rgba(20,33,61,0.12); }}
  h1 {{ color: #14213D; font-size: 18px; margin: 0 0 12px; }}
  p {{ color: #5B6B82; font-size: 13.5px; line-height: 1.5; margin: 0 0 18px; }}
  input {{ width: 100%; padding: 10px 12px; border: 1px solid #E4E8EF; border-radius: 6px;
           font-size: 13px; margin-bottom: 12px; box-sizing: border-box; }}
  button {{ width: 100%; padding: 10px; border: 0; border-radius: 6px; background: #14213D;
            color: white; font-weight: 700; font-size: 13px; cursor: pointer; }}
  #msg {{ margin-top: 12px; font-size: 12.5px; }}
</style></head>
<body>
  <div class="box">
    <h1>Dashboard de Licitaciones</h1>
    <p>{lic['motivo']}</p>
    {"<input type='password' id='clave' placeholder='Clave o código de renovación'><button onclick='renovar()'>Renovar</button>" if mostrar_form else ""}
    <div id="msg"></div>
  </div>
  <script>
    async function renovar() {{
      const clave = document.getElementById('clave').value;
      const resp = await fetch('/api/licencia/renovar', {{
        method: 'POST', headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{clave}})
      }});
      const data = await resp.json();
      const msg = document.getElementById('msg');
      if (data.ok) {{
        msg.style.color = '#059669';
        msg.textContent = data.mensaje + ' Recargando...';
        setTimeout(() => location.reload(), 1200);
      }} else {{
        msg.style.color = '#DC2626';
        msg.textContent = data.error;
      }}
    }}
  </script>
</body></html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length else {}

        if self.path == '/api/descartar':
            resultado = descartar_proceso(
                body.get('numero', ''), 
                body.get('motivo', '')
            )
        elif self.path == '/api/reactivar':
            resultado = reactivar_proceso(body.get('numero', ''))
        elif self.path == '/api/ejecutar':
            resultado = ejecutar_script(body.get('script', ''), forzar=bool(body.get('forzar', False)))
        elif self.path == '/api/notas/agregar':
            resultado = agregar_nota(body.get('texto', ''))
        elif self.path == '/api/notas/marcar':
            resultado = marcar_nota(body.get('id'), body.get('hecha', True))
        elif self.path == '/api/notas/eliminar':
            resultado = eliminar_nota(body.get('id'))
        elif self.path == '/api/registrar_impresion':
            resultado = registrar_impresion(body.get('numero', ''))
        elif self.path == '/api/resetear':
            resultado = resetear_datos()
        elif self.path == '/api/expediente':
            resultado = buscar_expediente_en_pdfs(body.get('numero', ''))
        elif self.path == '/api/licencia/renovar':
            resultado = renovar_licencia(body.get('clave', ''))
        else:
            resultado = {'ok': False, 'error': 'Endpoint desconocido'}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        # Silenciar logs del servidor
        pass


def main():
    puerto = 8765
    print("="*60)
    print("🚀 Dashboard de Licitaciones")
    print("="*60)

    lic = verificar_licencia()
    if lic['ok']:
        print(f"🔑 Licencia: {lic['motivo']}")
    else:
        print(f"🔒 Licencia BLOQUEADA: {lic['motivo']}")
        print("   El servidor arranca igual, pero el dashboard va a mostrar la")
        print("   pantalla de renovación en vez del contenido hasta que se resuelva.")
    print("="*60)

    print(f"📍 Accedé a: http://localhost:{puerto}")
    print("📁 Archivos:")
    print(f"   - cronograma_procesos.xlsx")
    print(f"   - registro_gestion.xlsx")
    print(f"   - notas_mejoras.json")
    print(f"   - detalle_procesos/")
    print(f"⏱️  Scheduler automático: revisa cada {INTERVALO_CHEQUEO_MINUTOS} min si toca correr")
    print(f"   comprar.py / detalle_proceso.py (cada uno se autolimita a 1 vez por día).")
    print("="*60)
    print("Presioná Ctrl+C para detener el servidor")
    print("="*60)
    
    # Generar dashboard inicial
    generar_dashboard()

    # Scheduler automático: corre en background mientras el servidor esté vivo
    threading.Thread(target=scheduler_automatico, daemon=True).start()

    # Iniciar servidor
    server = HTTPServer(('localhost', puerto), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
        server.shutdown()


if __name__ == "__main__":
    main()
