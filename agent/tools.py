# agent/tools.py — Herramientas del agente
# Generado por AgentKit

"""
Herramientas específicas del negocio Web Jose.
Estas funciones extienden las capacidades del agente más allá de responder texto.
"""

import os
import pathlib
import yaml
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("agentkit")

# Limites para protegerse contra archivos enormes en /knowledge que
# agotarían memoria o consumo de tokens en Claude
MAX_BYTES_ARCHIVO = 5 * 1024 * 1024   # 5 MB por archivo
MAX_RESULTADOS = 5                     # Top-N resultados de búsqueda
KNOWLEDGE_DIR = pathlib.Path("knowledge").resolve()

# Zona horaria Argentina (UTC-3) — Web Jose opera desde Argentina
TZ_AR = timezone(timedelta(hours=-3))


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    """
    Retorna el horario de atención de Web Jose y si está abierto ahora.
    Lunes-Viernes: 8-18 hs. Sábados-Domingos: 8-12 hs.
    """
    info = cargar_info_negocio()
    ahora = datetime.now(TZ_AR)
    dia_semana = ahora.weekday()  # 0=lunes, 6=domingo
    hora = ahora.hour

    if dia_semana < 5:  # lunes a viernes
        esta_abierto = 8 <= hora < 18
    else:  # sábado y domingo
        esta_abierto = 8 <= hora < 12

    return {
        "horario": info.get("negocio", {}).get("horario", "No disponible"),
        "esta_abierto": esta_abierto,
        "hora_actual_ar": ahora.strftime("%Y-%m-%d %H:%M"),
    }


def buscar_en_knowledge(consulta: str) -> str:
    """
    Busca información relevante en los archivos de /knowledge.
    Retorna hasta MAX_RESULTADOS coincidencias.
    """
    if not consulta or len(consulta) > 500:
        return "Consulta inválida."

    if not KNOWLEDGE_DIR.exists():
        return "No hay archivos de conocimiento disponibles."

    resultados = []
    for ruta in KNOWLEDGE_DIR.iterdir():
        if not ruta.is_file() or ruta.name.startswith("."):
            continue
        # Defensa en profundidad: aunque iterdir() no debería salirse,
        # verificamos que la ruta resuelta esté dentro de KNOWLEDGE_DIR
        # (protege contra symlinks que apunten fuera)
        try:
            ruta_real = ruta.resolve()
            ruta_real.relative_to(KNOWLEDGE_DIR)
        except ValueError:
            logger.warning(f"Symlink fuera de knowledge/ ignorado: {ruta.name}")
            continue
        # Saltar archivos demasiado grandes
        if ruta.stat().st_size > MAX_BYTES_ARCHIVO:
            logger.warning(f"Archivo demasiado grande, ignorado: {ruta.name}")
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read(MAX_BYTES_ARCHIVO)
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{ruta.name}]: {contenido[:500]}")
                    if len(resultados) >= MAX_RESULTADOS:
                        break
        except (UnicodeDecodeError, IOError, OSError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


# ════════════════════════════════════════════════════════════
# Herramientas para Web Jose — placeholders para integraciones futuras.
# Por ahora son stubs que registran la intención; el equipo de Web Jose
# puede integrarlas con su CRM/calendario real cuando lo necesiten.
# ════════════════════════════════════════════════════════════

def registrar_lead(telefono: str, nombre: str = "", interes: str = "",
                   presupuesto: str = "", urgencia: str = "") -> dict:
    """
    Registra un lead calificado para que el equipo comercial lo contacte.
    Por ahora guarda en logs; integrar con CRM (HubSpot, Pipedrive, etc.) cuando esté disponible.
    """
    lead = {
        "telefono": telefono,
        "nombre": nombre,
        "interes": interes,
        "presupuesto": presupuesto,
        "urgencia": urgencia,
        "fecha": datetime.now(TZ_AR).isoformat(),
    }
    logger.info(f"LEAD CALIFICADO: {lead}")
    return {"ok": True, "mensaje": "Lead registrado. El equipo comercial te contactará pronto."}


def agendar_consultoria(telefono: str, nombre: str, fecha_preferida: str,
                        tema: str = "") -> dict:
    """
    Solicita una reunión de consultoría. Por ahora registra la intención;
    integrar con Calendly/Google Calendar cuando esté disponible.
    """
    solicitud = {
        "telefono": telefono,
        "nombre": nombre,
        "fecha_preferida": fecha_preferida,
        "tema": tema,
        "fecha_solicitud": datetime.now(TZ_AR).isoformat(),
    }
    logger.info(f"CONSULTORIA SOLICITADA: {solicitud}")
    return {
        "ok": True,
        "mensaje": "Tu solicitud fue registrada. Te enviaremos confirmación con horarios disponibles dentro del horario de atención."
    }


def escalar_a_humano(telefono: str, motivo: str, contexto: str = "") -> dict:
    """
    Marca la conversación para que un humano del equipo la atienda.
    Por ahora solo loguea; integrar con sistema de tickets o notificación al equipo.
    """
    escalacion = {
        "telefono": telefono,
        "motivo": motivo,
        "contexto": contexto,
        "fecha": datetime.now(TZ_AR).isoformat(),
    }
    logger.info(f"ESCALACION A HUMANO: {escalacion}")
    return {
        "ok": True,
        "mensaje": "Listo, te derivé con alguien del equipo. Te contactarán en breve dentro del horario de atención."
    }


def crear_ticket_soporte(telefono: str, problema: str, prioridad: str = "media") -> dict:
    """
    Crea un ticket de soporte post-venta para clientes existentes.
    Por ahora solo loguea; integrar con sistema de tickets cuando esté disponible.
    """
    ticket_id = f"WJ-{int(datetime.now(TZ_AR).timestamp())}"
    ticket = {
        "id": ticket_id,
        "telefono": telefono,
        "problema": problema,
        "prioridad": prioridad,
        "fecha": datetime.now(TZ_AR).isoformat(),
    }
    logger.info(f"TICKET CREADO: {ticket}")
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "mensaje": f"Tu ticket {ticket_id} fue creado. Te responderemos en el menor tiempo posible."
    }
