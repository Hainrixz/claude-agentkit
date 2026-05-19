# agent/tools.py — Herramientas del agente HELIX · AI
import os
import pathlib
import yaml
import logging

logger = logging.getLogger("agentkit")

MAX_BYTES_ARCHIVO = 5 * 1024 * 1024
MAX_RESULTADOS = 5
KNOWLEDGE_DIR = pathlib.Path("knowledge").resolve()


def cargar_info_negocio() -> dict:
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    info = cargar_info_negocio()
    return {
        "horario": info.get("negocio", {}).get("horario", "Lunes a Viernes 8:00 a 18:00 hs"),
        "esta_abierto": True,
    }


def buscar_en_knowledge(consulta: str) -> str:
    """Busca información relevante en los archivos de /knowledge."""
    if not consulta or len(consulta) > 500:
        return "Consulta inválida."

    if not KNOWLEDGE_DIR.exists():
        return "No hay archivos de conocimiento disponibles."

    resultados = []
    for ruta in KNOWLEDGE_DIR.iterdir():
        if not ruta.is_file() or ruta.name.startswith("."):
            continue
        try:
            ruta_real = ruta.resolve()
            ruta_real.relative_to(KNOWLEDGE_DIR)
        except ValueError:
            logger.warning(f"Symlink fuera de knowledge/ ignorado: {ruta.name}")
            continue
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


def registrar_lead(telefono: str, nombre: str, interes: str) -> str:
    """Registra un lead interesado en servicios de HELIX · AI."""
    logger.info(f"Lead registrado — tel: {telefono}, nombre: {nombre}, interés: {interes}")
    return f"Lead registrado correctamente para {nombre}."


def obtener_info_servicios(pilar: str = "") -> str:
    """Retorna información sobre los servicios según el pilar consultado."""
    servicios = {
        "estrategia": "Estrategia e Identidad: Branding, posicionamiento y propuesta de valor única.",
        "crecimiento": "Crecimiento Digital: Marketing estratégico, contenido con IA y gestión de redes sociales.",
        "automatizacion": "Automatización IA: Agentes 24/7, calificación de leads, agendamiento automático. Recuperás hasta 3 horas/día.",
        "web": "Infraestructura Web: Ecosistemas digitales integrados con CRM, calendarios y herramientas de negocio.",
        "auditoria": "Auditoría de Crecimiento: Diagnóstico inicial gratuito donde analizamos tu situación y los procesos más automatizables.",
    }
    if pilar.lower() in servicios:
        return servicios[pilar.lower()]
    return "\n".join(servicios.values())
