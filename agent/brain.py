# agent/brain.py — Cerebro del agente: conexión con cualquier LLM via LiteLLM
import os
import yaml
import logging
import litellm
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agentkit")

litellm.suppress_debug_info = True

PRIMARY_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")

# Fallback automático: si el primario falla, LiteLLM prueba cada uno en orden
FALLBACK_MODELS = [
    "groq/llama-3.3-70b-versatile",
    "gemini/gemini-1.5-pro",
    "openai/gpt-4o",
    "perplexity/sonar",
]

# Compatibilidad: si LLM_API_KEY está seteada (variable legacy) y no hay
# ANTHROPIC_API_KEY, la mapeamos para no romper deploys existentes
_legacy_key = os.getenv("LLM_API_KEY")
if _legacy_key and not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = _legacy_key


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
    """Genera una respuesta usando el LLM configurado, con fallback automático."""
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
            model=PRIMARY_MODEL,
            messages=mensajes,
            max_tokens=1024,
            timeout=30,
            num_retries=2,
            fallbacks=FALLBACK_MODELS,
        )
        modelo_usado = response.model or PRIMARY_MODEL
        respuesta = response.choices[0].message.content
        logger.info(
            f"Respuesta generada — modelo: {modelo_usado} "
            f"({response.usage.prompt_tokens} in / {response.usage.completion_tokens} out)"
        )
        return respuesta

    except Exception as e:
        logger.error(f"Todos los proveedores LLM fallaron: {e}")
        return obtener_mensaje_error()
