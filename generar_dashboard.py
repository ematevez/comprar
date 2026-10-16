<<<<<<< HEAD
"""
generar_dashboard.py
Lee cronograma_procesos.xlsx y genera dashboard.html con agenda visual.
VERSIÓN CON EMAIL Y TELEGRAM AGREGADOS (sin modificar el diseño original)
"""
import os
import re
import sys
import json
import time
import shutil
import subprocess
import threading
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

EXCEL_CRONOGRAMA = "cronograma_procesos.xlsx"
EXCEL_PROCESOS = "procesos_armada.xlsx"
EXCEL_GESTION = "registro_gestion.xlsx"
CARPETA_DETALLES = "detalle_procesos"
DASHBOARD_HTML = "dashboard.html"
LOG_COMPRAR = "logs_comprar.txt"
LOG_DETALLE = "logs_detalle.txt"
NOTAS_PATH = "notas_mejoras.json"
EMAILS_FILE = "data/emails_reporte.json"
TELEGRAM_CONFIG_FILE = "data/telegram_config.json"
FAVORITOS_FILE = "data/favoritos.json"


def cargar_cronograma() -> pd.DataFrame:
    if os.path.exists(EXCEL_CRONOGRAMA):
        df = pd.read_excel(EXCEL_CRONOGRAMA)
        if 'Estado gestión' not in df.columns:
            df['Estado gestión'] = 'ACTIVA'
        if 'Motivo descarte' not in df.columns:
            df['Motivo descarte'] = ''
        return df
    return pd.DataFrame()


def guardar_cronograma(df: pd.DataFrame):
    df.to_excel(EXCEL_CRONOGRAMA, index=False)


def cargar_notas() -> list:
=======
"""
generar_dashboard.py
Lee cronograma_procesos.xlsx y genera dashboard.html con agenda visual.
"""
import os
import re
import sys
import json
import time
import shutil
import subprocess
import threading
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

EXCEL_CRONOGRAMA = "cronograma_procesos.xlsx"
EXCEL_PROCESOS = "procesos_armada.xlsx"  # el que arma comprar.py; se usa como respaldo del nombre
EXCEL_GESTION = "registro_gestion.xlsx"
CARPETA_DETALLES = "detalle_procesos"
DASHBOARD_HTML = "dashboard.html"
LOG_COMPRAR = "logs_comprar.txt"
LOG_DETALLE = "logs_detalle.txt"
NOTAS_PATH = "notas_mejoras.json"


def cargar_cronograma() -> pd.DataFrame:
    """Carga el cronograma o crea DataFrame vacío."""
    if os.path.exists(EXCEL_CRONOGRAMA):
        df = pd.read_excel(EXCEL_CRONOGRAMA)
        if 'Estado gestión' not in df.columns:
            df['Estado gestión'] = 'ACTIVA'
        if 'Motivo descarte' not in df.columns:
            df['Motivo descarte'] = ''
        return df
    return pd.DataFrame()


def guardar_cronograma(df: pd.DataFrame):
    """Guarda el cronograma actualizado."""
    df.to_excel(EXCEL_CRONOGRAMA, index=False)


def cargar_notas() -> list:
    """Lista de notas de mejora: [{id, texto, hecha, fecha}]. Vive en NOTAS_PATH."""
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
    if os.path.exists(NOTAS_PATH):
        with open(NOTAS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_notas(notas: list):
    with open(NOTAS_PATH, "w", encoding="utf-8") as f:
        json.dump(notas, f, ensure_ascii=False, indent=2)


def agregar_nota(texto: str) -> dict:
    texto = (texto or "").strip()
    if not texto:
        return {"ok": False, "error": "El texto de la nota está vacío"}
    notas = cargar_notas()
    nuevo_id = (max((n["id"] for n in notas), default=0)) + 1
    notas.append({
        "id": nuevo_id,
        "texto": texto,
        "hecha": False,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    guardar_notas(notas)
    return {"ok": True, "notas": notas}


def marcar_nota(nota_id, hecha: bool) -> dict:
    notas = cargar_notas()
    encontrada = False
    for n in notas:
        if n["id"] == int(nota_id):
            n["hecha"] = bool(hecha)
            encontrada = True
            break
    if not encontrada:
        return {"ok": False, "error": "Nota no encontrada"}
    guardar_notas(notas)
    return {"ok": True, "notas": notas}


def eliminar_nota(nota_id) -> dict:
    notas = cargar_notas()
    notas_filtradas = [n for n in notas if n["id"] != int(nota_id)]
    if len(notas_filtradas) == len(notas):
        return {"ok": False, "error": "Nota no encontrada"}
    guardar_notas(notas_filtradas)
    return {"ok": True, "notas": notas_filtradas}


<<<<<<< HEAD
# ============================================
# FUNCIONES DE EMAIL (NUEVAS)
# ============================================
def cargar_emails() -> dict:
    os.makedirs(os.path.dirname(EMAILS_FILE), exist_ok=True)
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            return json.load(f)
    return {"emails": [], "updated": None}


def guardar_emails(data: dict):
    os.makedirs(os.path.dirname(EMAILS_FILE), exist_ok=True)
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================
# FUNCIONES DE TELEGRAM (NUEVAS)
# ============================================
def cargar_telegram_config() -> dict:
    os.makedirs(os.path.dirname(TELEGRAM_CONFIG_FILE), exist_ok=True)
    if os.path.exists(TELEGRAM_CONFIG_FILE):
        with open(TELEGRAM_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"bot_token": "", "chat_ids": [], "activo": False}


def guardar_telegram_config(config: dict):
    os.makedirs(os.path.dirname(TELEGRAM_CONFIG_FILE), exist_ok=True)
    config["updated"] = datetime.now().isoformat()
    with open(TELEGRAM_CONFIG_FILE, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ============================================
# FUNCIONES DE FAVORITOS (NUEVAS)
# ============================================
def cargar_favoritos() -> dict:
    """Carga la lista de procesos favoritos/seleccionados."""
    os.makedirs(os.path.dirname(FAVORITOS_FILE), exist_ok=True)
    if os.path.exists(FAVORITOS_FILE):
        with open(FAVORITOS_FILE, "r") as f:
            return json.load(f)
    return {"favoritos": [], "updated": None}


def guardar_favoritos(data: dict):
    """Guarda la lista de favoritos."""
    os.makedirs(os.path.dirname(FAVORITOS_FILE), exist_ok=True)
    data["updated"] = datetime.now().isoformat()
    with open(FAVORITOS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def agregar_favorito(numero_proceso: str) -> dict:
    """Agrega un proceso a favoritos."""
    numero_proceso = (numero_proceso or "").strip()
    if not numero_proceso:
        return {"ok": False, "error": "Número de proceso requerido"}
    
    data = cargar_favoritos()
    if numero_proceso in data["favoritos"]:
        return {"ok": False, "error": "Ya está en favoritos"}
    
    data["favoritos"].append(numero_proceso)
    guardar_favoritos(data)
    return {"ok": True, "mensaje": f"Proceso {numero_proceso} agregado a favoritos"}


def quitar_favorito(numero_proceso: str) -> dict:
    """Quita un proceso de favoritos."""
    numero_proceso = (numero_proceso or "").strip()
    data = cargar_favoritos()
    
    if numero_proceso not in data["favoritos"]:
        return {"ok": False, "error": "No está en favoritos"}
    
    data["favoritos"].remove(numero_proceso)
    guardar_favoritos(data)
    return {"ok": True, "mensaje": f"Proceso {numero_proceso} quitado de favoritos"}


def es_favorito(numero_proceso: str) -> bool:
    """Verifica si un proceso es favorito."""
    data = cargar_favoritos()
    return numero_proceso in data.get("favoritos", [])


def detectar_palabras_clave(proc: dict) -> list:
    """Detecta palabras clave importantes en un proceso (FONDEF, 6.8.7, 6.8.2)."""
    palabras_clave = []
    
    # Verificar campos específicos
    if proc.get('PDF - FONDEF'):
        palabras_clave.append('FONDEF')
    if proc.get('PDF - Menciona 6.8.7') == 'Sí':
        palabras_clave.append('6.8.7')
    if proc.get('PDF - Menciona 6.8.2') == 'Sí':
        palabras_clave.append('6.8.2')
    
    return palabras_clave


def buscar_expediente_en_pdfs(numero_proceso: str) -> dict:
=======
def buscar_expediente_en_pdfs(numero_proceso: str) -> dict:
    """
    Busca, dentro de los PDF ya descargados de un proceso, la frase ancla
    "Identificación del Expediente Administrativo por el que tramitará el
    citado procedimiento:" y extrae el código EX-... que la sigue.
    Se corre solo cuando el usuario lo pide desde la card (no en el scraping masivo).
    """
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
    import glob
    try:
        from pypdf import PdfReader
    except ImportError:
        return {"ok": False, "error": "Falta instalar pypdf (pip install pypdf)"}

    numero_proceso = (numero_proceso or "").strip()
    carpeta = os.path.join(CARPETA_DETALLES, re.sub(r'[\\/*?:"<>|]', "_", numero_proceso))
    pdfs = glob.glob(os.path.join(carpeta, "*.pdf"))
    if not pdfs:
        return {"ok": False, "error": f"No hay PDF descargados en {carpeta}"}

    ancla = "identificación del expediente administrativo"

    for pdf in pdfs:
        try:
            reader = PdfReader(pdf)
            texto = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            continue

        idx = texto.lower().find(ancla)
        if idx == -1:
            continue

        resto = texto[idx:]
        fin_frase = resto.find(':')
        if fin_frase == -1:
            continue

<<<<<<< HEAD
=======
        # Ventana amplia después de los ":" -- el código puede empezar en la
        # línea siguiente, no necesariamente pegado a los dos puntos.
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
        ventana = resto[fin_frase + 1: fin_frase + 1 + 400]
        idx_ex = re.search(r'EX-', ventana, re.IGNORECASE)
        if not idx_ex:
            continue

        desde_ex = ventana[idx_ex.start():]
        fin_linea = desde_ex.find('\n')
        linea = desde_ex[:fin_linea] if fin_linea != -1 else desde_ex[:100]

        expediente = re.sub(r'\s{3,}', '  ', linea).strip()[:100]
        if not expediente:
            continue

        return {"ok": True, "expediente": expediente, "archivo": os.path.basename(pdf)}

    return {"ok": False, "error": "No encontré la frase del expediente en los PDF de este proceso."}


<<<<<<< HEAD
def agregar_a_gestion(registro: dict):
    df = pd.read_excel(EXCEL_GESTION) if os.path.exists(EXCEL_GESTION) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    df.to_excel(EXCEL_GESTION, index=False)


def obtener_ultima_ejecucion(archivo_log: str) -> str | None:
    if not os.path.exists(archivo_log):
        return None
    try:
        with open(archivo_log, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            if not lines:
                return None
            for line in reversed(lines):
                if re.search(r'\d{2}/\d{2}/\d{4}', line):
                    return line
            return lines[-1] if lines else None
    except Exception:
        return None


def obtener_duracion_ultima_ejecucion(archivo_log: str) -> str:
=======
def agregar_a_gestion(registro: dict):
    """Agrega fila inmutable al registro de gestión."""
    df = pd.read_excel(EXCEL_GESTION) if os.path.exists(EXCEL_GESTION) else pd.DataFrame()
    df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    df.to_excel(EXCEL_GESTION, index=False)


def obtener_ultima_ejecucion(archivo_log: str) -> str | None:
    """Lee la última línea del archivo de log que tenga timestamp."""
    if not os.path.exists(archivo_log):
        return None
    try:
        with open(archivo_log, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            if not lines:
                return None
            # Busca la última línea con formato de fecha
            for line in reversed(lines):
                if re.search(r'\d{2}/\d{2}/\d{4}', line):
                    return line
            return lines[-1] if lines else None
    except Exception:
        return None


def obtener_duracion_ultima_ejecucion(archivo_log: str) -> str:
    """
    Busca el ÚLTIMO par 'Ejecución iniciada' / 'Ejecución finalizada' en el log
    y devuelve cuánto duró, formateado tipo '2m 15s'. Si el script sigue corriendo
    (no hay 'finalizada' después del último 'iniciada'), devuelve ''.
    """
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
    if not os.path.exists(archivo_log):
        return ''
    try:
        with open(archivo_log, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        idx_inicio = None
        for i in range(len(lineas) - 1, -1, -1):
            if lineas[i].startswith('Ejecución iniciada:'):
                idx_inicio = i
                break
        if idx_inicio is None:
            return ''

        idx_fin = None
        for i in range(idx_inicio + 1, len(lineas)):
            if lineas[i].startswith('Ejecución finalizada:'):
                idx_fin = i
                break
        if idx_fin is None:
<<<<<<< HEAD
            return ''
=======
            return ''  # sigue corriendo (o se cortó sin cerrar bien)
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d

        fmt = '%d/%m/%Y %H:%M:%S'
        t_inicio = datetime.strptime(lineas[idx_inicio].split(':', 1)[1].strip(), fmt)
        t_fin = datetime.strptime(lineas[idx_fin].split(':', 1)[1].strip(), fmt)
        segundos = int((t_fin - t_inicio).total_seconds())
        minutos, segs = divmod(max(segundos, 0), 60)
        return f"{minutos}m {segs}s" if minutos else f"{segs}s"
    except Exception:
        return ''


<<<<<<< HEAD
def obtener_resumen_ejecucion(archivo_log: str) -> str:
    if not os.path.exists(archivo_log):
        return ''
    try:
        with open(archivo_log, 'r', encoding='utf-8') as f:
            lineas = [l.strip() for l in f.readlines() if l.strip()]
        ignorar_prefijos = ('=', 'STDOUT', 'STDERR', 'Ejecución iniciada', 'Ejecución finalizada',
                            'Intérprete:', 'Código de salida')
        for linea in reversed(lineas):
            if linea.startswith(ignorar_prefijos):
                continue
            return linea[:110]
    except Exception:
        pass
    return ''


def registrar_impresion(numero_proceso: str) -> dict:
    agregar_a_gestion({
        'Fecha decisión': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'Número de proceso': (numero_proceso or '').strip(),
        'Decisión': 'FICHA IMPRESA',
        'Motivo': '',
        'Fecha descarte': '',
        'Carpeta borrada': '',
    })
    return {"ok": True}


def resetear_datos() -> dict:
    archivos = ["estado_procesos.json", "estado_detalle.json",
                EXCEL_PROCESOS, EXCEL_CRONOGRAMA]
    borrados = []
    for f in archivos:
        if os.path.exists(f):
            os.remove(f)
            borrados.append(f)

    if os.path.isdir(CARPETA_DETALLES):
        shutil.rmtree(CARPETA_DETALLES)
        borrados.append(CARPETA_DETALLES + "/")

    return {"ok": True, "borrados": borrados}


def _texto(valor) -> str:
    if valor is None:
        return ''
    if isinstance(valor, float) and pd.isna(valor):
        return ''
    texto = str(valor).strip()
    return '' if texto.lower() == 'nan' else texto


def dias_para_apertura(fecha_apertura_str) -> int | None:
    if not fecha_apertura_str or pd.isna(fecha_apertura_str):
        return None
    try:
        for fmt in ('%d/%m/%Y %H:%M Hrs.', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
            try:
                fecha = datetime.strptime(str(fecha_apertura_str).strip(), fmt)
                return (fecha - datetime.now()).days
            except ValueError:
                continue
        fecha = pd.to_datetime(fecha_apertura_str, dayfirst=True, errors='coerce')
        if pd.isna(fecha):
            return None
        return (fecha - datetime.now()).days
    except Exception:
        return None


def marcar_seguimiento(numero_proceso: str, motivo: str = "") -> dict:
    """Marca un proceso como EN SEGUIMIENTO (sin borrar carpeta)."""
    numero_proceso = (numero_proceso or "").strip()
    df = cargar_cronograma()
    mask = df['Número de proceso'].astype(str).str.strip() == numero_proceso
    if not mask.any():
        return {"ok": False, "error": f"Proceso '{numero_proceso}' no encontrado en {EXCEL_CRONOGRAMA}"}

    fecha_seguimiento = datetime.now().strftime('%d/%m/%Y %H:%M')

    df.loc[mask, 'Estado gestión'] = 'EN SEGUIMIENTO'
    df.loc[mask, 'Motivo descarte'] = motivo
    df.loc[mask, 'Fecha seguimiento'] = fecha_seguimiento
    guardar_cronograma(df)

    agregar_a_gestion({
        'Fecha decisión': fecha_seguimiento,
        'Número de proceso': numero_proceso,
        'Decisión': 'EN SEGUIMIENTO',
        'Motivo': motivo,
        'Fecha descarte': '',
        'Carpeta borrada': 'No',
    })

    return {"ok": True, "fecha_seguimiento": fecha_seguimiento}


def limpiar_procesos_vencidos(dias_vencidos: int = 15) -> dict:
    """
    Borra carpetas de procesos vencidos hace más de X días.
    Mantiene el registro en el Excel pero elimina los PDFs para liberar espacio.
    """
    df = cargar_cronograma()
    limpiados = []
    
    for _, row in df.iterrows():
        numero = str(row.get('Número de proceso', '')).strip()
        if not numero:
            continue
        
        # Solo procesar si está vencido
        fecha_apertura = row.get('Fecha acto de apertura', '')
        if not fecha_apertura or pd.isna(fecha_apertura):
            continue
        
        try:
            # Parsear fecha
            fecha_dt = None
            for fmt in ('%d/%m/%Y %H:%M Hrs.', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
                try:
                    fecha_dt = datetime.strptime(str(fecha_apertura).strip(), fmt)
                    break
                except:
                    continue
            
            if not fecha_dt:
                continue
            
            # Calcular días desde vencimiento
            dias_desde_vencimiento = (datetime.now() - fecha_dt).days
            
            if dias_desde_vencimiento > dias_vencidos:
                # Buscar carpeta
                carpeta = os.path.join(CARPETA_DETALLES, re.sub(r'[\\/*?:"<>|]', "_", numero))
                
                if os.path.isdir(carpeta):
                    shutil.rmtree(carpeta)
                    limpiados.append(numero)
                    
                    # Registrar en gestión
                    agregar_a_gestion({
                        'Fecha decisión': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'Número de proceso': numero,
                        'Decisión': 'LIMPIEZA AUTOMÁTICA',
                        'Motivo': f'Vencido hace {dias_desde_vencimiento} días (> {dias_vencidos} días)',
                        'Fecha descarte': '',
                        'Carpeta borrada': 'Sí',
                    })
                    
                    print(f"🗑️ Carpeta eliminada: {numero} (vencido hace {dias_desde_vencimiento} días)")
        
        except Exception as e:
            print(f"⚠️ Error procesando {numero}: {e}")
            continue
    
    return {
        "ok": True,
        "limpiados": len(limpiados),
        "numeros": limpiados
    }


def descartar_proceso(numero_proceso: str, motivo: str = "") -> dict:
    numero_proceso = (numero_proceso or "").strip()
    df = cargar_cronograma()
    mask = df['Número de proceso'].astype(str).str.strip() == numero_proceso
    if not mask.any():
        return {"ok": False, "error": f"Proceso '{numero_proceso}' no encontrado en {EXCEL_CRONOGRAMA}"}

    carpeta = os.path.join(CARPETA_DETALLES, re.sub(r'[\\/*?:"<>|]', "_", numero_proceso))
    borrado = False
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta)
        borrado = True

    fecha_descarte = datetime.now().strftime('%d/%m/%Y %H:%M')

    df.loc[mask, 'Estado gestión'] = 'DESCARTADA'
    df.loc[mask, 'Motivo descarte'] = motivo
    df.loc[mask, 'Fecha descarte'] = fecha_descarte
    guardar_cronograma(df)

    agregar_a_gestion({
        'Fecha decisión': fecha_descarte,
        'Número de proceso': numero_proceso,
        'Decisión': 'DESCARTADA',
        'Motivo': motivo,
        'Fecha descarte': fecha_descarte,
        'Carpeta borrada': 'Sí' if borrado else 'No existía',
    })

    return {"ok": True, "carpeta_borrada": borrado, "fecha_descarte": fecha_descarte}


def reactivar_proceso(numero_proceso: str) -> dict:
    numero_proceso = (numero_proceso or "").strip()
    df = cargar_cronograma()
    mask = df['Número de proceso'].astype(str).str.strip() == numero_proceso
    if not mask.any():
        return {"ok": False, "error": f"Proceso '{numero_proceso}' no encontrado en {EXCEL_CRONOGRAMA}"}
    df.loc[mask, 'Estado gestión'] = 'ACTIVA'
    df.loc[mask, 'Motivo descarte'] = ''
    df.loc[mask, 'Fecha descarte'] = ''
    guardar_cronograma(df)

    agregar_a_gestion({
        'Fecha decisión': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'Número de proceso': numero_proceso,
        'Decisión': 'REACTIVADA',
        'Motivo': '',
        'Fecha descarte': '',
        'Carpeta borrada': '',
    })
    return {"ok": True}


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_lock_ejecuciones = threading.Lock()
_en_ejecucion = {'comprar': False, 'detalle': False}


def estado_ejecucion(script_name: str) -> dict:
    script_map = {'comprar': LOG_COMPRAR, 'detalle': LOG_DETALLE}
    log_file = script_map.get(script_name)
    ultimas_lineas = []
    if log_file and os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            ultimas_lineas = [l.rstrip('\n') for l in f.readlines()][-15:]
    return {
        "corriendo": _en_ejecucion.get(script_name, False),
        "ultimas_lineas": ultimas_lineas,
    }


def ejecutar_script(script_name: str, forzar: bool = False) -> dict:
    script_map = {
        'comprar': ('comprar.py', LOG_COMPRAR),
        'detalle': ('detalle_proceso.py', LOG_DETALLE)
    }
    timeout_map = {'comprar': 600, 'detalle': 3600}
    timeout_segundos = timeout_map.get(script_name, 600)

    if script_name not in script_map:
        return {"ok": False, "error": "Script desconocido"}

    script_file, log_file = script_map[script_name]
    ruta_script = os.path.join(_BASE_DIR, script_file)

    if not os.path.exists(ruta_script):
        return {"ok": False, "error": f"Archivo {script_file} no encontrado en {_BASE_DIR}"}

    with _lock_ejecuciones:
        if _en_ejecucion.get(script_name):
            return {"ok": False, "error": f"{script_file} ya está corriendo, esperá a que termine"}
        _en_ejecucion[script_name] = True

    def run_and_log():
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"\n{'='*60}\n")
            log.write(f"Ejecución iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            log.write(f"Intérprete: {sys.executable}\n")
            if forzar:
                log.write("Modo: FORZADO manualmente (ignora el límite de 24h)\n")
            log.write(f"{'='*60}\n")
            log.flush()
            proceso = None
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["PYTHONUTF8"] = "1"
                if forzar:
                    env["FORZAR_EJECUCION"] = "1"
                proceso = subprocess.Popen(
                    [sys.executable, "-u", ruta_script],
                    cwd=_BASE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=env,
                )
                inicio = time.time()
                for linea in proceso.stdout:
                    log.write(linea)
                    log.flush()
                    if time.time() - inicio > timeout_segundos:
                        proceso.kill()
                        log.write(f"\n⚠️ TIMEOUT: La ejecución superó los {timeout_segundos//60} minutos, se mató el proceso.\n")
                        break
                proceso.wait(timeout=30)
                log.write(f"\nEjecución finalizada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                log.write(f"Código de salida: {proceso.returncode}\n")
            except Exception as e:
                log.write(f"\n❌ Error: {str(e)}\n")
                if proceso:
                    try:
                        proceso.kill()
                    except Exception:
                        pass
            finally:
                with _lock_ejecuciones:
                    _en_ejecucion[script_name] = False

    thread = threading.Thread(target=run_and_log, daemon=True)
    thread.start()

    return {"ok": True, "message": f"Ejecución de {script_name} iniciada en background"}


def generar_dashboard():
    """Genera el HTML del dashboard."""
    df = cargar_cronograma()

    nombres_respaldo = {}
    if os.path.exists(EXCEL_PROCESOS):
        try:
            df_procesos = pd.read_excel(EXCEL_PROCESOS)
            col_num = next((c for c in df_procesos.columns if 'úmero de proceso' in c), None)
            col_nom = next((c for c in df_procesos.columns if 'ombre de proceso' in c), None)
            if col_num and col_nom:
                for _, r in df_procesos.iterrows():
                    n = _texto(r.get(col_num))
                    if n:
                        nombres_respaldo[n] = _texto(r.get(col_nom))
        except Exception as e:
            print(f"⚠️ No pude leer {EXCEL_PROCESOS} para respaldo de nombres: {e}")

    ultima_comprar = obtener_ultima_ejecucion(LOG_COMPRAR)
    ultima_detalle = obtener_ultima_ejecucion(LOG_DETALLE)
    
    tarjetas = []
    tarjetas_vencidas = []
    for _, row in df.iterrows():
        numero = _texto(row.get('Número de proceso', ''))
        dias = dias_para_apertura(row.get('Fecha acto de apertura'))
        estado = row.get('Estado gestión', 'ACTIVA')
        
        if estado == 'DESCARTADA':
            clase = 'descartada'
            etiqueta = 'DESCARTADA'
        elif estado == 'EN SEGUIMIENTO':
            clase = 'seguimiento'
            etiqueta = 'EN SEGUIMIENTO'
        elif dias is None:
            clase = 'sin-fecha'
            etiqueta = '—'
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
        
        hallazgos = []
        palabras_clave = []
        
        # Detectar palabras clave importantes (se destacarán)
        if _texto(row.get('PDF - FONDEF')):
            hallazgos.append('FONDEF')
            palabras_clave.append('FONDEF')
        if row.get('PDF - Menciona 6.8.7') == 'Sí':
            hallazgos.append('6.8.7')
            palabras_clave.append('6.8.7')
        if row.get('PDF - Menciona 6.8.2') == 'Sí':
            hallazgos.append('6.8.2')
            palabras_clave.append('6.8.2')
        
        # Otros hallazgos (no destacados)
        if _texto(row.get('PDF - Pago adelantado')):
            hallazgos.append('Pago adelantado')
        if _texto(row.get('Objeto del gasto (detalle)')):
            hallazgos.append(f"Objeto: {_texto(row['Objeto del gasto (detalle)'])}")
        
        # Verificar si es favorito
        es_fav = es_favorito(numero)
        
        tarjeta = {
            'numero': numero,
            'objeto': (_texto(row.get('Nombre de proceso', '')) or nombres_respaldo.get(numero, ''))[:80] or 'Sin nombre',
            'dias_label': etiqueta,
            'clase': clase,
            'fecha_apertura': _texto(row.get('Fecha acto de apertura', '')),
            'fecha_publicacion': _texto(row.get('Fecha publicación portal', '')),
            'hallazgos': hallazgos,
            'palabras_clave': palabras_clave,
            'favorito': es_fav,
            'estado': estado,
            'unidad': _texto(row.get('Unidad Ejecutora', '')),
        }

        if clase == 'vencido' and estado != 'DESCARTADA':
            tarjetas_vencidas.append(tarjeta)
        else:
            tarjetas.append(tarjeta)
    
    orden = {'urgente': 0, 'vencido': 1, 'seguimiento': 2, 'lejana': 3, 'sin-fecha': 4, 'descartada': 5}
    tarjetas.sort(key=lambda t: (orden.get(t['clase'], 9), t['dias_label'] or '999'))
    tarjetas_vencidas.sort(key=lambda t: t['fecha_apertura'] or '', reverse=True)
    
    template_path = os.path.join(os.path.dirname(__file__), 'dashboard_template.html')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    else:
        html_template = TEMPLATE_DASHBOARD
    
    html = html_template.replace('/*TARJETAS*/', json.dumps(tarjetas, ensure_ascii=False))
    html = html.replace('/*TARJETAS_VENCIDAS*/', json.dumps(tarjetas_vencidas, ensure_ascii=False))
    html = html.replace('/*ULTIMA_COMPRAR*/', ultima_comprar or 'Nunca')
    html = html.replace('/*ULTIMA_DETALLE*/', ultima_detalle or 'Nunca')
    def _resumen_con_duracion(log_file):
        resumen = obtener_resumen_ejecucion(log_file)
        duracion = obtener_duracion_ultima_ejecucion(log_file)
        if duracion:
            return f"{resumen} · duró {duracion}" if resumen else f"Duró {duracion}"
        return resumen

    html = html.replace('/*RESUMEN_COMPRAR*/', _resumen_con_duracion(LOG_COMPRAR))
    html = html.replace('/*RESUMEN_DETALLE*/', _resumen_con_duracion(LOG_DETALLE))
    
    with open(DASHBOARD_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generado en {os.path.abspath(DASHBOARD_HTML)}")


TEMPLATE_DASHBOARD = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agenda de Licitaciones - Armada</title>
<script>
  if (localStorage.getItem('modoNocturno') === '1') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
</script>
<style>
  :root {
    --navy: #14213D;
    --navy-soft: #1E2E52;
    --ink: #1F2A3C;
    --slate: #5B6B82;
    --slate-light: #8A97AB;
    --border: #E4E8EF;
    --bg: #F4F6F9;
    --surface: #FFFFFF;
    --urgente: #DC2626;
    --urgente-bg: #FEE2E2;
    --urgente-bg-soft: #FFF1F1;
    --seguimiento: #D97706;
    --seguimiento-bg: #FEF3C7;
    --seguimiento-bg-soft: #FFFAEF;
    --lejana: #059669;
    --lejana-bg: #D1FAE5;
    --lejana-bg-soft: #F0FDF7;
    --vencido: #44403C;
    --vencido-bg: #E7E5E4;
    --descartada: #64748B;
    --descartada-bg: #E2E8F0;
  }

  [data-theme="dark"] {
    --navy: #E8ECF5;
    --navy-soft: #C7D0E8;
    --ink: #E4E8F0;
    --slate: #9CA9C0;
    --slate-light: #6B7690;
    --border: #2A3448;
    --bg: #0F1521;
    --surface: #1A2233;
    --urgente: #F87171;
    --urgente-bg: #3D1E1E;
    --urgente-bg-soft: #241717;
    --seguimiento: #FBBF24;
    --seguimiento-bg: #3D3319;
    --seguimiento-bg-soft: #241f13;
    --lejana: #34D399;
    --lejana-bg: #143329;
    --lejana-bg-soft: #12241d;
    --vencido: #A8A29E;
    --vencido-bg: #292522;
    --descartada: #94A3B8;
    --descartada-bg: #232B3A;
  }
  [data-theme="dark"] body { background: var(--bg); }
  [data-theme="dark"] .card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.4); }
  [data-theme="dark"] .modal-bg { background: rgba(0,0,0,0.65); }
  [data-theme="dark"] .toast { background: var(--surface); color: var(--ink); }
  [data-theme="dark"] .badge.urgente, [data-theme="dark"] .badge.seguimiento,
  [data-theme="dark"] .badge.lejana, [data-theme="dark"] .badge.vencido,
  [data-theme="dark"] .badge.descartada { filter: brightness(1.15); }
  [data-theme="dark"] .hallazgo { background: #232B3A; color: #A5B4FC; }
  [data-theme="dark"] .expediente-resultado { background: #23203A; border-color: #3B3266; color: #C4B5FD; }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
    background: var(--bg);
    min-height: 100vh;
    padding: 28px;
    color: var(--ink);
    font-size: 14px;
    line-height: 1.5;
  }
  .container { max-width: 1450px; margin: 0 auto; }

  .header {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 22px 26px;
    margin-bottom: 20px;
  }
  .header h1 {
    font-size: 22px;
    font-weight: 800;
    color: var(--navy);
    letter-spacing: 0.2px;
  }
  .header .sub { color: var(--slate); font-size: 13px; margin-top: 4px; }

  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(230px, 100%), 1fr));
    gap: 14px;
    margin-bottom: 20px;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .stat-card h3 {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--slate);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 8px;
  }
  .stat-card .value { font-size: 20px; font-weight: 800; color: var(--navy); }
  .stat-card .timestamp { font-size: 11px; color: var(--slate-light); margin-top: 4px; }

  .toolbar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    align-items: center;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 14px;
    border-radius: 10px;
  }
  .toolbar button {
    padding: 10px 20px;
    border: 0;
    border-radius: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    cursor: pointer;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.2px;
    box-shadow: 0 2px 6px rgba(102,126,234,0.35);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .toolbar button:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(102,126,234,0.4); }
  .toolbar button.secondary {
    background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
    box-shadow: 0 2px 6px rgba(100,116,139,0.3);
  }
  .toolbar button.success {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    box-shadow: 0 2px 6px rgba(17,153,142,0.35);
  }
  .toolbar .view-toggle {
    margin-left: auto;
    display: flex;
    gap: 4px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 4px;
  }
  .toolbar .view-toggle button {
    background: transparent;
    color: var(--slate);
    box-shadow: none;
    padding: 7px 14px;
    font-size: 12.5px;
  }
  .toolbar .view-toggle button:hover { transform: none; box-shadow: none; background: var(--border); }
  .toolbar .view-toggle button.active {
    background: var(--navy);
    color: white;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
    gap: 16px;
  }
  .card {
    border-radius: 12px;
    padding: 18px;
    border: 1px solid transparent;
    border-left: 6px solid var(--descartada);
    background: var(--surface);
    box-shadow: 0 2px 6px rgba(20,33,61,0.06);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(20,33,61,0.12); }
  .card.urgente      { border-left-color: var(--urgente);     background: var(--urgente-bg-soft); }
  .card.seguimiento  { border-left-color: var(--seguimiento); background: var(--seguimiento-bg-soft); }
  .card.lejana       { border-left-color: var(--lejana);      background: var(--lejana-bg-soft); }
  .card.vencido      { border-left-color: var(--vencido);     background: #FAFAF9; }
  .card.sin-fecha    { border-left-color: var(--descartada);  background: var(--surface); }
  .card.descartada   { opacity: 0.65; border-left-color: var(--descartada); background: var(--bg); }
  .card.en-seguimiento { border-left-color: #F59E0B; background: #FFFBEB; }

  .card .num {
    font-weight: 800;
    font-size: 15px;
    font-family: 'Consolas', 'Courier New', monospace;
    color: var(--navy);
    letter-spacing: 0.2px;
  }
  .card .obj {
    color: var(--slate);
    font-size: 12.5px;
    margin: 8px 0 12px;
    min-height: 36px;
    line-height: 1.4;
  }
  .card .meta {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }
  .card .dias {
    font-size: 22px;
    font-weight: 800;
    color: var(--ink);
    text-align: right;
    white-space: nowrap;
  }
  .card .dias .clock { font-size: 15px; margin-right: 2px; }
  .card .dias small {
    display: block;
    font-size: 10px;
    font-weight: 600;
    color: var(--slate-light);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }
  .badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 10.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .badge.urgente     { background: var(--urgente-bg);     color: #991B1B; }
  .badge.seguimiento { background: var(--seguimiento-bg); color: #92400E; }
  .badge.lejana      { background: var(--lejana-bg);      color: #065F46; }
  .badge.vencido     { background: var(--vencido-bg);     color: var(--vencido); }
  .badge.descartada  { background: var(--descartada-bg);  color: #475569; }

  .hallazgos {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 12px 0;
  }
  .hallazgo {
    background: #EFF6FF;
    color: #1E40AF;
    padding: 4px 11px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
  }
  .hallazgo.destacado {
    background: linear-gradient(135deg, #FFD700, #FFA500);
    color: #14213D;
    border: 2px solid #FF8C00;
    box-shadow: 0 2px 4px rgba(255,165,0,0.3);
    font-weight: 800;
  }
  .card.favorito {
    border: 2px solid #FFD700;
    box-shadow: 0 4px 12px rgba(255,215,0,0.3);
    position: relative;
  }
  .card.favorito::before {
    content: '⭐';
    position: absolute;
    top: -10px;
    right: -10px;
    font-size: 24px;
    background: white;
    border-radius: 50%;
    padding: 2px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
  .btn-favorito {
    background: #FEF3C7;
    color: #92400E;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 700;
  }
  .btn-favorito:hover {
    background: #FDE68A;
  }
  .btn-favorito.activo {
    background: #FFD700;
    color: #14213D;
  }
  
  /* Estilos para botones de filtro */
  .filter-btn {
    background: #F3F4F6;
    color: #374151;
    border: 2px solid #E5E7EB;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.2s;
  }
  
  .filter-btn:hover {
    background: #E5E7EB;
    border-color: #D1D5DB;
  }
  
  .filter-btn.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
  }
  
  .filter-btn.active:hover {
    background: #5568d3;
  }

  .actions {
    display: flex;
    gap: 8px;
    margin-top: 14px;
    flex-wrap: wrap;
  }
  .actions button {
    flex: 1;
    min-width: 80px;
    padding: 8px 12px;
    border: 0;
    border-radius: 7px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 700;
    transition: all 0.15s;
  }
  .btn-descartar { background: #FEE2E2; color: #991B1B; }
  .btn-descartar:hover { background: #FECACA; }
  .btn-seguimiento { background: #FEF3C7; color: #92400E; }
  .btn-seguimiento:hover { background: #FDE68A; }
  .btn-reactivar { background: #D1FAE5; color: #065F46; }
  .btn-reactivar:hover { background: #A7F3D0; }
  .btn-imprimir  { background: #DBEAFE; color: #1E40AF; }
  .btn-imprimir:hover { background: #BFDBFE; }
  .btn-ver       { background: #F3F4F6; color: #374151; }
  .btn-ver:hover { background: #E5E7EB; }
  .btn-expediente { background: #EDE9FE; color: #5B21B6; }
  .btn-expediente:hover { background: #DDD6FE; }
  .expediente-resultado {
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    border-radius: 7px;
    padding: 8px 10px;
    margin: 8px 0;
    font-size: 11px;
    color: #5B21B6;
    font-family: 'Consolas', 'Courier New', monospace;
    word-break: break-word;
  }

  .consola-ejecucion {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 400px;
    background: #0B1220;
    border-top: 3px solid #667eea;
    box-shadow: 0 -8px 24px rgba(0,0,0,0.35);
    z-index: 1500;
    display: flex;
    flex-direction: column;
  }
  .consola-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 18px;
    background: #151E33;
    color: #A5B4FC;
    font-size: 14px;
    font-weight: 700;
    border-bottom: 1px solid #334155;
  }
  .consola-header .status-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #10B981;
    margin-right: 8px;
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
  .consola-header button {
    background: transparent;
    border: 1px solid #334155;
    color: #94A3B8;
    padding: 5px 12px;
    border-radius: 5px;
    font-size: 12px;
    cursor: pointer;
    box-shadow: none;
  }
  .consola-header button:hover { background: #1E293B; transform: none; }
  #consolaContenido {
    margin: 0;
    padding: 15px 18px;
    overflow-y: auto;
    color: #D1D5DB;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    flex: 1;
  }
  #consolaContenido::-webkit-scrollbar {
    width: 10px;
  }
  #consolaContenido::-webkit-scrollbar-track {
    background: #1E293B;
  }
  #consolaContenido::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 5px;
  }
  #consolaContenido::-webkit-scrollbar-thumb:hover {
    background: #64748B;
  }

  .modal-bg {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(20,33,61,0.5);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(3px);
  }
  .modal-bg.open { display: flex; }
  .modal {
    background: var(--surface);
    border-radius: 12px;
    padding: 26px;
    max-width: 520px;
    width: 90%;
    box-shadow: 0 20px 40px rgba(20,33,61,0.2);
  }
  .modal h3 {
    margin-bottom: 10px;
    font-size: 17px;
    font-weight: 800;
    color: var(--navy);
  }
  .modal p { color: var(--slate); font-size: 13px; margin-bottom: 14px; line-height: 1.5; }
  .modal textarea, .modal input[type="text"], .modal input[type="email"] {
    width: 100%;
    min-height: 90px;
    padding: 10px 12px;
    border: 2px solid var(--border);
    border-radius: 8px;
    font-family: inherit;
    font-size: 13px;
    resize: vertical;
  }
  .modal textarea:focus, .modal input:focus {
    outline: none;
    border-color: #667eea;
  }
  .modal .btns {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 18px;
  }
  .modal button {
    padding: 10px 20px;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 700;
    font-size: 13px;
  }
  .modal .confirm { background: var(--urgente); color: white; }
  .modal .confirm:hover { background: #B91C1C; }
  .modal .cancel  { background: var(--border); color: var(--slate); }
  .modal .cancel:hover { background: #CBD5E1; }
  .modal .success { background: #059669; color: white; }
  .modal .success:hover { background: #047857; }

  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: white;
    padding: 15px 22px;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    z-index: 2000;
    display: none;
    font-size: 13px;
    font-weight: 700;
    color: var(--ink);
    animation: slideIn 0.25s ease;
  }
  .toast.show { display: block; }
  .toast.success { border-left: 4px solid #059669; }
  .toast.error { border-left: 4px solid #DC2626; }
  @keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }

  /* Estilos para Email y Telegram */
  .config-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
  }
  .config-section h3 {
    font-size: 16px;
    font-weight: 800;
    color: var(--navy);
    margin-bottom: 15px;
  }
  .email-list, .chat-list {
    margin-top: 15px;
  }
  .email-item, .chat-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px;
    background: var(--bg);
    border-radius: 6px;
    margin-bottom: 8px;
  }
  .email-item span, .chat-item span {
    font-family: 'Consolas', monospace;
    font-size: 13px;
  }
  .btn-remove {
    background: #FEE2E2;
    color: #991B1B;
    border: none;
    padding: 5px 10px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 12px;
  }
  .btn-remove:hover { background: #FECACA; }
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>Agenda de Licitaciones</h1>
    <p class="sub">Seguimiento de procesos de compra - Armada Argentina</p>
  </div>
  
  <div class="stats">
    <div class="stat-card">
      <h3>Última ejecución — comprar.py</h3>
      <div class="value" id="statComprar">/*ULTIMA_COMPRAR*/</div>
      <div class="timestamp" id="resumenComprar">/*RESUMEN_COMPRAR*/</div>
    </div>
    <div class="stat-card">
      <h3>Última ejecución — detalle_proceso.py</h3>
      <div class="value" id="statDetalle">/*ULTIMA_DETALLE*/</div>
      <div class="timestamp" id="resumenDetalle">/*RESUMEN_DETALLE*/</div>
    </div>
    <div class="stat-card">
      <h3>Total procesos</h3>
      <div class="value" id="statTotal">0</div>
    </div>
    <div class="stat-card">
      <h3>Urgentes (&lt; 3 días)</h3>
      <div class="value" id="statUrgentes">0</div>
    </div>
  </div>

  <div class="toolbar">
    <!-- Grupo 1: Ejecución -->
    <div style="display:flex; gap:8px; align-items:center; border-right:2px solid #E4E8EF; padding-right:12px;">
      <button onclick="ejecutarScript('comprar')" class="success">▶ comprar.py</button>
      <button onclick="ejecutarScript('detalle')" class="success">▶ detalle.py</button>
      <label style="display:flex; align-items:center; gap:5px; font-size:11px; color:#5B6B82; font-weight:600; cursor:pointer;">
        <input type="checkbox" id="chkForzar" style="accent-color:#667eea; width:14px; height:14px;">
        Forzar
      </label>
    </div>
    
    <!-- Grupo 2: Filtros -->
    <div style="display:flex; gap:8px; align-items:center; border-right:2px solid #E4E8EF; padding-right:12px;">
      <button onclick="filtrarTarjetas('todos')" class="filter-btn active">Todos</button>
      <button onclick="filtrarTarjetas('favoritos')" class="filter-btn">⭐ Favoritos</button>
      <button onclick="filtrarTarjetas('fondef')" class="filter-btn">🏷️ FONDEF</button>
      <button onclick="filtrarTarjetas('6.8.7')" class="filter-btn">🏷️ 6.8.7</button>
      <button onclick="filtrarTarjetas('6.8.2')" class="filter-btn">🏷️ 6.8.2</button>
    </div>
    
    <!-- Grupo 3: Notificaciones -->
    <div style="display:flex; gap:8px; align-items:center; border-right:2px solid #E4E8EF; padding-right:12px;">
      <button onclick="forzarNotificaciones()" style="background:linear-gradient(135deg, #10b981, #059669);">📧🤖 Notificaciones</button>
    </div>
    
    <!-- Grupo 4: Gestión -->
    <div style="display:flex; gap:8px; align-items:center; border-right:2px solid #E4E8EF; padding-right:12px;">
      <button onclick="location.reload()">🔄 Refrescar</button>
      <button class="secondary" onclick="mostrarGestion()">📋 Gestión</button>
      <button class="secondary" onclick="toggleNotas()">📝 Notas</button>
      <button class="secondary" onclick="window.print()">🖨️ Imprimir</button>
    </div>
    
    <!-- Grupo 5: Configuración -->
    <div style="display:flex; gap:8px; align-items:center;">
      <button id="btnModoNocturno" class="secondary" onclick="toggleModoNocturno()">🌙</button>
      <button class="secondary" onclick="mostrarConfigEmail()">📧</button>
      <button class="secondary" onclick="mostrarConfigTelegram()">🤖</button>
      <button style="background:linear-gradient(135deg, #f87171, #dc2626);" onclick="abrirReseteo()">⚠️ Reset</button>
    </div>
  </div>

  <div class="grid" id="grid"></div>
</div>

<div class="consola-ejecucion" id="consolaEjecucion" style="display:none">
  <div class="consola-header">
    <span id="consolaTitulo"><span class="status-indicator"></span>Ejecutando...</span>
    <div>
      <button onclick="document.getElementById('consolaContenido').scrollTop = document.getElementById('consolaContenido').scrollHeight">📜 Ir al final</button>
      <button onclick="document.getElementById('consolaEjecucion').style.display='none'" style="margin-left:8px;">✕ Cerrar</button>
    </div>
  </div>
  <pre id="consolaContenido"></pre>
</div>

<!-- Modal Email -->
<div class="modal-bg" id="modalEmail">
  <div class="modal">
    <h3>📧 Configurar Emails para Reportes</h3>
    <p>Agregá emails para recibir el reporte diario automático.</p>
    <input type="email" id="nuevoEmail" placeholder="email@ejemplo.com">
    <div class="btns">
      <button class="cancel" onclick="document.getElementById('modalEmail').classList.remove('open')">Cerrar</button>
      <button class="success" onclick="agregarEmail()">Agregar</button>
      <button class="btn-imprimir" onclick="probarEmail()">📧 Enviar Email de Prueba</button>
    </div>
    <div id="listaEmails" class="email-list"></div>
  </div>
</div>

<!-- Modal Telegram -->
<div class="modal-bg" id="modalTelegram">
  <div class="modal">
    <h3>🤖 Configurar Bot de Telegram</h3>
    <p>Configurá el token del bot y los chat IDs autorizados.</p>
    <input type="text" id="telegramToken" placeholder="Token del bot (de @BotFather)">
    <input type="text" id="telegramChats" placeholder="Chat IDs (separados por coma)">
    <div class="btns">
      <button class="cancel" onclick="document.getElementById('modalTelegram').classList.remove('open')">Cerrar</button>
      <button class="success" onclick="guardarTelegram()">Guardar</button>
      <button class="btn-imprimir" onclick="probarTelegram()">🤖 Enviar Mensaje de Prueba</button>
    </div>
  </div>
</div>

<!-- Modal descartar -->
<div class="modal-bg" id="modalDescartar">
  <div class="modal">
    <h3>Descartar proceso</h3>
    <p>Esta acción eliminará permanentemente la carpeta con los PDFs y documentos descargados.</p>
    <textarea id="motivoDescarte" placeholder="Motivo del descarte (obligatorio)..."></textarea>
    <div class="btns">
      <button class="cancel" onclick="cerrarModal()">Cancelar</button>
      <button class="confirm" onclick="confirmarDescarte()">Confirmar descarte</button>
    </div>
  </div>
</div>

<!-- Modal reseteo -->
<div class="modal-bg" id="modalReseteo">
  <div class="modal">
    <h3>Reseteo general</h3>
    <p>Esto borra todos los datos de scraping. El registro de gestión y las notas NO se tocan.</p>
    <div class="btns">
      <button class="cancel" onclick="document.getElementById('modalReseteo').classList.remove('open')">Cancelar</button>
      <button class="confirm" onclick="confirmarReseteo()">Sí, resetear todo</button>
    </div>
  </div>
</div>

<!-- Modal gestión -->
<div class="modal-bg" id="modalGestion">
  <div class="modal" style="max-width:800px;">
    <h3>Registro de Gestión</h3>
    <div id="gestionContent" style="max-height:500px;overflow:auto;font-size:13px;margin:16px 0;"></div>
    <div class="btns">
      <button class="cancel" onclick="document.getElementById('modalGestion').classList.remove('open')">Cerrar</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const TARJETAS = /*TARJETAS*/;
let procesoADescartar = null;

const total = TARJETAS.length;
const urgentes = TARJETAS.filter(t => t.clase === 'urgente').length;
document.getElementById('statTotal').textContent = total;
document.getElementById('statUrgentes').textContent = urgentes;

// Función para filtrar tarjetas
function filtrarTarjetas(criterio) {
  // Actualizar botones activos
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  event.target.classList.add('active');
  
  const grid = document.getElementById('grid');
  let tarjetasFiltradas = TARJETAS;
  
  switch(criterio) {
    case 'favoritos':
      tarjetasFiltradas = TARJETAS.filter(t => t.favorito);
      break;
    case 'fondef':
      tarjetasFiltradas = TARJETAS.filter(t => t.palabras_clave && t.palabras_clave.includes('FONDEF'));
      break;
    case '6.8.7':
      tarjetasFiltradas = TARJETAS.filter(t => t.palabras_clave && t.palabras_clave.includes('6.8.7'));
      break;
    case '6.8.2':
      tarjetasFiltradas = TARJETAS.filter(t => t.palabras_clave && t.palabras_clave.includes('6.8.2'));
      break;
    case 'todos':
    default:
      tarjetasFiltradas = TARJETAS;
  }
  
  if (tarjetasFiltradas.length === 0) {
    grid.innerHTML = `<div style="padding:40px;text-align:center;color:var(--slate);">No hay procesos con filtro: ${criterio}</div>`;
    return;
  }
  
  grid.innerHTML = tarjetasFiltradas.map(t => `
    <div class="card ${t.clase} ${t.favorito ? 'favorito' : ''}">
      <div class="meta">
        <div class="num">${t.numero}</div>
        <div class="dias">${t.dias_label}<small>para apertura</small></div>
      </div>
      <div class="obj">${t.objeto || 'Sin descripción'}</div>
      ${t.hallazgos.length ? `<div class="hallazgos">${t.hallazgos.map(h => {
        const esDestacado = t.palabras_clave && t.palabras_clave.includes(h);
        return `<span class="hallazgo ${esDestacado ? 'destacado' : ''}">${esDestacado ? '⭐ ' : ''}${h}</span>`;
      }).join('')}</div>` : ''}
      <div class="actions">
        <button class="btn-favorito ${t.favorito ? 'activo' : ''}" onclick="toggleFavorito('${t.numero}', this)">${t.favorito ? '⭐ Favorito' : '☆ Favorito'}</button>
        <button class="btn-ver" onclick="verDetalle('${t.numero}')">Ver</button>
        ${t.estado === 'DESCARTADA'
          ? `<button class="btn-reactivar" onclick="reactivar('${t.numero}')">Reactivar</button>`
          : t.estado === 'EN SEGUIMIENTO'
            ? `<button class="btn-descartar" onclick="abrirDescarte('${t.numero}')">Descartar</button>`
            : `<button class="btn-seguimiento" onclick="marcarSeguimiento('${t.numero}')">📌 Seguimiento</button>
               <button class="btn-descartar" onclick="abrirDescarte('${t.numero}')">Descartar</button>`}
        <button class="btn-imprimir" onclick="imprimirUno('${t.numero}')">Ficha</button>
      </div>
    </div>
  `).join('');
}

function render() {
  const grid = document.getElementById('grid');
  if (TARJETAS.length === 0) {
    grid.innerHTML = '<div style="padding:40px;text-align:center;color:var(--slate);">No hay procesos cargados</div>';
    return;
  }
  grid.innerHTML = TARJETAS.map(t => `
    <div class="card ${t.clase}">
      <div class="meta">
        <div class="num">${t.numero}</div>
        <div class="dias">${t.dias_label}<small>para apertura</small></div>
      </div>
      <div class="obj">${t.objeto || 'Sin descripción'}</div>
      ${t.hallazgos.length ? `<div class="hallazgos">${t.hallazgos.map(h => {
        const esDestacado = t.palabras_clave && t.palabras_clave.includes(h);
        return `<span class="hallazgo ${esDestacado ? 'destacado' : ''}">${esDestacado ? '⭐ ' : ''}${h}</span>`;
      }).join('')}</div>` : ''}
      <div class="actions">
        <button class="btn-favorito ${t.favorito ? 'activo' : ''}" onclick="toggleFavorito('${t.numero}', this)">${t.favorito ? '⭐ Favorito' : '☆ Favorito'}</button>
        <button class="btn-ver" onclick="verDetalle('${t.numero}')">Ver</button>
        ${t.estado === 'DESCARTADA'
          ? `<button class="btn-reactivar" onclick="reactivar('${t.numero}')">Reactivar</button>`
          : t.estado === 'EN SEGUIMIENTO'
            ? `<button class="btn-descartar" onclick="abrirDescarte('${t.numero}')">Descartar</button>`
            : `<button class="btn-seguimiento" onclick="marcarSeguimiento('${t.numero}')">📌 Seguimiento</button>
               <button class="btn-descartar" onclick="abrirDescarte('${t.numero}')">Descartar</button>`}
        <button class="btn-imprimir" onclick="imprimirUno('${t.numero}')">Ficha</button>
      </div>
    </div>
  `).join('');
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 4000);
}

function abrirDescarte(num) {
  procesoADescartar = num;
  document.getElementById('motivoDescarte').value = '';
  document.getElementById('modalDescartar').classList.add('open');
}

function cerrarModal() {
  document.getElementById('modalDescartar').classList.remove('open');
  procesoADescartar = null;
}

function abrirReseteo() {
  document.getElementById('modalReseteo').classList.add('open');
}

async function confirmarReseteo() {
  const resp = await fetch('/api/resetear', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}' });
  const data = await resp.json();
  document.getElementById('modalReseteo').classList.remove('open');
  if (data.ok) {
    showToast(`Reseteo completado`);
    setTimeout(() => location.reload(), 2000);
  } else {
    showToast('Error: ' + data.error, 'error');
  }
}

async function confirmarDescarte() {
  const motivo = document.getElementById('motivoDescarte').value.trim();
  if (!motivo) {
    alert('Ingresá el motivo del descarte');
    return;
  }
  const resp = await fetch('/api/descartar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: procesoADescartar, motivo})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast(`Proceso descartado`);
    setTimeout(() => location.reload(), 1500);
  } else {
    showToast('Error: ' + data.error, 'error');
  }
  cerrarModal();
}

async function reactivar(num) {
  const resp = await fetch('/api/reactivar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: num})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast(`Proceso reactivado`);
    setTimeout(() => location.reload(), 1000);
  } else {
    showToast('Error: ' + data.error, 'error');
  }
}

async function marcarSeguimiento(num) {
  if (!confirm(`¿Marcar proceso ${num} como EN SEGUIMIENTO?`)) return;
  
  const resp = await fetch('/api/seguimiento', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: num, motivo: 'Marcado desde dashboard'})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast(`✅ Proceso marcado como EN SEGUIMIENTO`);
    setTimeout(() => location.reload(), 1000);
  } else {
    showToast('Error: ' + data.error, 'error');
  }
}

async function toggleFavorito(num, btn) {
  const esFavorito = btn.classList.contains('activo');
  const endpoint = esFavorito ? '/api/favoritos/quitar' : '/api/favoritos/agregar';
  
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: num})
  });
  const data = await resp.json();
  
  if (data.ok) {
    if (esFavorito) {
      btn.classList.remove('activo');
      btn.textContent = '☆ Favorito';
      showToast(`⭐ Proceso quitado de favoritos`);
    } else {
      btn.classList.add('activo');
      btn.textContent = '⭐ Favorito';
      showToast(`⭐ Proceso agregado a favoritos`);
    }
  } else {
    showToast('Error: ' + data.error, 'error');
  }
}

let consolaPollInterval = null;

async function ejecutarScript(script) {
  const forzar = document.getElementById('chkForzar').checked;
  const btnText = script === 'comprar' ? 'comprar.py' : 'detalle_proceso.py';
  
  showToast(`🚀 Iniciando ${btnText}...`, 'success');
  
  const resp = await fetch('/api/ejecutar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({script, forzar})
  });
  const data = await resp.json();
  
  if (!data.ok) {
    showToast('❌ ' + data.error, 'error');
    return;
  }
  
  // Mostrar consola
  const consola = document.getElementById('consolaEjecucion');
  consola.style.display = 'flex';
  document.getElementById('consolaTitulo').innerHTML = `<span class="status-indicator"></span>Ejecutando ${btnText}...`;
  document.getElementById('consolaContenido').textContent = `🚀 Iniciando ${btnText}...\n${'='.repeat(60)}\n\n`;
  
  // Limpiar polling anterior si existe
  if (consolaPollInterval) {
    clearInterval(consolaPollInterval);
  }
  
  // Iniciar polling para mostrar la consola en tiempo real
  consolaPollInterval = setInterval(async () => {
    try {
      const estadoResp = await fetch(`/api/estado?script=${script}`);
      const estadoData = await estadoResp.json();
      
      // Mostrar las últimas líneas del log en la consola
      if (estadoData.ultimas_lineas && estadoData.ultimas_lineas.length > 0) {
        document.getElementById('consolaContenido').textContent = estadoData.ultimas_lineas.join('\n');
        
        // Auto-scroll al final
        const consola = document.getElementById('consolaContenido');
        consola.scrollTop = consola.scrollHeight;
      }
      
      // Si terminó la ejecución
      if (!estadoData.corriendo) {
        clearInterval(consolaPollInterval);
        consolaPollInterval = null;
        
        // Verificar si hubo errores
        const lineas = estadoData.ultimas_lineas || [];
        const tieneError = lineas.some(l => l.includes('ERROR') || l.includes('❌') || l.includes('Traceback'));
        
        // Agregar mensaje de finalización a la consola
        const consolaContent = document.getElementById('consolaContenido');
        const mensajeFinal = tieneError 
          ? `\n\n${'='.repeat(60)}\n❌ ${btnText} terminó con errores\n${'='.repeat(60)}\n`
          : `\n\n${'='.repeat(60)}\n✅ ${btnText} completado exitosamente\n${'='.repeat(60)}\n`;
        consolaContent.textContent += mensajeFinal;
        
        // Cambiar el título y el indicador
        const statusIndicator = document.querySelector('.status-indicator');
        if (statusIndicator) {
          statusIndicator.style.background = tieneError ? '#EF4444' : '#10B981';
          statusIndicator.style.animation = 'none';
        }
        document.getElementById('consolaTitulo').innerHTML = `<span class="status-indicator" style="background:${tieneError ? '#EF4444' : '#10B981'};animation:none;"></span>${btnText} finalizado`;
        
        if (tieneError) {
          showToast(`❌ ${btnText} terminó con errores`, 'error');
        } else {
          showToast(`✅ ${btnText} completado exitosamente`, 'success');
          
          // Actualizar las stats cards con la nueva fecha/hora
          actualizarStats(script);
          
          // Si se marcó "Forzar", enviar notificaciones automáticamente
          if (forzar) {
            setTimeout(async () => {
              showToast('📧🤖 Enviando notificaciones...', 'success');
              try {
                const notifResp = await fetch('/api/notificaciones/forzar', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({})
                });
                const notifData = await notifResp.json();
                if (notifData.ok) {
                  showToast('✅ Email y Telegram enviados', 'success');
                } else {
                  showToast('⚠️ ' + notifData.error, 'error');
                }
              } catch (e) {
                showToast('❌ Error enviando notificaciones', 'error');
              }
            }, 1000);
          }
        }
        
        // Recargar el dashboard automáticamente después de 2 segundos
        setTimeout(() => {
          location.reload();
        }, 2000);
      }
    } catch (e) {
      console.error('Error en polling:', e);
    }
  }, 1000); // Polling cada 1 segundo
  
  showToast(`✅ ${btnText} iniciado correctamente`, 'success');
}

function verDetalle(num) {
  const carpeta = 'detalle_procesos/' + num.replace(/[\\/*?:"<>|]/g, '_');
  window.open(carpeta, '_blank');
}

function actualizarStats(script) {
  // Actualizar la fecha/hora de última ejecución en las stats cards
  const ahora = new Date();
  const fechaFormateada = ahora.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  
  if (script === 'comprar') {
    const statComprar = document.getElementById('statComprar');
    if (statComprar) {
      statComprar.textContent = fechaFormateada;
      statComprar.style.color = '#059669'; // Verde para indicar que se actualizó
      setTimeout(() => {
        statComprar.style.color = ''; // Volver al color original
      }, 2000);
    }
  } else if (script === 'detalle') {
    const statDetalle = document.getElementById('statDetalle');
    if (statDetalle) {
      statDetalle.textContent = fechaFormateada;
      statDetalle.style.color = '#059669'; // Verde para indicar que se actualizó
      setTimeout(() => {
        statDetalle.style.color = ''; // Volver al color original
      }, 2000);
    }
  }
}

function imprimirUno(num) {
  const t = TARJETAS.find(x => x.numero === num);
  if (!t) return;
  const w = window.open('', '_blank');
  w.document.write(`<html><body><h1>${t.numero}</h1><p>${t.objeto}</p></body></html>`);
  w.document.close();
  setTimeout(() => w.print(), 250);
}

async function mostrarGestion() {
  const resp = await fetch('/api/gestion');
  const data = await resp.json();
  document.getElementById('modalGestion').classList.add('open');
}

function toggleModoNocturno() {
  const activo = document.documentElement.getAttribute('data-theme') === 'dark';
  if (activo) {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('modoNocturno', '0');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('modoNocturno', '1');
  }
  document.getElementById('btnModoNocturno').textContent = activo ? '🌙 Modo nocturno' : '☀️ Modo claro';
}

// ============================================
// FUNCIONES DE EMAIL (NUEVAS)
// ============================================
async function mostrarConfigEmail() {
  document.getElementById('modalEmail').classList.add('open');
  await cargarEmails();
}

async function cargarEmails() {
  const resp = await fetch('/api/emails');
  const data = await resp.json();
  const lista = document.getElementById('listaEmails');
  if (data.emails && data.emails.length > 0) {
    lista.innerHTML = data.emails.map(email => `
      <div class="email-item">
        <span>${email}</span>
        <button class="btn-remove" onclick="eliminarEmail('${email}')">Eliminar</button>
      </div>
    `).join('');
  } else {
    lista.innerHTML = '<p style="color:var(--slate);font-size:13px;">No hay emails configurados</p>';
  }
}

async function agregarEmail() {
  const input = document.getElementById('nuevoEmail');
  const email = input.value.trim();
  if (!email) return;
  const resp = await fetch('/api/emails/agregar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email})
  });
  const data = await resp.json();
  if (data.ok) {
    input.value = '';
    showToast('Email agregado');
    await cargarEmails();
  } else {
    showToast(data.error, 'error');
  }
}

async function eliminarEmail(email) {
  const resp = await fetch('/api/emails/eliminar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast('Email eliminado');
    await cargarEmails();
  }
}

// ============================================
// FUNCIONES DE TELEGRAM (NUEVAS)
// ============================================
async function mostrarConfigTelegram() {
  document.getElementById('modalTelegram').classList.add('open');
  const resp = await fetch('/api/telegram/status');
  const data = await resp.json();
  if (data.config) {
    document.getElementById('telegramToken').value = data.config.bot_token || '';
    document.getElementById('telegramChats').value = (data.config.chat_ids || []).join(',');
  }
}

async function guardarTelegram() {
  const token = document.getElementById('telegramToken').value.trim();
  const chats = document.getElementById('telegramChats').value.trim();
  const resp = await fetch('/api/telegram/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({token, chats})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast('✅ Configuración guardada');
    document.getElementById('modalTelegram').classList.remove('open');
  } else {
    showToast('❌ Error: ' + data.error, 'error');
  }
}

async function probarTelegram() {
  showToast('🤖 Enviando mensaje de prueba...', 'success');
  const resp = await fetch('/api/telegram/test', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast(data.mensaje, 'success');
  } else {
    showToast('❌ ' + data.error, 'error');
  }
}

async function forzarNotificaciones() {
  showToast('📧🤖 Enviando notificaciones forzadas...', 'success');
  const resp = await fetch('/api/notificaciones/forzar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast('✅ Email y Telegram enviados correctamente', 'success');
  } else {
    showToast('❌ ' + data.error, 'error');
  }
}

async function probarEmail() {
  showToast('📧 Enviando email de prueba...', 'success');
  const resp = await fetch('/api/emails/test', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast(data.mensaje, 'success');
  } else {
    showToast('❌ ' + data.error, 'error');
  }
}

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    generar_dashboard()
=======
def obtener_resumen_ejecucion(archivo_log: str) -> str:
    """
    Última línea 'con contenido real' del log (no separadores ni encabezados),
    para mostrar de un vistazo qué pasó la última vez sin abrir el archivo.
    """
    if not os.path.exists(archivo_log):
        return ''
    try:
        with open(archivo_log, 'r', encoding='utf-8') as f:
            lineas = [l.strip() for l in f.readlines() if l.strip()]
        ignorar_prefijos = ('=', 'STDOUT', 'STDERR', 'Ejecución iniciada', 'Ejecución finalizada',
                            'Intérprete:', 'Código de salida')
        for linea in reversed(lineas):
            if linea.startswith(ignorar_prefijos):
                continue
            return linea[:110]
    except Exception:
        pass
    return ''


def registrar_impresion(numero_proceso: str) -> dict:
    """Deja constancia en el registro de gestión de que se imprimió la ficha de un proceso."""
    agregar_a_gestion({
        'Fecha decisión': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'Número de proceso': (numero_proceso or '').strip(),
        'Decisión': 'FICHA IMPRESA',
        'Motivo': '',
        'Fecha descarte': '',
        'Carpeta borrada': '',
    })
    return {"ok": True}


def resetear_datos() -> dict:
    """
    Reseteo general: borra el estado y los Excel generados por comprar.py /
    detalle_proceso.py, y la carpeta de PDF descargados, para que la próxima
    corrida traiga todo de cero -- sin depender de comparar contra nada viejo.

    NO toca: registro_gestion.xlsx (historial de decisiones), notas_mejoras.json
    y licencia.json/codigos_renovacion.json (eso no es "datos de scraping").
    """
    archivos = ["estado_procesos.json", "estado_detalle.json",
                EXCEL_PROCESOS, EXCEL_CRONOGRAMA]
    borrados = []
    for f in archivos:
        if os.path.exists(f):
            os.remove(f)
            borrados.append(f)

    if os.path.isdir(CARPETA_DETALLES):
        shutil.rmtree(CARPETA_DETALLES)
        borrados.append(CARPETA_DETALLES + "/")

    return {"ok": True, "borrados": borrados}


def _texto(valor) -> str:
    """Convierte un valor de pandas a texto legible, tratando NaN/None como vacío
    (evita el bug de bool(nan) == True y el "nan" literal en pantalla)."""
    if valor is None:
        return ''
    if isinstance(valor, float) and pd.isna(valor):
        return ''
    texto = str(valor).strip()
    return '' if texto.lower() == 'nan' else texto


def dias_para_apertura(fecha_apertura_str) -> int | None:
    """Calcula días restantes hasta la apertura."""
    if not fecha_apertura_str or pd.isna(fecha_apertura_str):
        return None
    try:
        for fmt in ('%d/%m/%Y %H:%M Hrs.', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
            try:
                fecha = datetime.strptime(str(fecha_apertura_str).strip(), fmt)
                return (fecha - datetime.now()).days
            except ValueError:
                continue
        fecha = pd.to_datetime(fecha_apertura_str, dayfirst=True, errors='coerce')
        if pd.isna(fecha):
            return None
        return (fecha - datetime.now()).days
    except Exception:
        return None


def descartar_proceso(numero_proceso: str, motivo: str = "") -> dict:
    """
    Marca como DESCARTADA, borra carpeta física, deja registro histórico.
    """
    numero_proceso = (numero_proceso or "").strip()
    df = cargar_cronograma()
    mask = df['Número de proceso'].astype(str).str.strip() == numero_proceso
    if not mask.any():
        return {"ok": False, "error": f"Proceso '{numero_proceso}' no encontrado en {EXCEL_CRONOGRAMA}"}

    # Borrar carpeta física
    carpeta = os.path.join(CARPETA_DETALLES, re.sub(r'[\\/*?:"<>|]', "_", numero_proceso))
    borrado = False
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta)
        borrado = True

    fecha_descarte = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Actualizar estado
    df.loc[mask, 'Estado gestión'] = 'DESCARTADA'
    df.loc[mask, 'Motivo descarte'] = motivo
    df.loc[mask, 'Fecha descarte'] = fecha_descarte
    guardar_cronograma(df)

    # Registro histórico
    agregar_a_gestion({
        'Fecha decisión': fecha_descarte,
        'Número de proceso': numero_proceso,
        'Decisión': 'DESCARTADA',
        'Motivo': motivo,
        'Fecha descarte': fecha_descarte,
        'Carpeta borrada': 'Sí' if borrado else 'No existía',
    })

    return {"ok": True, "carpeta_borrada": borrado, "fecha_descarte": fecha_descarte}


def reactivar_proceso(numero_proceso: str) -> dict:
    """Vuelve a marcar como ACTIVA."""
    numero_proceso = (numero_proceso or "").strip()
    df = cargar_cronograma()
    mask = df['Número de proceso'].astype(str).str.strip() == numero_proceso
    if not mask.any():
        return {"ok": False, "error": f"Proceso '{numero_proceso}' no encontrado en {EXCEL_CRONOGRAMA}"}
    df.loc[mask, 'Estado gestión'] = 'ACTIVA'
    df.loc[mask, 'Motivo descarte'] = ''
    df.loc[mask, 'Fecha descarte'] = ''
    guardar_cronograma(df)

    agregar_a_gestion({
        'Fecha decisión': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'Número de proceso': numero_proceso,
        'Decisión': 'REACTIVADA',
        'Motivo': '',
        'Fecha descarte': '',
        'Carpeta borrada': '',
    })
    return {"ok": True}


# Directorio donde vive este archivo -> ahí también deberían estar comprar.py y
# detalle_proceso.py. Fijamos el cwd del subproceso a esto explícitamente,
# así no importa desde dónde se haya lanzado servidor_dashboard.py.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Candado de concurrencia: evita que dos clicks (o un click doble) lancen el
# mismo script dos veces en simultáneo, pisándose el Excel/JSON.
_lock_ejecuciones = threading.Lock()
_en_ejecucion = {'comprar': False, 'detalle': False}


def estado_ejecucion(script_name: str) -> dict:
    """Consulta si un script está corriendo ahora mismo, y la cola del log."""
    script_map = {'comprar': LOG_COMPRAR, 'detalle': LOG_DETALLE}
    log_file = script_map.get(script_name)
    ultimas_lineas = []
    if log_file and os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            ultimas_lineas = [l.rstrip('\n') for l in f.readlines()][-15:]
    return {
        "corriendo": _en_ejecucion.get(script_name, False),
        "ultimas_lineas": ultimas_lineas,
    }


def ejecutar_script(script_name: str, forzar: bool = False) -> dict:
    """Ejecuta un script Python y registra en log. forzar=True ignora el
    límite de 24h que el script se aplica solo (para correr on-demand)."""
    script_map = {
        'comprar': ('comprar.py', LOG_COMPRAR),
        'detalle': ('detalle_proceso.py', LOG_DETALLE)
    }
    # detalle_proceso.py recorre TODOS los procesos uno por uno (con carga de
    # página real por cada uno) -- 10 minutos se quedaba corto con más de un
    # puñado de procesos y lo matábamos a la fuerza antes de que llegue a
    # guardar el Excel. comprar.py es mucho más rápido, se queda con el límite chico.
    timeout_map = {'comprar': 600, 'detalle': 3600}  # segundos: 10 min vs 60 min
    timeout_segundos = timeout_map.get(script_name, 600)

    if script_name not in script_map:
        return {"ok": False, "error": "Script desconocido"}

    script_file, log_file = script_map[script_name]
    ruta_script = os.path.join(_BASE_DIR, script_file)

    if not os.path.exists(ruta_script):
        return {"ok": False, "error": f"Archivo {script_file} no encontrado en {_BASE_DIR}"}

    with _lock_ejecuciones:
        if _en_ejecucion.get(script_name):
            return {"ok": False, "error": f"{script_file} ya está corriendo, esperá a que termine"}
        _en_ejecucion[script_name] = True

    def run_and_log():
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"\n{'='*60}\n")
            log.write(f"Ejecución iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            log.write(f"Intérprete: {sys.executable}\n")
            if forzar:
                log.write("Modo: FORZADO manualmente (ignora el límite de 24h)\n")
            log.write(f"{'='*60}\n")
            log.flush()
            proceso = None
            try:
                # Popen + lectura línea a línea (en vez de subprocess.run con capture_output,
                # que buferiza TODO hasta que el proceso termina) -- así el log se va
                # escribiendo en tiempo real y la consola en vivo del dashboard sirve de algo.
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["PYTHONUTF8"] = "1"
                if forzar:
                    env["FORZAR_EJECUCION"] = "1"
                proceso = subprocess.Popen(
                    [sys.executable, "-u", ruta_script],  # -u: stdout sin buffer en el hijo
                    cwd=_BASE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",  # nunca revienta el proceso por un emoji que la consola no soporte
                    bufsize=1,
                    env=env,
                )
                inicio = time.time()
                for linea in proceso.stdout:
                    log.write(linea)
                    log.flush()
                    if time.time() - inicio > timeout_segundos:
                        proceso.kill()
                        log.write(f"\n⚠️ TIMEOUT: La ejecución superó los {timeout_segundos//60} minutos, se mató el proceso.\n")
                        break
                proceso.wait(timeout=30)
                log.write(f"\nEjecución finalizada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                log.write(f"Código de salida: {proceso.returncode}\n")
            except Exception as e:
                log.write(f"\n❌ Error: {str(e)}\n")
                if proceso:
                    try:
                        proceso.kill()
                    except Exception:
                        pass
            finally:
                with _lock_ejecuciones:
                    _en_ejecucion[script_name] = False

    # Ejecutar en background
    thread = threading.Thread(target=run_and_log, daemon=True)
    thread.start()

    return {"ok": True, "message": f"Ejecución de {script_name} iniciada en background"}


def generar_dashboard():
    """Genera el HTML del dashboard."""
    df = cargar_cronograma()

    # Respaldo de nombres: si detalle_proceso.py todavía no corrió (o corrió antes
    # de este fix) para un proceso, buscamos el nombre en procesos_armada.xlsx,
    # que comprar.py ya completa para todos los procesos listados.
    nombres_respaldo = {}
    if os.path.exists(EXCEL_PROCESOS):
        try:
            df_procesos = pd.read_excel(EXCEL_PROCESOS)
            col_num = next((c for c in df_procesos.columns if 'úmero de proceso' in c), None)
            col_nom = next((c for c in df_procesos.columns if 'ombre de proceso' in c), None)
            if col_num and col_nom:
                for _, r in df_procesos.iterrows():
                    n = _texto(r.get(col_num))
                    if n:
                        nombres_respaldo[n] = _texto(r.get(col_nom))
        except Exception as e:
            print(f"⚠️ No pude leer {EXCEL_PROCESOS} para respaldo de nombres: {e}")

    # Obtener últimas ejecuciones
    ultima_comprar = obtener_ultima_ejecucion(LOG_COMPRAR)
    ultima_detalle = obtener_ultima_ejecucion(LOG_DETALLE)
    
    tarjetas = []
    tarjetas_vencidas = []
    for _, row in df.iterrows():
        numero = _texto(row.get('Número de proceso', ''))
        dias = dias_para_apertura(row.get('Fecha acto de apertura'))
        estado = row.get('Estado gestión', 'ACTIVA')
        
        # Clasificación visual
        if estado == 'DESCARTADA':
            clase = 'descartada'
            etiqueta = 'DESCARTADA'
        elif dias is None:
            clase = 'sin-fecha'
            etiqueta = '—'
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
        
        # Hallazgos clave
        hallazgos = []
        if _texto(row.get('PDF - FONDEF')):
            hallazgos.append('FONDEF')
        if _texto(row.get('PDF - Pago adelantado')):
            hallazgos.append('Pago adelantado')
        if row.get('PDF - Menciona 6.8.7') == 'Sí':
            hallazgos.append('Cláusula 6.8.7')
        if row.get('PDF - Menciona 6.8.2') == 'Sí':
            hallazgos.append('Cláusula 6.8.2')
        if _texto(row.get('Objeto del gasto (detalle)')):
            hallazgos.append(f"Objeto: {_texto(row['Objeto del gasto (detalle)'])}")
        
        tarjeta = {
            'numero': numero,
            'objeto': (_texto(row.get('Nombre de proceso', '')) or nombres_respaldo.get(numero, ''))[:80] or 'Sin nombre',
            'dias_label': etiqueta,
            'clase': clase,
            'fecha_apertura': _texto(row.get('Fecha acto de apertura', '')),
            'fecha_publicacion': _texto(row.get('Fecha publicación portal', '')),
            'hallazgos': hallazgos,
            'estado': estado,
            'unidad': _texto(row.get('Unidad Ejecutora', '')),
        }

        # Los vencidos van aparte -- no se mezclan con la vista principal
        # (tarjetas/Gantt), pero siguen disponibles en su propia pestaña.
        if clase == 'vencido' and estado != 'DESCARTADA':
            tarjetas_vencidas.append(tarjeta)
        else:
            tarjetas.append(tarjeta)
    
    # Ordenar: urgentes primero, descartadas al final
    orden = {'urgente': 0, 'vencido': 1, 'seguimiento': 2, 'lejana': 3, 'sin-fecha': 4, 'descartada': 5}
    tarjetas.sort(key=lambda t: (orden.get(t['clase'], 9), t['dias_label'] or '999'))
    tarjetas_vencidas.sort(key=lambda t: t['fecha_apertura'] or '', reverse=True)
    
    # Cargar template
    template_path = os.path.join(os.path.dirname(__file__), 'dashboard_template.html')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    else:
        html_template = TEMPLATE_DASHBOARD
    
    html = html_template.replace('/*TARJETAS*/', json.dumps(tarjetas, ensure_ascii=False))
    html = html.replace('/*TARJETAS_VENCIDAS*/', json.dumps(tarjetas_vencidas, ensure_ascii=False))
    html = html.replace('/*ULTIMA_COMPRAR*/', ultima_comprar or 'Nunca')
    html = html.replace('/*ULTIMA_DETALLE*/', ultima_detalle or 'Nunca')
    def _resumen_con_duracion(log_file):
        resumen = obtener_resumen_ejecucion(log_file)
        duracion = obtener_duracion_ultima_ejecucion(log_file)
        if duracion:
            return f"{resumen} · duró {duracion}" if resumen else f"Duró {duracion}"
        return resumen

    html = html.replace('/*RESUMEN_COMPRAR*/', _resumen_con_duracion(LOG_COMPRAR))
    html = html.replace('/*RESUMEN_DETALLE*/', _resumen_con_duracion(LOG_DETALLE))
    
    with open(DASHBOARD_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generado en {os.path.abspath(DASHBOARD_HTML)}")


TEMPLATE_DASHBOARD = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agenda de Licitaciones - Armada</title>
<script>
  // Se aplica ANTES del CSS para que no haya un parpadeo claro->oscuro al cargar.
  if (localStorage.getItem('modoNocturno') === '1') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
</script>
<style>
  :root {
    --navy: #14213D;
    --navy-soft: #1E2E52;
    --ink: #1F2A3C;
    --slate: #5B6B82;
    --slate-light: #8A97AB;
    --border: #E4E8EF;
    --bg: #F4F6F9;
    --surface: #FFFFFF;
    --urgente: #DC2626;
    --urgente-bg: #FEE2E2;
    --urgente-bg-soft: #FFF1F1;
    --seguimiento: #D97706;
    --seguimiento-bg: #FEF3C7;
    --seguimiento-bg-soft: #FFFAEF;
    --lejana: #059669;
    --lejana-bg: #D1FAE5;
    --lejana-bg-soft: #F0FDF7;
    --vencido: #44403C;
    --vencido-bg: #E7E5E4;
    --descartada: #64748B;
    --descartada-bg: #E2E8F0;
  }

  [data-theme="dark"] {
    --navy: #E8ECF5;
    --navy-soft: #C7D0E8;
    --ink: #E4E8F0;
    --slate: #9CA9C0;
    --slate-light: #6B7690;
    --border: #2A3448;
    --bg: #0F1521;
    --surface: #1A2233;
    --urgente: #F87171;
    --urgente-bg: #3D1E1E;
    --urgente-bg-soft: #241717;
    --seguimiento: #FBBF24;
    --seguimiento-bg: #3D3319;
    --seguimiento-bg-soft: #241f13;
    --lejana: #34D399;
    --lejana-bg: #143329;
    --lejana-bg-soft: #12241d;
    --vencido: #A8A29E;
    --vencido-bg: #292522;
    --descartada: #94A3B8;
    --descartada-bg: #232B3A;
  }
  [data-theme="dark"] body { background: var(--bg); }
  [data-theme="dark"] .card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.4); }
  [data-theme="dark"] .modal-bg { background: rgba(0,0,0,0.65); }
  [data-theme="dark"] .toast { background: var(--surface); color: var(--ink); }
  [data-theme="dark"] .badge.urgente, [data-theme="dark"] .badge.seguimiento,
  [data-theme="dark"] .badge.lejana, [data-theme="dark"] .badge.vencido,
  [data-theme="dark"] .badge.descartada { filter: brightness(1.15); }
  [data-theme="dark"] .hallazgo { background: #232B3A; color: #A5B4FC; }
  [data-theme="dark"] .expediente-resultado { background: #23203A; border-color: #3B3266; color: #C4B5FD; }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
    background: var(--bg);
    min-height: 100vh;
    padding: 28px;
    color: var(--ink);
    font-size: 14px;
    line-height: 1.5;
  }
  .container { max-width: 1450px; margin: 0 auto; }

  /* Header */
  .header {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 22px 26px;
    margin-bottom: 20px;
  }
  .header h1 {
    font-size: 22px;
    font-weight: 800;
    color: var(--navy);
    letter-spacing: 0.2px;
  }
  .header .sub { color: var(--slate); font-size: 13px; margin-top: 4px; }

  /* Stats bar */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(230px, 100%), 1fr));
    gap: 14px;
    margin-bottom: 20px;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .stat-card h3 {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--slate);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 8px;
  }
  .stat-card .value { font-size: 20px; font-weight: 800; color: var(--navy); }
  .stat-card .timestamp { font-size: 11px; color: var(--slate-light); margin-top: 4px; }

  /* Toolbar -- botones llamativos con gradiente */
  .toolbar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    align-items: center;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 14px;
    border-radius: 10px;
  }
  .toolbar button {
    padding: 10px 20px;
    border: 0;
    border-radius: 8px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    cursor: pointer;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.2px;
    box-shadow: 0 2px 6px rgba(102,126,234,0.35);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .toolbar button:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(102,126,234,0.4); }
  .toolbar button.secondary {
    background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
    box-shadow: 0 2px 6px rgba(100,116,139,0.3);
  }
  .toolbar button.success {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    box-shadow: 0 2px 6px rgba(17,153,142,0.35);
  }
  .toolbar .view-toggle {
    margin-left: auto;
    display: flex;
    gap: 4px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 4px;
  }
  .toolbar .view-toggle button {
    background: transparent;
    color: var(--slate);
    box-shadow: none;
    padding: 7px 14px;
    font-size: 12.5px;
  }
  .toolbar .view-toggle button:hover { transform: none; box-shadow: none; background: var(--border); }
  .toolbar .view-toggle button.active {
    background: var(--navy);
    color: white;
  }

  .filtro-clausulas {
    display: flex;
    align-items: center;
    gap: 14px;
    width: 100%;
    padding-top: 10px;
    margin-top: 4px;
    border-top: 1px solid var(--border);
    font-size: 12.5px;
  }
  .filtro-label { color: var(--slate); font-weight: 700; }
  .filtro-clausulas label {
    display: flex;
    align-items: center;
    gap: 5px;
    color: var(--ink);
    font-weight: 600;
    cursor: pointer;
  }
  .filtro-clausulas input[type=checkbox] {
    accent-color: #5B21B6;
    width: 14px;
    height: 14px;
  }
  #filtroActivoAviso {
    color: #5B21B6;
    font-weight: 700;
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    padding: 3px 10px;
    border-radius: 20px;
  }

  /* Notas de mejora */
  .notas-wrap { position: relative; }
  .notas-badge {
    display: inline-block;
    background: var(--urgente);
    color: white;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 800;
    padding: 1px 7px;
    margin-left: 6px;
  }
  .notas-dropdown {
    display: none;
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    width: 340px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: 0 12px 28px rgba(20,33,61,0.18);
    z-index: 100;
    overflow: hidden;
  }
  .notas-dropdown.open { display: block; }
  .notas-header {
    padding: 12px 16px;
    font-weight: 800;
    font-size: 13px;
    color: var(--navy);
    border-bottom: 1px solid var(--border);
    background: var(--bg);
  }
  .notas-lista { max-height: 280px; overflow-y: auto; padding: 6px; }
  .nota-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 7px;
  }
  .nota-item:hover { background: var(--bg); }
  .nota-item input[type=checkbox] {
    margin-top: 3px;
    width: 15px;
    height: 15px;
    accent-color: #667eea;
    cursor: pointer;
    flex-shrink: 0;
  }
  .nota-item .nota-texto {
    flex: 1;
    font-size: 12.5px;
    color: var(--ink);
    line-height: 1.4;
    cursor: pointer;
  }
  .nota-item.hecha .nota-texto {
    text-decoration: line-through;
    color: var(--slate-light);
  }
  .nota-item .nota-borrar {
    background: none;
    border: none;
    color: var(--slate-light);
    cursor: pointer;
    font-size: 15px;
    line-height: 1;
    padding: 0 2px;
    flex-shrink: 0;
    box-shadow: none;
  }
  .nota-item .nota-borrar:hover { color: var(--urgente); transform: none; }
  .notas-vacio { padding: 20px; text-align: center; color: var(--slate-light); font-size: 12.5px; }
  .notas-nueva {
    display: flex;
    gap: 6px;
    padding: 10px;
    border-top: 1px solid var(--border);
    background: var(--bg);
  }
  .notas-nueva input {
    flex: 1;
    padding: 8px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 12.5px;
    font-family: inherit;
  }
  .notas-nueva input:focus { outline: none; border-color: #667eea; }
  .notas-nueva button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 6px;
    width: 34px;
    font-size: 16px;
    font-weight: 800;
    cursor: pointer;
    box-shadow: none;
  }

  /* Grid de tarjetas -- pasteles */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
    gap: 16px;
  }
  .card {
    border-radius: 12px;
    padding: 18px;
    border: 1px solid transparent;
    border-left: 6px solid var(--descartada);
    background: var(--surface);
    box-shadow: 0 2px 6px rgba(20,33,61,0.06);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(20,33,61,0.12); }
  .card.urgente      { border-left-color: var(--urgente);     background: var(--urgente-bg-soft); }
  .card.seguimiento  { border-left-color: var(--seguimiento); background: var(--seguimiento-bg-soft); }
  .card.lejana       { border-left-color: var(--lejana);      background: var(--lejana-bg-soft); }
  .card.vencido      { border-left-color: var(--vencido);     background: #FAFAF9; }
  .card.sin-fecha    { border-left-color: var(--descartada);  background: var(--surface); }
  .card.descartada   { opacity: 0.65; border-left-color: var(--descartada); background: var(--bg); }

  .card .num {
    font-weight: 800;
    font-size: 15px;
    font-family: 'Consolas', 'Courier New', monospace;
    color: var(--navy);
    letter-spacing: 0.2px;
  }
  .card .obj {
    color: var(--slate);
    font-size: 12.5px;
    margin: 8px 0 12px;
    min-height: 36px;
    line-height: 1.4;
  }
  .card .meta {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
  }
  .card .dias {
    font-size: 22px;
    font-weight: 800;
    color: var(--ink);
    text-align: right;
    white-space: nowrap;
  }
  .card .dias .clock { font-size: 15px; margin-right: 2px; }
  .card .dias small {
    display: block;
    font-size: 10px;
    font-weight: 600;
    color: var(--slate-light);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }
  .badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 10.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .badge.urgente     { background: var(--urgente-bg);     color: #991B1B; }
  .badge.seguimiento { background: var(--seguimiento-bg); color: #92400E; }
  .badge.lejana      { background: var(--lejana-bg);      color: #065F46; }
  .badge.vencido     { background: var(--vencido-bg);     color: var(--vencido); }
  .badge.descartada  { background: var(--descartada-bg);  color: #475569; }

  .hallazgos {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 12px 0;
  }
  .hallazgo {
    background: #EFF6FF;
    color: #1E40AF;
    padding: 4px 11px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
  }

  .actions {
    display: flex;
    gap: 8px;
    margin-top: 14px;
    flex-wrap: wrap;
  }
  .actions button {
    flex: 1;
    min-width: 80px;
    padding: 8px 12px;
    border: 0;
    border-radius: 7px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 700;
    transition: all 0.15s;
  }
  .btn-descartar { background: #FEE2E2; color: #991B1B; }
  .btn-descartar:hover { background: #FECACA; }
  .btn-reactivar { background: #D1FAE5; color: #065F46; }
  .btn-reactivar:hover { background: #A7F3D0; }
  .btn-imprimir  { background: #DBEAFE; color: #1E40AF; }
  .btn-imprimir:hover { background: #BFDBFE; }
  .btn-ver       { background: #F3F4F6; color: #374151; }
  .btn-ver:hover { background: #E5E7EB; }
  .btn-expediente { background: #EDE9FE; color: #5B21B6; }
  .btn-expediente:hover { background: #DDD6FE; }
  .expediente-resultado {
    background: #F5F3FF;
    border: 1px solid #DDD6FE;
    border-radius: 7px;
    padding: 8px 10px;
    margin: 8px 0;
    font-size: 11px;
    color: #5B21B6;
    font-family: 'Consolas', 'Courier New', monospace;
    word-break: break-word;
  }

  /* Consola de ejecución en vivo */
  .consola-ejecucion {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    max-height: 260px;
    background: #0B1220;
    border-top: 2px solid #667eea;
    box-shadow: 0 -8px 24px rgba(0,0,0,0.25);
    z-index: 1500;
    display: flex;
    flex-direction: column;
  }
  .consola-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 14px;
    background: #151E33;
    color: #A5B4FC;
    font-size: 12px;
    font-weight: 700;
  }
  .consola-header button {
    background: transparent;
    border: 1px solid #334155;
    color: #94A3B8;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 11px;
    cursor: pointer;
    box-shadow: none;
  }
  .consola-header button:hover { background: #1E293B; transform: none; }
  #consolaContenido {
    margin: 0;
    padding: 10px 14px;
    overflow-y: auto;
    color: #D1D5DB;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11.5px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* Gantt */
  .gantt-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .gantt-scale {
    display: grid;
    grid-template-columns: 280px 1fr;
    margin-bottom: 6px;
  }
  .gantt-scale .labels-head { }
  .gantt-scale .dates-head {
    position: relative;
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--slate-light);
    font-weight: 700;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  .gantt-rows { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
  .gantt-row {
    display: grid;
    grid-template-columns: 280px 1fr;
    align-items: center;
    gap: 10px;
  }
  .gantt-label {
    font-size: 12px;
    color: var(--ink);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .gantt-label .num {
    font-family: 'Consolas', 'Courier New', monospace;
    font-weight: 800;
    color: var(--navy);
    display: block;
    font-size: 12px;
  }
  .gantt-label .nombre {
    display: block;
    color: var(--slate);
    font-size: 11px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .gantt-track {
    position: relative;
    height: 26px;
    background: var(--bg);
    border-radius: 6px;
    border: 1px solid var(--border);
  }
  .gantt-bar {
    position: absolute;
    top: 3px;
    bottom: 3px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    padding: 0 8px;
    font-size: 10.5px;
    font-weight: 700;
    color: white;
    white-space: nowrap;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  }
  .gantt-bar.urgente      { background: linear-gradient(135deg, #f87171, #dc2626); }
  .gantt-bar.seguimiento  { background: linear-gradient(135deg, #fbbf24, #d97706); }
  .gantt-bar.lejana       { background: linear-gradient(135deg, #34d399, #059669); }
  .gantt-bar.vencido      { background: linear-gradient(135deg, #78716c, #44403c); }
  .gantt-bar.descartada   { background: linear-gradient(135deg, #cbd5e1, #94a3b8); }
  .gantt-today {
    position: absolute;
    top: -4px;
    bottom: -4px;
    width: 2px;
    background: #667eea;
    z-index: 5;
  }
  .gantt-today::after {
    content: 'HOY';
    position: absolute;
    top: -16px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 8.5px;
    font-weight: 800;
    color: #667eea;
    letter-spacing: 0.5px;
  }
  .gantt-empty { color: var(--slate-light); font-size: 13px; padding: 30px; text-align: center; }

  /* Modal */
  .modal-bg {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(20,33,61,0.5);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(3px);
  }
  .modal-bg.open { display: flex; }
  .modal {
    background: var(--surface);
    border-radius: 12px;
    padding: 26px;
    max-width: 520px;
    width: 90%;
    box-shadow: 0 20px 40px rgba(20,33,61,0.2);
  }
  .modal h3 {
    margin-bottom: 10px;
    font-size: 17px;
    font-weight: 800;
    color: var(--navy);
  }
  .modal p { color: var(--slate); font-size: 13px; margin-bottom: 14px; line-height: 1.5; }
  .modal textarea {
    width: 100%;
    min-height: 90px;
    padding: 10px 12px;
    border: 2px solid var(--border);
    border-radius: 8px;
    font-family: inherit;
    font-size: 13px;
    resize: vertical;
  }
  .modal textarea:focus {
    outline: none;
    border-color: #667eea;
  }
  .modal .btns {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 18px;
  }
  .modal button {
    padding: 10px 20px;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 700;
    font-size: 13px;
  }
  .modal .confirm { background: var(--urgente); color: white; }
  .modal .confirm:hover { background: #B91C1C; }
  .modal .cancel  { background: var(--border); color: var(--slate); }
  .modal .cancel:hover { background: #CBD5E1; }

  /* Impresión */
  @media print {
    body { background: white; padding: 0; }
    .toolbar, .actions, .modal-bg, .stats { display: none !important; }
    .card { break-inside: avoid; box-shadow: none; border: 1px solid var(--border); }
    .grid { grid-template-columns: 1fr; }
    .header { box-shadow: none; border: 1px solid var(--border); }
    #printFiltroInfo { display: block !important; }
  }
  #printFiltroInfo {
    display: none;
    font-size: 12px;
    font-weight: 700;
    color: #5B21B6;
    margin: -10px 0 14px;
  }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: white;
    padding: 15px 22px;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    z-index: 2000;
    display: none;
    font-size: 13px;
    font-weight: 700;
    color: var(--ink);
    animation: slideIn 0.25s ease;
  }
  .toast.show { display: block; }
  .toast.success { border-left: 4px solid #059669; }
  .toast.error { border-left: 4px solid #DC2626; }
  @keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>Agenda de Licitaciones</h1>
    <p class="sub">Seguimiento de procesos de compra - Armada Argentina</p>
  </div>

  <div id="printFiltroInfo"></div>
  
  <div class="stats">
    <div class="stat-card">
      <h3>Última ejecución — comprar.py</h3>
      <div class="value" id="statComprar">/*ULTIMA_COMPRAR*/</div>
      <div class="timestamp" id="resumenComprar">/*RESUMEN_COMPRAR*/</div>
    </div>
    <div class="stat-card">
      <h3>Última ejecución — detalle_proceso.py</h3>
      <div class="value" id="statDetalle">/*ULTIMA_DETALLE*/</div>
      <div class="timestamp" id="resumenDetalle">/*RESUMEN_DETALLE*/</div>
    </div>
    <div class="stat-card">
      <h3>Total procesos</h3>
      <div class="value" id="statTotal">0</div>
    </div>
    <div class="stat-card">
      <h3>Urgentes (&lt; 3 días)</h3>
      <div class="value" id="statUrgentes">0</div>
    </div>
  </div>

  <div class="toolbar">
    <button onclick="ejecutarScript('comprar')" class="success">Ejecutar comprar.py</button>
    <button onclick="ejecutarScript('detalle')" class="success">Ejecutar detalle_proceso.py</button>
    <label style="display:flex; align-items:center; gap:5px; font-size:12px; color:#5B6B82; font-weight:600; cursor:pointer;" title="Corre aunque no hayan pasado las 24h desde la última vez -- solo esta corrida, no cambia el scheduler automático">
      <input type="checkbox" id="chkForzar" style="accent-color:#667eea; width:14px; height:14px;">
      Forzar (ignorar límite de 24h)
    </label>
    <button onclick="location.reload()">Refrescar dashboard</button>
    <button class="secondary" onclick="mostrarGestion()">Registro de gestión</button>
    <button class="secondary" onclick="window.print()">Imprimir agenda</button>
    <button style="background:linear-gradient(135deg, #f87171, #dc2626); box-shadow:0 2px 6px rgba(220,38,38,0.35);" onclick="abrirReseteo()">Reseteo general</button>
    <button id="btnModoNocturno" class="secondary" onclick="toggleModoNocturno()">🌙 Modo nocturno</button>
    <div class="notas-wrap">
      <button class="secondary" onclick="toggleNotas()">Notas / Mejoras <span id="notasPendientesBadge" class="notas-badge" style="display:none">0</span></button>
      <div class="notas-dropdown" id="notasDropdown">
        <div class="notas-header">Notas de mejora</div>
        <div class="notas-lista" id="notasLista"></div>
        <div class="notas-nueva">
          <input type="text" id="notaNuevaInput" placeholder="Agregar una nota..." onkeydown="if(event.key==='Enter') agregarNota()">
          <button onclick="agregarNota()">+</button>
        </div>
      </div>
    </div>
    <div class="view-toggle">
      <button id="btnVistaTarjetas" class="active" onclick="cambiarVista('tarjetas')">Tarjetas</button>
      <button id="btnVistaGantt" onclick="cambiarVista('gantt')">Gantt</button>
      <button id="btnVistaVencidos" onclick="cambiarVista('vencidos')">Vencidos <span id="vencidosBadge" class="notas-badge" style="display:none">0</span></button>
    </div>
    <div class="filtro-clausulas">
      <span class="filtro-label">Filtrar por cláusula:</span>
      <label><input type="checkbox" id="chk687" onchange="aplicarFiltroClausulas()"> 6.8.7</label>
      <label><input type="checkbox" id="chk682" onchange="aplicarFiltroClausulas()"> 6.8.2</label>
      <span id="filtroActivoAviso" style="display:none"></span>
    </div>
  </div>

  <div class="grid" id="grid"></div>
  <div class="gantt-wrap" id="ganttView" style="display:none"></div>
  <div class="grid" id="gridVencidos" style="display:none"></div>
</div>

<div class="consola-ejecucion" id="consolaEjecucion" style="display:none">
  <div class="consola-header">
    <span id="consolaTitulo">Ejecutando...</span>
    <button onclick="document.getElementById('consolaEjecucion').style.display='none'">Cerrar</button>
  </div>
  <pre id="consolaContenido"></pre>
</div>

<!-- Modal descartar -->
<div class="modal-bg" id="modalDescartar">
  <div class="modal">
    <h3>️ Descartar proceso</h3>
    <p>
      Esta acción eliminará permanentemente la carpeta con los PDFs y documentos descargados.
      Los datos de gestión quedarán registrados en el histórico con estado "DESCARTADA".
    </p>
    <textarea id="motivoDescarte" placeholder="Motivo del descarte (obligatorio)..."></textarea>
    <div class="btns">
      <button class="cancel" onclick="cerrarModal()">Cancelar</button>
      <button class="confirm" onclick="confirmarDescarte()">Confirmar descarte</button>
    </div>
  </div>
</div>

<!-- Modal reseteo general -->
<div class="modal-bg" id="modalReseteo">
  <div class="modal">
    <h3>Reseteo general</h3>
    <p>
      Esto borra <strong>estado_procesos.json</strong>, <strong>estado_detalle.json</strong>,
      <strong>procesos_armada.xlsx</strong>, <strong>cronograma_procesos.xlsx</strong> y la carpeta
      <strong>detalle_procesos/</strong> (todos los PDF descargados).<br><br>
      El registro de gestión, las notas de mejora y la licencia <strong>NO</strong> se tocan.<br><br>
      Después de resetear, la próxima corrida de <code>comprar.py</code> va a traer todo de cero.
      Esta acción no se puede deshacer.
    </p>
    <div class="btns">
      <button class="cancel" onclick="document.getElementById('modalReseteo').classList.remove('open')">Cancelar</button>
      <button class="confirm" onclick="confirmarReseteo()">Sí, resetear todo</button>
    </div>
  </div>
</div>

<!-- Modal registro de gestión -->
<div class="modal-bg" id="modalGestion">
  <div class="modal" style="max-width:800px;">
    <h3> Registro de Gestión</h3>
    <div id="gestionContent" style="max-height:500px;overflow:auto;font-size:13px;margin:16px 0;"></div>
    <div class="btns">
      <button class="cancel" onclick="document.getElementById('modalGestion').classList.remove('open')">Cerrar</button>
      <button class="success" onclick="imprimirGestion()">Imprimir</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
const TARJETAS = /*TARJETAS*/;
const TARJETAS_VENCIDAS = /*TARJETAS_VENCIDAS*/;
let procesoADescartar = null;

// Calcular estadísticas
const total = TARJETAS.length;
const urgentes = TARJETAS.filter(t => t.clase === 'urgente').length;
document.getElementById('statTotal').textContent = total;
document.getElementById('statUrgentes').textContent = urgentes;

function tarjetasFiltradas() {
  const elChk687 = document.getElementById('chk687');
  const elChk682 = document.getElementById('chk682');
  const aviso = document.getElementById('filtroActivoAviso');
  const printInfo = document.getElementById('printFiltroInfo');

  // Si por algún motivo faltan los elementos del filtro, no rompemos todo
  // el render -- simplemente mostramos todas las tarjetas sin filtrar.
  if (!elChk687 || !elChk682) {
    return TARJETAS;
  }

  const filtro687 = elChk687.checked;
  const filtro682 = elChk682.checked;

  if (!filtro687 && !filtro682) {
    if (aviso) aviso.style.display = 'none';
    if (printInfo) printInfo.textContent = 'Listado completo (sin filtro por cláusula).';
    return TARJETAS;
  }

  const etiquetas = [];
  if (filtro687) etiquetas.push('Cláusula 6.8.7');
  if (filtro682) etiquetas.push('Cláusula 6.8.2');

  if (aviso) {
    aviso.style.display = 'inline-block';
    aviso.textContent = `Filtro activo: ${etiquetas.join(' / ')}`;
  }
  if (printInfo) printInfo.textContent = `Listado filtrado por: ${etiquetas.join(' / ')}`;

  return TARJETAS.filter(t => etiquetas.some(e => t.hallazgos.includes(e)));
}

function aplicarFiltroClausulas() {
  render();
}

function render() {
  const grid = document.getElementById('grid');
  const filtradas = tarjetasFiltradas();

  if (filtradas.length === 0) {
    grid.innerHTML = '<div class="gantt-empty">Ningún proceso activo coincide con el filtro seleccionado.</div>';
    return;
  }

  grid.innerHTML = filtradas.map(t => `
    <div class="card ${t.clase}" data-num="${t.numero}">
      <div class="meta">
        <div class="num">${t.numero}</div>
        <div class="dias">${/^\d+\s/.test(t.dias_label) ? '<span class="clock">⏱️</span>' : ''}${t.dias_label}<small>para apertura</small></div>
      </div>
      <div class="obj">${t.objeto || 'Sin descripción'}</div>
      ${t.hallazgos.length ? `<div class="hallazgos">${t.hallazgos.map(h=>`<span class="hallazgo">${h}</span>`).join('')}</div>` : ''}
      <div style="font-size:11px;color:var(--slate);margin:8px 0;">
        <div>Apertura: ${t.fecha_apertura || '—'}</div>
        <div>Publicación: ${t.fecha_publicacion || '—'}</div>
        ${t.unidad ? `<div>${t.unidad}</div>` : ''}
      </div>
      <div class="expediente-resultado" id="expediente-${t.numero.replace(/[^a-zA-Z0-9]/g,'_')}" style="display:none"></div>
      <div class="actions">
        <button class="btn-ver" onclick="verDetalle('${t.numero}')">Ver</button>
        ${t.estado === 'DESCARTADA'
          ? `<button class="btn-reactivar" onclick="reactivar('${t.numero}')">Reactivar</button>`
          : `<button class="btn-descartar" onclick="abrirDescarte('${t.numero}')">Descartar</button>`}
        <button class="btn-imprimir" onclick="imprimirUno('${t.numero}')">Ficha</button>
        <button class="btn-expediente" onclick="buscarExpediente('${t.numero}', this)">Expediente</button>
      </div>
    </div>
  `).join('');
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 4000);
}

function abrirDescarte(num) {
  procesoADescartar = num;
  document.getElementById('motivoDescarte').value = '';
  document.getElementById('modalDescartar').classList.add('open');
}

function cerrarModal() {
  document.getElementById('modalDescartar').classList.remove('open');
  procesoADescartar = null;
}

function abrirReseteo() {
  document.getElementById('modalReseteo').classList.add('open');
}

async function confirmarReseteo() {
  const resp = await fetch('/api/resetear', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}' });
  const data = await resp.json();
  document.getElementById('modalReseteo').classList.remove('open');

  if (data.ok) {
    const detalle = data.borrados.length ? data.borrados.join(', ') : '(no había nada para borrar)';
    showToast(`Reseteo listo -- se borró: ${detalle}`);
    setTimeout(() => location.reload(), 2000);
  } else {
    showToast('Error al resetear: ' + (data.error || 'desconocido'), 'error');
  }
}

async function confirmarDescarte() {
  const motivo = document.getElementById('motivoDescarte').value.trim();
  if (!motivo) {
    alert('Por favor ingresá el motivo del descarte');
    return;
  }
  
  const resp = await fetch('/api/descartar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: procesoADescartar, motivo})
  });
  const data = await resp.json();
  
  if (data.ok) {
    showToast(`Proceso ${procesoADescartar} descartado correctamente`);
    setTimeout(() => location.reload(), 1500);
  } else {
    showToast('Error: ' + data.error, 'error');
  }
  cerrarModal();
}

async function reactivar(num) {
  const resp = await fetch('/api/reactivar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: num})
  });
  const data = await resp.json();
  if (data.ok) {
    showToast(`Proceso ${num} reactivado`);
    setTimeout(() => location.reload(), 1000);
  } else {
    showToast('Error: ' + data.error, 'error');
  }
}

async function ejecutarScript(script) {
  const nombres = {comprar: 'comprar.py', detalle: 'detalle_proceso.py'};
  const forzar = document.getElementById('chkForzar').checked;

  const resp = await fetch('/api/ejecutar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({script, forzar})
  });
  const data = await resp.json();

  if (!data.ok) {
    showToast(data.error, 'error');
    return;
  }

  document.getElementById('consolaTitulo').textContent = `Corriendo ${nombres[script]}... (00:00)`;
  document.getElementById('consolaContenido').textContent = 'Arrancando...';
  document.getElementById('consolaEjecucion').style.display = 'flex';

  monitorearEjecucion(script, nombres[script]);
}

function formatoCronometro(segundos) {
  const m = Math.floor(segundos / 60).toString().padStart(2, '0');
  const s = Math.floor(segundos % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

async function monitorearEjecucion(script, nombreLegible) {
  const contenido = document.getElementById('consolaContenido');
  const titulo = document.getElementById('consolaTitulo');
  const inicio = Date.now();

  // Cronómetro visual, tickea cada segundo aunque el poll de logs sea cada 2s.
  const cronometro = setInterval(() => {
    const segundos = (Date.now() - inicio) / 1000;
    titulo.textContent = `Corriendo ${nombreLegible}... (${formatoCronometro(segundos)})`;
  }, 1000);

  const poll = setInterval(async () => {
    const resp = await fetch(`/api/estado?script=${script}`);
    const data = await resp.json();

    if (data.ultimas_lineas && data.ultimas_lineas.length) {
      contenido.textContent = data.ultimas_lineas.join('\n');
      contenido.scrollTop = contenido.scrollHeight;
    }

    if (!data.corriendo) {
      clearInterval(poll);
      clearInterval(cronometro);
      const total = formatoCronometro((Date.now() - inicio) / 1000);
      titulo.textContent = `${nombreLegible} terminó (tardó ${total})`;
      showToast(`${nombreLegible} terminó en ${total}`);
      setTimeout(() => location.reload(), 1800);
    }
  }, 2000);
}

function verDetalle(num) {
  const carpeta = 'detalle_procesos/' + num.replace(/[\\/*?:"<>|]/g, '_');
  window.open(carpeta, '_blank');
}

function imprimirUno(num) {
  const t = TARJETAS.find(x => x.numero === num) || TARJETAS_VENCIDAS.find(x => x.numero === num);
  if (!t) return;

  fetch('/api/registrar_impresion', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({numero: num})
  }).catch(() => {});

  const w = window.open('', '_blank', 'width=800,height=700');
  w.document.write(`
    <html><head><title>Ficha ${num}</title>
    <style>
      body{font-family:'Segoe UI',sans-serif;padding:32px;max-width:700px;margin:0 auto;}
      h1{color:#14213D;border-bottom:2px solid #E4E8EF;padding-bottom:12px;}
      .row{margin:10px 0;padding:8px 10px;background:#F4F6F9;border-radius:5px;border:1px solid #E4E8EF;}
      .label{font-weight:700;color:#5B6B82;display:inline-block;width:180px;font-size:12px;text-transform:uppercase;letter-spacing:0.3px;}
      .hallazgo{display:inline-block;background:#F4F6F9;border:1px solid #E4E8EF;color:#5B6B82;padding:3px 10px;border-radius:4px;margin:3px;font-size:11px;font-weight:600;}
      .badge{display:inline-block;padding:4px 12px;border-radius:4px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.4px;}
      .badge.urgente{background:#FBEDEC;color:#B0413E;}
      .badge.seguimiento{background:#FBF3E6;color:#A9762B;}
      .badge.lejana{background:#EBF5F0;color:#2F7A5C;}
      .badge.descartada{background:#EFF1F4;color:#5B6B82;}
      @media print{body{padding:0;}}
    </style></head><body>
    <h1>📋 Ficha de Proceso</h1>
    <h2 style="color:#333;margin:16px 0;">${t.numero}</h2>
    <p style="font-size:16px;color:#666;line-height:1.6;">${t.objeto || 'Sin descripción'}</p>
    
    <div class="row"><span class="label">Estado:</span> 
      <span class="badge ${t.clase}">${t.estado}</span>
    </div>
    <div class="row"><span class="label">Días para apertura:</span> ${t.dias_label}</div>
    <div class="row"><span class="label">Fecha de apertura:</span> ${t.fecha_apertura || '—'}</div>
    <div class="row"><span class="label">Fecha publicación:</span> ${t.fecha_publicacion || '—'}</div>
    <div class="row"><span class="label">Unidad ejecutora:</span> ${t.unidad || '—'}</div>
    
    <div class="row">
      <span class="label">Hallazgos:</span><br>
      ${t.hallazgos.length ? t.hallazgos.map(h=>`<span class="hallazgo">${h}</span>`).join(' ') : '<span style="color:#999;">Sin hallazgos destacados</span>'}
    </div>
    
    <div style="margin-top:32px;padding-top:16px;border-top:2px solid #e2e8f0;font-size:11px;color:#999;">
      Generado el ${new Date().toLocaleString('es-AR')}
    </div>
    </body></html>
  `);
  w.document.close();
  setTimeout(() => w.print(), 250);
}

async function mostrarGestion() {
  const resp = await fetch('/api/gestion');
  const data = await resp.json();
  const div = document.getElementById('gestionContent');
  
  if (!data.rows || !data.rows.length) {
    div.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">Sin registros de gestión aún</p>';
  } else {
    div.innerHTML = '<table style="width:100%;border-collapse:collapse;font-size:12px;">' +
      '<thead style="background:#14213D;color:white;"><tr>' +
      '<th style="padding:12px;text-align:left;">Fecha</th>' +
      '<th style="padding:12px;text-align:left;">Proceso</th>' +
      '<th style="padding:12px;text-align:left;">Decisión</th>' +
      '<th style="padding:12px;text-align:left;">Motivo</th>' +
      '<th style="padding:12px;text-align:left;">Carpeta</th>' +
      '</tr></thead><tbody>' +
      data.rows.map(r => `<tr style="border-bottom:1px solid #e2e8f0;">
        <td style="padding:10px;">${r['Fecha decisión']||''}</td>
        <td style="padding:10px;"><strong>${r['Número de proceso']||''}</strong></td>
        <td style="padding:10px;">${r['Decisión']||''}</td>
        <td style="padding:10px;color:#666;">${r['Motivo']||''}</td>
        <td style="padding:10px;">${r['Carpeta borrada']||''}</td>
      </tr>`).join('') +
      '</tbody></table>';
  }
  document.getElementById('modalGestion').classList.add('open');
}

function imprimirGestion() {
  const contenido = document.getElementById('gestionContent').innerHTML;
  const w = window.open('', '_blank', 'width=900,height=700');
  w.document.write(`
    <html><head><title>Registro de Gestión</title>
    <style>
      body{font-family:'Segoe UI',sans-serif;padding:32px;}
      h1{color:#14213D;}
      table{width:100%;border-collapse:collapse;}
      th,td{border:1px solid #ddd;padding:10px;text-align:left;font-size:11px;}
      th{background:#14213D;color:white;}
      tr:nth-child(even){background:#f8f9fa;}
    </style></head>
    <body>
    <h1>📋 Registro de Gestión</h1>
    <p style="color:#666;font-size:12px;">Generado el ${new Date().toLocaleString('es-AR')}</p>
    ${contenido}
    </body></html>
  `);
  w.document.close();
  setTimeout(() => w.print(), 250);
}

function parseFechaAR(str) {
  // Formato esperado: "dd/mm/yyyy HH:MM Hrs." (tolera variantes con menos partes)
  if (!str || typeof str !== 'string') return null;
  const m = str.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?/);
  if (!m) return null;
  const [, d, mo, y, h, mi] = m;
  const fecha = new Date(+y, +mo - 1, +d, h ? +h : 0, mi ? +mi : 0);
  return isNaN(fecha.getTime()) ? null : fecha;
}

function cambiarVista(vista) {
  const grid = document.getElementById('grid');
  const gantt = document.getElementById('ganttView');
  const gridVencidos = document.getElementById('gridVencidos');
  const btnT = document.getElementById('btnVistaTarjetas');
  const btnG = document.getElementById('btnVistaGantt');
  const btnV = document.getElementById('btnVistaVencidos');

  grid.style.display = 'none';
  gantt.style.display = 'none';
  gridVencidos.style.display = 'none';
  btnT.classList.remove('active');
  btnG.classList.remove('active');
  btnV.classList.remove('active');

  if (vista === 'gantt') {
    gantt.style.display = 'block';
    btnG.classList.add('active');
    renderGantt();
  } else if (vista === 'vencidos') {
    gridVencidos.style.display = 'grid';
    btnV.classList.add('active');
    renderVencidos();
  } else {
    grid.style.display = 'grid';
    btnT.classList.add('active');
  }
}

function renderVencidos() {
  const cont = document.getElementById('gridVencidos');
  if (TARJETAS_VENCIDAS.length === 0) {
    cont.innerHTML = '<div class="gantt-empty">No hay procesos vencidos por ahora.</div>';
    return;
  }
  cont.innerHTML = TARJETAS_VENCIDAS.map(t => `
    <div class="card vencido">
      <div class="meta">
        <div class="num">${t.numero}</div>
        <div class="dias">${t.dias_label}<small>para apertura</small></div>
      </div>
      <div class="obj">${t.objeto || 'Sin descripción'}</div>
      ${t.hallazgos.length ? `<div class="hallazgos">${t.hallazgos.map(h=>`<span class="hallazgo">${h}</span>`).join('')}</div>` : ''}
      <div style="font-size:11px;color:var(--slate);margin:8px 0;">
        <div>Apertura: ${t.fecha_apertura || '—'}</div>
        <div>Publicación: ${t.fecha_publicacion || '—'}</div>
        ${t.unidad ? `<div>${t.unidad}</div>` : ''}
      </div>
      <div class="expediente-resultado" id="expediente-${t.numero.replace(/[^a-zA-Z0-9]/g,'_')}" style="display:none"></div>
      <div class="actions">
        <button class="btn-ver" onclick="verDetalle('${t.numero}')">Ver</button>
        <button class="btn-descartar" onclick="abrirDescarte('${t.numero}')">Descartar</button>
        <button class="btn-imprimir" onclick="imprimirUno('${t.numero}')">Ficha</button>
        <button class="btn-expediente" onclick="buscarExpediente('${t.numero}', this)">Expediente</button>
      </div>
    </div>
  `).join('');
}

function actualizarBadgeVencidos() {
  const badge = document.getElementById('vencidosBadge');
  if (TARJETAS_VENCIDAS.length > 0) {
    badge.style.display = 'inline-block';
    badge.textContent = TARJETAS_VENCIDAS.length;
  }
}

function renderGantt() {
  const cont = document.getElementById('ganttView');

  const filas = TARJETAS
    .map(t => ({ t, pub: parseFechaAR(t.fecha_publicacion), ape: parseFechaAR(t.fecha_apertura) }))
    .filter(f => f.pub && f.ape && f.ape >= f.pub);

  if (filas.length === 0) {
    cont.innerHTML = '<div class="gantt-empty">No hay procesos con fechas de publicación y apertura completas para graficar.</div>';
    return;
  }

  const hoy = new Date();
  let minFecha = new Date(Math.min(...filas.map(f => f.pub.getTime())));
  let maxFecha = new Date(Math.max(...filas.map(f => f.ape.getTime())));
  // Un poco de margen a los costados (10% del rango total)
  const margen = Math.max((maxFecha - minFecha) * 0.08, 1000 * 60 * 60 * 24);
  minFecha = new Date(minFecha.getTime() - margen);
  maxFecha = new Date(maxFecha.getTime() + margen);
  const rangoTotal = maxFecha - minFecha;

  const pct = (fecha) => Math.min(100, Math.max(0, ((fecha - minFecha) / rangoTotal) * 100));
  const hoyPct = pct(hoy);
  const mostrarHoy = hoy >= minFecha && hoy <= maxFecha;

  const fmt = (f) => f.toLocaleDateString('es-AR', { day: '2-digit', month: 'short' });

  let html = `
    <div class="gantt-scale">
      <div class="labels-head"></div>
      <div class="dates-head"><span>${fmt(minFecha)}</span><span>${fmt(maxFecha)}</span></div>
    </div>
    <div class="gantt-rows">
  `;

  filas.forEach(({ t, pub, ape }) => {
    const left = pct(pub);
    const width = Math.max(pct(ape) - left, 1.5); // ancho mínimo para que se vea aunque sea 1 día
    html += `
      <div class="gantt-row">
        <div class="gantt-label">
          <span class="num">${t.numero}</span>
          <span class="nombre">${t.objeto}</span>
        </div>
        <div class="gantt-track">
          <div class="gantt-bar ${t.clase}" style="left:${left}%;width:${width}%" title="${t.numero} — Publicación: ${t.fecha_publicacion} / Apertura: ${t.fecha_apertura}">${t.dias_label}</div>
          ${mostrarHoy ? `<div class="gantt-today" style="left:${hoyPct}%"></div>` : ''}
        </div>
      </div>
    `;
  });

  html += '</div>';
  cont.innerHTML = html;
}

let NOTAS_CACHE = [];

async function cargarNotas() {
  try {
    const resp = await fetch('/api/notas');
    const data = await resp.json();
    NOTAS_CACHE = data.notas || [];
    renderNotas();
  } catch (e) {
    NOTAS_CACHE = [];
  }
}

function renderNotas() {
  const lista = document.getElementById('notasLista');
  const badge = document.getElementById('notasPendientesBadge');

  if (NOTAS_CACHE.length === 0) {
    lista.innerHTML = '<div class="notas-vacio">Todavía no hay notas cargadas.</div>';
  } else {
    lista.innerHTML = NOTAS_CACHE.map(n => `
      <div class="nota-item ${n.hecha ? 'hecha' : ''}">
        <input type="checkbox" ${n.hecha ? 'checked' : ''} onchange="marcarNota(${n.id}, this.checked)">
        <span class="nota-texto" onclick="const cb=this.previousElementSibling; cb.checked=!cb.checked; marcarNota(${n.id}, cb.checked);">${n.texto}</span>
        <button class="nota-borrar" onclick="borrarNota(${n.id})" title="Eliminar">×</button>
      </div>
    `).join('');
  }

  const pendientes = NOTAS_CACHE.filter(n => !n.hecha).length;
  if (pendientes > 0) {
    badge.style.display = 'inline-block';
    badge.textContent = pendientes;
  } else {
    badge.style.display = 'none';
  }
}

function toggleNotas() {
  const dd = document.getElementById('notasDropdown');
  dd.classList.toggle('open');
  if (dd.classList.contains('open')) cargarNotas();
}

document.addEventListener('click', (e) => {
  const wrap = document.querySelector('.notas-wrap');
  if (wrap && !wrap.contains(e.target)) {
    document.getElementById('notasDropdown').classList.remove('open');
  }
});

async function agregarNota() {
  const input = document.getElementById('notaNuevaInput');
  const texto = input.value.trim();
  if (!texto) return;
  const resp = await fetch('/api/notas/agregar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({texto})
  });
  const data = await resp.json();
  if (data.ok) {
    NOTAS_CACHE = data.notas;
    renderNotas();
    input.value = '';
  }
}

async function marcarNota(id, hecha) {
  const resp = await fetch('/api/notas/marcar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id, hecha})
  });
  const data = await resp.json();
  if (data.ok) {
    NOTAS_CACHE = data.notas;
    renderNotas();
  }
}

async function borrarNota(id) {
  const resp = await fetch('/api/notas/eliminar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id})
  });
  const data = await resp.json();
  if (data.ok) {
    NOTAS_CACHE = data.notas;
    renderNotas();
  }
}

cargarNotas();
async function buscarExpediente(num, btn) {
  const idSeguro = num.replace(/[^a-zA-Z0-9]/g, '_');
  const div = document.getElementById('expediente-' + idSeguro);
  const textoOriginal = btn.textContent;
  btn.textContent = 'Buscando...';
  btn.disabled = true;

  try {
    const resp = await fetch('/api/expediente', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({numero: num})
    });
    const data = await resp.json();

    if (data.ok) {
      div.style.display = 'block';
      div.innerHTML = `<strong>Expediente:</strong> ${data.expediente}<br><span style="opacity:0.7">(${data.archivo})</span>`;
      showToast('Expediente encontrado');
    } else {
      div.style.display = 'block';
      div.innerHTML = data.error;
      showToast(data.error, 'error');
    }
  } catch (e) {
    showToast('Error consultando el expediente', 'error');
  } finally {
    btn.textContent = textoOriginal;
    btn.disabled = false;
  }
}

function toggleModoNocturno() {
  const activo = document.documentElement.getAttribute('data-theme') === 'dark';
  if (activo) {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('modoNocturno', '0');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('modoNocturno', '1');
  }
  actualizarBotonModoNocturno();
}

function actualizarBotonModoNocturno() {
  const activo = document.documentElement.getAttribute('data-theme') === 'dark';
  document.getElementById('btnModoNocturno').textContent = activo ? '☀️ Modo claro' : '🌙 Modo nocturno';
}

render();
actualizarBadgeVencidos();
actualizarBotonModoNocturno();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    generar_dashboard()
>>>>>>> 4ba397a7e8115f1ed48d8188face0b9b4f32d19d
