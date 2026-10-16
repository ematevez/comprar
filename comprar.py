# pip install playwright pandas openpyxl
# playwright install chromium

import os
import sys
import json
import logging
import threading
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import pandas as pd

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================
LOG_FILE = "logs_comprar.txt"

# Configurar logger que escribe a archivo Y consola
logger = logging.getLogger("comprar")
logger.setLevel(logging.INFO)

# Handler para archivo
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
file_handler.setFormatter(file_fmt)

# Handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_fmt = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_fmt)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_info(msg):
    """Log de información."""
    logger.info(msg)


def log_error(msg):
    """Log de error."""
    logger.error(msg)


def log_warning(msg):
    """Log de advertencia."""
    logger.warning(msg)


# ============================================================
# WATCHDOG DE INACTIVIDAD
# ============================================================
class InactivityWatchdog:
    """
    Monitorea la actividad del script. Si no hay actividad en X segundos,
    cierra el navegador y termina la ejecución.
    """
    
    def __init__(self, timeout_seconds=60, browser=None):
        self.timeout = timeout_seconds
        self.browser = browser
        self.last_activity = datetime.now()
        self._timer = None
        self._stopped = False
    
    def start(self):
        """Inicia el watchdog."""
        self._schedule_check()
    
    def stop(self):
        """Detiene el watchdog."""
        self._stopped = True
        if self._timer:
            self._timer.cancel()
    
    def ping(self):
        """Registra actividad (llamar cada vez que algo importante ocurre)."""
        self.last_activity = datetime.now()
    
    def _schedule_check(self):
        """Programa el próximo check."""
        if self._stopped:
            return
        self._timer = threading.Timer(10.0, self._check)
        self._timer.daemon = True
        self._timer.start()
    
    def _check(self):
        """Verifica si hubo inactividad."""
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
            # Terminar el proceso
            os._exit(1)
        else:
            self._schedule_check()


# ============================================================
# FUNCIONES ORIGINALES (sin cambios)
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
    """
    True si ya pasó el intervalo mínimo desde la última corrida (o si nunca corrió).
    """
    ultima = estado.get("ultima_ejecucion")
    if not ultima:
        return True
    ultima_dt = datetime.fromisoformat(ultima)
    return datetime.now() - ultima_dt >= timedelta(hours=intervalo_horas)


def login_comprar(page, cuit: str, password: str, nombre_perfil: str = "MEZZINAMIRIAN"):
    """
    Login según el flujo mostrado en las capturas:
    1) Pantalla inicial: se ingresa el CUIT.
    2) Aparece un combo "Seleccionar" con los distintos perfiles asociados a ese CUIT
    (ej: mezzinam, MEZZINAMIRIAN (Proveedor), PSalvage007). Hay que elegir el perfil correcto.
    3) Recién ahí aparece el campo de contraseña y el botón real es #btnIngresar
    (no un <button>, es un <input type="submit" id="btnIngresar">).
    """
    page.goto("https://comprar.gob.ar/Login.aspx")
    page.fill('input[id="txtUsername_txtTextBox"]', cuit)
    page.click('a#lnkConfirmar')
    page.wait_for_load_state('networkidle')
    
    # Combo de selección de perfil (Seleccionar / mezzinam / MEZZINAMIRIAN (Proveedor) / PSalvage007)
    # Es un <select> nativo: no hace falta clickear ni esperar visibilidad de las <option>,
    # se selecciona directo por texto parcial.
    select_locator = page.locator("select").first
    opciones = select_locator.locator("option").all_inner_texts()
    perfil = next((o for o in opciones if nombre_perfil in o.upper()), None)
    if not perfil:
        raise Exception(f"No encontré el perfil '{nombre_perfil}' entre las opciones: {opciones}")
    select_locator.select_option(label=perfil)
    
    # Pantalla de "Ingresá" con el perfil ya elegido -> pide la contraseña
    page.get_by_placeholder("Contraseña").fill(password)
    page.click('#btnIngresar')
    page.wait_for_load_state('networkidle')
    log_info("✅ Login completado.")
    
    # Botón "Acceder" al Escritorio del Comprador (si aparece)
    try:
        page.wait_for_selector('#z9GQt', timeout=5000)
        page.click('#z9GQt')
        log_info("✅ Accediste al Escritorio del Comprador.")
    except Exception:
        log_warning("⚠️ No se encontró el botón 'Acceder' (puede que ya hayas entrado directo).")


def listar_campos_formulario(page):
    """
    Diagnóstico: imprime todos los <input>, <select> y <a> con id de la página actual,
    para poder identificar los selectores correctos sin adivinar.
    """
    log_info("\n--- INPUTS ---")
    for el in page.query_selector_all("input"):
        log_info({
            "id": el.get_attribute("id"),
            "name": el.get_attribute("name"),
            "type": el.get_attribute("type"),
            "placeholder": el.get_attribute("placeholder"),
        })
    log_info("\n--- SELECTS ---")
    for el in page.query_selector_all("select"):
        opts = [o.inner_text().strip() for o in el.query_selector_all("option")]
        log_info({"id": el.get_attribute("id"), "name": el.get_attribute("name"), "opciones": opts})
    log_info("\n--- LINKS/BOTONES con id ---")
    for el in page.query_selector_all("a[id], button[id]"):
        log_info({"id": el.get_attribute("id"), "texto": el.inner_text().strip()})
    log_info("--- FIN DIAGNÓSTICO ---\n")


def extraer_pagina_actual(page):
    """
    Extrae los datos de la tabla ctl00_CPH1_GridListaPliegos tal como está
    actualmente renderizada (una sola página).
    """
    tabla = page.query_selector('#ctl00_CPH1_GridListaPliegos')
    if not tabla:
        return [], []
    header_row = tabla.query_selector('tr.tr-header')
    if not header_row:
        return [], []
    headers = [th.inner_text().strip() for th in header_row.query_selector_all('th')]
    # Descartamos la columna de botones/acciones, no tiene datos útiles para el Excel.
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
    # Perfil Proveedor -> se usa el menú Proceso > Buscar Proceso, que apunta acá:
    page.goto("https://comprar.gob.ar/OFE/BusquedaAvanzadaProveedor.aspx")
    page.wait_for_load_state('networkidle')
    if watchdog: watchdog.ping()

    # Chequeo defensivo: si hay algún <select> de organismo/jurisdicción que haya
    # quedado con "Armada" preseleccionado (en vez de "Seleccionar"/"Todos"), lo
    # reseteamos -- así no nos perdemos LPU de otros organismos sin darnos cuenta.
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
                    print(f"ℹ️ Filtro de organismo ('{sel_id}') estaba en '{seleccionada_actual}' -> "
                          f"lo reseteé a '{opcion_todos}' para traer LPU de todos los organismos.")
    except Exception as e:
        print(f"⚠️ No pude chequear el filtro de organismo: {e}")
    if watchdog: watchdog.ping()
    
    page.fill('#ctl00_CPH1_devDteEdtFechaDesde_I', fecha_desde)
    page.fill('#ctl00_CPH1_devDteEdtFechaHasta_I', fecha_hasta)
    # Tipo de proceso: "Licitacion Pública" (value=1) ya viene seleccionado por defecto,
    # pero lo seteamos explícito por las dudas.
    page.select_option('#ctl00_CPH1_ddlTipoProceso', value="1")
    # Estado: por defecto "Publicado" (value=6). Si en algún momento querés "En Apertura"
    # (value=13) o "En Apertura Segundo Sobre" (value=53), cambiá estado_label.
    page.select_option('#ctl00_CPH1_ddlEstado', label=estado_label)
    page.click('#ctl00_CPH1_btnBusquedaAvanzada')
    if watchdog: watchdog.ping()
    
    log_info("🕒 Esperando respuesta del buscador (puede tardar)...")
    
    # Si saltó el modal de error del sitio, mostrarlo
    modal_error = page.query_selector('#ctl00_CPH1_ModalError')
    if modal_error and modal_error.is_visible():
        log_error(f"❌ Apareció un modal de error en el sitio: {modal_error.inner_text().strip()}")
        return []
    
    # Esperamos directamente a que aparezca el grid real, en vez de confiar en networkidle.
    try:
        page.wait_for_selector('#ctl00_CPH1_GridListaPliegos', timeout=90000)
        if watchdog: watchdog.ping()
    except Exception:
        page.screenshot(path="debug_resultados.png", full_page=True)
        with open("debug_resultados.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        log_warning(f"⚠️ No apareció la tabla de resultados en 90s. Guardé debug en: "
                    f"{os.path.abspath('debug_resultados.png')} y {os.path.abspath('debug_resultados.html')}")
        return []
    
    data_total, headers = extraer_pagina_actual(page)
    log_info(f"📄 Página 1: {len(data_total)} registros.")
    if watchdog: watchdog.ping()
    
    if not data_total and not headers:
        page.screenshot(path="debug_resultados.png", full_page=True)
        with open("debug_resultados.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        log_warning(f"⚠️ El grid apareció pero no pude leer filas/encabezados. Guardé debug en: "
                    f"{os.path.abspath('debug_resultados.png')} y {os.path.abspath('debug_resultados.html')}")
        return []
    
    # Paginación: <a href="javascript:__doPostBack('ctl00$CPH1$GridListaPliegos','Page$2')">2</a>
    # El pager de ASP.NET solo MUESTRA un grupo de números por vez (ej. 1-6) y
    # cuando hay más resultados aparece un "..." para saltar al siguiente grupo
    # (7-12, etc.) -- si nos fijábamos en qué número está VISIBLE, nos quedábamos
    # pegados en el primer grupo y perdíamos todo lo que viene después. Ahora
    # avanzamos siempre por número (el postback funciona aunque el link no se
    # vea) y cortamos solo cuando una página viene vacía o se repite.
    pagina = 2
    primer_numero_pagina_anterior = data_total[0].get('Número de proceso') if data_total else None
    MAX_PAGINAS = 500  # tope de seguridad, no debería llegar ni cerca
    while pagina <= MAX_PAGINAS:
        log_info(f"➡️ Yendo a la página {pagina}...")
        page.evaluate(f"__doPostBack('ctl00$CPH1$GridListaPliegos','Page${pagina}')")
        if watchdog: watchdog.ping()
        
        try:
            page.wait_for_load_state('networkidle', timeout=60000)
        except Exception:
            pass
        # Esperar a que el overlay de carga termine de desaparecer, si seguía activo
        try:
            page.wait_for_selector('#divPanelFondoTransparente', state='hidden', timeout=60000)
        except Exception:
            pass
        # Margen extra fijo para que termine de renderizar el grid antes de leerlo
        page.wait_for_timeout(5000)
        if watchdog: watchdog.ping()
        
        data_pagina, _ = extraer_pagina_actual(page)
        if not data_pagina:
            log_info(f"🏁 Página {pagina} vino vacía -- fin de la paginación.")
            break

        # Si el primer registro de esta página es igual al de la página anterior,
        # es que el postback no avanzó realmente (nos quedamos pegados) -- cortamos
        # para no repetir para siempre.
        primer_numero_actual = data_pagina[0].get('Número de proceso')
        if primer_numero_actual == primer_numero_pagina_anterior:
            log_info(f"🏁 La página {pagina} repite el contenido anterior -- fin de la paginación.")
            break
        primer_numero_pagina_anterior = primer_numero_actual

        log_info(f"📄 Página {pagina}: {len(data_pagina)} registros.")
        data_total.extend(data_pagina)
        pagina += 1
    
    log_info(f"✅ Total registros extraídos (todas las páginas): {len(data_total)}")
    return data_total


def filtrar_en_apertura(data, columna_estado="Estado de proceso"):
    """
    Se queda solo con los procesos cuyo estado indique que están abiertos
    a oferta. Como ya filtramos por 'estado_label' en la búsqueda (ej. 'Publicado'),
    esto es una doble verificación por si el sitio devuelve estados mezclados.
    """
    palabras_clave = ["apertura", "abiert", "convocator", "publicad"]
    filtrados = [
        d for d in data
        if any(p in d.get(columna_estado, '').lower() for p in palabras_clave)
    ]
    log_info(f"🔎 Procesos en apertura/publicados: {len(filtrados)} de {len(data)}")
    return filtrados


def login_comprar_y_extraer(cuit: str, password: str, fecha_desde: str, fecha_hasta: str, 
                            estado_label: str = "Publicado", intervalo_minimo_horas: float = 24, 
                            estado_path: str = "estado_procesos.json", timeout_inactividad: int = 60):
    """
    Función principal modificada con watchdog de inactividad.
    
    Args:
        timeout_inactividad: Segundos de inactividad antes de cerrar automáticamente (default: 60)
    """
    log_info("=" * 60)
    log_info("🚀 INICIO DE EJECUCIÓN - comprar.py")
    log_info("=" * 60)
    
    estado = cargar_estado(estado_path)
    forzado = os.environ.get("FORZAR_EJECUCION") == "1"
    if not forzado and not debe_ejecutar(estado, intervalo_minimo_horas):
        ultima_dt = datetime.fromisoformat(estado["ultima_ejecucion"])
        proxima = ultima_dt + timedelta(hours=intervalo_minimo_horas)
        log_info(f" Ya corrió hace menos de {intervalo_minimo_horas}h (última vez: {ultima_dt.strftime('%d/%m/%Y %H:%M')}). "
                 f"Próxima corrida habilitada a partir de {proxima.strftime('%d/%m/%Y %H:%M')}. No se abre el navegador.")
        return
    if forzado:
        log_info("🔓 Ejecución FORZADA manualmente -- se ignora el límite de 24h.")
    
    browser = None
    watchdog = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Iniciar watchdog de inactividad
            watchdog = InactivityWatchdog(timeout_seconds=timeout_inactividad, browser=browser)
            watchdog.start()
            log_info(f"️ Watchdog activado: {timeout_inactividad}s de inactividad cierra el navegador")
            
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
                    log_info(f"🗑️ Procesos que ya no están ({len(eliminados)}): {', '.join(eliminados) if eliminados else '-'}")
                    if excel_faltante and not nuevos and not eliminados:
                        log_info(f"ℹ️ {nombre_excel} no existía (se ve que se borró) -- lo regenero igual aunque no haya novedades.")
                    df = pd.DataFrame(list(actuales.values()))
                    df.to_excel(nombre_excel, index=False)
                    log_info(f"📁 Excel actualizado en {os.path.abspath(nombre_excel)} ({len(actuales)} registros vigentes).")
                else:
                    log_info("✅ Sin novedades respecto a la última corrida. No se reescribe el Excel.")
                estado["procesos"] = actuales
            else:
                log_warning("⚠️ No se extrajo ningún dato. Revisá los filtros o el debug_resultados.png/.html generado.")
            
            estado["ultima_ejecucion"] = datetime.now().isoformat()
            guardar_estado(estado_path, estado)
            
            # Captura de pantalla para revisar qué quedó en pantalla después de buscar
            try:
                page.screenshot(path="debug_resultado_busqueda.png", full_page=True)
                log_info(f"📸 Captura guardada en {os.path.abspath('debug_resultado_busqueda.png')}")
            except Exception as e:
                log_warning(f"️ No pude tomar la captura: {e}")
            
            # Cerrar watchdog antes de cerrar el navegador
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
    CUIT = "25418019"       # CUIT que se ingresa en la pantalla inicial de login
    PASSWORD = "25418019"   # Contraseña del perfil MEZZINAMIRIAN (verificar dígitos)
    
    # Cuántas horas mínimo tienen que pasar entre corridas. 24 = una vez por día.
    # Poné 0 para no limitar (correr siempre que se ejecute el script).
    INTERVALO_MINIMO_HORAS = 24
    
    # Timeout de inactividad en segundos (60 = 1 minuto)
    TIMEOUT_INACTIVIDAD = 60
    
    hoy = datetime.now()
    hace_un_mes = hoy - timedelta(days=30)
    fecha_desde = hace_un_mes.strftime("%d/%m/%Y")
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    
    log_info(f"📅 Período de búsqueda: {fecha_desde} a {fecha_hasta}")
    log_info(f"⏱️ Timeout de inactividad: {TIMEOUT_INACTIVIDAD}s")
    
    login_comprar_y_extraer(
        CUIT, 
        PASSWORD, 
        fecha_desde=fecha_desde, 
        fecha_hasta=fecha_hasta,
        estado_label="Publicado", 
        intervalo_minimo_horas=INTERVALO_MINIMO_HORAS,
        timeout_inactividad=TIMEOUT_INACTIVIDAD
    )