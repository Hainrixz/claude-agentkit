# agent/security.py — Funciones puras de seguridad
# Generado por AgentKit

import os
import sys
import time
import logging
import unicodedata
from collections import OrderedDict, defaultdict

logger = logging.getLogger("agentkit")

# Límites de entrada — protegen contra abuso y consumo excesivo de tokens
MAX_LONGITUD_MENSAJE = 4000           # WhatsApp permite hasta 4096; truncamos antes
RATE_LIMIT_MENSAJES = 10              # mensajes por ventana
RATE_LIMIT_VENTANA_SEGUNDOS = 60

# Tracker en memoria por número de teléfono.
# Nota: con múltiples workers cada uno tiene su propio tracker — usar Redis si
# corre con --workers > 1.
RATE_LIMIT_TRACKER: dict[str, list[float]] = defaultdict(list)

# Cache de mensajes ya procesados — evita procesar duplicados cuando Meta
# hace retry del webhook (Meta espera 200 en <20s o reenvía).
# OrderedDict para FIFO: descartamos los más viejos al alcanzar el límite.
MENSAJES_PROCESADOS: OrderedDict[str, float] = OrderedDict()
MENSAJES_PROCESADOS_MAX = 10000
MENSAJES_PROCESADOS_TTL = 3600  # 1h


def validar_configuracion() -> None:
    """
    Falla rápido al arrancar si falta configuración crítica.
    Mejor un error claro al inicio que respuestas raras en producción.
    """
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

    # verify_token predecible es vulnerable
    vt = os.getenv("META_VERIFY_TOKEN", "")
    if proveedor == "meta" and (vt in ("agentkit-verify", "verify", "test", "token") or len(vt) < 16):
        logger.warning("META_VERIFY_TOKEN es débil. Genera uno aleatorio: "
                       "python -c 'import secrets;print(secrets.token_urlsafe(32))'")


def rate_limit_excedido(telefono: str) -> bool:
    """True si el número superó el límite de mensajes en la ventana."""
    ahora = time.time()
    ventana = RATE_LIMIT_TRACKER[telefono]
    # Mantener solo timestamps dentro de la ventana
    ventana[:] = [t for t in ventana if ahora - t < RATE_LIMIT_VENTANA_SEGUNDOS]
    if len(ventana) >= RATE_LIMIT_MENSAJES:
        return True
    ventana.append(ahora)
    return False


def sanitizar_mensaje(texto: str) -> str:
    """
    Normaliza Unicode y elimina caracteres de control.
    NFKC colapsa variantes (homoglyphs, fullwidth) a su forma canónica.
    Mantenemos \\n y \\t por si el usuario envía mensajes multilínea.
    """
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
    # Limpiar entradas expiradas
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
