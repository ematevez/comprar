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


def _pdf_contiene(numero: str, patron: str) -> bool:
    """Busca un regex dentro de los PDF descargados del proceso (si existen)."""
    carpeta = os.path.join(BASE_DIR, "detalle_procesos", sanitizar_nombre(numero))
    if not os.path.isdir(carpeta):
        return False
    try:
        from pypdf import PdfReader
    except ImportError:
        return False
    pat = re.compile(patron, re.IGNORECASE)
    for fn in os.listdir(carpeta):
        if not fn.lower().endswith(".pdf"):
            continue
        try:
            reader = PdfReader(os.path.join(carpeta, fn))
            for page in reader.pages:
                if pat.search(page.extract_text() or ""):
                    return True
        except Exception:
            continue
    return False


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
    groups.append({"h": "2 · Cotización con el proveedor",
                   "w": "Pedir ya. Verificar alcances, plazos y moneda contra lo que exige el pliego.",
                   "items": [
                       ["Cotización formal del producto/servicio",
                        "Vigente hasta después de la apertura. Si es del exterior, indicar condición de entrega (ej. CIF) y moneda.", "—"],
                       ["Folletería / ficha técnica del producto",
                        "Debe mostrar las características pedidas en el Anexo de Especificaciones Técnicas.", "Pliego"],
                       ["Marca, modelo y código / número de parte",
                        "Datos del fabricante: razón social, dirección, web y número de parte (sirven también para la catalogación).", "Pliego"],
                       ["Certificaciones exigidas por el pliego (ISO, CE, etc.)",
                        "Si se adjuntan a la oferta, traducidas por traductor público y legalizadas.", "Pliego"],
                       ["Garantía del fabricante",
                        "Respaldar la garantía técnica que se declara en la oferta.", "Pliego"],
                       ["Confirmar plazo y lugar de entrega exigidos",
                        f"Comparar contra el cronograma del expediente antes de comprometerla.", "Cronograma"],
                   ]})

    # 3 · Documentación de la oferta en COMPR.AR
    doc_items = [
        ["Garantía de mantenimiento de oferta: 5%",
         "Póliza electrónica de caución a favor del organismo contratante, en la moneda de la oferta. Si no es electrónica, el original va a Tesorería dentro de los 2 días hábiles.", "15.1", 1],
        ["Declaración Jurada de Intereses (Decreto 202/17)",
         "Formulario digital de la Oficina Anticorrupción.", "15.2 · Anexo I"],
        ["DDJJ de Elegibilidad", "Firmada.", "15.3 · Anexo III"],
        ["DDJJ de Habilidad para Contratar", "Firmada.", "15.3 · Anexo IV"],
        ["Certificado de garantía técnica firmado",
         "Completar CUIT, domicilio, marca y modelo.", "15.4 · Pliego", 1],
        ["Documentación técnica traducida (si corresponde)",
         "Traductor público, legalizada por el Colegio de Traductores.", "15"],
        ["Precio ofertado completo",
         "Incluir flete, seguro, aranceles y descarga donde exija el pliego.", "Pliego"],
        ["Confirmar la oferta con el Administrador Legitimado",
         "Una oferta editada y NO reconfirmada antes de la apertura se considera retirada.", "16", 1],
    ]
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
        fin_items.append(["Contragarantía del anticipo: 3 días hábiles de perfeccionado el contrato",
                          "Sin ella no se cobra el anticipo. Póliza electrónica a favor del mismo organismo.", "43 · 26", 1])
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
        ["Coordinar la entrega con el área requirente",
         "Lugar, horario y contacto indicados en el pliego; embalaje original sellado.", "38.1–38.3"],
    ]
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
