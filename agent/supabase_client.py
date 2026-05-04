# agent/supabase_client.py — Cliente centralizado de Supabase
# Maneja todas las operaciones con la base de datos centralizada

import os
import logging
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agentkit")

# Inicializar cliente de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("SUPABASE_URL o SUPABASE_KEY no configurados — usando SQLite local")
    supabase_client: Client = None
else:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Cliente de Supabase inicializado correctamente")
    except Exception as e:
        logger.error(f"Error inicializando Supabase: {e}")
        supabase_client = None


def is_supabase_enabled() -> bool:
    """Retorna True si Supabase está disponible."""
    return supabase_client is not None


async def registrar_lead_si_nuevo(client_id: str, telefono: str, primer_mensaje: str = None):
    """
    Registra un contacto nuevo en bot_leads si su teléfono no existe aún.
    Se llama en cada mensaje entrante — solo inserta si es la primera vez.

    Args:
        client_id: UUID del cliente (negocio)
        telefono: Número del contacto (usuario final)
        primer_mensaje: Primer mensaje enviado (opcional)
    """
    if not is_supabase_enabled():
        return

    try:
        # Verificar si ya existe
        existente = supabase_client.table("bot_leads").select("id").eq(
            "client_id", client_id
        ).eq("phone", telefono).limit(1).execute()

        if existente.data and len(existente.data) > 0:
            return  # Ya registrado — no duplicar

        # Registrar como nuevo lead
        supabase_client.table("bot_leads").insert({
            "client_id": client_id,
            "phone": telefono,
            "message": primer_mensaje,
        }).execute()
        logger.info(f"Nuevo lead registrado: {telefono} para cliente {client_id}")

    except Exception as e:
        logger.error(f"Error registrando lead {telefono}: {e}")


async def obtener_config_cliente(client_id: str) -> dict:
    """
    Lee la configuración del bot desde la tabla ai_prompts en Supabase.

    Args:
        client_id: UUID del cliente en Supabase

    Returns:
        Dict con system_prompt, tone, business_type, objective
    """
    if not is_supabase_enabled():
        return {}

    try:
        result = supabase_client.table("ai_prompts").select("*").eq("client_id", client_id).limit(1).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return {}
    except Exception as e:
        logger.error(f"Error obteniendo config del cliente {client_id}: {e}")
        return {}


async def obtener_cliente_por_telefono(telefono: str) -> dict:
    """
    Busca el cliente por su número de teléfono en la tabla clients.

    Args:
        telefono: Número de teléfono del cliente

    Returns:
        Dict con datos del cliente (id, name, business_type, etc.) o empty dict
    """
    if not is_supabase_enabled():
        return {}

    try:
        result = supabase_client.table("clients").select("*").eq("whatsapp", telefono).limit(1).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return {}
    except Exception as e:
        logger.error(f"Error buscando cliente con teléfono {telefono}: {e}")
        return {}


async def guardar_mensaje_supabase(client_id: str, telefono: str, role: str, content: str):
    """
    Guarda un mensaje en la tabla conversations.

    Args:
        client_id: UUID del cliente
        telefono: Número de teléfono
        role: "user" o "assistant"
        content: Contenido del mensaje
    """
    if not is_supabase_enabled():
        return

    try:
        supabase_client.table("conversations").insert({
            "client_id": client_id,
            "telefono": telefono,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        logger.error(f"Error guardando mensaje en Supabase: {e}")


async def obtener_historial_supabase(client_id: str, telefono: str, limite: int = 20) -> list[dict]:
    """
    Obtiene el historial de conversaciones de un cliente.

    Args:
        client_id: UUID del cliente
        telefono: Número de teléfono
        limite: Máximo de mensajes a recuperar

    Returns:
        Lista de mensajes ordenados por fecha (más antiguos primero)
    """
    if not is_supabase_enabled():
        return []

    try:
        result = supabase_client.table("conversations").select("*").eq(
            "client_id", client_id
        ).eq(
            "telefono", telefono
        ).order("created_at", desc=False).limit(limite).execute()

        if result.data:
            return [
                {"role": msg["role"], "content": msg["content"]}
                for msg in result.data
            ]
        return []
    except Exception as e:
        logger.error(f"Error obteniendo historial de {telefono}: {e}")
        return []


async def crear_ticket_supabase(client_id: str, ticket_numero: str, nombre_cliente: str,
                                telefono: str, dispositivo: str, problema: str, agente: str = None) -> bool:
    """
    Crea un ticket en la tabla tickets.

    Args:
        client_id: UUID del cliente
        ticket_numero: Número único del ticket (ej: MUN-20260328-001)
        nombre_cliente: Nombre del cliente
        telefono: Número de teléfono
        dispositivo: Dispositivo a reparar
        problema: Descripción del problema
        agente: Nombre del agente (opcional)

    Returns:
        True si fue exitoso, False si falló
    """
    if not is_supabase_enabled():
        return False

    try:
        supabase_client.table("tickets").insert({
            "client_id": client_id,
            "ticket_numero": ticket_numero,
            "nombre_cliente": nombre_cliente,
            "telefono": telefono,
            "dispositivo": dispositivo,
            "problema": problema,
            "estado": "abierto",
            "agente": agente
        }).execute()
        logger.info(f"Ticket creado en Supabase: {ticket_numero}")
        return True
    except Exception as e:
        logger.error(f"Error creando ticket en Supabase: {e}")
        return False


async def obtener_tickets_cliente(client_id: str, telefono: str) -> list[dict]:
    """
    Obtiene todos los tickets de un cliente por teléfono.

    Args:
        client_id: UUID del cliente
        telefono: Número de teléfono

    Returns:
        Lista de tickets
    """
    if not is_supabase_enabled():
        return []

    try:
        result = supabase_client.table("tickets").select("*").eq(
            "client_id", client_id
        ).eq(
            "telefono", telefono
        ).order("fecha_creacion", desc=True).execute()

        if result.data:
            return result.data
        return []
    except Exception as e:
        logger.error(f"Error obteniendo tickets de {telefono}: {e}")
        return []


async def actualizar_ticket_supabase(ticket_numero: str, estado: str = None, notas: str = None) -> bool:
    """
    Actualiza el estado o notas de un ticket.

    Args:
        ticket_numero: Número del ticket
        estado: Nuevo estado (opcional)
        notas: Nuevas notas (opcional)

    Returns:
        True si fue exitoso
    """
    if not is_supabase_enabled():
        return False

    try:
        update_data = {}
        if estado:
            update_data["estado"] = estado
        if notas:
            update_data["notas"] = notas

        if update_data:
            supabase_client.table("tickets").update(update_data).eq(
                "ticket_numero", ticket_numero
            ).execute()

        return True
    except Exception as e:
        logger.error(f"Error actualizando ticket {ticket_numero}: {e}")
        return False


# ════════════════════════════════════════════════════════════
# FUNCIONES PARA PLANES, PAGOS Y EXTRAS
# ════════════════════════════════════════════════════════════

async def obtener_plan_cliente(client_id: str) -> dict:
    """
    Obtiene el plan y detalles de suscripción de un cliente.

    Args:
        client_id: UUID del cliente

    Returns:
        Dict con plan, precio, estado_pago, fecha_expiracion_soporte
    """
    if not is_supabase_enabled():
        return {}

    try:
        result = supabase_client.table("clients").select(
            "plan, precio_base, precio_total, estado_pago, fecha_expiracion_soporte, creditos_disponibles"
        ).eq("id", client_id).limit(1).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return {}
    except Exception as e:
        logger.error(f"Error obteniendo plan del cliente {client_id}: {e}")
        return {}


async def verificar_soporte_vigente(client_id: str) -> bool:
    """
    Verifica si el soporte del cliente aún está vigente.

    Args:
        client_id: UUID del cliente

    Returns:
        True si soporte vigente, False si expiró
    """
    from datetime import datetime

    plan = await obtener_plan_cliente(client_id)
    if not plan or "fecha_expiracion_soporte" not in plan:
        return False

    fecha_expiracion = plan.get("fecha_expiracion_soporte")
    if not fecha_expiracion:
        return False

    try:
        fecha_exp = datetime.fromisoformat(fecha_expiracion)
        return datetime.utcnow() <= fecha_exp
    except:
        return False


async def registrar_pago(client_id: str, concepto: str, monto: float,
                        metodo_pago: str = "transferencia",
                        referencia: str = None) -> bool:
    """
    Registra un pago en el historial.

    Args:
        client_id: UUID del cliente
        concepto: Descripción del pago (ej: "Pago 50% Starter")
        monto: Cantidad pagada
        metodo_pago: Cómo se pagó
        referencia: Número de transacción/comprobante

    Returns:
        True si fue exitoso
    """
    if not is_supabase_enabled():
        return False

    try:
        supabase_client.table("pagos").insert({
            "client_id": client_id,
            "concepto": concepto,
            "monto": monto,
            "metodo_pago": metodo_pago,
            "referencia_transaccion": referencia,
            "estado": "pagado",
            "fecha_pagado": datetime.now().date().isoformat()
        }).execute()

        logger.info(f"Pago registrado para cliente {client_id}: {concepto} ${monto}")
        return True
    except Exception as e:
        logger.error(f"Error registrando pago: {e}")
        return False


async def agregar_extra(client_id: str, nombre: str, costo_mensual: float = None,
                       costo_unico: float = None) -> bool:
    """
    Agrega un extra/complemento al plan del cliente.

    Args:
        client_id: UUID del cliente
        nombre: Nombre del extra ('analytics_avanzados', 'soporte_prioritario', etc)
        costo_mensual: Costo mensual si aplica
        costo_unico: Costo único si aplica

    Returns:
        True si fue exitoso
    """
    if not is_supabase_enabled():
        return False

    try:
        supabase_client.table("extras_contratados").insert({
            "client_id": client_id,
            "nombre": nombre,
            "costo_mensual": costo_mensual,
            "costo_unico": costo_unico,
            "estado": "activo",
            "fecha_inicio": datetime.now().date().isoformat()
        }).execute()

        logger.info(f"Extra '{nombre}' agregado a cliente {client_id}")
        return True
    except Exception as e:
        logger.error(f"Error agregando extra: {e}")
        return False


async def obtener_pagos_pendientes(client_id: str) -> list[dict]:
    """
    Obtiene los pagos pendientes de un cliente.

    Args:
        client_id: UUID del cliente

    Returns:
        Lista de pagos pendientes
    """
    if not is_supabase_enabled():
        return []

    try:
        result = supabase_client.table("pagos").select("*").eq(
            "client_id", client_id
        ).eq(
            "estado", "pendiente"
        ).order("fecha_vencimiento", desc=False).execute()

        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error obteniendo pagos pendientes: {e}")
        return []


async def obtener_extras_activos(client_id: str) -> list[dict]:
    """
    Obtiene los extras/complementos activos de un cliente.

    Args:
        client_id: UUID del cliente

    Returns:
        Lista de extras activos
    """
    if not is_supabase_enabled():
        return []

    try:
        result = supabase_client.table("extras_contratados").select("*").eq(
            "client_id", client_id
        ).eq(
            "estado", "activo"
        ).execute()

        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error obteniendo extras activos: {e}")
        return []


async def actualizar_uso_mensajes(client_id: str, cantidad: int = 1) -> bool:
    """
    Actualiza el contador de mensajes usados en el mes.

    Args:
        client_id: UUID del cliente
        cantidad: Cantidad de mensajes a sumar

    Returns:
        True si fue exitoso
    """
    if not is_supabase_enabled():
        return False

    try:
        # Obtener uso actual
        client = await obtener_cliente_por_telefono_by_id(client_id)
        if not client:
            return False

        uso_actual = client.get("mensajes_usados_este_mes", 0) or 0
        nuevo_uso = uso_actual + cantidad

        supabase_client.table("clients").update({
            "mensajes_usados_este_mes": nuevo_uso
        }).eq("id", client_id).execute()

        logger.info(f"Uso actualizado para cliente {client_id}: {nuevo_uso} mensajes")
        return True
    except Exception as e:
        logger.error(f"Error actualizando uso: {e}")
        return False


async def obtener_cliente_por_id(client_id: str) -> dict:
    """
    Obtiene información completa de un cliente por su ID.

    Args:
        client_id: UUID del cliente

    Returns:
        Dict con información del cliente
    """
    if not is_supabase_enabled():
        return {}

    try:
        result = supabase_client.table("clients").select("*").eq(
            "id", client_id
        ).limit(1).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return {}
    except Exception as e:
        logger.error(f"Error obteniendo cliente {client_id}: {e}")
        return {}


async def obtener_cliente_por_telefono_by_id(client_id: str) -> dict:
    """Alias para obtener_cliente_por_id"""
    return await obtener_cliente_por_id(client_id)
