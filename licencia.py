"""
licencia.py
Control simple de "licencia" atada a la MAC de la máquina, con renovación
periódica obligatoria cada N días.

IMPORTANTE -- limitaciones honestas de este mecanismo:
- No es un sistema de DRM real. Cualquiera con acceso al código puede
  editar este archivo, borrar licencia.json, o cambiar CLAVE_RENOVACION.
  Sirve como freno razonable para que la carpeta no se copie y ande sola
  en otra PC sin que vos te enteres/lo autorices -- no como protección
  a prueba de un usuario técnico con mala intención.
- La verificación de MAC puede fallar en máquinas con varias placas de
  red (VPN, virtualización, adaptadores USB): uuid.getnode() puede
  devolver una MAC distinta según el orden en que Windows enumere las
  interfaces. Si notás falsos "no autorizada" en la MISMA máquina,
  avisame y cambiamos el criterio (por ejemplo, atar a un ID de disco
  en vez de a la MAC).
"""
import json
import os
import uuid
import hashlib
from datetime import datetime, timedelta

LICENCIA_PATH = "licencia.json"
DIAS_VALIDEZ = 15

# Clave para renovar la licencia cada 15 días. CAMBIÁ ESTE TEXTO por el que
# quieras usar vos -- se guarda hasheada (SHA-256) más abajo, nunca en
# texto plano, así que si alguien abre este archivo no la ve directamente
# salvo que sepa que este es justo el valor que hasheaste.
CLAVE_RENOVACION = "ARMADA-2026"
CLAVE_RENOVACION_HASH = hashlib.sha256(CLAVE_RENOVACION.encode()).hexdigest()


CODIGOS_PATH = "codigos_renovacion.json"


def _cargar_codigos() -> list:
    if os.path.exists(CODIGOS_PATH):
        with open(CODIGOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _guardar_codigos(codigos: list):
    with open(CODIGOS_PATH, "w", encoding="utf-8") as f:
        json.dump(codigos, f, ensure_ascii=False, indent=2)


def generar_codigos(cantidad: int = 5) -> list:
    """
    Genera códigos de renovación de UN SOLO USO (para dar a alguien puntual,
    o guardarte una reserva sin repetir siempre la clave maestra). Corré esto
    vos mismo por consola -- no hay forma de generarlos desde el dashboard
    web, a propósito, para que no los pueda crear cualquiera.
    """
    import secrets
    codigos = _cargar_codigos()
    nuevos = []
    for _ in range(cantidad):
        codigo = '-'.join(secrets.token_hex(2).upper() for _ in range(3))  # ej: A1B2-C3D4-E5F6
        codigos.append({"codigo": codigo, "usado": False, "fecha_creacion": datetime.now().isoformat()})
        nuevos.append(codigo)
    _guardar_codigos(codigos)
    return nuevos


def _consumir_codigo(codigo: str) -> bool:
    codigos = _cargar_codigos()
    for c in codigos:
        if c["codigo"] == codigo.strip().upper() and not c["usado"]:
            c["usado"] = True
            c["fecha_uso"] = datetime.now().isoformat()
            _guardar_codigos(codigos)
            return True
    return False


def obtener_mac() -> str:
    """MAC de la máquina actual, normalizada como string."""
    n = uuid.getnode()
    return ':'.join(f'{(n >> ele) & 0xff:02x}' for ele in range(40, -8, -8))


def cargar_licencia() -> dict:
    if os.path.exists(LICENCIA_PATH):
        with open(LICENCIA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_licencia(datos: dict):
    with open(LICENCIA_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def verificar_licencia() -> dict:
    """
    {'ok': bool, 'motivo': str, 'requiere_renovacion': bool, 'dias_restantes': int|None}

    - Primera vez que corre en una máquina -> se activa sola, atada a esa MAC.
    - Si la MAC no coincide con la que quedó guardada -> bloqueada.
    - Si pasaron más de DIAS_VALIDEZ desde la última renovación -> requiere
      renovación (se puede seguir usando la MISMA máquina, pero hay que
      escribir la clave de nuevo para extender otros 15 días).
    """
    mac_actual = obtener_mac()
    licencia = cargar_licencia()

    if not licencia:
        licencia = {
            "mac_autorizada": mac_actual,
            "fecha_activacion": datetime.now().isoformat(),
            "fecha_ultima_renovacion": datetime.now().isoformat(),
        }
        guardar_licencia(licencia)
        return {"ok": True, "motivo": "Activada por primera vez en esta máquina.",
                "requiere_renovacion": False, "dias_restantes": DIAS_VALIDEZ}

    if licencia.get("mac_autorizada") != mac_actual:
        return {"ok": False,
                "motivo": "Esta instalación está autorizada para otra máquina (la dirección MAC no coincide).",
                "requiere_renovacion": False, "dias_restantes": None}

    ultima = datetime.fromisoformat(licencia["fecha_ultima_renovacion"])
    vence = ultima + timedelta(days=DIAS_VALIDEZ)
    dias_restantes = (vence - datetime.now()).days

    if datetime.now() > vence:
        return {"ok": False,
                "motivo": f"La licencia venció el {vence.strftime('%d/%m/%Y')}. Hay que renovarla.",
                "requiere_renovacion": True, "dias_restantes": 0}

    return {"ok": True, "motivo": f"Licencia vigente ({dias_restantes} días restantes).",
            "requiere_renovacion": False, "dias_restantes": dias_restantes}


def renovar_licencia(clave: str) -> dict:
    clave = (clave or "").strip()
    es_clave_maestra = hashlib.sha256(clave.encode()).hexdigest() == CLAVE_RENOVACION_HASH
    es_codigo_valido = not es_clave_maestra and _consumir_codigo(clave)

    if not es_clave_maestra and not es_codigo_valido:
        return {"ok": False, "error": "Clave o código de renovación incorrecto."}

    # La clave/código correcto renueva los 15 días Y re-autoriza esta MAC --
    # así sirve tanto para extender la licencia vencida en la misma máquina
    # como para autorizar deliberadamente una máquina nueva (mismo mecanismo).
    licencia = {
        "mac_autorizada": obtener_mac(),
        "fecha_activacion": cargar_licencia().get("fecha_activacion", datetime.now().isoformat()),
        "fecha_ultima_renovacion": datetime.now().isoformat(),
    }
    guardar_licencia(licencia)
    tipo = "código de un solo uso" if es_codigo_valido else "clave maestra"
    return {"ok": True, "mensaje": f"Licencia renovada/autorizada por {DIAS_VALIDEZ} días más en esta máquina ({tipo})."}