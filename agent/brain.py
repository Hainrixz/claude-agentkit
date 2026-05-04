# agent/brain.py — Cerebro del agente: conexión con Claude API
# Generado por AgentKit

"""
Lógica de IA del agente. Lee el system prompt de:
1. Supabase (ai_prompts) si está configurado
2. config/prompts.yaml como fallback local

Genera respuestas usando la API de Anthropic Claude.
"""

import os
import yaml
import logging
from anthropic import AsyncAnthropic
from datetime import datetime, timedelta
from dotenv import load_dotenv

from agent.supabase_client import obtener_config_cliente, is_supabase_enabled

load_dotenv()
logger = logging.getLogger("agentkit")

# Cliente de Anthropic
# Soporta ANTHROPIC_API_KEY o CLAVE_API_ANTRÓPICA (Railway en español)
client = AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAVE_API_ANTRÓPICA") or os.getenv("CLAVE_API_ANTROPICA")
)


def cargar_config_prompts_local() -> dict:
    """Lee configuración desde config/prompts.yaml (fallback local)."""
    try:
        with open("config/prompts.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("config/prompts.yaml no encontrado")
        return {}


async def obtener_system_prompt(client_id: str = None) -> str:
    """
    Obtiene el system prompt del bot desde:
    1. Supabase (ai_prompts) si client_id se proporciona
    2. config/prompts.yaml como fallback

    Args:
        client_id: UUID del cliente en Supabase (opcional)

    Returns:
        System prompt personalizado para el bot
    """
    # Si Supabase está disponible y tenemos client_id, intentar desde ahí
    if is_supabase_enabled() and client_id:
        try:
            config = await obtener_config_cliente(client_id)
            if config and config.get("system_prompt"):
                logger.info(f"System prompt cargado desde Supabase para cliente {client_id}")
                return config["system_prompt"]
        except Exception as e:
            logger.warning(f"Error obteniendo config de Supabase: {e}, usando fallback local")

    # Fallback: leer desde archivo local
    config = cargar_config_prompts_local()
    return config.get("system_prompt", "Eres un asistente útil. Responde en español.")


def obtener_mensaje_error() -> str:
    """Retorna el mensaje de error configurado."""
    config = cargar_config_prompts_local()
    return config.get("error_message", "Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos minutos.")


def obtener_mensaje_fallback() -> str:
    """Retorna el mensaje de fallback configurado."""
    config = cargar_config_prompts_local()
    return config.get("fallback_message", "Disculpa, no entendí tu mensaje. ¿Podrías reformularlo?")


async def generar_respuesta(mensaje: str, historial: list[dict], client_id: str = None) -> str:
    """
    Genera una respuesta usando Claude API.

    Args:
        mensaje: El mensaje nuevo del usuario
        historial: Lista de mensajes anteriores [{"role": "user/assistant", "content": "..."}]
        client_id: UUID del cliente en Supabase (opcional)

    Returns:
        La respuesta generada por Claude
    """
    # Si el mensaje es muy corto o vacío, usar fallback
    if not mensaje or len(mensaje.strip()) < 2:
        return obtener_mensaje_fallback()

    system_prompt = await obtener_system_prompt(client_id)

    # Agregar fecha de hoy para que Claude pueda convertir "mañana", "próximo lunes", etc.
    hoy = datetime.utcnow()
    mañana = (hoy + timedelta(days=1)).strftime("%Y-%m-%d")
    system_prompt += f"\n\n## Información de contexto\nFecha de hoy: {hoy.strftime('%Y-%m-%d')} ({hoy.strftime('%A')})\nMañana será: {mañana}\nCuando el cliente mencione fechas relativas (mañana, pasado mañana, próximo lunes, etc.), CONVIERTE siempre a formato ISO (YYYY-MM-DD)."

    # Construir mensajes para la API
    mensajes = []
    for msg in historial:
        mensajes.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Agregar el mensaje actual
    mensajes.append({
        "role": "user",
        "content": mensaje
    })

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=mensajes
        )

        respuesta = response.content[0].text
        logger.info(f"Respuesta generada ({response.usage.input_tokens} in / {response.usage.output_tokens} out)")
        return respuesta

    except Exception as e:
        logger.error(f"Error Claude API: {e}")
        return obtener_mensaje_error()
