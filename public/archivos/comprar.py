# comprar.py - VERSIÓN SEGURA (sin credenciales hardcodeadas)
# Las credenciales se cargan desde variables de entorno (.env)
# pip install playwright pandas openpyxl python-dotenv
# playwright install chromium

import os
import sys
import json
import logging
import threading
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================
# CREDENCIALES - Ahora desde variables de entorno (SEGURO)
# ============================================================
CUIT = os.environ.get("CUIT")
PASSWORD = os.environ.get("PASSWORD")

if not CUIT or not PASSWORD:
    print("❌ ERROR: Faltan variables de entorno CUIT y/o PASSWORD")
    print("   Configurá tu archivo .env (ver .env.example)")
    sys.exit(1)

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================
LOG_FILE = "logs_comprar.txt"

logger = logging.getLogger("comprar")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
file_handler.setFormatter(file_fmt)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_fmt = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_fmt)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_info(msg):
    logger.info(msg)


def log_error(msg):
    logger.error(msg)


def log_warning(msg):
    logger.warning(msg)


# ============================================================
# WATCHDOG DE INACTIVIDAD
# ============================================================
class InactivityWatchdog:
    def __init__(self, timeout_seconds=60, browser=None):
        self.timeout = timeout_seconds
        self.browser = browser
        self.last_activity = datetime.now()
        self._timer = None
        self._stopped = False
    
    def start(self):
        self._schedule_check()
    
    def stop(self):
        self._stopped = True
        if self._timer:
            self._timer.cancel()
    
    def ping(self):
        self.last_activity = datetime.now()
    
    def _schedule_check(self):
        if self._stopped:
            return
        self._timer = threading.Timer(10.0, self._check)
        self._timer.daemon = True
        self._timer.start()
    
    def _check(self):
        if self._stopped:
            return
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        if elapsed > self.timeout:
            log_warning(f"⚠️ INACTIVIDAD DETECTADA: {elapsed:.0f}s sin actividad. Cerrando navegador...")
            if self.browser:
                try:
                    self.browser.close()
                    log_info("🔒 Navegador cerrado por inactividad.")
                except Exception as e:
                    log_error(f"Error cerrando navegador: {e}")
            os._exit(1)
        else:
            self._schedule_check()


# ============================================================
# FUNCIONES (sin cambios respecto al original)
# ============================================================
def cargar_estado(path="estado_procesos.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ultima_ejecucion": None, "procesos": {}}


def guardar_estado(path, estado):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def debe_ejecutar(estado, intervalo_horas):
    ultima = estado.get("ultima_ejecucion")
    if not ultima:
        return True
    ultima_dt = datetime.fromisoformat(ultima)
    return datetime.now() - ultima_dt >= timedelta(hours=intervalo_horas)


def login_comprar(page, cuit: str, password: str, nombre_perfil: str = "MEZZINAMIRIAN"):
    page.goto("https://comprar.gob.ar/Login.aspx")
    page.fill('input[id="txtUsername_txtTextBox"]', cuit)
    page.click('a#lnkConfirmar')
    page.wait_for_load_state('networkidle')
    
    select_locator = page.locator("select").first
    opciones = select_locator.locator("option").all_inner_texts()
    perfil = next((o for o in opciones if nombre_perfil in o.upper()), None)
    if not perfil:
        raise Exception(f"No encontré el perfil '{nombre_perfil}' entre las opciones: {opciones}")
    select_locator.select_option(label=perfil)
    
    page.get_by_placeholder("Contraseña").fill(password)
    page.click('#btnIngresar')
    page.wait_for_load_state('networkidle')
    log_info("✅ Login completado.")
    
    try:
        page.wait_for_selector('#z9GQt', timeout=5000)
        page.click('#z9GQt')
        log_info("✅ Accediste al Escritorio del Comprador.")
    except Exception:
        log_warning("⚠️ No se encontró el botón 'Acceder' (puede que ya hayas entrado directo).")


def extraer_pagina_actual(page):
    tabla = page.query_selector('#ctl00_CPH1_GridListaPliegos')
    if not tabla:
        return [], []
    header_row = tabla.query_selector('tr.tr-header')
    if not header_row:
        return [], []
    headers = [th.inner_text().strip() for th in header_row.query_selector_all('th')]
    indices_utiles = [i for i, h in enumerate(headers) if h != 'Acciones']
    headers_utiles = [headers[i] for i in indices_utiles]
    data = []
    filas = tabla.query_selector_all('tr')
    for row in filas:
        clase = row.get_attribute('class') or ''
        if 'tr-header' in clase or 'pagination-gv' in clase:
            continue
        cols = row.query_selector_all('td')
        if len(cols) < len(headers):
            continue
        registro = {headers_utiles[j]: cols[i].inner_text().strip() for j, i in enumerate(indices_utiles)}
        if any(registro.values()):
            data.append(registro)
    return data, headers_utiles


def buscar_lpu_en_apertura(page, fecha_desde: str, fecha_hasta: str, estado_label: str = "Publicado", watchdog=None):
    page.goto("https://comprar.gob.ar/OFE/BusquedaAvanzadaProveedor.aspx")
    page.wait_for_load_state('networkidle')
    if watchdog: watchdog.ping()

    try:
        for sel in page.query_selector_all('select'):
            opciones_texto = [o.inner_text() for o in sel.query_selector_all('option')]
            tiene_armada = any('armada' in t.lower() for t in opciones_texto)
            opcion_todos = next((t for t in opciones_texto if 'seleccionar' in t.lower() or t.strip().lower() in ('todas', 'todos', 'todas las unidades')), None)
            if tiene_armada and opcion_todos:
                sel_id = sel.get_attribute('id')
                seleccionada_actual = sel.evaluate("el => el.options[el.selectedIndex].text")
                if seleccionada_actual != opcion_todos:
                    page.select_option(f'#{sel_id}', label=opcion_todos)
                    print(f"ℹ️ Filtro de organismo ('{sel_id}') estaba en '{seleccionada_actual}' -> lo reseteé a '{opcion_todos}'.")
    except Exception as e:
        print(f"⚠️ No pude chequear el filtro de organismo: {e}")
    if watchdog: watchdog.ping()
    
    page.fill('#ctl00_CPH1_devDteEdtFechaDesde_I', fecha_desde)
    page.fill('#ctl00_CPH1_devDteEdtFechaHasta_I', fecha_hasta)
    page.select_option('#ctl00_CPH1_ddlTipoProceso', value="1")
    page.select_option('#ctl00_CPH1_ddlEstado', label=estado_label)
    page.click('#ctl00_CPH1_btnBusquedaAvanzada')
    if watchdog: watchdog.ping()
    
    log_info("🕒 Esperando respuesta del buscador (puede tardar)...")
    
    modal_error = page.query_selector('#ctl00_CPH1_ModalError')
    if modal_error and modal_error.is_visible():
        log_error(f"❌ Apareció un modal de error en el sitio: {modal_error.inner_text().strip()}")
        return []
    
    try:
        page.wait_for_selector('#ctl00_CPH1_GridListaPliegos', timeout=90000)
        if watchdog: watchdog.ping()
    except Exception:
        page.screenshot(path="debug_resultados.png", full_page=True)
        with open("debug_resultados.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        log_warning(f"⚠️ No apareció la tabla de resultados en 90s.")
        return []
    
    data_total, headers = extraer_pagina_actual(page)
    log_info(f"📄 Página 1: {len(data_total)} registros.")
    if watchdog: watchdog.ping()
    
    if not data_total and not headers:
        page.screenshot(path="debug_resultados.png", full_page=True)
        with open("debug_resultados.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        return []
    
    pagina = 2
    primer_numero_pagina_anterior = data_total[0].get('Número de proceso') if data_total else None
    MAX_PAGINAS = 500
    while pagina <= MAX_PAGINAS:
        log_info(f"➡️ Yendo a la página {pagina}...")
        page.evaluate(f"__doPostBack('ctl00$CPH1$GridListaPliegos','Page${pagina}')")
        if watchdog: watchdog.ping()
        
        try:
            page.wait_for_load_state('networkidle', timeout=60000)
        except Exception:
            pass
        try:
            page.wait_for_selector('#divPanelFondoTransparente', state='hidden', timeout=60000)
        except Exception:
            pass
        page.wait_for_timeout(5000)
        if watchdog: watchdog.ping()
        
        data_pagina, _ = extraer_pagina_actual(page)
        if not data_pagina:
            log_info(f"🏁 Página {pagina} vino vacía -- fin de la paginación.")
            break

        primer_numero_actual = data_pagina[0].get('Número de proceso')
        if primer_numero_actual == primer_numero_pagina_anterior:
            log_info(f"🏁 La página {pagina} repite el contenido anterior -- fin de la paginación.")
            break
        primer_numero_pagina_anterior = primer_numero_actual

        log_info(f"📄 Página {pagina}: {len(data_pagina)} registros.")
        data_total.extend(data_pagina)
        pagina += 1
    
    log_info(f"✅ Total registros extraídos: {len(data_total)}")
    return data_total


def login_comprar_y_extraer(cuit: str, password: str, fecha_desde: str, fecha_hasta: str, 
                            estado_label: str = "Publicado", intervalo_minimo_horas: float = 24, 
                            estado_path: str = "estado_procesos.json", timeout_inactividad: int = 60):
    log_info("=" * 60)
    log_info("🚀 INICIO DE EJECUCIÓN - comprar.py")
    log_info("=" * 60)
    
    estado = cargar_estado(estado_path)
    forzado = os.environ.get("FORZAR_EJECUCION") == "1"
    if not forzado and not debe_ejecutar(estado, intervalo_minimo_horas):
        ultima_dt = datetime.fromisoformat(estado["ultima_ejecucion"])
        proxima = ultima_dt + timedelta(hours=intervalo_minimo_horas)
        log_info(f" Ya corrió hace menos de {intervalo_minimo_horas}h. Próxima: {proxima.strftime('%d/%m/%Y %H:%M')}.")
        return
    if forzado:
        log_info("🔓 Ejecución FORZADA manualmente.")
    
    browser = None
    watchdog = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            watchdog = InactivityWatchdog(timeout_seconds=timeout_inactividad, browser=browser)
            watchdog.start()
            log_info(f"️ Watchdog activado: {timeout_inactividad}s de inactividad")
            
            login_comprar(page, cuit, password)
            watchdog.ping()
            
            data = buscar_lpu_en_apertura(page, fecha_desde, fecha_hasta, 
                                         estado_label=estado_label, watchdog=watchdog)
            watchdog.ping()
            
            if data:
                clave = 'Número de proceso'
                actuales = {d[clave]: d for d in data if d.get(clave)}
                anteriores = estado.get("procesos", {})
                nuevos = [k for k in actuales if k not in anteriores]
                eliminados = [k for k in anteriores if k not in actuales]
                nombre_excel = os.environ.get("NOMBRE_EXCEL", "procesos_armada.xlsx")
                excel_faltante = not os.path.exists(nombre_excel)

                if nuevos or eliminados or excel_faltante:
                    log_info(f"🆕 Nuevos procesos ({len(nuevos)}): {', '.join(nuevos) if nuevos else '-'}")
                    log_info(f"🗑️ Eliminados ({len(eliminados)}): {', '.join(eliminados) if eliminados else '-'}")
                    df = pd.DataFrame(list(actuales.values()))
                    df.to_excel(nombre_excel, index=False)
                    log_info(f"📁 Excel actualizado: {nombre_excel} ({len(actuales)} registros).")
                else:
                    log_info("✅ Sin novedades. No se reescribe el Excel.")
                estado["procesos"] = actuales
            else:
                log_warning("⚠️ No se extrajo ningún dato.")
            
            estado["ultima_ejecucion"] = datetime.now().isoformat()
            guardar_estado(estado_path, estado)
            
            if watchdog:
                watchdog.stop()
            browser.close()
            log_info("🔒 Navegador cerrado correctamente.")
    
    except Exception as e:
        log_error(f"❌ ERROR FATAL: {e}")
        if watchdog:
            watchdog.stop()
        if browser:
            try:
                browser.close()
            except:
                pass
        raise
    
    log_info("=" * 60)
    log_info("✅ FIN DE EJECUCIÓN - comprar.py")
    log_info("=" * 60)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    # Las credenciales YA están cargadas arriba desde os.environ
    # CUIT y PASSWORD vienen del .env
    
    INTERVALO_MINIMO_HORAS = int(os.environ.get("INTERVALO_HORAS", "24"))
    TIMEOUT_INACTIVIDAD = int(os.environ.get("TIMEOUT_INACTIVIDAD", "60"))
    
    hoy = datetime.now()
    hace_un_mes = hoy - timedelta(days=30)
    fecha_desde = hace_un_mes.strftime("%d/%m/%Y")
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    
    log_info(f"📅 Período de búsqueda: {fecha_desde} a {fecha_hasta}")
    log_info(f"⏱️ Timeout de inactividad: {TIMEOUT_INACTIVIDAD}s")
    log_info(f"🔐 Credenciales cargadas desde variables de entorno ✅")
    
    login_comprar_y_extraer(
        CUIT, 
        PASSWORD, 
        fecha_desde=fecha_desde, 
        fecha_hasta=fecha_hasta,
        estado_label="Publicado", 
        intervalo_minimo_horas=INTERVALO_MINIMO_HORAS,
        timeout_inactividad=TIMEOUT_INACTIVIDAD
    )
