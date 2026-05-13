# agent/main.py — Servidor FastAPI + Webhook de WhatsApp
# Generado por AgentKit

"""
Servidor principal del agente de WhatsApp.
Funciona con cualquier proveedor (Meta, Twilio) gracias a la capa de providers.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial
from agent.providers import obtener_proveedor
from agent.security import (
    validar_configuracion,
    sanitizar_mensaje,
    ya_procesado,
    marcar_procesado,
    rate_limit_excedido,
)

load_dotenv()

# Configuración de logging según entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger("agentkit")

validar_configuracion()
proveedor = obtener_proveedor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar el servidor."""
    await inicializar_db()
    logger.info("Base de datos inicializada")
    logger.info(f"Servidor AgentKit corriendo en puerto {PORT}")
    logger.info(f"Proveedor de WhatsApp: {proveedor.__class__.__name__}")
    yield


app = FastAPI(
    title="AgentKit — WhatsApp AI Agent",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def health_check():
    """Endpoint de salud para Railway/monitoreo."""
    return {"status": "ok", "service": "agentkit"}


@app.get("/webhook")
async def webhook_verificacion(request: Request):
    """Verificación GET del webhook (requerido por Meta Cloud API, no-op para otros)."""
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Recibe mensajes de WhatsApp via el proveedor configurado.
    Procesa el mensaje, genera respuesta con Claude y la envía de vuelta.
    """
    try:
        # Parsear webhook — el proveedor normaliza el formato
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            # Ignorar mensajes propios o vacíos
            if msg.es_propio or not msg.texto:
                continue

            # Idempotencia: Meta reenvía el webhook si no respondemos a tiempo.
            # Sin este check el mismo mensaje genera 2 llamadas a Claude y 2 respuestas.
            if ya_procesado(msg.mensaje_id):
                logger.info(f"Mensaje duplicado ignorado: {msg.mensaje_id}")
                continue
            marcar_procesado(msg.mensaje_id)

            # Rate limiting por número — protege contra abuso y costos descontrolados
            if rate_limit_excedido(msg.telefono):
                logger.warning(f"Rate limit excedido: {msg.telefono}")
                await proveedor.enviar_mensaje(
                    msg.telefono,
                    "Has enviado muchos mensajes muy rápido. "
                    "Por favor esperá un momento e intentá de nuevo."
                )
                continue

            # Normalización + truncado evita prompt injection con caracteres invisibles
            # y consumo excesivo de tokens con mensajes gigantes
            msg.texto = sanitizar_mensaje(msg.texto)
            if not msg.texto:
                continue

            logger.info(f"Mensaje de {msg.telefono}: {msg.texto}")

            # Obtener historial ANTES de guardar el mensaje actual
            # (brain.py agrega el mensaje actual, evitando duplicados)
            historial = await obtener_historial(msg.telefono)

            # Generar respuesta con Claude
            respuesta = await generar_respuesta(msg.texto, historial)

            # Guardar mensaje del usuario Y respuesta del agente en memoria
            await guardar_mensaje(msg.telefono, "user", msg.texto)
            await guardar_mensaje(msg.telefono, "assistant", respuesta)

            # Enviar respuesta por WhatsApp via el proveedor
            await proveedor.enviar_mensaje(msg.telefono, respuesta)

            logger.info(f"Respuesta a {msg.telefono}: {respuesta}")

        return {"status": "ok"}

    except HTTPException:
        # Errores de validación (firma inválida, etc.) — re-lanzar tal cual
        raise
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        detail = str(e) if ENVIRONMENT == "development" else "Error interno"
        raise HTTPException(status_code=500, detail=detail)
