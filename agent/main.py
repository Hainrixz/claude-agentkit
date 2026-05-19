# agent/main.py — Servidor FastAPI + Webhook de WhatsApp — HELIX · AI
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

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger("agentkit")

validar_configuracion()
proveedor = obtener_proveedor()
PORT = int(os.getenv("PORT", 8000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await inicializar_db()
    logger.info("Base de datos inicializada")
    logger.info(f"Servidor AgentKit — HELIX · AI corriendo en puerto {PORT}")
    logger.info(f"Proveedor de WhatsApp: {proveedor.__class__.__name__}")
    yield


app = FastAPI(
    title="Sofía — Agente WhatsApp de HELIX · AI",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "helix-ai-agentkit", "agente": "Sofía"}


@app.get("/webhook")
async def webhook_verificacion(request: Request):
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            if msg.es_propio or not msg.texto:
                continue

            if ya_procesado(msg.mensaje_id):
                logger.info(f"Mensaje duplicado ignorado: {msg.mensaje_id}")
                continue
            marcar_procesado(msg.mensaje_id)

            if rate_limit_excedido(msg.telefono):
                logger.warning(f"Rate limit excedido: {msg.telefono}")
                await proveedor.enviar_mensaje(
                    msg.telefono,
                    "Enviaste muchos mensajes muy rápido. Por favor esperá un momento e intentá de nuevo 🙏"
                )
                continue

            msg.texto = sanitizar_mensaje(msg.texto)
            if not msg.texto:
                continue

            logger.info(f"Mensaje de {msg.telefono}: {msg.texto}")

            historial = await obtener_historial(msg.telefono)
            respuesta = await generar_respuesta(msg.texto, historial)

            await guardar_mensaje(msg.telefono, "user", msg.texto)
            await guardar_mensaje(msg.telefono, "assistant", respuesta)

            await proveedor.enviar_mensaje(msg.telefono, respuesta)
            logger.info(f"Respuesta a {msg.telefono}: {respuesta}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        detail = str(e) if ENVIRONMENT == "development" else "Error interno"
        raise HTTPException(status_code=500, detail=detail)
