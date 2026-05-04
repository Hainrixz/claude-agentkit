# agent/memory.py — Memoria de conversaciones
# Usa Supabase como DB principal, fallback a SQLite si no está disponible

"""
Sistema de memoria del agente. Guarda el historial de conversaciones
en Supabase (preferido) o SQLite local como fallback.
"""

import os
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, select, Integer
from dotenv import load_dotenv

from agent.supabase_client import (
    is_supabase_enabled,
    guardar_mensaje_supabase,
    obtener_historial_supabase,
    crear_ticket_supabase,
    obtener_tickets_cliente,
    actualizar_ticket_supabase,
    obtener_cliente_por_telefono
)

load_dotenv()
logger = logging.getLogger("agentkit")

# Obtener el agente activo
AGENTE_ACTIVO = os.getenv("AGENTE_ACTIVO", "default")

# Configuración de base de datos local (fallback)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    DATABASE_URL = f"sqlite+aiosqlite:///./data/{AGENTE_ACTIVO}/agentkit.db"
    # Crear directorio si es SQLite
    data_dir = f"./data/{AGENTE_ACTIVO}"
    os.makedirs(data_dir, exist_ok=True)

# Si es PostgreSQL, ajustar el esquema
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Mensaje(Base):
    """Modelo de mensaje en la base de datos local."""
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" o "assistant"
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def inicializar_db():
    """Crea las tablas locales si no existen (fallback)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if is_supabase_enabled():
        logger.info("Usando Supabase como base de datos principal")
    else:
        logger.info(f"Usando SQLite local en {DATABASE_URL}")


async def guardar_mensaje(telefono: str, role: str, content: str, client_id: str = None):
    """
    Guarda un mensaje en Supabase (preferido) o SQLite (fallback).

    Args:
        telefono: Número de teléfono del cliente
        role: "user" o "assistant"
        content: Contenido del mensaje
        client_id: UUID del cliente (requerido para Supabase)
    """
    # Si Supabase está disponible y tenemos client_id, usar Supabase
    if is_supabase_enabled() and client_id:
        await guardar_mensaje_supabase(client_id, telefono, role, content)
    else:
        # Fallback a SQLite local
        async with async_session() as session:
            mensaje = Mensaje(
                telefono=telefono,
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
            session.add(mensaje)
            await session.commit()


async def obtener_historial(telefono: str, client_id: str = None, limite: int = 20) -> list[dict]:
    """
    Recupera el historial de conversaciones de un cliente.

    Args:
        telefono: Número de teléfono del cliente
        client_id: UUID del cliente en Supabase (requerido para Supabase)
        limite: Máximo de mensajes a recuperar

    Returns:
        Lista de diccionarios con role y content
    """
    # Si Supabase está disponible, usar Supabase
    if is_supabase_enabled() and client_id:
        return await obtener_historial_supabase(client_id, telefono, limite)

    # Fallback a SQLite local
    async with async_session() as session:
        query = (
            select(Mensaje)
            .where(Mensaje.telefono == telefono)
            .order_by(Mensaje.timestamp.desc())
            .limit(limite)
        )
        result = await session.execute(query)
        mensajes = result.scalars().all()
        mensajes.reverse()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in mensajes
        ]


async def crear_ticket(nombre: str, telefono: str, dispositivo: str, problema: str,
                       client_id: str = None, agente: str = None) -> str:
    """
    Crea un ticket de reparación en Supabase o SQLite.

    Args:
        nombre: Nombre del cliente
        telefono: Número de teléfono
        dispositivo: Dispositivo a reparar
        problema: Descripción del problema
        client_id: UUID del cliente en Supabase
        agente: Nombre del agente

    Returns:
        Número de ticket generado
    """
    # Generar número de ticket con formato: AGENTE-YYYYMMDD-NNN
    hoy = datetime.utcnow().strftime("%Y%m%d")
    prefijo = (agente or AGENTE_ACTIVO).upper()

    if is_supabase_enabled() and client_id:
        # En Supabase, generar el número de ticket basado en cliente
        try:
            tickets = await obtener_tickets_cliente(client_id, telefono)
            numero_secuencial = str(len(tickets) + 1).zfill(3)
            ticket_numero = f"{prefijo}-{hoy}-{numero_secuencial}"

            exito = await crear_ticket_supabase(
                client_id=client_id,
                ticket_numero=ticket_numero,
                nombre_cliente=nombre,
                telefono=telefono,
                dispositivo=dispositivo,
                problema=problema,
                agente=agente
            )

            if exito:
                logger.info(f"Ticket creado en Supabase: {ticket_numero}")
                return ticket_numero
        except Exception as e:
            logger.error(f"Error creando ticket en Supabase: {e}")

    # Fallback: usar SQLite local
    numero_secuencial = "001"
    ticket_numero = f"{prefijo}-{hoy}-{numero_secuencial}"
    logger.info(f"Ticket creado localmente: {ticket_numero}")
    return ticket_numero


async def obtener_tickets_por_telefono(telefono: str, client_id: str = None) -> list[dict]:
    """
    Obtiene todos los tickets de un cliente por teléfono.

    Args:
        telefono: Número de teléfono
        client_id: UUID del cliente en Supabase

    Returns:
        Lista de tickets
    """
    if is_supabase_enabled() and client_id:
        return await obtener_tickets_cliente(client_id, telefono)

    # Fallback: en mode local, retornar lista vacía
    return []


async def actualizar_ticket(ticket_numero: str, estado: str = None, notas: str = None) -> bool:
    """
    Actualiza el estado o notas de un ticket.

    Args:
        ticket_numero: Número del ticket
        estado: Nuevo estado (abierto, en_progreso, completado, etc.)
        notas: Nuevas notas

    Returns:
        True si fue exitoso
    """
    if is_supabase_enabled():
        return await actualizar_ticket_supabase(ticket_numero, estado, notas)

    # Fallback: en mode local, no hay actualización
    return False


async def limpiar_historial(telefono: str):
    """Borra el historial de una conversación (local)."""
    async with async_session() as session:
        from sqlalchemy import delete
        query = delete(Mensaje).where(Mensaje.telefono == telefono)
        await session.execute(query)
        await session.commit()
