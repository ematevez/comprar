# pip install playwright pandas openpyxl pypdf
# playwright install chromium

import os
import re
import glob
import pandas as pd
from playwright.sync_api import sync_playwright

from comprar import login_comprar  # reutiliza el login ya probado en comprar_pr.py

CUIT = "25418019"
PASSWORD = "25418019"
EXCEL_ENTRADA = os.environ.get("NOMBRE_EXCEL", "procesos_armada.xlsx")
CARPETA_SALIDA = "detalle_procesos"


def sanitizar_nombre(texto: str) -> str:
    """Reemplaza caracteres inválidos para nombres de archivo/carpeta (ej: '38/19-0369-LPU26' tiene '/')."""
    return re.sub(r'[\\/*?:"<>|]', "_", texto)


def buscar_proceso_por_numero(page, numero_proceso: str) -> bool:
    """
    Usa el buscador rápido (Buscar Proceso > Número de proceso) y hace click
    en el resultado. Devuelve False si no lo encontró.
    """
    page.fill('#ctl00_CPH1_txtNumProceso', numero_proceso)
    page.click('#ctl00_CPH1_btnBusquedaRapida')

    try:
        page.wait_for_load_state('networkidle', timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    link = page.locator(f'a:has-text("{numero_proceso}")').first
    try:
        link.wait_for(timeout=15000)
    except Exception:
        print(f"   ⚠️ No encontré el link del proceso {numero_proceso} tras la búsqueda rápida.")
        return False

    link.click()
    try:
        page.wait_for_load_state('load', timeout=30000)
    except Exception:
        pass
    try:
        page.wait_for_load_state('networkidle', timeout=30000)
    except Exception:
        pass

    # wait_for_selector reintenta a través de navegaciones (a diferencia de query_selector),
    # así que esperamos acá a que la página de detalle esté realmente lista.
    try:
        page.wait_for_selector(
            '#ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaPublicacion, '
            '#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos',
            timeout=30000
        )
    except Exception:
        print(f"   ⚠️ La página de detalle de {numero_proceso} no terminó de cargar en 30s.")

    page.wait_for_timeout(1000)
    return True


def extraer_cronograma(page) -> dict:
    """Lee los campos del panel 'Cronograma' por sus id fijos. Si un campo no existe, queda None."""
    campos = {
        'Fecha publicación portal': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaPublicacion',
        'Fecha publicación boletín oficial': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaPublicacionOficial',
        'Fecha inicio consultas': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaInicioConsultas',
        'Fecha final consultas': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaFinalConsultas',
        'Fecha inicio recepción documentos físicos': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaInicioRecepcionDocumentos',
        'Fecha fin recepción documentos físicos': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaFinRecepcionDocumentos',
        'Cantidad de días a publicar': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblCantidadDiasPublicar',
        'Fecha acto de apertura': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaActoApertura',
        'Fecha inicio recepción de muestras': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaInicioRecepcionMuestra',
        'Fecha fin recepción de muestras': 'ctl00_CPH1_UCVistaPreviaPliego_UC_Cronograma_lblFechaFinRecepcionMuestra',
    }
    cronograma = {}
    for nombre, elid in campos.items():
        el = page.query_selector(f'#{elid}')
        cronograma[nombre] = el.inner_text().strip() if el else None
    return cronograma


def descargar_clausulas(page, carpeta_destino: str) -> list:
    """
    Descarga todos los documentos listados en la tabla de Actos Administrativos
    (Cláusulas Particulares, etc.) ejecutando el __doPostBack directamente y
    capturando la descarga con page.expect_download().
    """
    tabla = page.query_selector('#ctl00_CPH1_UCVistaPreviaPliego_UC_Clausulas_gvActosAdministrativos')
    if not tabla:
        print("   ⚠️ No encontré la tabla de documentos/actos administrativos en este proceso.")
        return []

    filas = tabla.query_selector_all('tbody tr')
    descargados = []

    for i, fila in enumerate(filas):
        link = fila.query_selector('a[id*="btnVer"]')
        nombre_doc_el = fila.query_selector('span[id*="lblDocumento"]')
        nombre_doc = nombre_doc_el.inner_text().strip() if nombre_doc_el else f"documento_{i}"

        if not link:
            continue

        # 1) Extraer el target del href="javascript:__doPostBack('TARGET','')"
        href = link.get_attribute("href") or ""
        match = re.search(r"__doPostBack\(\s*'([^']+)'\s*,\s*'([^']*)'\s*\)", href)
        if not match:
            print(f"   ⚠️ '{nombre_doc}': no pude parsear el __doPostBack del href: {href}")
            continue
        target, argument = match.group(1), match.group(2)

        # 2) Skip si ya existe el archivo (evita re-descargas)
        ya_existe = glob.glob(os.path.join(carpeta_destino, sanitizar_nombre(nombre_doc) + ".*"))
        if ya_existe:
            print(f"   ⏭️ '{nombre_doc}' ya estaba descargado ({os.path.abspath(ya_existe[0])}), lo salteo.")
            descargados.append(ya_existe[0])
            continue

        # 3) Contar cuántas pestañas/páginas hay antes del click, para detectar popup
        paginas_antes = set(p for p in page.context.pages)

        # 4) Capturar la descarga con el helper oficial de Playwright
        try:
            with page.expect_download(timeout=30000) as download_info:
                # Ejecutamos el postback directamente: es el mismo camino que usa el sitio
                page.evaluate(f"__doPostBack('{target}', '{argument}')")

            download = download_info.value
            extension = os.path.splitext(download.suggested_filename)[1] or ".pdf"
            nombre_archivo = sanitizar_nombre(nombre_doc) + extension
            destino = os.path.join(carpeta_destino, nombre_archivo)
            download.save_as(destino)

            if os.path.exists(destino) and os.path.getsize(destino) > 0:
                print(f"   📥 Descargado: {os.path.abspath(destino)}")
                descargados.append(destino)
            else:
                print(f"   ⚠️ '{nombre_doc}': el archivo quedó vacío o no se guardó.")
                try:
                    download.delete()
                except Exception:
                    pass

        except Exception as e:
            # 5) Fallback: a veces COMPR.AR abre el PDF en una nueva pestaña en vez de descargarlo
            print(f"   ⚠️ '{nombre_doc}' no disparó descarga directa ({e}). Buscando popup...")
            try:
                # Esperamos un poco a que aparezca la nueva página
                page.wait_for_timeout(2000)
                paginas_nuevas = [p for p in page.context.pages if p not in paginas_antes]
                if paginas_nuevas:
                    popup = paginas_nuevas[0]
                    popup.wait_for_load_state("networkidle", timeout=15000)
                    # Si es un PDF embebido, la URL suele terminar en .pdf o el content-type lo indica
                    url_popup = popup.url
                    nombre_archivo = sanitizar_nombre(nombre_doc) + ".pdf"
                    destino = os.path.join(carpeta_destino, nombre_archivo)
                    # Pedimos el contenido crudo de la respuesta
                    resp = popup.request.get(url_popup)
                    with open(destino, "wb") as f:
                        f.write(resp.body())
                    popup.close()
                    if os.path.exists(destino) and os.path.getsize(destino) > 0:
                        print(f"   📥 Descargado desde popup: {os.path.abspath(destino)}")
                        descargados.append(destino)
                    else:
                        print(f"   ❌ '{nombre_doc}': no pude guardar el PDF del popup.")
                else:
                    print(f"   ❌ '{nombre_doc}': no hubo descarga ni popup. "
                          f"(postback target: {target})")
                    # Debug opcional
                    try:
                        page.screenshot(path=os.path.join(carpeta_destino, "debug_sin_descarga.png"),
                                        full_page=True)
                    except Exception:
                        pass
            except Exception as e2:
                print(f"   ❌ '{nombre_doc}': fallback de popup también falló: {e2}")

        # 6) Esperar a que el UpdatePanel termine su postback (overlay de carga)
        try:
            page.wait_for_selector('#divPanelFondoTransparente', state='hidden', timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(800)

    return descargados


def buscar_terminos_en_pdfs(rutas_pdf: list) -> dict:
    """
    Abre cada PDF descargado, extrae el texto y busca menciones a FONDEF,
    'pago adelantado' y TODAS las referencias de cláusula tipo 6.8.X (no solo la primera).
    """
    resultado = {
        'PDF - FONDEF': None,
        'PDF - Pago adelantado': None,
        'PDF - Cláusulas 6.8.X encontradas': None,
        'PDF - Menciona 6.8.7': 'No',
        'PDF - Menciona 6.8.2': 'No',
        'PDF - Archivo fuente': None,
    }
    try:
        from pypdf import PdfReader
    except ImportError:
        resultado['PDF - Error'] = "Falta instalar pypdf (pip install pypdf)"
        return resultado

    clausulas_vistas = []  # (clausula, contexto) sin duplicados, en orden de aparición
    clausulas_ya_agregadas = set()

    for ruta in rutas_pdf:
        if not ruta.lower().endswith('.pdf'):
            continue
        try:
            reader = PdfReader(ruta)
            texto = " ".join((p.extract_text() or "") for p in reader.pages)
            texto = re.sub(r'\s+', ' ', texto).strip()
        except Exception as e:
            print(f"   ⚠️ No pude leer '{ruta}': {e}")
            continue

        if resultado['PDF - FONDEF'] is None:
            m = re.search(r'.{0,60}fondef.{0,150}', texto, re.IGNORECASE)
            if m:
                resultado['PDF - FONDEF'] = m.group(0).strip()

        if resultado['PDF - Pago adelantado'] is None:
            m = re.search(r'.{0,60}pago\s+adelantado.{0,150}', texto, re.IGNORECASE)
            if m:
                resultado['PDF - Pago adelantado'] = m.group(0).strip()

        # Todas las coincidencias de 6.8.X en este documento (no solo la primera)
        for m in re.finditer(r'(?:inc\.?\s*)?6\.8\.\d+', texto, re.IGNORECASE):
            clausula = re.sub(r'\s+', ' ', m.group(0)).strip()
            clave = clausula.lower().replace('inc', '').replace('.', '').strip()
            if clave in clausulas_ya_agregadas:
                continue
            clausulas_ya_agregadas.add(clave)

            contexto_inicio = max(0, m.start() - 60)
            contexto_fin = min(len(texto), m.end() + 150)
            contexto = texto[contexto_inicio:contexto_fin].strip()
            clausulas_vistas.append((clausula, contexto))

            if '6.8.7' in clausula:
                resultado['PDF - Menciona 6.8.7'] = 'Sí'
            if '6.8.2' in clausula:
                resultado['PDF - Menciona 6.8.2'] = 'Sí'

        if clausulas_vistas or resultado['PDF - FONDEF'] or resultado['PDF - Pago adelantado']:
            resultado['PDF - Archivo fuente'] = os.path.basename(ruta)

    if clausulas_vistas:
        # Ej: "6.8.2 (...contexto...) | 6.8.7 (...contexto...)"
        resultado['PDF - Cláusulas 6.8.X encontradas'] = " | ".join(
            f"{c} ({ctx})" for c, ctx in clausulas_vistas
        )

    return resultado


def extraer_forma_pago(page) -> dict:
    """
    Busca en TODO el HTML de la página de detalle (no solo lo visible) menciones a
    'forma de pago' y referencias de cláusula tipo '6.8.7' / 'inc. 6.8.X'.
    Como no sabemos en qué panel/pestaña puntual aparece, buscamos sobre el HTML
    completo así no dependemos de un id específico.
    """
    html = page.content()
    texto = re.sub(r'<[^>]+>', ' ', html)   # saca tags
    texto = re.sub(r'&nbsp;', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()

    resultado = {
        'Forma de pago (contexto)': None,
        'FONDEF (página)': None,
        'Cláusula referenciada': None,
    }

    # Contexto alrededor de "forma de pago" (80 caracteres antes, 250 después)
    match_contexto = re.search(r'.{0,80}forma de pago.{0,250}', texto, re.IGNORECASE)
    if match_contexto:
        resultado['Forma de pago (contexto)'] = match_contexto.group(0).strip()

    # FONDEF como medio de pago, mencionado directo en la página (no solo en el PDF)
    match_fondef = re.search(r'.{0,80}fondef.{0,250}', texto, re.IGNORECASE)
    if match_fondef:
        resultado['FONDEF (página)'] = match_fondef.group(0).strip()

    # Referencias tipo "6.8.7", "inc. 6.8.12", "Inc 6.8.3" (6.8.X con X = uno o más dígitos)
    match_clausula = re.search(r'(?:inc\.?\s*)?6\.8\.\d+', texto, re.IGNORECASE)
    if match_clausula:
        resultado['Cláusula referenciada'] = match_clausula.group(0).strip()

    return resultado


def procesar_detalle(numeros_proceso: list) -> list:
    resumen = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        login_comprar(page, CUIT, PASSWORD)

        for numero in numeros_proceso:
            print(f"\n➡️ Procesando {numero}...")
            carpeta = os.path.join(CARPETA_SALIDA, sanitizar_nombre(numero))
            os.makedirs(carpeta, exist_ok=True)

            cronograma = {'Número de proceso': numero}
            try:
                # Arrancamos siempre desde el buscador para no acumular estado de navegación previo.
                page.goto("https://comprar.gob.ar/OFE/BusquedaAvanzadaProveedor.aspx", timeout=60000, wait_until="domcontentloaded")
                page.wait_for_load_state('networkidle')

                if not buscar_proceso_por_numero(page, numero):
                    cronograma['Error'] = 'No encontrado en búsqueda rápida'
                    resumen.append(cronograma)
                    continue

                cronograma.update(extraer_cronograma(page))
                cronograma.update(extraer_forma_pago(page))
            except Exception as e:
                print(f"   ❌ Error obteniendo cronograma de {numero}: {e}")
                cronograma['Error'] = str(e)
                resumen.append(cronograma)
                page.wait_for_timeout(1500)
                continue

            # La descarga va en un try separado: si falla, no perdemos el cronograma
            # que ya conseguimos arriba -- solo anotamos el error de descarga en la misma fila.
            try:
                descargar_clausulas_resultado = descargar_clausulas(page, carpeta)
                if descargar_clausulas_resultado:
                    cronograma.update(buscar_terminos_en_pdfs(descargar_clausulas_resultado))
            except Exception as e:
                print(f"   ❌ Error descargando cláusulas de {numero}: {e}")
                cronograma['Error descarga'] = str(e)

            resumen.append(cronograma)
            page.wait_for_timeout(1500)  # margen entre procesos para no saturar el sitio

        browser.close()

    return resumen


if __name__ == "__main__":
    df_entrada = pd.read_excel(EXCEL_ENTRADA)
    numeros = df_entrada['Número de proceso'].dropna().unique().tolist()
    print(f"📋 {len(numeros)} procesos a detallar (leídos de {os.path.abspath(EXCEL_ENTRADA)}).")

    resumen = procesar_detalle(numeros)

    df_resumen = pd.DataFrame(resumen)
    nombre_salida = "cronograma_procesos.xlsx"
    df_resumen.to_excel(nombre_salida, index=False)
    print(f"\n📁 Resumen de cronogramas guardado en {os.path.abspath(nombre_salida)}")
    print(f"📁 Cláusulas descargadas en {os.path.abspath(CARPETA_SALIDA)}/<número de proceso>/")