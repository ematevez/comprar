# pip install playwright pandas openpyxl pypdf
# playwright install chromium

import os
import re
import glob
import pandas as pd
from playwright.sync_api import sync_playwright

from comprar import login_comprar, InactivityWatchdog, cargar_estado, debe_ejecutar, guardar_estado  # reutiliza login, watchdog y auto-límite de comprar.py
from datetime import datetime, timedelta

CUIT = "25418019"
PASSWORD = "25418019"
EXCEL_ENTRADA = os.environ.get("NOMBRE_EXCEL", "procesos_armada.xlsx")
CARPETA_SALIDA = "detalle_procesos"
ESTADO_PATH = "estado_detalle.json"  # separado del estado_procesos.json de comprar.py


def sanitizar_nombre(texto: str) -> str:
    """Reemplaza caracteres inválidos para nombres de archivo/carpeta."""
    return re.sub(r'[\\/*?:"<>|]', "_", texto)


def buscar_proceso_por_numero(page, numero_proceso: str) -> bool:
    """Usa el buscador rápido y hace click en el resultado."""
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
    """Lee los campos del panel 'Cronograma' por sus id fijos."""
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


def extraer_nombre_proceso(page) -> str:
    """
    Nombre descriptivo del proceso, desde la cabecera del pliego
    (id ...usrCabeceraPliego_lblNomPliego). cronograma_procesos.xlsx nunca
    lo tenía -- solo estaba en procesos_armada.xlsx (el de comprar.py) -- por
    eso el dashboard mostraba siempre "Sin nombre".
    """
    el = page.query_selector('span[id*="usrCabeceraPliego_lblNomPliego"]')
    if el:
        texto = el.inner_text().strip()
        if texto:
            return texto
    return None


def extraer_objeto_gasto(page) -> str:
    """
    NUEVA FUNCIÓN: Busca en las tablas de la página la que tenga "Objeto del gasto"
    y devuelve los códigos encontrados separados por coma (ej: "4.3.3, 4.3.8").
    """
    tablas = page.query_selector_all('table')
    for tabla in tablas:
        headers = [th.inner_text().strip() for th in tabla.query_selector_all('th')]
        if 'Objeto del gasto' in headers:
            idx_objeto = headers.index('Objeto del gasto')
            objetos = set()
            for tr in tabla.query_selector_all('tbody tr'):
                cols = tr.query_selector_all('td')
                if len(cols) > idx_objeto:
                    val = cols[idx_objeto].inner_text().strip()
                    if val:
                        objetos.add(val)
            if objetos:
                return ', '.join(sorted(objetos))
    return None


def descargar_clausulas(page, carpeta_destino: str) -> list:
    """Descarga documentos ejecutando __doPostBack y capturando con expect_download."""
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

        href = link.get_attribute("href") or ""
        match = re.search(r"__doPostBack\(\s*'([^']+)'\s*,\s*'([^']*)'\s*\)", href)
        if not match:
            print(f"   ⚠️ '{nombre_doc}': no pude parsear el __doPostBack del href: {href}")
            continue
        target, argument = match.group(1), match.group(2)

        ya_existe = glob.glob(os.path.join(carpeta_destino, sanitizar_nombre(nombre_doc) + ".*"))
        if ya_existe:
            print(f"   ⏭️ '{nombre_doc}' ya estaba descargado ({os.path.abspath(ya_existe[0])}), lo salteo.")
            descargados.append(ya_existe[0])
            continue

        paginas_antes = set(p for p in page.context.pages)

        try:
            with page.expect_download(timeout=30000) as download_info:
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
            print(f"   ⚠️ '{nombre_doc}' no disparó descarga directa ({e}). Buscando popup...")
            try:
                page.wait_for_timeout(2000)
                paginas_nuevas = [p for p in page.context.pages if p not in paginas_antes]
                if paginas_nuevas:
                    popup = paginas_nuevas[0]
                    popup.wait_for_load_state("networkidle", timeout=15000)
                    url_popup = popup.url
                    nombre_archivo = sanitizar_nombre(nombre_doc) + ".pdf"
                    destino = os.path.join(carpeta_destino, nombre_archivo)
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
                    print(f"   ❌ '{nombre_doc}': no hubo descarga ni popup. (postback target: {target})")
                    try:
                        page.screenshot(path=os.path.join(carpeta_destino, "debug_sin_descarga.png"), full_page=True)
                    except Exception:
                        pass
            except Exception as e2:
                print(f"   ❌ '{nombre_doc}': fallback de popup también falló: {e2}")

        try:
            page.wait_for_selector('#divPanelFondoTransparente', state='hidden', timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(800)

    return descargados


def buscar_terminos_en_pdfs(rutas_pdf: list) -> dict:
    """Abre cada PDF y busca menciones a FONDEF, pago adelantado y cláusulas 6.8.X"""
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

    clausulas_vistas = []
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
        resultado['PDF - Cláusulas 6.8.X encontradas'] = " | ".join(
            f"{c} ({ctx})" for c, ctx in clausulas_vistas
        )

    return resultado


def extraer_forma_pago(page) -> dict:
    """Busca en el HTML de la página menciones a forma de pago y cláusulas."""
    html = page.content()
    texto = re.sub(r'<[^>]+>', ' ', html)
    texto = re.sub(r'&nbsp;', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()

    resultado = {
        'Forma de pago (contexto)': None,
        'FONDEF (página)': None,
        'Cláusula referenciada': None,
    }

    match_contexto = re.search(r'.{0,80}forma de pago.{0,250}', texto, re.IGNORECASE)
    if match_contexto:
        resultado['Forma de pago (contexto)'] = match_contexto.group(0).strip()

    match_fondef = re.search(r'.{0,80}fondef.{0,250}', texto, re.IGNORECASE)
    if match_fondef:
        resultado['FONDEF (página)'] = match_fondef.group(0).strip()

    match_clausula = re.search(r'(?:inc\.?\s*)?6\.8\.\d+', texto, re.IGNORECASE)
    if match_clausula:
        resultado['Cláusula referenciada'] = match_clausula.group(0).strip()

    return resultado


def procesar_detalle(numeros_proceso: list, timeout_inactividad: int = 90, guardar_parcial_cada: int = 10) -> list:
    """
    timeout_inactividad: si no hay actividad (login, avance entre procesos, descarga)
    en estos segundos, el watchdog cierra el navegador y termina el proceso solo --
    así el dashboard nunca se queda esperando un proceso hijo colgado para siempre.

    guardar_parcial_cada: cada tantos procesos, escribe cronograma_procesos.xlsx
    con lo que hay hasta el momento (no solo al final). Así, si el proceso se corta
    a la fuerza desde afuera (ej. el timeout del dashboard), se pierde como máximo
    esa cantidad de procesos en vez de la corrida entera.
    """
    resumen = []
    browser = None
    watchdog = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            watchdog = InactivityWatchdog(timeout_seconds=timeout_inactividad, browser=browser)
            watchdog.start()

            login_comprar(page, CUIT, PASSWORD)
            watchdog.ping()

            for numero in numeros_proceso:
                print(f"\n➡️ Procesando {numero}...")
                carpeta = os.path.join(CARPETA_SALIDA, sanitizar_nombre(numero))
                os.makedirs(carpeta, exist_ok=True)

                cronograma = {'Número de proceso': numero}
                try:
                    page.goto("https://comprar.gob.ar/OFE/BusquedaAvanzadaProveedor.aspx", timeout=60000, wait_until="domcontentloaded")
                    page.wait_for_load_state('networkidle')

                    if not buscar_proceso_por_numero(page, numero):
                        cronograma['Error'] = 'No encontrado en búsqueda rápida'
                        resumen.append(cronograma)
                        watchdog.ping()
                        continue

                    cronograma.update(extraer_cronograma(page))
                    cronograma.update(extraer_forma_pago(page))

                    nombre_proceso = extraer_nombre_proceso(page)
                    cronograma['Nombre de proceso'] = nombre_proceso or 'Sin nombre en la página'

                    # ==========================================
                    # AQUÍ SE AGREGÓ LA EXTRACCIÓN DEL OBJETO DEL GASTO
                    # ==========================================
                    objeto_gasto = extraer_objeto_gasto(page)
                    if objeto_gasto:
                        cronograma['Objeto del gasto (detalle)'] = objeto_gasto
                    else:
                        cronograma['Objeto del gasto (detalle)'] = 'No encontrado en tabla'
                    # ==========================================

                except Exception as e:
                    print(f"   ❌ Error obteniendo cronograma de {numero}: {e}")
                    cronograma['Error'] = str(e)
                    resumen.append(cronograma)
                    page.wait_for_timeout(1500)
                    watchdog.ping()
                    continue

                try:
                    descargar_clausulas_resultado = descargar_clausulas(page, carpeta)
                    if descargar_clausulas_resultado:
                        cronograma.update(buscar_terminos_en_pdfs(descargar_clausulas_resultado))
                except Exception as e:
                    print(f"   ❌ Error descargando cláusulas de {numero}: {e}")
                    cronograma['Error descarga'] = str(e)

                resumen.append(cronograma)
                watchdog.ping()  # avanzamos de proceso -> hubo actividad, reseteamos el reloj

                if guardar_parcial_cada and len(resumen) % guardar_parcial_cada == 0:
                    try:
                        pd.DataFrame(resumen).to_excel("cronograma_procesos.xlsx", index=False)
                        print(f"   💾 Guardado parcial ({len(resumen)} procesos hasta ahora).")
                    except Exception as e:
                        print(f"   ⚠️ No pude guardar el parcial: {e}")

                page.wait_for_timeout(1500)

            watchdog.stop()
            browser.close()
            print("🔒 Navegador cerrado correctamente.")

    except Exception as e:
        print(f"❌ ERROR FATAL: {e}")
        if watchdog:
            watchdog.stop()
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        print(f"⚠️ No se relanza el error -- se guardan los {len(resumen)} procesos que se "
              f"alcanzaron a procesar antes de que esto pasara, en vez de perderlos todos.")
        # Antes acá había un "raise" que hacía perder TODO el resumen acumulado si algo
        # fallaba a mitad de camino (login, un error grande fuera del try por-proceso, etc.)
        # -- ahora devolvemos lo parcial en vez de cortar antes de escribir el Excel.

    return resumen


if __name__ == "__main__":
    INTERVALO_MINIMO_HORAS = 24  # una vez por día -- poné 0 para no limitar

    estado = cargar_estado(ESTADO_PATH)
    forzado = os.environ.get("FORZAR_EJECUCION") == "1"
    if not forzado and not debe_ejecutar(estado, INTERVALO_MINIMO_HORAS):
        ultima_dt = datetime.fromisoformat(estado["ultima_ejecucion"])
        proxima = ultima_dt + timedelta(hours=INTERVALO_MINIMO_HORAS)
        print(f"⏳ Ya corrió hace menos de {INTERVALO_MINIMO_HORAS}h (última vez: {ultima_dt.strftime('%d/%m/%Y %H:%M')}). "
              f"Próxima corrida habilitada a partir de {proxima.strftime('%d/%m/%Y %H:%M')}. No se abre el navegador.")
        raise SystemExit(0)
    if forzado:
        print("🔓 Ejecución FORZADA manualmente -- se ignora el límite de 24h.")

    df_entrada = pd.read_excel(EXCEL_ENTRADA)
    numeros = df_entrada['Número de proceso'].dropna().unique().tolist()
    # Filtro por proceso único: lo usa el botón 🎯 Participar del dashboard
    # (descargar_expediente_proceso) para bajar solo las cláusulas de ese LPU.
    filtro = os.environ.get("PROCESO_ESPECIFICO", "").strip()
    if filtro:
        numeros = [n for n in numeros if str(n).strip() == filtro]
        print(f"🎯 PROCESO_ESPECIFICO={filtro} -> {len(numeros)} proceso(s) a detallar.")
    else:
        print(f"📋 {len(numeros)} procesos a detallar (leídos de {os.path.abspath(EXCEL_ENTRADA)}).")

    resumen = procesar_detalle(numeros)

    # En modo proceso único (botón 🎯 Participar) NO se sobreescribe el Excel:
    # se actualiza solo la fila de ese proceso, para no perder las demás.
    if filtro and resumen:
        try:
            df_actual = pd.read_excel(EXCEL_ENTRADA)
            col_num = 'Número de proceso'
            fila_nueva = pd.DataFrame(resumen)
            mask = df_actual[col_num].astype(str).str.strip() == str(
                fila_nueva.iloc[0][col_num]).strip()
            for col in fila_nueva.columns:
                if col not in df_actual.columns:
                    df_actual[col] = None
            df_actual.loc[mask, fila_nueva.columns] = fila_nueva.values
            df_actual.to_excel(EXCEL_ENTRADA, index=False)
            print(f"\n📁 Fila de {filtro} actualizada en {os.path.abspath(EXCEL_ENTRADA)} "
                  f"(resto del cronograma intacto)")
        except Exception as e:
            print(f"⚠️ No se pudo actualizar la fila individual: {e}")
            pd.DataFrame(resumen).to_excel("cronograma_parcial.xlsx", index=False)
            print("   Se guardó en cronograma_parcial.xlsx en su lugar.")
    else:
        df_resumen = pd.DataFrame(resumen)
        nombre_salida = "cronograma_procesos.xlsx"
        df_resumen.to_excel(nombre_salida, index=False)
        print(f"\n📁 Resumen de cronogramas guardado en {os.path.abspath(nombre_salida)}")
    print(f"📁 Cláusulas descargadas en {os.path.abspath(CARPETA_SALIDA)}/<número de proceso>/")

    estado["ultima_ejecucion"] = datetime.now().isoformat()
    guardar_estado(ESTADO_PATH, estado)