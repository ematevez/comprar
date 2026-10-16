"""
checklist.py - Genera el "Checklist de Participación" para un proceso.

Se abre desde el botón 🎯 Participar del dashboard (GET /checklist/<numero>).
El maquetado replica el diseño del checklist de ejemplo (agrupado por etapa,
barra de progreso por grupo y total, tildes guardadas en localStorage).

Las fechas, montos y cláusulas se leen SIEMPRE del cronograma_procesos.xlsx
(misma fuente que el dashboard), así los datos son exactamente los mismos.
"""
import os
import re
import json
import html as htmllib
from datetime import datetime

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_CRONOGRAMA = os.path.join(BASE_DIR, "cronograma_procesos.xlsx")


# ---------------------------------------------------------------- utilidades
def _texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    s = str(valor).strip()
    return "" if s.lower() in ("nan", "none") else s


def _parse_fecha(valor):
    """Acepta 'DD/MM/AAAA HH:MM Hrs.' o datetime de pandas."""
    s = _texto(valor)
    if not s:
        return None
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", s)
    if m:
        d, mo, y, hh, mm = m.groups()
        try:
            return datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0))
        except ValueError:
            return None
    try:
        dt = pd.to_datetime(s, dayfirst=True)
        return dt.to_pydatetime()
    except Exception:
        return None


def _fmt_fechita(dt):
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%Y %H:%M")


def _dias_hasta(dt):
    if not dt:
        return None
    delta = dt.date() - datetime.now().date()
    return delta.days


def sanitizar_nombre(texto: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", texto).strip()[:80]


def _esc(s: str) -> str:
    return htmllib.escape(str(s), quote=True)


# ------------------------------------------------------------------ datos
def fila_proceso(numero: str) -> dict | None:
    if not os.path.exists(EXCEL_CRONOGRAMA):
        return None
    try:
        df = pd.read_excel(EXCEL_CRONOGRAMA)
    except Exception:
        return None
    col_num = next((c for c in df.columns if "úmero de proceso" in c), None)
    if not col_num:
        return None
    row = df[df[col_num].astype(str).str.strip() == numero.strip()]
    if row.empty:
        return None
    r = row.iloc[0]
    out = {}
    for c in df.columns:
        out[c] = _texto(r.get(c))
    # alias simples
    def get(*claves):
        for k in claves:
            for c in df.columns:
                if k.lower() in c.lower():
                    v = out.get(c, "")
                    if v:
                        return v
        return ""

    out["_num"] = numero
    out["_nombre"] = get("Nombre de proceso") or numero
    out["_apertura"] = get("Fecha acto de apertura")
    out["_publicacion"] = get("Fecha publicación portal")
    out["_ini_consultas"] = get("Fecha inicio consultas")
    out["_fin_consultas"] = get("Fecha final consultas")
    out["_ini_docfis"] = get("inicio recepción documentos físicos")
    out["_fin_docfis"] = get("fin recepción documentos físicos")
    out["_ini_muestras"] = get("inicio recepción de muestras")
    out["_fin_muestras"] = get("fin recepción de muestras")
    out["_fondef_pdf"] = get("PDF - FONDEF")
    out["_pago_adelantado"] = get("Pago adelantado")
    out["_687"] = get("Menciona 6.8.7")
    out["_682"] = get("Menciona 6.8.2")
    out["_estado"] = get("Estado gestión") or "ACTIVA"
    return out


_carpeta_cache = {}


def _carpeta_pdfs(numero: str) -> str | None:
    """Carpeta de PDFs del proceso. Prueba el nombre sanitizado y variantes
    (el scraper a veces guarda con guiones bajos o subcarpetas)."""
    if numero in _carpeta_cache:
        return _carpeta_cache[numero]
    base = os.path.join(BASE_DIR, "detalle_procesos")
    resultado = None
    if os.path.isdir(base):
      candidatos = [sanitizar_nombre(numero), numero.replace("/", "_")]
      for cand in candidatos:
          p = os.path.join(base, cand)
          if os.path.isdir(p):
              resultado = p
              break
      if resultado is None:  # búsqueda por prefijo normalizado
          norm = re.sub(r"[^a-z0-9]", "", numero.lower())
          for d in os.listdir(base):
              if norm and norm in re.sub(r"[^a-z0-9]", "", d.lower()):
                  resultado = os.path.join(base, d)
                  break
    _carpeta_cache[numero] = resultado
    return resultado


def _texto_pdfs(numero: str) -> str:
    """Texto completo de todos los PDF del proceso (cacheado por número)."""
    clave = "_txt_" + numero
    if clave in _carpeta_cache:
        return _carpeta_cache[clave]
    carpeta = _carpeta_pdfs(numero)
    txt = ""
    if carpeta:
        try:
            from pypdf import PdfReader
        except ImportError:
            PdfReader = None
        if PdfReader:
            partes = []
            for raiz, _, archivos in os.walk(carpeta):
                for fn in archivos:
                    if not fn.lower().endswith(".pdf"):
                        continue
                    try:
                        reader = PdfReader(os.path.join(raiz, fn))
                        partes.append("\n".join((p.extract_text() or "") for p in reader.pages))
                    except Exception:
                        continue
            txt = "\n".join(partes)
    _carpeta_cache[clave] = txt
    return txt


def _pdf_contiene(numero: str, patron: str) -> bool:
    """Busca un regex dentro de los PDF descargados del proceso (si existen)."""
    txt = _texto_pdfs(numero)
    if not txt:
        return False
    return bool(re.search(patron, txt, re.IGNORECASE))


def _pdf_extraer(numero: str, patron: str, default: str = "") -> str:
    """Primer match de un regex sobre el texto de los PDFs (para datos reales)."""
    txt = _texto_pdfs(numero)
    if not txt:
        return default
    m = re.search(patron, txt, re.IGNORECASE)
    if not m:
        return default
    for g in m.groups():
        if g:
            return g.strip()
    return default


# Los PDFs del pliego traen saltos de línea y espacios partidos ("individu alizada",
# "DOS (2) días"). Normalizamos el whitespace antes de buscar cláusulas.
def _norm_txt(txt: str) -> str:
    return re.sub(r"\s+", " ", txt or "")


_PALABRAS_NUM = {
    "UNO": 1, "DOS": 2, "TRES": 3, "CUATRO": 4, "CINCO": 5, "SEIS": 6,
    "SIETE": 7, "OCHO": 8, "NUEVE": 9, "DIEZ": 10, "ONCE": 11, "DOCE": 12,
    "QUINCE": 15, "VEINTE": 20, "TREINTA": 30, "CUARENTA": 40, "CINCUENTA": 50,
    "SESENTA": 60, "SETENTA": 70, "OCHENTA": 80, "NOVENTA": 90, "CIENTO": 100,
}

# % de la garantía de mantenimiento de oferta escrito como "CINCO POR CIENTO (5)"
# o variantes sueltas "POR CIENTO (5)".
_RE_GMO_PCT = re.compile(
    r"(?:(UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ|QUINCE|VEINTE|TREINTA|CUARENTA|CINCUENTA)\s+POR\s+CIENTO\s*)?\(\s*(\d{1,3})\s*\)",
    re.I)


def _clausula_garantia_oferta(numero: str) -> dict:
    """Extrae de las Cláusulas Particulares (PDF del expediente) los datos reales
    de la garantía de mantenimiento de oferta: porcentaje, moneda, destino de la
    garantía física y plazo de presentación."""
    txt = _norm_txt(_texto_pdfs(numero))
    out = {"pct": "", "moneda": "", "lugar": "", "plazo_dias": ""}
    if not txt:
        return out

    # --- porcentaje: buscar "equivaldrá al CINCO POR CIENTO (5%)" en la zona
    #     de la garantía de mantenimiento (hasta 1200 chars después, para no
    #     capturar porcentajes de otras cláusulas como multas o adelantos).
    pct_buscar = [m.start() for m in re.finditer(r"garant[íi]a de mantenimiento", txt, re.I)]
    for ini in pct_buscar:
        zona = txt[ini:ini + 1200]
        mp = re.search(
            r"(?:POR\s+CIENTO|%)?\s*\(\s*(\d{1,3}(?:[.,]\d+)?)\s*%\s*\)", zona, re.I)
        if not mp:
            mp = re.search(r"CINCO\s+POR\s+CIENTO|DOS\s+POR\s+CIENTO|UNO\s+POR\s+CIENTO|"
                           r"TRES\s+POR\s+CIENTO|CUATRO\s+POR\s+CIENTO|DIEZ\s+POR\s+CIENTO",
                           zona, re.I)
            if mp:
                palabra = mp.group(0).split()[0].upper()
                num = {"UNO": "1", "DOS": "2", "TRES": "3", "CUATRO": "4",
                       "CINCO": "5", "DIEZ": "10"}.get(palabra, "")
                if num:
                    out["pct"] = num + "%"
                    break
        elif mp:
            val = mp.group(1).replace(".", "").replace(",", ".")
            try:
                f = float(val)
                if 0 < f <= 20:  # fuera de rango => es otra cláusula, seguir buscando
                    out["pct"] = (("%g" % f)) + "%"
                    break
            except ValueError:
                pass

    # --- moneda ------------------------------------------------------------
    mm = re.search(r"(MONEDA NACIONAL|PESOS|D[UÓ]LARES(?:\s+AMERICANOS)?|USD)", txt, re.I)
    if mm:
        t = mm.group(1).upper()
        out["moneda"] = ("Moneda nacional (pesos)" if t in ("MONEDA NACIONAL", "PESOS")
                         else "Dólares (USD)")

    # --- destino / lugar de presentación si no es electrónica --------------
    ml = re.search(r"garant[íi]as no electr[oó]nicas.{0,600}?en el \u201c([^”]{4,90})\u201d", txt, re.I)
    if not ml:
        ml = re.search(r"entregarse el original.{0,400}?en el \u201c([^”]{4,90})\u201d", txt, re.I)
    if not ml:
        ml = re.search(r"en \u201c?(TESORER[IÍ]A GENERAL DE LA NACI[OÓ]N|Departamento de Compras)\u201d?", txt, re.I)
    if ml:
        out["lugar"] = re.sub(r"\s+", " ", ml.group(1)).strip().title()

    # --- plazo para presentarla: "DOS (2) días ... apertura" / "plazo de X días"
    for ini in pct_buscar:
        zona = txt[ini:ini + 900]
        md = re.search(r"\b(UNO|UN|DOS|TRES|CUATRO|CINCO|SEIS|DIEZ)\s*"
                       r"(?:\(\s*\d+\s*\))?\s+d[ií]as\b[^.]{0,80}?(apertura|presentaci|entrega|constituci)",
                       zona, re.I)
        if not md:
            # "dentro del plazo que va desde la fecha y hora de apertura ... hasta
            #  un plazo de DOS (2) días" — solo si el tramo no habla de renovación
            m2 = re.search(r"apertura.{0,140}?(?:plazo|t[eé]rmino)\s+(?:que va\s+)?(?:de|desde|al|del|hasta)?\s*"
                           r"(UNO|UN|DOS|TRES|CUATRO|CINCO|SEIS|DIEZ)\s*(?:\(\s*\d+\s*\))?\s+d[ií]as",
                           zona, re.I | re.S)
            if m2 and "renov" not in zona[max(0, m2.start()-60):m2.start()]:
                clave = m2.group(1).upper()
                out["plazo_dias"] = {"UN": "1"}.get(clave) or str(_PALABRAS_NUM.get(clave, ""))
                if out["plazo_dias"]:
                    break
            continue
        clave = md.group(1).upper()
        out["plazo_dias"] = {"UN": "1"}.get(clave) or str(_PALABRAS_NUM.get(clave, ""))
        if out["plazo_dias"]:
            break
    return out


# ------------------------------------------------------------- generador
def construir_checklist(fila: dict) -> list:
    """Devuelve la lista de grupos con sus ítems, según los datos reales."""
    num = fila["_num"]
    apertura = _parse_fecha(fila["_apertura"])
    dias_ap = _dias_hasta(apertura)
    fin_consultas = _parse_fecha(fila["_fin_consultas"])
    dias_consultas = _dias_hasta(fin_consultas)
    doc_fis_fin = _parse_fecha(fila["_fin_docfis"])
    mue_ini = _parse_fecha(fila["_ini_muestras"])
    mue_fin = _parse_fecha(fila["_fin_muestras"])

    tiene_anticipo = bool(fila["_pago_adelantado"]) or _pdf_contiene(num, r"anticipo")
    tiene_contrag = _pdf_contiene(num, r"contragarant[ií]a")
    es_fondef = bool(fila["_fondef_pdf"]) or fila["_687"] == "Sí"

    # --- datos reales extraídos de los PDFs del expediente (si existen) ---
    txt_pdfs = _texto_pdfs(num)
    moneda = ""
    for m in re.finditer(r"\b(USD|D[oó]lares(?:\s+americanos)?|PESOS|ARS)\b", txt_pdfs):
        t = m.group(1).upper()
        moneda = "USD" if t.startswith("D") or t == "USD" else ("ARS" if t in ("PESOS", "ARS") else "")
        if moneda:
            break
    anticipo_pct = _pdf_extraer(num, r"anticipo.{0,160}?\(\s*(\d{1,3})\s*%")
    if anticipo_pct:
        anticipo_pct += "%"
    plazo_entrega = _pdf_extraer(num, r"plazo de (?:entrega|suministro|ejecuci[oó]n)[^.]{0,90}?(\d+\s*(?:meses|d[ií]as h[aá]biles|d[ií]as corridos))")
    lugar_entrega = _pdf_extraer(num, r"((?:Base Naval|Área[ A-Za-zÁÉÍÓÚ]*Alfabetizada)[A-Za-z ÁÉÍÓÚÑ]{3,40}?)(?=[,.]|\s+(?:que|Que|CP|\(|$))")
    cantidad = _pdf_extraer(num, r"\b([A-ZÁÉÍÓÚÑ]+ \((?:\d+|[a-z]+)\))\s+(?:unidades|unidad|equipos|botes|computadoras|servicios|m[oó]dulos)")
    requiere_muestras = _pdf_contiene(num, r"recepci[oó]n de muestras|presentaci[oó]n de muestras")
    requiere_traduccion = _pdf_contiene(num, r"traducci[oó]n.{0,120}traductor p[uú]blico|traductor p[uú]blico.{0,120}traducci[oó]n|folleter[ií]a")
    organismo = ""
    m_org = re.search(r"a favor d[eé]l?\s+(?:la\s+)?((?:ESTADO MAYOR GENERAL DE LA|ESTADO MAYOR|ARMADA ARGENTINA)[A-ZÁÉÍÓÚÑ ]{0,40})", txt_pdfs)
    if m_org:
        organismo = re.sub(r"\s+", " ", m_org.group(1)).strip()
        if organismo.upper().startswith("ESTADO MAYOR GENERAL DE LA"):
            organismo += " ARMADA"
    else:
        for cand in re.findall(r"(ESTADO MAYOR GENERAL DE\s*\n?\s*LA\s*\n?\s*ARMADA)", txt_pdfs):
            organismo = "ESTADO MAYOR GENERAL DE LA ARMADA"
            break
    organismo = organismo.title() if organismo else "organismo contratante"

    groups = []

    # 1 · Antes de ofertar (plazos del expediente)
    plazos_items = [
        ["Revisar Pliego de Bases y Condiciones y Anexos publicados en COMPR.AR",
         "Descargarlos desde el propio proceso; ante duda, consultar dentro del período habilitado.", "—"],
    ]
    if fin_consultas:
        alerta = f'⏳ Cierra en {dias_consultas} día(s)' if dias_consultas is not None and dias_consultas >= 0 else '🚫 Período cerrado'
        plazos_items.append(["Realizar consultas / preguntas al organismo",
                             f"Período: {_fmt_fechita(_parse_fecha(fila['_ini_consultas']))} → {_fmt_fechita(fin_consultas)} · {alerta}",
                             "Cronograma"])
    if doc_fis_fin:
        plazos_items.append(["Presentar documentación física (si el pliego lo exige)",
                             f"Hasta {_fmt_fechita(doc_fis_fin)} — verificar destino y horario de Tesorería/mesa de entradas.",
                             "Cronograma"])
    if mue_fin:
        plazos_items.append(["Entrega de muestras (si aplica)",
                             f"Ventana: {_fmt_fechita(mue_ini)} → {_fmt_fechita(mue_fin)}",
                             "Cronograma"])
    grupos_clave = [f for f in (fila["_687"], fila["_682"]) if f == "Sí"]
    if grupos_clave:
        plazos_items.append([f"Analizar cláusulas {' y '.join(grupos_clave)} del pliego",
                             "Condiciones especiales detectadas en los PDF del expediente (catálogo, garantía, pagos).",
                             " · ".join(grupos_clave)])
    groups.append({"h": "1 · Análisis del expediente",
                   "w": "Primero leer, después cotizar. Todo lo que mande el proveedor en inglés hay que traducirlo antes de subirlo.",
                   "items": plazos_items})

    # 2 · Proveedor / cotización
    grupos_prov = ["2 · Proveedor y cotización",
                   "Pedir ya. Todo lo que mande el proveedor en inglés hay que traducirlo antes de subirlo."]
    prov_items = [
        ["Cotización formal" + (f" por {cantidad}" if cantidad else ""),
         ("Vigente hasta después de la apertura. Condición de entrega y moneda acordes al pliego"
          + (f" (mon detectada: {moneda})." if not moneda else f" en {moneda}.")), "—"],
        ["Folletería / ficha técnica del producto",
         "Debe mostrar las características pedidas en el Anexo de Especificaciones Técnicas.", "Pliego"],
        ["Marca, modelo y código / número de parte",
         "Datos del fabricante: razón social, dirección, web y número de parte (sirven también para la catalogación).", "Pliego"],
        ["Certificaciones exigidas por el pliego (ISO, CE, etc.)",
         "Si se adjuntan a la oferta, traducidas por traductor público y legalizadas.", "Pliego"],
        ["Garantía del fabricante",
         "Respaldar la garantía técnica que se declara en la oferta.", "Pliego"],
    ]
    detalle_entrega = "Comparar contra el cronograma del expediente antes de comprometerla."
    extras_entrega = " · ".join(x for x in [plazo_entrega.capitalize() if plazo_entrega else "",
                                             lugar_entrega.title() if lugar_entrega else ""] if x)
    if extras_entrega:
        detalle_entrega = f"Detectado en el pliego: {extras_entrega}. Confirmar margen para aduana/traslado."
    prov_items.append(["Confirmar plazo y lugar de entrega exigidos", detalle_entrega, "Cronograma"])
    groups.append({"h": grupos_prov[0], "w": grupos_prov[1], "items": prov_items})

    # 2b · Traducciones (solo si el expediente las exige)
    if requiere_traduccion:
        groups.append({"h": "2b · Traducciones",
                       "w": "Traductor público, legalizado por el Colegio de Traductores.",
                       "items": [
                           ["Traducir la folletería / ficha técnica", "", "Pliego"],
                           ["Traducir certificados del fabricante (ISO / CE)",
                            "Documentos de autoridad extranjera, además, legalizados.", "Pliego"],
                       ]})

    # --- cláusulas particulares reales sobre la garantía de oferta (del PDF) ---
    gmo = _clausula_garantia_oferta(num)
    pct_gmo = gmo["pct"] or "5%"
    moneda_gmo = gmo["moneda"] or (moneda and f"en {'moneda nacional (pesos)' if moneda=='ARS' else 'dólares (USD)'}") or "en la moneda de la oferta"
    lugar_gmo = gmo["lugar"] or "Tesorería General de la Nación / oficina que indique el pliego"
    dias_gmo = gmo["plazo_dias"] or "2"
    detalle_gmo = (f"Póliza electrónica de caución a favor de {organismo.lower()}, {moneda_gmo}. "
                   f"Si NO es electrónica: entregar el original en {lugar_gmo} dentro de los "
                   f"{dias_gmo} día(s) de la apertura.")
    if not gmo["pct"]:
        detalle_gmo += " ⚠️ El % no figura explícito en el PDF del expediente: confirmar en el pliego publicado (regla general: 5% del total de la oferta)."
    if not txt_pdfs:
        detalle_gmo += " (Sin PDF del expediente: verificar % y destino en el pliego publicado.)"

    # 3 · Documentación de la oferta en COMPR.AR
    doc_items = [
        [f"Garantía de mantenimiento de oferta: {pct_gmo}",
         detalle_gmo, "Cláusulas Particulares", 1],
        ["Declaración Jurada de Intereses (Decreto 202/17)",
         "Formulario digital de la Oficina Anticorrupción.", "15.2 · Anexo I"],
        ["DDJJ de Elegibilidad", "Firmada.", "15.3 · Anexo III"],
        ["DDJJ de Habilidad para Contratar", "Firmada.", "15.3 · Anexo IV"],
        ["Certificado de garantía técnica firmado",
         "Completar CUIT, domicilio, marca y modelo.", "15.4 · Pliego", 1],
    ]
    if requiere_traduccion:
        doc_items.append(["Documentación técnica traducida",
                          "Traductor público, legalizada por el Colegio de Traductores.", "15"])
    doc_items += [
        ["Precio ofertado completo" + (f" en {moneda}" if moneda else ""),
         "Incluir flete, seguro, aranceles y descarga donde exija el pliego.", "Pliego"],
        ["Confirmar la oferta con el Administrador Legitimado",
         "Una oferta editada y NO reconfirmada antes de la apertura se considera retirada.", "16", 1],
    ]
    if mue_fin or requiere_muestras:
        doc_items.append(["Presentar muestras si el pliego lo exige",
                          f"Ventana: {_fmt_fechita(mue_ini)} → {_fmt_fechita(mue_fin)}" if mue_fin
                          else "Detectada en los PDF del pliego: confirmar modalidad y lugar.", "Pliego"])
    groups.append({"h": "3 · Oferta en COMPR.AR",
                   "w": "Todo se carga ANTES de la apertura. Revisar el pliego particular: puede exigir ítems extra.",
                   "items": doc_items})

    # 4 · Registros al día
    groups.append({"h": "4 · Registros al día",
                   "w": "No se suben, pero los verifica el organismo.",
                   "items": [
                       ["SIPC / COMPR.AR: inscripción y datos actualizados",
                        "Incluye DDJJ cargadas y representante con facultades vigentes.", "1 · 15.3"],
                       ["ARCA (ex AFIP): sin deuda impositiva ni previsional",
                        "Si hay deuda, intiman 3 días y después desestiman.", "36"],
                       ["Padrón Único de Entes (e-SIDIF): alta como beneficiario",
                        "Si no figura, pedirla junto con la oferta.", "18"],
                   ]})

    # 5 · Financiero (solo si el expediente lo menciona)
    fin_items = []
    if tiene_anticipo:
        pct_txt = f"del {anticipo_pct}" if anticipo_pct and "%" in anticipo_pct else "del porcentaje indicado en el pliego"
        fin_items.append([f"Contragarantía del anticipo ({anticipo_pct or '%'}): 3 días hábiles de perfeccionado el contrato",
                          f"Sin ella no se cobra el anticipo ({pct_txt}). Póliza electrónica a favor del mismo organismo.", "43 · 26", 1])
        fin_items.append(["Factura del anticipo",
                          "Se paga a los 30 días corridos de presentada, junto con la contragarantía.", "43"])
    if tiene_contrag:
        fin_items.append(["Verificar condiciones de anticipo / contragarantía en el pliego",
                          "Detectado en los PDF del expediente: confirmar % y modalidad.", "Pliego"])
    if es_fondef:
        fin_items.append(["Cláusula 6.8.7 (FONDEF / pago con anticipos)",
                          "Este expediente referencia 6.8.7: revisar régimen de adelantos y catálogo.", "6.8.7"])
    if not fin_items:
        fin_items.append(["Verificar forma de pago en el pliego",
                          "No se detectaron anticipos/FONDEF en los PDF: confirmar igual la forma de pago publicada.", "Pliego"])
    groups.append({"h": "5 · Financiero",
                   "w": "Lo que se detectó en este expediente en particular (PDFs del pliego).",
                   "items": fin_items})

    # 6 · Si adjudican
    adm_items = [
        ["Garantía de cumplimiento 10%: 5 días hábiles",
         "Desde la comunicación de la adjudicación.", "24", 1],
        ["Perfeccionamiento del contrato",
         "Firma/aceptación dentro del plazo que indica la resolución.", "Pliego"],
        ["Datos de catalogación al organismo (si aplica)",
         "Fabricante, número de parte, marca/modelo, descripción y normas.", "38.5"],
    ]
    entrega_txt = "Lugar, horario y contacto indicados en el pliego; embalaje original sellado."
    if lugar_entrega:
        entrega_txt = f"Destino detectado en el pliego: {lugar_entrega.title()}. Coordinar día/horario; embalaje original sellado."
    adm_items.append(["Coordinar la entrega con el área requirente", entrega_txt, "38.1–38.3"])
    groups.append({"h": "6 · Si adjudican",
                   "w": "Plazos cortos desde que se perfecciona el contrato.",
                   "items": adm_items})

    return groups


# -------------------------------------------------------------------- HTML
CSS_CHECKLIST = """
:root{
  --bg:#F6F8F9; --surface:#FFFFFF; --fg:#16211F; --muted:#5B6967; --line:#D9E1E2;
  --accent:#1C98B4; --accent-soft:#E3F3F7; --warn:#B4531C; --warn-soft:#FBEDE4; --done:#2F7D5B;
  --f-display:"Segoe UI","Helvetica Neue",Arial,sans-serif;
  --f-body:"Segoe UI",system-ui,-apple-system,Arial,sans-serif;
  --f-mono:ui-monospace,"Cascadia Mono",Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0F1617; --surface:#162123; --fg:#E4ECEC; --muted:#93A4A3; --line:#2A3A3C;
  --accent:#4FC0D8; --accent-soft:#16343B; --warn:#E89566; --warn-soft:#3A2418; --done:#6CC39B; color-scheme:dark}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--f-body);font-size:15px;line-height:1.5;margin:0;padding:28px 16px 48px}
.wrap{max-width:760px;margin:0 auto;display:flex;flex-direction:column;gap:22px}
header{display:flex;flex-direction:column;gap:6px}
.ref{font-family:var(--f-mono);font-size:12px;color:var(--muted);letter-spacing:.02em}
h1{font-weight:700;font-size:28px;line-height:1.15;margin:0;text-wrap:balance}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--muted)}
.meta b{color:var(--fg);font-weight:600}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;border-radius:4px;padding:2px 8px;background:var(--accent-soft);color:var(--accent)}
.total{display:flex;align-items:center;gap:12px;margin-top:8px}
.bar{flex:1;height:8px;border-radius:4px;background:var(--line);overflow:hidden}
.bar i{display:block;height:100%;width:0;background:var(--accent);transition:width .25s}
.total span{font-family:var(--f-mono);font-size:13px;font-variant-numeric:tabular-nums;color:var(--muted);min-width:56px;text-align:right}
section{background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden}
section>h2{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:0;padding:12px 16px;
  font-size:15px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--line)}
section>h2 small{font-family:var(--f-mono);font-size:12px;font-weight:500;color:var(--muted);letter-spacing:0;text-transform:none;font-variant-numeric:tabular-nums}
.when{padding:8px 16px;font-size:13px;color:var(--muted);background:var(--accent-soft);border-bottom:1px solid var(--line)}
ul{list-style:none;margin:0;padding:0}
li{border-bottom:1px solid var(--line)}
li:last-child{border-bottom:0}
label{display:grid;grid-template-columns:22px 1fr;gap:10px;padding:11px 16px;cursor:pointer;align-items:start}
label:hover{background:var(--accent-soft)}
input[type=checkbox]{width:18px;height:18px;margin:2px 0 0;accent-color:var(--accent)}
input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.t{min-width:0}
.t strong{font-weight:600}
.t .d{display:block;font-size:13px;color:var(--muted);margin-top:2px}
.src{font-family:var(--f-mono);font-size:11px;color:var(--muted);white-space:nowrap}
.flag{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--warn);background:var(--warn-soft);border-radius:4px;padding:1px 6px;margin-left:6px;vertical-align:1px}
li.ok .t strong{text-decoration:line-through;text-decoration-color:var(--muted);color:var(--muted)}
.foot{font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
button{font:inherit;font-size:12px;color:var(--muted);background:none;border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer}
button:hover{color:var(--fg);border-color:var(--muted)}
a.back{color:var(--accent);text-decoration:none;font-size:13px}
a.back:hover{text-decoration:underline}
@media (prefers-reduced-motion: reduce){.bar i{transition:none}}
@media print{
  body{background:#fff;padding:0}
  section{break-inside:avoid;border-color:#bbb}
  .foot button,a.back{display:none}
}
"""

JS_CHECKLIST = """
const KEY = "checklist-" + PROC_NUM;
let st = {}; try { st = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
document.querySelectorAll('input[type=checkbox]').forEach(cb => {
  cb.checked = !!st[cb.id];
  cb.closest("li").classList.toggle("ok", cb.checked);
  cb.addEventListener("change", () => {
    st[cb.id] = cb.checked;
    cb.closest("li").classList.toggle("ok", cb.checked);
    save(); upd();
  });
});
function upd() {
  let a = 0, t = 0;
  document.querySelectorAll("section").forEach((s, gi) => {
    const boxes = s.querySelectorAll("input[type=checkbox]");
    let d = 0; boxes.forEach(b => { if (b.checked) d++; });
    a += d; t += boxes.length;
    const counter = s.querySelector("h2 small");
    if (counter) counter.textContent = d + "/" + boxes.length;
  });
  document.getElementById("nAll").textContent = a + " / " + t;
  document.getElementById("pAll").style.width = (t ? a / t * 100 : 0) + "%";
}
document.getElementById("reset").addEventListener("click", () => {
  st = {}; save();
  document.querySelectorAll("input[type=checkbox]").forEach(c => { c.checked = false; c.closest("li").classList.remove("ok"); });
  upd();
});
upd();
"""


def render_checklist_html(numero: str, fila: dict, grupos: list) -> str:
    apertura = _parse_fecha(fila["_apertura"])
    dias_ap = _dias_hasta(apertura)
    publicacion = _parse_fecha(fila["_publicacion"])
    fin_consultas = _parse_fecha(fila["_fin_consultas"])

    etiquetas = []
    if dias_ap is not None and dias_ap > 0:
        etiquetas.append(f"Apertura en <b>{dias_ap} día(s)</b>")
    elif dias_ap is not None and dias_ap <= 0:
        etiquetas.append("<b>Abierto / vencido</b>")
    if fila["_estado"] != "ACTIVA":
        etiquetas.append(f"Estado: <b>{_esc(fila['_estado'])}</b>")

    meta_html = "".join(
        f"<span>{lbl}: <b>{_esc(val)}</b></span>" for lbl, val in [
            ("Publicación", _fmt_fechita(publicacion)),
            ("Consultas hasta", _fmt_fechita(fin_consultas)),
            ("Apertura", _fmt_fechita(apertura)),
        ] if val != "—"
    )

    secciones = []
    for gi, g in enumerate(grupos):
        items_html = []
        for ii, it in enumerate(g["items"]):
            titulo, detalle, src = it[0], it[1], it[2]
            flag = len(it) > 3 and it[3]
            cid = f"i{gi}-{ii}"
            items_html.append(
                '<li><label for="{id}"><input type="checkbox" id="{id}">'
                '<span class="t"><strong>{tit}</strong>{flag}{det}<span class="src">Ref. {src}</span></span>'
                "</label></li>".format(
                    id=cid,
                    tit=_esc(titulo),
                    flag='<span class="flag">Causal de rechazo</span>' if flag else "",
                    det=f'<span class="d">{_esc(detalle)}</span>' if detalle else "",
                    src=_esc(src),
                )
            )
        secciones.append(
            "<section><h2><span>{h}</span><small></small></h2>{w}<ul>{items}</ul></section>".format(
                h=_esc(g["h"]),
                w=f'<div class="when">{_esc(g["w"])}</div>' if g.get("w") else "",
                items="".join(items_html),
            )
        )

    return f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Checklist {htmllib.escape(numero)} · {htmllib.escape(fila['_nombre'][:60])}</title>
<style>{CSS_CHECKLIST}</style>
</head><body>
<div class="wrap">
<header>
  <div class="ref"><a class="back" href="/">← Volver al dashboard</a> &nbsp;·&nbsp; LPU {_esc(numero)}</div>
  <h1>Checklist de participación<br><span style="font-size:19px;font-weight:600;color:var(--muted)">{_esc(fila['_nombre'])}</span></h1>
  <div class="meta">{meta_html} {" ".join(etiquetas)}</div>
  <div class="total"><div class="bar"><i id="pAll"></i></div><span id="nAll">0 / 0</span></div>
</header>
{"".join(secciones)}
<div class="foot">
  <span>Las tildes se guardan solo en este navegador (localStorage). Datos leídos del cronograma del dashboard.</span>
  <span><button id="reset" type="button">Desmarcar todo</button> <button type="button" onclick="window.print()">🖨️ Imprimir</button></span>
</div>
</div>
<script>const PROC_NUM = {json.dumps(numero)};</script>
<script>{JS_CHECKLIST}</script>
</body></html>"""


def generar_checklist_page(numero: str) -> tuple[int, str, str]:
    """(status_code, content_type, html) para el servidor."""
    fila = fila_proceso(numero)
    if fila is None:
        return 404, "text/html; charset=utf-8", (
            f"<h2>Proceso {htmllib.escape(numero)} no encontrado en cronograma_procesos.xlsx</h2>"
            f'<a href="/">Volver al dashboard</a>')
    grupos = construir_checklist(fila)
    return 200, "text/html; charset=utf-8", render_checklist_html(numero, fila, grupos)


if __name__ == "__main__":
    import sys
    n = sys.argv[1] if len(sys.argv) > 1 else "38/3-0429-LPU26"
    code, _, html_out = generar_checklist_page(n)
    with open("checklist_preview.html", "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"[{code}] checklist de {n} escrito en checklist_preview.html")
