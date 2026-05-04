# agent/main.py — Servidor FastAPI + Webhook de WhatsApp
# Generado por AgentKit

"""
Servidor principal del agente de WhatsApp.
Funciona con cualquier proveedor (Whapi, Meta, Twilio) gracias a la capa de providers.
"""

import os
import re
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial
from agent.providers import obtener_proveedor
from agent.tools import crear_evento_calendario, detectar_tipo_pregunta, crear_ticket_desde_cita, buscar_estado_reparacion
from agent.supabase_client import is_supabase_enabled, registrar_lead_si_nuevo
from agent.admin import admin_router

load_dotenv()

# Configuración de logging según entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger("agentkit")

# Proveedor de WhatsApp (se configura en .env con WHATSAPP_PROVIDER)
proveedor = obtener_proveedor()
PORT = int(os.getenv("PORT", 8000))

# ID del cliente en Supabase — soporta CLIENT_ID o ID_DE_CLIENTE (Railway en español)
CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("ID_DE_CLIENTE")


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

# Incluir rutas del admin
app.include_router(admin_router)


@app.get("/")
async def health_check():
    """Endpoint de salud para Railway/monitoreo."""
    return {"status": "ok", "service": "agentkit"}


async def extraer_datos_confirmacion(respuesta: str) -> dict:
    """
    Extrae datos de una confirmación de cita de la respuesta del bot.
    Busca patrones como "Nombre: Oscar Elias", "Dispositivo: iPhone 14", etc.
    Ignora símbolos de markdown (*, _, etc.)
    """
    datos = {}

    # Limpiar markdown: remover * y _ alrededor de palabras
    respuesta_clean = re.sub(r'\*([^*]*)\*', r'\1', respuesta)
    respuesta_clean = re.sub(r'_([^_]*)_', r'\1', respuesta_clean)

    # Buscar nombre - después de "Nombre:" capturar hasta fin de línea, ignorando emojis
    nombre_match = re.search(r'Nombre[:\s]*\*?([^:\n*_]+)', respuesta_clean, re.IGNORECASE)
    if nombre_match:
        datos['nombre'] = nombre_match.group(1).strip()

    # Buscar teléfono/contacto - capturar números
    tel_match = re.search(r'(?:Teléfono|Telefono|Contacto)[:\s]*\*?([^\n*_]+)', respuesta_clean, re.IGNORECASE)
    if tel_match:
        tel_raw = tel_match.group(1).strip()
        # Extraer solo números del teléfono
        tel_nums = re.sub(r'[^\d]', '', tel_raw)
        if tel_nums:
            datos['telefono'] = tel_nums

    # Buscar dispositivo
    disp_match = re.search(r'Dispositivo[:\s]*\*?([^\n*_]+)', respuesta_clean, re.IGNORECASE)
    if disp_match:
        datos['dispositivo'] = disp_match.group(1).strip()

    # Buscar servicio (a veces en lugar de "problema")
    serv_match = re.search(r'(?:Servicio|Problema)[:\s]*\*?([^\n*_]+)', respuesta_clean, re.IGNORECASE)
    if serv_match:
        datos['problema'] = serv_match.group(1).strip()

    # Buscar fecha - buscar "Martes 31 de marzo de 2026" y convertir a YYYY-MM-DD
    fecha_match = re.search(r'(?:Martes|Lunes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', respuesta_clean, re.IGNORECASE)
    if fecha_match:
        dia, mes_str, ano = fecha_match.groups()
        meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
                 'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
        mes = meses.get(mes_str.lower(), '01')
        datos['fecha'] = f"{ano}-{mes}-{dia.zfill(2)}"
    else:
        # Intentar formato ISO directo
        fecha_iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', respuesta_clean)
        if fecha_iso_match:
            datos['fecha'] = fecha_iso_match.group(1)

    # Buscar hora (HH:MM)
    hora_match = re.search(r'(?:Hora|Horario)[:\s]*\*?(\d{2}:\d{2})', respuesta_clean, re.IGNORECASE)
    if hora_match:
        datos['hora'] = hora_match.group(1).strip()

    logger.info(f"Datos extraídos del resumen: {datos}")
    return datos


async def procesar_cita_si_existe(respuesta: str, telefono: str, client_id: str = None) -> str:
    """
    Detecta si la respuesta contiene un bloque [CITA]...[/CITA].
    Si existe, crea:
    1. Evento en Google Calendar
    2. Ticket de soporte/reparación en la base de datos
    Elimina el tag del texto visible.

    Soporta dos formatos:
    1. Pipe format: [CITA]nombre|teléfono|dispositivo|YYYY-MM-DD|HH:MM[/CITA]
    2. JSON format: [CITA: nombre="...", telefono="...", dispositivo="...", fecha="...", hora="..."]
    """
    # Intentar formato pipe primero
    patron_pipe = r'\[CITA\](.*?)\[/CITA\]'
    match = re.search(patron_pipe, respuesta, re.DOTALL)

    nombre, telefono_cita, dispositivo, fecha, hora = None, None, None, None, None

    if match:
        # Formato pipe
        datos_raw = match.group(1).strip()
        partes = datos_raw.split("|")
        if len(partes) == 5:
            nombre, telefono_cita, dispositivo, fecha, hora = [p.strip() for p in partes]
    else:
        # Intentar formato JSON (muy flexible)
        patron_json = r'\[CITA:\s*(.*?)\]'
        match = re.search(patron_json, respuesta, re.DOTALL)
        if match:
            datos_raw = match.group(1)

            # Buscar nombre (aceptar "nombre" o "cliente")
            nombre_match = re.search(r'(?:nombre|cliente)\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)

            # Buscar teléfono (aceptar "telefono", "contacto" o "teléfono")
            tel_match = re.search(r'(?:telefono|contacto|teléfono)\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)

            # Buscar dispositivo
            disp_match = re.search(r'dispositivo\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)

            # Buscar problema
            prob_match = re.search(r'problema\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)

            # Buscar fecha
            fecha_match = re.search(r'fecha\s*=\s*["\']?(\d{4}-\d{2}-\d{2})["\']?', datos_raw)

            # Buscar hora
            hora_match = re.search(r'hora\s*=\s*["\']?(\d{2}:\d{2})["\']?', datos_raw)

            if all([nombre_match, tel_match, disp_match, prob_match, fecha_match, hora_match]):
                nombre = nombre_match.group(1).strip()
                telefono_cita = tel_match.group(1).strip()
                dispositivo = f"{disp_match.group(1).strip()} {prob_match.group(1).strip()}"
                fecha = fecha_match.group(1).strip()
                hora = hora_match.group(1).strip()

    # Si NO encontramos tag pero la respuesta parece una confirmación de cita,
    # intentar extraer datos del resumen (fallback)
    if not (nombre and telefono_cita and dispositivo and fecha and hora):
        confirmacion_keywords = ["confirmado", "confirmada", "agendé", "agendada", "listo", "perfecto", "resumen", "agendada exitosamente", "cita ha sido agendada"]
        if any(kw in respuesta.lower() for kw in confirmacion_keywords) or "Nombre:" in respuesta:
            datos_extraidos = await extraer_datos_confirmacion(respuesta)
            logger.info(f"Intentando fallback extraction: {datos_extraidos}")
            # Aceptar si tenemos al menos nombre, teléfono, dispositivo, fecha, hora
            if all(k in datos_extraidos for k in ['nombre', 'telefono', 'dispositivo', 'problema', 'fecha', 'hora']):
                nombre = datos_extraidos['nombre']
                telefono_cita = datos_extraidos['telefono']
                dispositivo = f"{datos_extraidos['dispositivo']} {datos_extraidos['problema']}"
                fecha = datos_extraidos['fecha']
                hora = datos_extraidos['hora']
                logger.info(f"✓ Datos de cita extraídos del resumen (fallback): {nombre} - {fecha} {hora}")

    # Si encontramos datos válidos (con o sin tag), procesar
    if nombre and telefono_cita and dispositivo and fecha and hora:
        # Limpiar símbolos del teléfono si los tiene
        telefono_cita = re.sub(r'[^\d]', '', telefono_cita)

        # Crear evento en Google Calendar
        exito_cal = await crear_evento_calendario(nombre, telefono_cita, dispositivo, fecha, hora)
        if exito_cal:
            logger.info(f"Cita agendada en Google Calendar: {nombre}")

        # Crear ticket de soporte
        try:
            ticket_numero = await crear_ticket_desde_cita(nombre, telefono_cita, dispositivo, "Reparación agendada", client_id=client_id)
            logger.info(f"Ticket creado: {ticket_numero}")
        except Exception as e:
            logger.error(f"Error creando ticket: {e}")

    # Eliminar TODOS los posibles tags del texto visible al cliente
    respuesta_limpia = re.sub(patron_pipe, "", respuesta, flags=re.DOTALL)
    respuesta_limpia = re.sub(r'\[CITA:\s*(.*?)\]', "", respuesta_limpia, flags=re.DOTALL)
    return respuesta_limpia.strip()


async def enriquecer_respuesta_soporte(respuesta: str, telefono: str, mensaje: str) -> str:
    """
    Si la pregunta es sobre soporte/estado de reparación,
    agrega el contexto de los tickets del cliente a la respuesta.
    """
    tipo_pregunta, _ = detectar_tipo_pregunta(mensaje)

    if tipo_pregunta != "soporte":
        return respuesta

    try:
        estado_tickets = await buscar_estado_reparacion(telefono, mensaje)
        # Agregar información de tickets al final de la respuesta
        respuesta += f"\n\n{estado_tickets}"
        logger.info(f"Respuesta enriquecida con información de tickets para {telefono}")
    except Exception as e:
        logger.error(f"Error enriqueciendo respuesta con tickets: {e}")

    return respuesta


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

            logger.info(f"Mensaje de {msg.telefono}: {msg.texto}")

            # Obtener client_id: primero desde .env, si no hay, advertir
            client_id = CLIENT_ID
            if is_supabase_enabled():
                if client_id:
                    logger.info(f"Usando CLIENT_ID configurado: {client_id}")
                    # Registrar contacto en bot_leads si es nuevo
                    await registrar_lead_si_nuevo(client_id, msg.telefono, msg.texto)
                else:
                    logger.warning("CLIENT_ID no configurado en .env — conversaciones no se guardarán en Supabase")

            # Obtener historial ANTES de guardar el mensaje actual
            historial = await obtener_historial(msg.telefono, client_id=client_id)

            # Generar respuesta con Claude
            respuesta = await generar_respuesta(msg.texto, historial, client_id=client_id)

            # Procesar cita si existe en la respuesta (detectar tag [CITA] y crear en Google Calendar + Ticket)
            respuesta = await procesar_cita_si_existe(respuesta, msg.telefono, client_id=client_id)

            # Guardar mensaje del usuario Y respuesta del agente en memoria
            await guardar_mensaje(msg.telefono, "user", msg.texto, client_id=client_id)
            await guardar_mensaje(msg.telefono, "assistant", respuesta, client_id=client_id)

            # Enviar respuesta por WhatsApp via el proveedor
            await proveedor.enviar_mensaje(msg.telefono, respuesta)

            logger.info(f"Respuesta a {msg.telefono}: {respuesta}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════
# ENDPOINTS DE PAGO
# ════════════════════════════════════════════════════════════

@app.post("/register-payment")
async def register_payment(request: Request):
    """
    Registra un pago manual en la tabla pagos de Supabase.

    Body:
    {
        "client_id": "uuid",
        "concepto": "Pago 50% Starter",
        "monto": 32.50,
        "metodo_pago": "manual",
        "estado": "pendiente",
        "referencia": "TRX-12345" (opcional)
    }
    """
    if not is_supabase_enabled():
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        from agent.supabase_client import registrar_pago

        body = await request.json()
        client_id = body.get("client_id")
        concepto = body.get("concepto")
        monto = body.get("monto")
        metodo = body.get("metodo_pago", "manual")
        referencia = body.get("referencia")

        if not all([client_id, concepto, monto]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        success = await registrar_pago(
            client_id=client_id,
            concepto=concepto,
            monto=float(monto),
            metodo_pago=metodo,
            referencia=referencia
        )

        if success:
            return {"status": "ok", "message": "Payment registered"}
        else:
            raise HTTPException(status_code=500, detail="Error registering payment")

    except Exception as e:
        logger.error(f"Error registering payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/checkout/mercado-pago")
async def checkout_mercado_pago(request: Request):
    """
    Crea un checkout de Mercado Pago.

    Body:
    {
        "client_id": "uuid",
        "concepto": "Pago 50% Starter",
        "monto": 32.50
    }

    Response:
    {
        "checkout_url": "https://www.mercadopago.com/checkout/v1/..."
    }
    """
    if not is_supabase_enabled():
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        import mercadopago

        mp_access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
        if not mp_access_token:
            raise HTTPException(status_code=503, detail="Mercado Pago not configured")

        body = await request.json()
        client_id = body.get("client_id")
        concepto = body.get("concepto")
        monto = float(body.get("monto", 0))

        if not all([client_id, concepto, monto]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Crear cliente de Mercado Pago
        sdk = mercadopago.SDK(mp_access_token)

        # Crear preferencia de pago
        preference_data = {
            "items": [
                {
                    "id": client_id,
                    "title": concepto,
                    "quantity": 1,
                    "unit_price": monto
                }
            ],
            "back_urls": {
                "success": f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment-success",
                "failure": f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment-failure",
                "pending": f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment-pending"
            },
            "notification_url": f"{os.getenv('APP_URL', 'http://localhost:8000')}/webhooks/mercado-pago",
            "external_reference": client_id,
            "auto_return": "approved"
        }

        preference_response = sdk.preference().create(preference_data)

        if preference_response["status"] == 201:
            checkout_url = preference_response["response"]["init_point"]
            logger.info(f"Mercado Pago checkout created for {client_id}: {checkout_url}")
            return {"checkout_url": checkout_url}
        else:
            logger.error(f"Mercado Pago error: {preference_response}")
            raise HTTPException(status_code=500, detail="Error creating checkout")

    except Exception as e:
        logger.error(f"Error creating Mercado Pago checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/mercado-pago")
async def webhook_mercado_pago(request: Request):
    """
    Webhook de Mercado Pago que confirma el pago.
    """
    if not is_supabase_enabled():
        return {"status": "ok"}

    try:
        from agent.supabase_client import registrar_pago, obtener_cliente_por_id

        body = await request.json()

        # Tipos de notificación: payment, plan, subscription, invoice
        tipo = body.get("type")
        dato = body.get("data", {})

        if tipo == "payment":
            payment_id = dato.get("id")

            # Obtener detalles del pago de Mercado Pago
            import mercadopago
            mp_access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
            if not mp_access_token:
                return {"status": "ok"}

            sdk = mercadopago.SDK(mp_access_token)
            payment_response = sdk.payment().get(payment_id)

            if payment_response["status"] == 200:
                payment = payment_response["response"]

                # payment.status: pending, approved, authorized, in_process, in_mediation, rejected, cancelled, refunded, charge_back
                if payment["status"] == "approved":
                    client_id = payment.get("external_reference")

                    if client_id:
                        # Registrar pago en Supabase
                        concepto = f"Pago via Mercado Pago (ID: {payment_id})"
                        monto = payment.get("transaction_amount", 0)

                        await registrar_pago(
                            client_id=client_id,
                            concepto=concepto,
                            monto=monto,
                            metodo_pago="mercado-pago",
                            referencia=str(payment_id)
                        )

                        logger.info(f"Mercado Pago payment confirmed for {client_id}: ${monto}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Mercado Pago webhook: {e}")
        return {"status": "ok"}  # MP espera status 200


@app.post("/checkout/stripe")
async def checkout_stripe(request: Request):
    """
    Crea una session de checkout de Stripe.

    Body:
    {
        "client_id": "uuid",
        "concepto": "Pago 50% Starter",
        "monto": 32.50
    }

    Response:
    {
        "checkout_url": "https://checkout.stripe.com/pay/cs_..."
    }
    """
    if not is_supabase_enabled():
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        import stripe

        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")

        stripe.api_key = stripe_key

        body = await request.json()
        client_id = body.get("client_id")
        concepto = body.get("concepto")
        monto = float(body.get("monto", 0))

        if not all([client_id, concepto, monto]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Crear session de Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": concepto,
                        },
                        "unit_amount": int(monto * 100),  # Stripe usa centavos
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('APP_URL', 'http://localhost:8000')}/payment-failure",
            metadata={"client_id": client_id, "concepto": concepto}
        )

        logger.info(f"Stripe checkout created for {client_id}: {session.id}")
        return {"checkout_url": session.url}

    except Exception as e:
        logger.error(f"Error creating Stripe checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/stripe")
async def webhook_stripe(request: Request):
    """
    Webhook de Stripe que confirma el pago.
    """
    if not is_supabase_enabled():
        return {"status": "ok"}

    try:
        from agent.supabase_client import registrar_pago
        import stripe

        body = await request.text()
        sig_header = request.headers.get("stripe-signature")

        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if not all([stripe_key, endpoint_secret]):
            return {"status": "ok"}

        stripe.api_key = stripe_key

        try:
            event = stripe.Webhook.construct_event(body, sig_header, endpoint_secret)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            if session["payment_status"] == "paid":
                client_id = session.get("metadata", {}).get("client_id")
                concepto = session.get("metadata", {}).get("concepto")
                monto = session.get("amount_total", 0) / 100  # Stripe usa centavos

                if client_id:
                    await registrar_pago(
                        client_id=client_id,
                        concepto=concepto or "Pago via Stripe",
                        monto=monto,
                        metodo_pago="stripe",
                        referencia=session.get("id")
                    )

                    logger.info(f"Stripe payment confirmed for {client_id}: ${monto}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        return {"status": "ok"}
