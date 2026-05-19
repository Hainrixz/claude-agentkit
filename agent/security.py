# agent/security.py — Funciones puras de seguridad
import os
import sys
import time
import logging
import unicodedata
from collections import OrderedDict, defaultdict

logger = logging.getLogger("agentkit")

MAX_LONGITUD_MENSAJE = 4000
RATE_LIMIT_MENSAJES = 10
RATE_LIMIT_VENTANA_SEGUNDOS = 60

RATE_LIMIT_TRACKER: dict[str, list[float]] = defaultdict(list)

MENSAJES_PROCESADOS: OrderedDict[str, float] = OrderedDict()
MENSAJES_PROCESADOS_MAX = 10000
MENSAJES_PROCESADOS_TTL = 3600


def validar_configuracion() -> None:
    """Falla rápido al arrancar si falta configuración crítica."""
    proveedor = os.getenv("WHATSAPP_PROVIDER", "").lower()
    requeridas = ["ANTHROPIC_API_KEY", "WHATSAPP_PROVIDER"]
    if proveedor == "meta":
        requeridas += ["META_ACCESS_TOKEN", "META_PHONE_NUMBER_ID",
                       "META_VERIFY_TOKEN", "META_APP_SECRET"]
    elif proveedor == "twilio":
        requeridas += ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
                       "TWILIO_PHONE_NUMBER"]

    faltan = [v for v in requeridas if not os.getenv(v)]
    if faltan:
        logger.error(f"Variables faltantes en .env: {', '.join(faltan)}")
        sys.exit(1)

    vt = os.getenv("META_VERIFY_TOKEN", "")
    if vt and vt in ("agentkit-verify", "verify", "test", "token") or len(vt) < 16:
        if proveedor == "meta":
            logger.warning("META_VERIFY_TOKEN es débil. Genera uno aleatorio: "
                           "python -c 'import secrets;print(secrets.token_urlsafe(32))'")


def rate_limit_excedido(telefono: str) -> bool:
    """True si el número superó el límite de mensajes en la ventana."""
    ahora = time.time()
    ventana = RATE_LIMIT_TRACKER[telefono]
    ventana[:] = [t for t in ventana if ahora - t < RATE_LIMIT_VENTANA_SEGUNDOS]
    if len(ventana) >= RATE_LIMIT_MENSAJES:
        return True
    ventana.append(ahora)
    return False


def sanitizar_mensaje(texto: str) -> str:
    """Normaliza Unicode y elimina caracteres de control."""
    if not texto:
        return ""
    if len(texto) > MAX_LONGITUD_MENSAJE:
        texto = texto[:MAX_LONGITUD_MENSAJE]
    texto = unicodedata.normalize("NFKC", texto)
    texto = "".join(
        c for c in texto
        if c in ("\n", "\t") or not unicodedata.category(c).startswith("C")
    )
    return texto.strip()


def ya_procesado(mensaje_id: str) -> bool:
    """True si el mensaje_id ya fue procesado dentro del TTL."""
    if not mensaje_id:
        return False
    ahora = time.time()
    while MENSAJES_PROCESADOS:
        primer_id = next(iter(MENSAJES_PROCESADOS))
        if ahora - MENSAJES_PROCESADOS[primer_id] > MENSAJES_PROCESADOS_TTL:
            MENSAJES_PROCESADOS.popitem(last=False)
        else:
            break
    return mensaje_id in MENSAJES_PROCESADOS


def marcar_procesado(mensaje_id: str) -> None:
    """Registra mensaje_id como procesado, manteniendo el cache acotado."""
    if not mensaje_id:
        return
    MENSAJES_PROCESADOS[mensaje_id] = time.time()
    while len(MENSAJES_PROCESADOS) > MENSAJES_PROCESADOS_MAX:
        MENSAJES_PROCESADOS.popitem(last=False)
