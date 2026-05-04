# agent/tools.py — Herramientas del agente
# Generado por AgentKit

"""
Herramientas específicas del negocio.
Estas funciones extienden las capacidades del agente más allá de responder texto.
Claude Code genera las funciones según los casos de uso elegidos en la entrevista.
"""

import os
import yaml
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger("agentkit")


def obtener_agente_activo() -> str:
    """Retorna el nombre del agente activo desde variables de entorno."""
    return os.getenv("AGENTE_ACTIVO", "default")


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde config/{AGENTE_ACTIVO}/business.yaml."""
    agente = obtener_agente_activo()
    ruta = f"config/{agente}/business.yaml"
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"{ruta} no encontrado")
        return {}


def obtener_horario() -> dict:
    """Retorna el horario de atención del negocio."""
    info = cargar_info_negocio()
    return {
        "horario": info.get("negocio", {}).get("horario", "No disponible"),
        "esta_abierto": True,  # TODO: calcular según hora actual y horario
    }


def buscar_en_knowledge(consulta: str) -> str:
    """
    Busca información relevante en los archivos de knowledge/{AGENTE_ACTIVO}.
    Retorna el contenido más relevante encontrado.
    """
    resultados = []
    agente = obtener_agente_activo()
    knowledge_dir = f"knowledge/{agente}"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                # Búsqueda simple por coincidencia de texto
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


def consultar_precios() -> dict:
    """
    Carga el catálogo de precios del agente activo desde precios.yaml.
    Retorna el diccionario completo con estructura de precios.
    """
    agente = obtener_agente_activo()
    ruta = f"config/{agente}/precios.yaml"

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            precios = yaml.safe_load(f) or {}
            logger.info(f"Catálogo de precios cargado para agente: {agente}")
            return precios
    except FileNotFoundError:
        logger.warning(f"Archivo de precios no encontrado: {ruta}")
        return {}


def detectar_tipo_pregunta(mensaje: str) -> tuple[str, str]:
    """
    Detecta el tipo de pregunta según los filtros configurados en prompts.yaml.
    Lee la configuración del agente activo y busca coincidencias con keywords.

    Retorna (tipo_detectado: str, instruccion_extra: str).
    Si no hay coincidencia, retorna ("general", "").
    """
    agente = obtener_agente_activo()
    ruta = f"config/{agente}/prompts.yaml"

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning(f"No se pudo cargar {ruta} para detectar tipo de pregunta")
        return "general", ""

    # Obtener los filtros configurados para este agente
    filtros = config.get("filtros", {})
    if not filtros:
        return "general", ""

    mensaje_lower = mensaje.lower()

    # Buscar el primer tipo que coincida con los keywords
    for tipo, cfg in filtros.items():
        keywords = cfg.get("keywords", [])
        instruccion = cfg.get("instruccion_extra", "")

        # Verificar si alguna keyword está en el mensaje
        if any(k in mensaje_lower for k in keywords):
            logger.info(f"Tipo de pregunta detectado: {tipo}")
            return tipo, instruccion

    return "general", ""


async def crear_evento_calendario(nombre: str, telefono: str, dispositivo: str,
                                   fecha: str, hora: str) -> bool:
    """
    Crea un evento en Google Calendar para la cita del cliente.

    Soporta 2 modos:
    1. Una cuenta maestra con múltiples calendarios (RECOMENDADO para vender)
       - GOOGLE_CALENDAR_CREDENTIALS: credenciales del proveedor (una sola)
       - calendar_id en config/{agente}/business.yaml por agente

    2. Cada cliente configura su propio
       - GOOGLE_CALENDAR_CREDENTIALS: credenciales del cliente
       - GOOGLE_CALENDAR_ID: su calendar ID

    Retorna True si fue exitoso, False si no hay credenciales o hubo error.
    """
    credentials_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")

    # Intentar obtener calendar_id del agente primero (modo multi-calendario)
    agente = obtener_agente_activo()
    calendar_id = None

    try:
        info = cargar_info_negocio()
        calendar_id = info.get("negocio", {}).get("calendar_id")
    except:
        pass

    # Si no está en business.yaml, intentar desde variable de entorno
    if not calendar_id:
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")

    if not credentials_json or not calendar_id:
        logger.warning(f"Google Calendar no configurado para {agente} — cita no creada en calendario")
        return False

    try:
        # Importar Google libraries (solo si están configuradas)
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # Parsear credenciales
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )

        # Construir cliente de Google Calendar
        service = build("calendar", "v3", credentials=credentials)

        # Crear timestamps
        inicio = f"{fecha}T{hora}:00"
        dt_inicio = datetime.fromisoformat(inicio)
        dt_fin = dt_inicio + timedelta(hours=1)
        fin = dt_fin.isoformat()

        # Obtener info del negocio para el evento
        agente = obtener_agente_activo()
        info = cargar_info_negocio()
        nombre_negocio = info.get("negocio", {}).get("nombre", agente)

        # Estructura del evento
        evento = {
            "summary": f"Cita - {dispositivo} ({nombre})",
            "description": (
                f"Cliente: {nombre}\n"
                f"Teléfono: {telefono}\n"
                f"Dispositivo: {dispositivo}\n"
                f"Agendado via {nombre_negocio} Bot"
            ),
            "start": {
                "dateTime": inicio,
                "timeZone": "America/Argentina/Buenos_Aires"
            },
            "end": {
                "dateTime": fin,
                "timeZone": "America/Argentina/Buenos_Aires"
            },
        }

        # Insertar evento en Google Calendar
        service.events().insert(calendarId=calendar_id, body=evento).execute()
        logger.info(f"Evento creado en Google Calendar: {nombre} - {fecha} {hora}")
        return True

    except Exception as e:
        logger.error(f"Error Google Calendar: {e}")
        return False


# ════════════════════════════════════════════════════════════
# Herramientas específicas para Mundo Electronico
# ════════════════════════════════════════════════════════════

def obtener_servicios_disponibles() -> list[str]:
    """Retorna la lista de servicios que ofrece el negocio."""
    return [
        "Reparación de celulares",
        "Reparación de tablets",
        "Reparación de notebooks",
        "Cambio de componentes",
        "Actualizaciones de software",
        "Venta de accesorios",
        "Punto Pickit",
        "Correo Argentino"
    ]


def validar_dispositivo(dispositivo: str) -> bool:
    """Valida si es un dispositivo que el negocio repara."""
    dispositivos_validos = ["celular", "smartphone", "teléfono", "tablet", "notebook", "laptop", "computadora portátil"]
    return any(d in dispositivo.lower() for d in dispositivos_validos)


def crear_resumen_cita(nombre: str, telefono: str, dispositivo: str, problema: str, horario: str) -> str:
    """Crea un resumen de cita para confirmar con el cliente."""
    return f"""
📋 **Resumen de tu cita:**
Nombre: {nombre}
Teléfono: {telefono}
Dispositivo: {dispositivo}
Problema: {problema}
Horario: {horario}

Te esperamos en nuestro local. ¡Gracias por tu confianza! 🙏
"""


# ════════════════════════════════════════════════════════════
# FUNCIONES PARA SISTEMA DE TICKETS (PHASE 5)
# ════════════════════════════════════════════════════════════

async def crear_ticket_desde_cita(nombre: str, telefono: str, dispositivo: str, problema: str, client_id: str = None) -> str:
    """
    Crea un ticket de soporte cuando se agenda una cita.
    Retorna el número de ticket.
    """
    from agent.memory import crear_ticket
    agente = obtener_agente_activo()
    ticket_numero = await crear_ticket(
        nombre=nombre,
        telefono=telefono,
        dispositivo=dispositivo,
        problema=problema,
        client_id=client_id,
        agente=agente
    )
    logger.info(f"Ticket creado: {ticket_numero}")
    return ticket_numero


async def buscar_estado_reparacion(telefono: str, consulta: str = "") -> str:
    """
    Busca el estado de los tickets del cliente.
    Si consulta menciona un número de ticket específico, busca ese.
    Si no, retorna resumen de todos los tickets del cliente.
    """
    from agent.memory import buscar_tickets_por_telefono, consultar_ticket
    import re

    # Intentar extraer número de ticket de la consulta (ej: "MER-20260328-001")
    patron_ticket = r'[A-Z]{3}-\d{8}-\d{3}'
    match = re.search(patron_ticket, consulta)

    if match:
        # El usuario menciona un ticket específico
        ticket_numero = match.group(0)
        ticket = await consultar_ticket(ticket_numero)
        if ticket:
            return f"""
📱 **Estado de tu reparación:**
Ticket: {ticket['ticket_numero']}
Dispositivo: {ticket['dispositivo']}
Estado: **{ticket['estado'].upper()}**
Problema: {ticket['problema']}
Creado: {ticket['fecha_creacion'][:10]}
Última actualización: {ticket['fecha_actualizacion'][:10]}

Notas: {ticket['notas'] if ticket['notas'] else 'Sin notas adicionales'}
"""
        else:
            return f"No encontré el ticket {ticket_numero}. Verifica el número."

    # Si no especifica ticket, mostrar todos los tickets del cliente
    tickets = await buscar_tickets_por_telefono(telefono)

    if not tickets:
        return "No tenés reparaciones registradas. ¿Necesitas agendar una?"

    respuesta = "📋 **Tus reparaciones:**\n"
    for i, t in enumerate(tickets, 1):
        estado_icon = {
            "abierto": "🆕",
            "en_progreso": "⚙️",
            "completado": "✅",
            "cerrado": "✓",
        }.get(t["estado"], "•")
        respuesta += f"\n{i}. {estado_icon} **{t['ticket_numero']}** — {t['dispositivo']}\n"
        respuesta += f"   Estado: {t['estado']} | Creado: {t['fecha_creacion'][:10]}\n"

    respuesta += "\n¿Cuál de estos tickets necesitas consultar?"
    return respuesta
