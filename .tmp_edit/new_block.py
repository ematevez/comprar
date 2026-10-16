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


def generar_html_reporte(procesos=None):
    """Genera el HTML del email con el mismo maquetado y datos que el dashboard.

    Usa tablas HTML con estilos inline (compatible con Gmail/Outlook) replicando
    la estructura de las cards del dashboard: número + días para apertura,
    objeto, badge de estado, chips de hallazgos (FONDEF / 6.8.7 / 6.8.2 en
    dorado), unidad ejecutora y fechas. Lee los MISMOS datos que el dashboard
    (cronograma_procesos.xlsx + registro de gestión + favoritos).
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
            'fecha_apertura': _texto(proc.get('Fecha acto de apertura', '')) or '—',
            'fecha_publicacion': _texto(proc.get('Fecha publicación portal', '')) or '—',
            'hallazgos': hallazgos,
            'palabras_clave': palabras_clave,
            'favorito': es_favorito(numero),
            'estado': estado,
            'unidad': _texto(proc.get('Unidad Ejecutora', '')) or unidades.get(numero, ''),
        })

    # Mismo ordenamiento por prioridad que el dashboard
    orden = {'urgente': 0, 'vencido': 1, 'en-seguimiento': 2, 'seguimiento': 2,
             'lejana': 3, 'sin-fecha': 4, 'descartada': 5}
    tarjetas.sort(key=lambda t: (orden.get(t['clase'], 9), t['dias_label'] or '999'))

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

    # Sección "Procesos vencidos" (igual que el panel separado del dashboard)
    if tarjetas_vencidas:
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
    borde_card = '2px solid #FFD700;' if t.get('favorito') else f'1px solid {fondo};'

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
          📅 Apertura: <span style="color:{C['slate']};">{t['fecha_apertura']}</span><br>
          📢 Publicación: <span style="color:{C['slate']};">{t['fecha_publicacion']}</span>
        </div>
      </td></tr>
      </table>
    </td>'''


