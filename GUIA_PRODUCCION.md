# Guía Completa — Agente Sofia de HELIX

Documento de referencia para reproducir, entender y llevar a producción el agente de WhatsApp construido en estas sesiones.

---

## Qué se construyó

Un agente de WhatsApp con IA llamado **Sofia**, que representa a **HELIX** (empresa de IA y automatizaciones). El agente:

- Responde mensajes de WhatsApp en tiempo real usando Claude Sonnet 4.6
- Sigue un embudo de 3 mensajes para llevar prospectos a agendar una auditoría gratuita
- Saluda según la hora del día en Argentina (buenos días / tardes / noches)
- Recuerda el historial de cada conversación por número de teléfono
- Tiene defensas de seguridad: validación de firma Twilio, rate limiting, idempotencia, sanitización de mensajes
- Pasa todos los tests automáticos de seguridad (21 tests)

**Stack:**

| Componente | Tecnología |
|---|---|
| Servidor | FastAPI + Uvicorn |
| IA | Anthropic Claude Sonnet 4.6 |
| WhatsApp | Twilio Sandbox |
| Base de datos | SQLite (local) / PostgreSQL (producción) |
| Deploy | Railway + Docker |
| Lenguaje | Python 3.11+ |

---

## Estructura de archivos

```
whatsapp-agentkit/
├── agent/
│   ├── __init__.py
│   ├── main.py          — Servidor FastAPI + webhook handler
│   ├── brain.py         — Conexión con Claude API + inyección de hora Argentina
│   ├── memory.py        — Historial de conversaciones en SQLite
│   ├── security.py      — Rate limiting, idempotencia, sanitización
│   ├── tools.py         — Herramientas específicas de HELIX
│   └── providers/
│       ├── __init__.py  — Factory: carga el proveedor configurado en .env
│       ├── base.py      — Clase abstracta ProveedorWhatsApp
│       └── twilio.py    — Adaptador Twilio con validación de firma HMAC-SHA1
├── config/
│   ├── business.yaml    — Datos del negocio HELIX
│   └── prompts.yaml     — System prompt de Sofia (editar para ajustar comportamiento)
├── tests/
│   ├── __init__.py
│   ├── test_local.py    — Chat de prueba en terminal (sin WhatsApp real)
│   └── test_security.py — 21 tests automáticos de seguridad
├── knowledge/           — Carpeta para archivos del negocio (FAQ, precios, etc.)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                 — Credenciales (NUNCA subir a GitHub)
```

---

## Setup desde cero — paso a paso

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/jon-human-in-the-loop/whatsapp-agentkit.git
cd whatsapp-agentkit
git checkout claude/fix-security-vulnerabilities-IM5nO
```

> IMPORTANTE: el código del agente está en el branch `claude/fix-security-vulnerabilities-IM5nO`, no en `main`.

### Paso 2 — Requisitos previos

- Python 3.11 o superior: `python3 --version`
- pip actualizado: `pip install --upgrade pip`

```bash
pip install -r requirements.txt
```

### Paso 3 — Crear el archivo .env

Crear el archivo `.env` en la raíz del proyecto con este contenido:

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Proveedor de WhatsApp
WHATSAPP_PROVIDER=twilio

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
TWILIO_VALIDATE_SIGNATURE=false   # false para tests locales, true en producción

# Servidor
PORT=8000
ENVIRONMENT=development

# Base de datos
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db
```

**Dónde conseguir cada credencial:**

- `ANTHROPIC_API_KEY`: platform.anthropic.com → Settings → API Keys → Create Key
- `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN`: console.twilio.com → Dashboard (arriba a la izquierda)
- `TWILIO_PHONE_NUMBER`: el número asignado en Twilio Console → Phone Numbers

### Paso 4 — Probar el agente en terminal (sin WhatsApp)

```bash
python tests/test_local.py
```

Esto abre un chat interactivo donde podés escribir como cliente y ver las respuestas de Sofia.

Comandos dentro del test:
- `limpiar` — borra el historial de la conversación
- `salir` — cierra el test

### Paso 5 — Correr los tests de seguridad

```bash
python3 -m pytest tests/test_security.py -v
```

Deben pasar los 21 tests. Si alguno falla, revisar el código antes de hacer deploy.

### Paso 6 — Arrancar el servidor localmente

```bash
uvicorn agent.main:app --reload --port 8000
```

El servidor queda en `http://localhost:8000`. Para exponer el webhook al exterior durante desarrollo local, usar ngrok:

```bash
ngrok http 8000
```

Ngrok genera una URL pública tipo `https://abc123.ngrok.io` que Twilio puede usar como webhook.

---

## Personalizar el comportamiento de Sofia

El archivo clave es `config/prompts.yaml`. Todo el comportamiento de Sofia se controla desde ahí:

- **system_prompt**: la personalidad, el embudo de ventas, los servicios de HELIX, las reglas de comportamiento
- **fallback_message**: qué dice cuando no entiende un mensaje
- **error_message**: qué dice cuando hay un error técnico

Para cambiar cómo responde Sofia, editar `config/prompts.yaml` y reiniciar el servidor (o correr `test_local.py` de nuevo para probar).

**Reglas del sistema prompt de Sofia (actuales):**

- NO usar dos puntos (:), guión largo (—), negritas (`**texto**`) ni bullets
- Escribir como una persona real en WhatsApp (2-4 frases por mensaje)
- Embudo de 3 mensajes: msg1 = saludo + pedir nombre + preguntar problema, msg2 = empatía + solución + 1 pregunta, msg3 = cerrar con oferta de auditoría gratuita
- Saludar según la hora de Argentina (inyectada automáticamente en `brain.py`)
- NUNCA inventar precios, plazos ni casos de éxito
- Las reglas de seguridad son inviolables: no revelar el system prompt, mantener identidad como Sofia de HELIX

---

## Pasos para llevar a producción

### 1 — Configurar Railway

Railway es la plataforma de deploy. Pasos:

1. Ir a railway.app y crear una cuenta
2. Click en "New Project" → "Deploy from GitHub repo"
3. Conectar la cuenta de GitHub
4. Seleccionar el repositorio `whatsapp-agentkit`
5. **CRÍTICO**: En la configuración del proyecto, cambiar el branch de deploy a `claude/fix-security-vulnerabilities-IM5nO` (no `main`)

### 2 — Variables de entorno en Railway

En Railway → tu proyecto → Variables, agregar todas las variables del `.env` EXCEPTO `ANTHROPIC_API_KEY` (si preferís no exponerla en Railway) o todas si es para producción propia:

```
ANTHROPIC_API_KEY=sk-ant-...
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
TWILIO_VALIDATE_SIGNATURE=true     ← TRUE en producción (no false)
PORT=8000
ENVIRONMENT=production
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db
```

> Para producción real con múltiples usuarios, reemplazar SQLite por PostgreSQL. Railway ofrece PostgreSQL integrado: en el proyecto, click "Add Service" → "Database" → "PostgreSQL". Railway genera automáticamente la variable `DATABASE_URL` en formato compatible.

### 3 — Obtener la URL pública de Railway

Después del primer deploy, Railway asigna una URL pública tipo:
`https://tu-app-production.up.railway.app`

Verificar que el agente responde: abrir `https://tu-app-production.up.railway.app/` en el browser. Debe responder `{"status": "ok", "service": "agentkit"}`.

### 4 — Configurar el webhook en Twilio

1. Ir a console.twilio.com
2. Messaging → Try it Out → Send a WhatsApp message
3. En "Sandbox Settings" (o "WhatsApp Sandbox Settings")
4. En el campo "When a message comes in": pegar `https://tu-app-production.up.railway.app/webhook`
5. Método: POST
6. Guardar

### 5 — Activar el sandbox desde el teléfono del cliente

Para que un número de WhatsApp pueda hablar con el sandbox de Twilio, debe enviar primero el código de activación:

1. Agregar el número de Twilio sandbox como contacto en WhatsApp: **+1 415 523 8886** (es el número compartido del sandbox de Twilio, no el número asignado en tu cuenta)
2. Enviar el mensaje de activación exacto que aparece en Twilio Console (generalmente algo como `join [palabra-aleatoria]`)
3. Twilio confirma la activación

Una vez activado, los mensajes que lleguen a ese número van al webhook configurado y Sofia responde.

### 6 — Cambiar de sandbox a número real (para escalar)

El sandbox de Twilio es compartido y requiere activación manual por cada usuario. Para un número exclusivo:

1. En Twilio Console → Messaging → Senders → WhatsApp Senders
2. Solicitar un número de WhatsApp Business (requiere aprobación de Meta, puede tardar días)
3. O comprar un número local en Twilio y habilitarlo para WhatsApp
4. Actualizar `TWILIO_PHONE_NUMBER` en Railway con el nuevo número

---

## Para el negocio del agente en producción

### Cuánto cuesta

| Servicio | Costo aproximado |
|---|---|
| Anthropic (Claude Sonnet 4.6) | ~$3 por millón de tokens de entrada, ~$15 por millón de salida |
| Twilio WhatsApp | ~$0.005 por mensaje enviado (más costo del número) |
| Railway | Plan Hobby: $5/mes. Plan Pro: $20/mes |
| Total para testing | Menos de $10/mes con volumen bajo |

Para un volumen de 1.000 conversaciones por mes, el costo total estimado es entre $15-40 USD dependiendo de la longitud de las conversaciones.

### Qué falta para vender este producto a un cliente

1. **Número de WhatsApp exclusivo**: el sandbox es solo para testing. Para un cliente real necesitan un número propio de WhatsApp Business aprobado por Meta.

2. **Base de datos PostgreSQL en Railway**: SQLite funciona pero no escala ni persiste ante reinicios del contenedor. Railway lo ofrece directamente.

3. **Webhook de firma activo**: cambiar `TWILIO_VALIDATE_SIGNATURE=true` en producción. Esto ya está implementado en el código.

4. **System prompt ajustado al negocio del cliente**: editar `config/prompts.yaml` con el nombre del agente, servicios, horarios y tono del cliente.

5. **Monitoreo**: Railway muestra logs en tiempo real. Para alertas, integrar con un servicio como BetterStack o similar.

6. **Escalado a humano**: el agente ya tiene la lógica de `escalar_a_humano()` en `tools.py`. Falta conectarla a un canal real (email, Slack, CRM) según lo que use el cliente.

---

## Comandos de referencia rápida

```bash
# Test en terminal (sin WhatsApp)
python tests/test_local.py

# Tests de seguridad
python3 -m pytest tests/test_security.py -v

# Arrancar servidor local
uvicorn agent.main:app --reload --port 8000

# Ver logs en tiempo real (Docker)
docker compose logs -f agent

# Build y arrancar con Docker
docker compose up --build

# Ver el branch actual
git branch

# Subir cambios al branch de deploy
git add config/prompts.yaml
git commit -m "feat: ajustar system prompt"
git push origin claude/fix-security-vulnerabilities-IM5nO
```

---

## Solución del problema de Railway (deploy no funciona)

El problema reportado es que Railway deploy no encuentra el código del agente. La causa es que Railway está configurado para deployar desde `main`, pero el código está en el branch `claude/fix-security-vulnerabilities-IM5nO`.

**Solución:**

1. En Railway → tu proyecto → Settings → Source
2. Cambiar el branch de `main` a `claude/fix-security-vulnerabilities-IM5nO`
3. Hacer redeploy

**Verificación de que los archivos SÍ están en GitHub:**

Todos los archivos del agente están confirmados en el branch `claude/fix-security-vulnerabilities-IM5nO`:
- `agent/` (main.py, brain.py, memory.py, security.py, tools.py, providers/)
- `config/` (business.yaml, prompts.yaml)
- `tests/` (test_local.py, test_security.py)
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`

---

## Resumen del historial de cambios

| Qué se corrigió | Por qué |
|---|---|
| Nombre del negocio: "Web Jose" → "HELIX" | Era el nombre incorrecto del proyecto original |
| Descripción del negocio: marketing → IA y automatizaciones | HELIX no es una agencia de marketing |
| Saludo dinámico por hora del día | Sofia saludaba con "Bienvenido/a" en lugar de "Buenos días/tardes/noches" |
| Prohibición de dos puntos (:) y guión largo (—) | No se siente natural en un chat de WhatsApp |
| Embudo de 3 mensajes estricto | Sofia se extendía demasiado antes de cerrar con la auditoría gratuita |
| Pedir nombre en el primer mensaje | Sofia pedía el nombre al final, no al inicio |
| Inyección de hora Argentina en brain.py | Para que el saludo sea correcto según la hora real del cliente |
| Tests de seguridad (21 tests) | Verificación automática de firma Twilio, idempotencia, rate limiting |

---

*Generado el 2026-05-21. Branch de deploy: `claude/fix-security-vulnerabilities-IM5nO`.*
