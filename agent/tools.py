# agent/tools.py — Herramientas del agente HELIX · AI
import os
import pathlib
import yaml
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("agentkit")

MAX_BYTES_ARCHIVO = 5 * 1024 * 1024
MAX_RESULTADOS = 5
KNOWLEDGE_DIR = pathlib.Path("knowledge").resolve()

# Palabras que indican que Sofía cerró una cita o capturó un lead completo
_PALABRAS_CONFIRMACION = [
    "agendad", "confirmad", "reservad", "quedamos para", "te espero",
    "nos vemos el", "reunión confirmada", "cita confirmada",
]


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


def detectar_confirmacion(texto: str) -> bool:
    """Devuelve True si el texto de Sofía indica que acaba de confirmar una cita o lead."""
    texto_lower = texto.lower()
    return any(p in texto_lower for p in _PALABRAS_CONFIRMACION)


def enviar_notificacion_lead(telefono: str, historial: list[dict], respuesta_sofia: str) -> bool:
    """
    Envía un email de notificación cuando Sofía confirma una cita o captura un lead.
    Requiere en .env: SMTP_EMAIL, SMTP_PASSWORD, NOTIFICATION_EMAIL.
    """
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    notification_email = os.getenv("NOTIFICATION_EMAIL")

    if not all([smtp_email, smtp_password, notification_email]):
        logger.warning("Notificación de lead omitida: SMTP_EMAIL, SMTP_PASSWORD o NOTIFICATION_EMAIL no configurados")
        return False

    # Armar resumen legible de la conversación
    lineas = []
    for m in historial[-20:]:  # últimos 20 mensajes
        rol = "Cliente" if m["role"] == "user" else "Sofía"
        lineas.append(f"{rol}: {m['content']}")
    lineas.append(f"Sofía: {respuesta_sofia}")
    resumen = "\n".join(lineas)

    cuerpo = f"""Sofía acaba de confirmar una cita o capturar un lead.

Teléfono del cliente: {telefono}

─── Conversación ───────────────────────
{resumen}
────────────────────────────────────────

Respondé por WhatsApp al: +{telefono}
"""

    msg = MIMEMultipart()
    msg["Subject"] = f"🔔 Nuevo lead de WhatsApp — {telefono}"
    msg["From"] = smtp_email
    msg["To"] = notification_email
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        logger.info(f"Notificación de lead enviada a {notification_email} — tel: {telefono}")
        return True
    except Exception as e:
        logger.error(f"Error enviando notificación de lead: {e}")
        return False
