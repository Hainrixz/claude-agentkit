# agent/brain.py — Cerebro del agente: conexión con cualquier LLM via LiteLLM
import os
import yaml
import logging
import litellm
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agentkit")

litellm.suppress_debug_info = True

LLM_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")
LLM_API_KEY = os.getenv("LLM_API_KEY")


def cargar_config_prompts() -> dict:
    try:
        with open("config/prompts.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("config/prompts.yaml no encontrado")
        return {}


def cargar_system_prompt() -> str:
    config = cargar_config_prompts()
    return config.get("system_prompt", "Eres un asistente útil. Responde en español.")


def obtener_mensaje_error() -> str:
    config = cargar_config_prompts()
    return config.get("error_message", "Lo siento, estoy teniendo problemas técnicos. Por favor intentá de nuevo en unos minutos.")


def obtener_mensaje_fallback() -> str:
    config = cargar_config_prompts()
    return config.get("fallback_message", "Disculpá, no entendí tu mensaje. ¿Podés contarme un poco más?")


async def generar_respuesta(mensaje: str, historial: list[dict]) -> str:
    """Genera una respuesta usando el LLM configurado en LLM_MODEL."""
    if not mensaje or len(mensaje.strip()) < 2:
        return obtener_mensaje_fallback()

    system_prompt = cargar_system_prompt()

    # LiteLLM usa el formato OpenAI: system va como primer mensaje
    mensajes = [{"role": "system", "content": system_prompt}]
    for msg in historial:
        mensajes.append({"role": msg["role"], "content": msg["content"]})
    mensajes.append({"role": "user", "content": mensaje})

    try:
        response = await litellm.acompletion(
            model=LLM_MODEL,
            messages=mensajes,
            max_tokens=1024,
            timeout=30,
            api_key=LLM_API_KEY,
            num_retries=2,
        )
        respuesta = response.choices[0].message.content
        logger.info(
            f"Respuesta generada — modelo: {LLM_MODEL} "
            f"({response.usage.prompt_tokens} in / {response.usage.completion_tokens} out)"
        )
        return respuesta

    except Exception as e:
        logger.error(f"Error LLM ({LLM_MODEL}): {e}")
        return obtener_mensaje_error()
