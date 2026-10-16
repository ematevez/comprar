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

# Carpeta del proyecto: los .env, .xlsx y .json se buscan SIEMPRE acá,
# sin importar desde dónde se lance el servidor (necesario en Docker).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Cargar variables de entorno
load_dotenv(os.path.join(BASE_DIR, ".env"))

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
    
    # Cargar los MISMOS datos que muestra el dashboard (cronograma + gestión)
    try:
        from generar_dashboard import cargar_cronograma
        df = cargar_cronograma()
        procesos = df.to_dict('records')
    except Exception as e:
        print(f"⚠️ No se pudo cargar el cronograma: {e}")
        procesos = []
    
    if not procesos:
        print("⚠️ No hay procesos para enviar")
        return
    
    # Generar HTML para email (con firma incrustada si hay imagen disponible)
    global _FIRMA_CID
    _FIRMA_CID = ''
    firma_path = _buscar_firma_imagen()
    if firma_path:
        _FIRMA_CID = 'firma_reporte'
    html_email = generar_html_reporte(procesos)

    # Enviar email
    try:
        from enviar_reporte_email import enviar_reporte
        emails = cargar_emails().get('emails', [])
        if emails:
            imagen = (_FIRMA_CID, firma_path) if (_FIRMA_CID and firma_path) else None
            enviados = enviar_reporte(emails, html_email=html_email, imagen_cid=imagen)
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


def _texto(valor) -> str:
    """Convierte un valor de Excel a texto limpio (NaN/NaT → '')."""
    import math
    if valor is None:
        return ''
    try:
        if isinstance(valor, float) and math.isnan(valor):
            return ''
    except Exception:
        pass
    s = str(valor).strip()
    return '' if s.lower() in ('nan', 'nat', 'none') else s


# Paleta idéntica al dashboard (variables CSS :root, modo claro)
_EMAIL_COLORES = {
    'navy': '#14213D', 'ink': '#1F2A3C', 'slate': '#5B6B82', 'slate-light': '#8A97AB',
    'border': '#E4E8EF', 'bg': '#F4F6F9', 'surface': '#FFFFFF',
    'urgente': '#DC2626', 'urgente-bg': '#FEE2E2', 'urgente-bg-soft': '#FFF1F1',
    'seguimiento': '#D97706', 'seguimiento-bg': '#FEF3C7', 'seguimiento-bg-soft': '#FFFAEF',
    'lejana': '#059669', 'lejana-bg': '#D1FAE5', 'lejana-bg-soft': '#F0FDF7',
    'vencido': '#44403C', 'vencido-bg': '#E7E5E4',
    'descartada': '#64748B', 'descartada-bg': '#E2E8F0',
}

# (borde izquierdo, fondo) por clase — mismos colores que .card.* del dashboard
_EMAIL_ESTILO_CARD = {
    'urgente':     (_EMAIL_COLORES['urgente'],     _EMAIL_COLORES['urgente-bg-soft']),
    'seguimiento': (_EMAIL_COLORES['seguimiento'], _EMAIL_COLORES['seguimiento-bg-soft']),
    'en-seguimiento': ('#F59E0B', '#FFFBEB'),
    'lejana':      (_EMAIL_COLORES['lejana'],      _EMAIL_COLORES['lejana-bg-soft']),
    'vencido':     (_EMAIL_COLORES['vencido'],     '#FAFAF9'),
    'sin-fecha':   (_EMAIL_COLORES['descartada'],  _EMAIL_COLORES['surface']),
    'descartada':  (_EMAIL_COLORES['descartada'],  _EMAIL_COLORES['bg']),
}

# Imagen de firma incrustada en el email (cid:) si existe; vacío si no.
_FIRMA_CID = ''


def _buscar_firma_imagen():
    """Busca una imagen de firma en lugares habituales del proyecto."""
    candidatos = [
        os.environ.get('FIRMA_IMAGEN', ''),
        'firma.png', 'firma.jpg', 'firma.jpeg', 'firma.gif',
        'data/firma.png', 'data/firma.jpg', 'data/firma.jpeg', 'data/firma.gif',
        'assets/firma.png', 'static/firma.png',
    ]
    for r in candidatos:
        if r and os.path.exists(r):
            return r
    return None


def generar_html_reporte(procesos=None, incluir_vencidos=True):
    """Genera el HTML del email con el mismo maquetado y datos que el dashboard.

    Usa tablas HTML con estilos inline (compatible con Gmail/Outlook) replicando
    la estructura de las cards del dashboard: número + días para apertura,
    objeto, badge de estado, chips de hallazgos (FONDEF / 6.8.7 / 6.8.2 en
    dorado), unidad ejecutora y fechas. Lee los MISMOS datos que el dashboard
    (cronograma_procesos.xlsx + registro de gestión + favoritos).

    incluir_vencidos=False omite la sección "Procesos vencidos" (el email se
    centra en lo que viene: urgentes, seguimiento y lejanos).
    """
    from datetime import datetime
    import pandas as pd
    from generar_dashboard import (cargar_cronograma, dias_para_apertura,
                                   es_favorito, EXCEL_PROCESOS)

    # --- Fuente de datos idéntica al dashboard ---
    df = cargar_cronograma()

    # Respaldos de nombre/unidad desde procesos_armada.xlsx (si existe)
    nombres_respaldo, unidades = {}, {}
    if os.path.exists(EXCEL_PROCESOS):
        try:
            dfp = pd.read_excel(EXCEL_PROCESOS)
            col_num = next((c for c in dfp.columns if 'úmero de proceso' in c), None)
            col_nom = next((c for c in dfp.columns if 'ombre de proceso' in c), None)
            col_uni = next((c for c in dfp.columns if 'Unidad Ejecutora' in c), None)
            if col_num and col_nom:
                for _, r in dfp.iterrows():
                    n = _texto(r.get(col_num))
                    if n:
                        nombres_respaldo[n] = _texto(r.get(col_nom))
                        if col_uni:
                            unidades[n] = _texto(r.get(col_uni))
        except Exception:
            pass

    # --- Construir tarjetas con la MISMA lógica que generar_dashboard() ---
    tarjetas = []
    for _, proc in df.iterrows():
        numero = _texto(proc.get('Número de proceso', ''))
        dias = dias_para_apertura(proc.get('Fecha acto de apertura'))
        estado = proc.get('Estado gestión', 'ACTIVA') or 'ACTIVA'

        # Filtrar filas sin datos reales (ej: números "1", "2", "3" creados por
        # búsquedas fallidas): sin fecha, sin nombre y sin publicación.
        nombre_fila = _texto(proc.get('Nombre de proceso', ''))
        if (dias is None and not nombre_fila
                and not _texto(proc.get('Fecha publicación portal', ''))):
            continue

        if estado == 'DESCARTADA':
            clase, etiqueta = 'descartada', 'DESCARTADA'
        elif estado == 'EN SEGUIMIENTO':
            clase, etiqueta = 'en-seguimiento', 'EN SEGUIMIENTO'
        elif dias is None:
            clase, etiqueta = 'sin-fecha', '—'
        elif dias <= 0:
            clase, etiqueta = 'vencido', 'VENCIDO'
        elif dias <= 3:
            clase, etiqueta = 'urgente', f'{dias} días'
        elif dias <= 14:
            clase, etiqueta = 'seguimiento', f'{dias} días'
        else:
            clase, etiqueta = 'lejana', f'{dias} días'

        hallazgos, palabras_clave = [], []
        if _texto(proc.get('PDF - FONDEF')):
            hallazgos.append('FONDEF'); palabras_clave.append('FONDEF')
        if proc.get('PDF - Menciona 6.8.7') == 'Sí':
            hallazgos.append('6.8.7'); palabras_clave.append('6.8.7')
        if proc.get('PDF - Menciona 6.8.2') == 'Sí':
            hallazgos.append('6.8.2'); palabras_clave.append('6.8.2')
        if _texto(proc.get('PDF - Pago adelantado')):
            hallazgos.append('Pago adelantado')
        detalle_objeto = _texto(proc.get('Objeto del gasto (detalle)'))
        if detalle_objeto:
            hallazgos.append(f"Objeto: {detalle_objeto}")

        tarjetas.append({
            'numero': numero or 'N/A',
            'objeto': (_texto(proc.get('Nombre de proceso', '')) or nombres_respaldo.get(numero, '') or 'Sin nombre')[:80],
            'dias_label': etiqueta,
            'clase': clase,
            'fecha_apertura': _email_fechas(proc.get('Fecha acto de apertura')),
            'fecha_publicacion': _email_fechas(proc.get('Fecha publicación portal')),
            'hallazgos': hallazgos,
            'palabras_clave': palabras_clave,
            'favorito': es_favorito(numero),
            'estado': estado,
            'unidad': _texto(proc.get('Unidad Ejecutora', '')) or unidades.get(numero, ''),
        })

    # Mismo ordenamiento por prioridad que el dashboard
    orden = {'urgente': 0, 'vencido': 1, 'en-seguimiento': 2, 'seguimiento': 2,
             'lejana': 3, 'sin-fecha': 4, 'descartada': 5}

    def _dias_num(t):
        """Número de días para ordenar ('—' / texto → 9999)."""
        lbl = str(t['dias_label'])
        d = ''.join(c for c in lbl if c.isdigit() or c == '-')
        try:
            return int(d) if d not in ('', '-') else 9999
        except ValueError:
            return 9999

    # Destacados primero (favoritos y con palabras clave), como en el dashboard;
    # luego por prioridad de clase y días a la apertura.
    def _es_destacado(t):
        return t['estado'] != 'DESCARTADA' and (t['favorito'] or bool(t['palabras_clave']))

    tarjetas.sort(key=lambda t: (0 if _es_destacado(t) else 1,
                                 orden.get(t['clase'], 9), _dias_num(t)))

    # Como en el dashboard: los vencidos van a una sección separada al final
    tarjetas_vencidas = [t for t in tarjetas if t['clase'] == 'vencido' and t['estado'] != 'DESCARTADA']
    tarjetas = [t for t in tarjetas if t not in tarjetas_vencidas]
    tarjetas_vencidas.sort(key=lambda t: t['fecha_apertura'] or '', reverse=True)

    # Stats iguales al dashboard
    n_total = len(tarjetas) + len(tarjetas_vencidas)
    n_urgentes = len([t for t in tarjetas if t['clase'] == 'urgente'])
    n_seguim = len([t for t in tarjetas if t['clase'] in ('seguimiento', 'en-seguimiento')])
    n_lejanos = len([t for t in tarjetas if t['clase'] == 'lejana'])
    n_vencidos = len(tarjetas_vencidas)
    n_descartados = len([t for t in tarjetas + tarjetas_vencidas if t['clase'] == 'descartada'])
    n_destacados = len([t for t in tarjetas if t['palabras_clave'] and t['estado'] != 'DESCARTADA'])

    C = _EMAIL_COLORES

    def stat_box(valor, titulo, color):
        return (f'<td width="16.6%" style="padding:6px;">'
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
                f'style="background:{C["surface"]};border:1px solid {C["border"]};border-radius:10px;">'
                f'<tr><td style="padding:14px 10px;text-align:center;">'
                f'<div style="font-size:24px;font-weight:800;color:{color};">{valor}</div>'
                f'<div style="font-size:9.5px;font-weight:700;color:{C["slate"]};'
                f'text-transform:uppercase;letter-spacing:0.6px;margin-top:4px;">{titulo}</div>'
                f'</td></tr></table></td>')

    partes = [f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agenda de Licitaciones - Armada</title>
</head>
<body style="margin:0;padding:0;background:{C['bg']};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:{C['ink']};font-size:14px;line-height:1.5;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C['bg']};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:1100px;">

  <!-- Header (igual al .header del dashboard) -->
  <tr><td style="padding-bottom:16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C['surface']};border:1px solid {C['border']};border-radius:10px;">
    <tr><td style="padding:20px 24px;">
      <div style="font-size:21px;font-weight:800;color:{C['navy']};letter-spacing:0.2px;">⚓ Agenda de Licitaciones — Armada Argentina</div>
      <div style="color:{C['slate']};font-size:13px;margin-top:4px;">Reporte automático · {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </td></tr></table>
  </td></tr>

  <!-- Stats (mismas métricas que las stat-cards del dashboard) -->
  <tr><td style="padding-bottom:16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr>
      {stat_box(n_total, 'Total procesos', C['navy'])}
      {stat_box(n_urgentes, '🔴 Urgentes ≤3d', C['urgente'])}
      {stat_box(n_seguim, '🟡 Seguimiento', C['seguimiento'])}
      {stat_box(n_lejanos, '🟢 Lejanos', C['lejana'])}
      {stat_box(n_destacados, '⭐ Destacados', '#B45309')}
      {stat_box(n_vencidos + n_descartados, 'Vencidos/Descart.', C['vencido'])}
    </tr></table>
  </td></tr>

  <!-- Grilla de cards (tabla fluida compatible con Outlook/Gmail) -->
  <tr><td>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
''']

    # 2 columnas por fila, como la grilla responsive del dashboard
    filas = [tarjetas[i:i + 2] for i in range(0, len(tarjetas), 2)]
    for fila in filas:
        partes.append('    <tr>')
        for t in fila:
            partes.append(_email_card_td(t))
        if len(fila) == 1:
            partes.append('<td width="50%"></td>')
        partes.append('</tr>\n')

    # Sección "Procesos vencidos" (opcional; el dashboard la muestra aparte)
    if incluir_vencidos and tarjetas_vencidas:
        partes.append(f'''    </table>
  </td></tr>
  <tr><td style="padding-top:10px;">
    <div style="font-size:16px;font-weight:800;color:{C['navy']};margin:14px 6px 4px;">⚫ Procesos vencidos ({len(tarjetas_vencidas)})</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
''')
        filas_v = [tarjetas_vencidas[i:i + 2] for i in range(0, len(tarjetas_vencidas), 2)]
        for fila in filas_v:
            partes.append('    <tr>')
            for t in fila:
                partes.append(_email_card_td(t))
            if len(fila) == 1:
                partes.append('<td width="50%"></td>')
            partes.append('</tr>\n')

    partes.append(f'''    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding-top:20px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C['surface']};border:1px solid {C['border']};border-radius:10px;">
    <tr><td style="padding:16px 24px;text-align:center;color:{C['slate']};font-size:11px;">
      {_firma_html()}
      <strong style="color:{C['navy']};">Dashboard de Licitaciones — Armada Argentina</strong><br>
      Reporte automático generado después de la ejecución de los scripts.<br>
      ⭐ Chips dorados = palabras clave importantes (FONDEF, 6.8.7, 6.8.2) · 🔖 = favorito
    </td></tr></table>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>''')

    return ''.join(partes)


def _firma_html():
    """Bloque de firma con imagen incrustada (cid:) si _FIRMA_CID está definido."""
    if not _FIRMA_CID:
        return ''
    C = _EMAIL_COLORES
    return (f'<div style="margin-bottom:12px;">'
            f'<img src="cid:{_FIRMA_CID}" alt="Firma" width="150" '
            f'style="display:block;margin:0 auto 6px;max-width:150px;height:auto;border:0;">'
            f'</div>')


def _email_fechas(valor) -> str:
    """Formatea fechas del Excel para el email (dd/mm/aaaa hh:mm).

    Acepta datetime/Timestamp de pandas o strings tipo '29/10/2026 12:00 Hrs.'
    Devuelve '' si no se puede parsear (la card muestra '—').
    """
    import math
    s = _texto(valor)
    if not s:
        return ''
    try:
        if isinstance(valor, float) and math.isnan(valor):
            return ''
    except Exception:
        pass
    # datetime / Timestamp → formatear directo
    try:
        import pandas as pd
        if isinstance(valor, pd.Timestamp) or hasattr(valor, 'strftime'):
            return valor.strftime('%d/%m/%Y %H:%M')
    except Exception:
        pass
    for fmt in ('%d/%m/%Y %H:%M Hrs.', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
        try:
            from datetime import datetime as _dt
            return _dt.strptime(s, fmt).strftime('%d/%m/%Y %H:%M')
        except ValueError:
            continue
    return s  # último recurso: mostrar tal cual


def _email_card_td(t):
    """Una tarjeta del dashboard convertida a celda de tabla para email."""
    C = _EMAIL_COLORES
    borde, fondo = _EMAIL_ESTILO_CARD.get(t['clase'], (C['descartada'], C['surface']))

    # Badge de estado (colores de .badge.* del dashboard)
    badge_map = {
        'urgente': (C['urgente-bg'], '#991B1B'),
        'seguimiento': (C['seguimiento-bg'], '#92400E'),
        'en-seguimiento': (C['seguimiento-bg'], '#92400E'),
        'lejana': (C['lejana-bg'], '#065F46'),
        'vencido': (C['vencido-bg'], C['vencido']),
        'descartada': (C['descartada-bg'], '#475569'),
    }
    bg_b, tx_b = badge_map.get(t['clase'], (C['border'], C['slate']))

    # Chips de hallazgos (palabras clave en dorado, como .hallazgo.destacado)
    chips = ''
    for h in t['hallazgos']:
        es_kw = h in t['palabras_clave']
        if es_kw:
            chips += ('<span style="display:inline-block;background:#FFC933;color:#14213D;'
                      'border:1px solid #FF8C00;padding:3px 10px;border-radius:20px;'
                      'font-size:10.5px;font-weight:800;margin:2px 3px 2px 0;">⭐ ' + h + '</span>')
        else:
            txt = h if len(h) <= 45 else h[:42] + '…'
            chips += ('<span style="display:inline-block;background:#EFF6FF;color:#1E40AF;'
                      'padding:3px 10px;border-radius:20px;font-size:10.5px;font-weight:700;'
                      'margin:2px 3px 2px 0;">' + txt + '</span>')

    fav = '🔖 ' if t.get('favorito') else ''
    unidad = (f'<div style="font-size:11px;color:{C["slate-light"]};margin-top:6px;">🏛️ {t["unidad"]}</div>'
              if t.get('unidad') else '')
    opacidad = 'opacity:0.75;' if t['clase'] == 'descartada' else ''
    # Borde exterior: dorado si es favorito, gris de borde si no; el color de
    # estado se conserva en la barra izquierda de 6px (como .card del dashboard)
    borde_card = '2px solid #FFD700;' if t.get('favorito') else f'1px solid {C["border"]};'

    return f'''<td width="50%" valign="top" style="padding:8px 6px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{fondo};border-left:6px solid {borde};border:{borde_card};border-radius:12px;{opacidad}">
      <tr><td style="padding:16px 18px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-weight:800;font-size:14px;color:{C['navy']};font-family:Consolas,'Courier New',monospace;letter-spacing:0.2px;">{fav}{t['numero']}</td>
          <td align="right" style="white-space:nowrap;">
            <span style="font-size:19px;font-weight:800;color:{C['ink']};">{t['dias_label']}</span>
            <span style="display:block;font-size:9px;font-weight:600;color:{C['slate-light']};text-transform:uppercase;letter-spacing:0.4px;">para apertura</span>
          </td>
        </tr>
        </table>
        <div style="color:{C['slate']};font-size:12px;margin:8px 0 10px;line-height:1.4;">{t['objeto']}</div>
        <div style="margin-bottom:8px;"><span style="display:inline-block;background:{bg_b};color:{tx_b};padding:4px 12px;border-radius:20px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;">{t['estado']}</span></div>
        {f'<div style="margin:10px 0;">{chips}</div>' if chips else ''}
        {unidad}
        <div style="font-size:10.5px;color:{C['slate-light']};margin-top:8px;border-top:1px solid {C['border']};padding-top:8px;">
          📅 Apertura: <span style="color:{C['slate']};">{t['fecha_apertura'] or '—'}</span><br>
          📢 Publicación: <span style="color:{C['slate']};">{t['fecha_publicacion'] or '—'}</span>
        </div>
      </td></tr>
      </table>
    </td>'''


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

    def __init__(self, *args, **kwargs):
        # Servir los archivos siempre desde la carpeta del proyecto,
        # sin importar el directorio de trabajo (Docker / systemd).
        super().__init__(*args, directory=BASE_DIR, **kwargs)

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
                # En Docker la MAC cambia en cada contenedor: si existe
                # LICENCIA_TOKEN en el .env, se auto-renueva en vez de bloquear.
                token_env = os.environ.get("LICENCIA_TOKEN", "").strip()
                if token_env and renovar_licencia(token_env).get("ok"):
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
    
    # Verificar configuración de Telegram (env o data/telegram_config.json)
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not telegram_token:
        try:
            tg_cfg = cargar_telegram_config()
            if tg_cfg.get('activo') and tg_cfg.get('bot_token'):
                telegram_token = tg_cfg['bot_token']
        except Exception:
            pass
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
    
    # Iniciar bot de Telegram en un thread separado.
    # IMPORTANTE: el polling de getUpdates solo admite UNA instancia por token.
    # Si ya hay otro proceso usando el mismo bot (otra terminal, contenedor Docker,
    # cron), se detecta y se omite el bot interactivo; los envíos por API REST
    # (reportes/notificaciones) siguen funcionando igual desde cualquier instancia.
    if telegram_token:
        def _otro_bot_activo():
            """Chequea si otra instancia ya está haciendo getUpdates con este token."""
            try:
                import urllib.request, json as _json
                url = f"https://api.telegram.org/bot{telegram_token}/getWebhookInfo"
                with urllib.request.urlopen(url, timeout=10) as resp:
                    info = _json.loads(resp.read().decode())
                desc = (info.get('description') or '')
                return 'another instance' in desc.lower() or 'terminated by other' in desc.lower()
            except Exception:
                return False

        if _otro_bot_activo():
            print("\n⚠️  Telegram: otro proceso ya usa este bot (getUpdates ocupado).")
            print("   El bot interactivo NO se inicia para evitar el conflicto.")
            print("   Los reportes por Telegram se envían igualmente. Cerrá la otra")
            print("   instancia (otra terminal o 'docker compose down') y reiniciá.")
        else:
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
