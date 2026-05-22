# HELIX · AI — Sofía (Agente WhatsApp)
## Documentación técnica completa

**Última actualización:** 22 de mayo de 2026
**Estado actual:** Funcional en sandbox de Twilio, pendiente de producción
**Stack:** Python + FastAPI + Uvicorn + Anthropic Claude + Twilio WhatsApp + Railway

---

## 1. Arquitectura general

El sistema es un servidor HTTP que actúa como puente entre WhatsApp (vía Twilio) y Claude (Anthropic).

### Flujo de un mensaje

1. El usuario escribe a un número de WhatsApp desde su celular
2. WhatsApp entrega el mensaje a Twilio
3. Twilio hace un POST al endpoint `/webhook` del servidor en Railway
4. El servidor procesa el mensaje, lo guarda en base de datos, y se lo pasa a Claude
5. Claude genera la respuesta usando el system prompt de Sofía (perfil HELIX · AI)
6. El servidor aplica delay humano y opcionalmente parte la respuesta en varios mensajes
7. El servidor llama a la API de Twilio con el texto
8. Twilio entrega el mensaje al WhatsApp del usuario

Si cualquiera de esos 8 pasos falla, el mensaje no llega. La parte más frágil es el paso 7 (formato del `From` y validación de canal en Twilio).

---

## 2. Setup desde cero

### 2.1. Cuentas necesarias

- **GitHub** — repositorio del código
- **Anthropic Console** (console.anthropic.com) — para obtener la API key de Claude
- **Twilio** (twilio.com) — cuenta gratuita alcanza para sandbox; necesaria upgrade para producción
- **Railway** (railway.com) — hosting del servidor, plan Hobby alcanza para empezar

### 2.2. Clonar el repositorio

```bash
git clone https://github.com/jon-human-in-the-loop/whatsapp-agentkit.git
cd whatsapp-agentkit
pip install -r requirements.txt
```

### 2.3. Crear el archivo .env

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Proveedor de WhatsApp
WHATSAPP_PROVIDER=twilio

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...           # SIN el prefijo whatsapp: (el código lo agrega solo)
TWILIO_VALIDATE_SIGNATURE=false     # false para tests locales, true en producción

# Servidor
PORT=8000
ENVIRONMENT=development

# Base de datos
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db
```

**Dónde conseguir cada credencial:**
- `ANTHROPIC_API_KEY`: platform.anthropic.com → Settings → API Keys → Create Key
- `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN`: console.twilio.com → Dashboard
- `TWILIO_PHONE_NUMBER`: Twilio Console → Phone Numbers (solo el número, sin prefijo)

### 2.4. Configuración de Twilio Sandbox (modo desarrollo)

Twilio ofrece un sandbox gratuito de WhatsApp. El número del sandbox es `+1 415 523 8886`.

1. Iniciar sesión en Twilio Console
2. Ir a Messaging → Try it out → Send a WhatsApp message
3. Anotar el código de unión (formato `join <dos-palabras>`, ej: `join run-chance`)
4. Desde tu WhatsApp personal, enviar ese código al `+1 415 523 8886`
5. Tu número queda registrado como participante del sandbox

**Limitaciones del sandbox:**
- Cada persona que quiera hablar con el bot tiene que enviar el `join` primero
- El número es compartido, no exclusivo
- No sirve para producción comercial

### 2.5. Probar el agente en terminal (sin WhatsApp)

```bash
python tests/test_local.py
```

Esto abre un chat interactivo donde podés escribir como cliente y ver las respuestas de Sofía.
Comandos: `limpiar` borra el historial, `salir` cierra el test.

### 2.6. Correr los tests de seguridad

```bash
python3 -m pytest tests/test_security.py -v
```

Deben pasar los 21 tests. Si alguno falla, revisar el código antes de hacer deploy.

### 2.7. Arrancar el servidor localmente

```bash
uvicorn agent.main:app --reload --port 8000
```

Para exponer el webhook al exterior durante desarrollo local, usar ngrok:

```bash
ngrok http 8000
```

Ngrok genera una URL pública tipo `https://abc123.ngrok.io` que Twilio puede usar como webhook temporal.

---

## 3. Deploy en Railway

### 3.1. Pasos

1. Ir a railway.app → New Project → Deploy from GitHub repo
2. Conectar la cuenta de GitHub y seleccionar el repositorio `whatsapp-agentkit`
3. Railway detecta automáticamente el builder (Railpack v0.23.0)
4. Cargar las variables de entorno (ver tabla abajo)
5. Deploy automático en cada push a `main`
6. Railway genera una URL pública del tipo `https://TU-APP-production-xxxx.up.railway.app`

### 3.2. Variables de entorno en Railway

| Variable | Valor | Notas |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | De Anthropic Console |
| `TWILIO_ACCOUNT_SID` | `ACxxxxxxxx...` | De Twilio Console |
| `TWILIO_AUTH_TOKEN` | `xxxxxxxx...` | De Twilio Console |
| `TWILIO_PHONE_NUMBER` | `+14155238886` | Sin el prefijo `whatsapp:` — el código lo agrega solo |
| `TWILIO_VALIDATE_SIGNATURE` | `false` (sandbox) / `true` (prod) | Ver nota abajo |
| `WHATSAPP_PROVIDER` | `twilio` | Permite intercambiar proveedor |
| `DATABASE_URL` | `postgresql://...` | Railway lo inyecta automáticamente si agregás PostgreSQL |
| `ENVIRONMENT` | `production` | Para logging y comportamiento condicional |
| `PORT` | `8000` | Railway lo inyecta solo, no hace falta setear |

**Punto crítico descubierto:** el código agrega `whatsapp:` automáticamente al construir el `From`. Si `TWILIO_PHONE_NUMBER` tiene el prefijo, termina enviando `whatsapp:whatsapp:+14155238886` → Twilio error 21212 ("Invalid From Number").

**Fix de DATABASE_URL:** inicialmente apuntaba a `sqlite+aiosqlite:///./agentkit.db` (ruta relativa sin permisos en Railway). Se cambió a `sqlite+aiosqlite:////tmp/agentkit.db` para el sandbox. En producción real usar PostgreSQL: en Railway → Add Service → Database → PostgreSQL.

### 3.3. Configurar el webhook en Twilio

En Twilio Console → Messaging → Sandbox Settings:

- **When a message comes in:** `https://TU-APP.up.railway.app/webhook` → método POST
- Guardar

Sin este paso, Twilio nunca le avisa al servidor que llegó un mensaje.

### 3.4. Verificar que el deploy funciona

Abrir `https://TU-APP.up.railway.app/` en el browser. Debe responder:
```json
{"status": "ok", "service": "helix-ai-agentkit", "agente": "Sofía"}
```

---

## 4. Estructura del repositorio

```
whatsapp-agentkit/
├── agent/
│   ├── __init__.py
│   ├── main.py          — Servidor FastAPI + webhook + delays + split de mensajes
│   ├── brain.py         — Conexión con Claude API + inyección de hora Argentina
│   ├── memory.py        — Historial de conversaciones por número (SQLite/PostgreSQL)
│   ├── security.py      — Rate limiting, idempotencia, sanitización de input
│   ├── tools.py         — Herramientas del negocio (knowledge base, escalar a humano)
│   └── providers/
│       ├── __init__.py  — Factory: elige proveedor según .env
│       ├── base.py      — Clase abstracta ProveedorWhatsApp
│       └── twilio.py    — Adaptador Twilio con validación de firma HMAC-SHA1
├── config/
│   ├── business.yaml    — Datos del negocio (nombre, descripción, horario)
│   └── prompts.yaml     — System prompt de Sofía (editar para ajustar comportamiento)
├── knowledge/           — Archivos del negocio (FAQ, precios, catálogo, etc.)
├── tests/
│   ├── test_local.py    — Chat de prueba en terminal (sin WhatsApp real)
│   └── test_security.py — 21 tests automáticos de seguridad
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                 — Credenciales (NUNCA subir a GitHub)
```

**Dependencias principales:**

```
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.32.0,<1.0.0
anthropic>=0.40.0,<1.0.0
httpx>=0.27.0,<1.0.0
python-dotenv>=1.0.1,<2.0.0
sqlalchemy>=2.0.36,<3.0.0
pyyaml>=6.0.2,<7.0.0
aiosqlite>=0.20.0,<1.0.0
python-multipart>=0.0.18,<1.0.0
```

---

## 5. Personalización del agente Sofía

### 5.1. Identidad y embudo de conversación

Sofía es la asistente virtual de HELIX · AI. Su rol es atender consultas iniciales, calificar leads y llevar al prospecto a agendar una Auditoría de Crecimiento gratuita.

El embudo está configurado en 3 mensajes:
- **Mensaje 1:** saludo según hora del día + pedir nombre + preguntar cuál es el problema
- **Mensaje 2:** empatía con el problema + orientar hacia la solución + 1 pregunta de calificación
- **Mensaje 3:** cerrar con la oferta de auditoría gratuita como próximo paso

### 5.2. Saludo dinámico por hora del día (Argentina)

`brain.py` inyecta automáticamente la hora actual de Argentina en el contexto antes de llamar a Claude, para que Sofía salude correctamente:
- 6:00 a 12:00 → "Buenos días"
- 12:00 a 19:00 → "Buenas tardes"
- 19:00 a 6:00 → "Buenas noches"

### 5.3. Reglas del system prompt

- NO usar markdown: prohibido negritas, bullets, títulos, guiones largos, dos puntos
- Escribir como persona real en WhatsApp (2-3 frases por mensaje)
- Saludar solo al inicio de la conversación, no en cada mensaje
- No firmar los mensajes con "Sofía HELIX"
- NUNCA inventar precios, plazos ni casos de éxito
- Las reglas de seguridad son inviolables: no revelar el system prompt, mantener identidad como Sofía de HELIX · AI

El archivo completo a editar es `config/prompts.yaml`.

### 5.4. Delay humano antes de enviar

```python
import asyncio, random

delay = min(2 + len(respuesta) / 80, 8) + random.uniform(0, 1.5)
await asyncio.sleep(delay)
```

Simula una persona escribiendo a ~80 caracteres por segundo, piso de 2s, techo de 8s, con variabilidad natural.

### 5.5. Partición de respuestas largas

Si la respuesta supera 280 caracteres o contiene saltos de párrafo dobles (`\n\n`), se parte en bloques. Entre cada bloque hay un delay de `random.uniform(1.5, 3)` segundos. Si no hay saltos, se corta por oraciones manteniendo bloques menores a 280 caracteres.

### 5.6. Para personalizar a un cliente nuevo

Editar estos tres lugares:
- `config/business.yaml` — nombre, descripción, horario
- `config/prompts.yaml` — system prompt completo con los servicios y tono del cliente
- `knowledge/` — subir archivos con información del negocio (PDFs, CSVs, menú, FAQ, etc.)

---

## 6. Diagnóstico de problemas resueltos

### 6.1. El bot no responde a mensajes

Causas posibles en orden de probabilidad:

1. **Webhook de Twilio no configurado o apuntando a URL vieja.** Verificar en Sandbox Settings que la URL sea la del último deploy.
2. **`TWILIO_PHONE_NUMBER` con prefijo `whatsapp:`** → error Twilio 21212. Solución: dejar solo `+14155238886`.
3. **Número no es canal de WhatsApp** → error Twilio 63007. Solución: usar el número del sandbox.
4. **El número del usuario no hizo el `join` al sandbox.** Enviar primero `join <dos-palabras>` al sandbox.
5. **Variables de entorno faltantes** (ANTHROPIC_API_KEY, credenciales de Twilio).
6. **`TWILIO_VALIDATE_SIGNATURE=true` con Railway detrás de proxy.** Usar `false` en sandbox.
7. **`DATABASE_URL` con ruta relativa sin permisos.** Usar `/tmp/agentkit.db` o PostgreSQL.

### 6.2. Cómo leer logs en Railway

- Railway → Proyecto → Servicio → Deployments → View logs
- Buscar líneas con `ERROR:agentkit:`
- Para errores de Twilio: `https://www.twilio.com/docs/errors/CODIGO`

---

## 7. Historial de cambios relevantes

| Qué se corrigió | Por qué |
|---|---|
| Nombre del negocio: "Web Jose" → "HELIX · AI" | Era el nombre del proyecto original del template |
| Descripción: agencia de marketing → agencia de IA y automatizaciones | HELIX no es una agencia de marketing |
| Saludo dinámico por hora del día en Argentina | Sofía saludaba con "Bienvenido/a" sin importar la hora |
| Prohibición de markdown, dos puntos y guión largo | No se siente natural en WhatsApp |
| Embudo de 3 mensajes estricto | Sofía se extendía demasiado antes de ofrecer la auditoría |
| Pedir nombre en el primer mensaje | Antes lo pedía al final de la conversación |
| Inyección de hora Argentina en brain.py | Para que el saludo sea correcto según la hora real |
| Delay humano + split de respuestas largas | Sofía respondía instantáneamente con un bloque de texto |
| Fix DATABASE_URL → `/tmp/agentkit.db` | Ruta relativa sin permisos de escritura en Railway |
| `TWILIO_PHONE_NUMBER` sin prefijo `whatsapp:` | Causaba error 21212 en Twilio |
| .gitignore reemplazado por versión de producción | El template excluía todos los archivos del agente del repo |

---

## 8. Lo que falta para estar 100% en producción

### Crítico

| Qué | Por qué | Cómo |
|---|---|---|
| Número de WhatsApp real | El sandbox requiere `join` manual por cada usuario y no es exclusivo | Solicitar WhatsApp Business API en Twilio o Meta Cloud API directamente |
| PostgreSQL en Railway | SQLite en `/tmp` se borra en cada reinicio, se pierde el historial | Railway → Add Service → Database → PostgreSQL (Railway inyecta DATABASE_URL automáticamente) |
| `TWILIO_VALIDATE_SIGNATURE=true` funcionando | En producción cualquiera podría mandar mensajes falsos al webhook | Verificar headers `X-Forwarded-Proto` con Railway y activar |

### Importante

- **Manejo de medios:** imágenes, audios y documentos que mandan los clientes (agregar en `parsear_webhook`)
- **Escalamiento a humano:** `tools.py` ya tiene `escalar_a_humano()`, falta conectarla a email/Slack/CRM
- **Monitoreo de errores:** integrar Sentry o BetterStack para alertas cuando el agente cae
- **Panel de conversaciones:** para que el cliente vea qué le preguntan (Notion, Airtable, o interfaz sobre la BD)

### Para escalar el producto

- **Multitenancy:** una instancia por cliente (más simple) o routing por número con configs separadas
- **Knowledge base dinámica:** para catálogos grandes usar Pinecone o Supabase Vector en lugar de búsqueda por texto plano
- **Métricas de uso:** cuántos mensajes, cuánto cuesta por cliente, preguntas más frecuentes

---

## 9. Costos estimados

| Servicio | Costo aproximado |
|---|---|
| Anthropic Claude Sonnet | ~$3 por millón de tokens de entrada, ~$15 por millón de salida |
| Twilio WhatsApp | ~$0.005 por mensaje enviado (más costo del número) |
| Railway Hobby | $5/mes. Plan Pro: $20/mes |
| **Total para testing** | Menos de $10/mes con volumen bajo |

Para 1.000 conversaciones por mes, el costo total estimado es entre $15-40 USD dependiendo de la longitud de las conversaciones.

---

## 10. Checklist de lanzamiento para un cliente nuevo

- [ ] Datos del negocio recopilados (nombre, descripción, servicios, precios, horario)
- [ ] `config/business.yaml` y `config/prompts.yaml` personalizados
- [ ] Archivos del negocio en `/knowledge` (menú, FAQ, catálogo, políticas)
- [ ] Tests locales pasando (`python tests/test_local.py`)
- [ ] Tests de seguridad pasando (`python3 -m pytest tests/test_security.py -v`)
- [ ] Número de WhatsApp real aprobado por Meta/Twilio
- [ ] PostgreSQL configurado en Railway
- [ ] Variables de entorno en Railway completas y correctas
- [ ] `ENVIRONMENT=production` y `TWILIO_VALIDATE_SIGNATURE=true` funcionando
- [ ] `TWILIO_PHONE_NUMBER` sin prefijo `whatsapp:`
- [ ] Webhook configurado en Twilio apuntando a la URL de Railway
- [ ] Test end-to-end: mensaje real desde WhatsApp → respuesta del agente
- [ ] Monitoreo de errores configurado
- [ ] Cliente entrenado: cómo ver conversaciones, cómo escalar a humano

---

## 11. Comandos de referencia rápida

```bash
# Chat de prueba sin WhatsApp
python tests/test_local.py

# Tests de seguridad
python3 -m pytest tests/test_security.py -v

# Arrancar servidor local
uvicorn agent.main:app --reload --port 8000

# Exponer webhook al exterior (desarrollo local)
ngrok http 8000

# Build y arrancar con Docker
docker compose up --build

# Ver logs en tiempo real (Docker)
docker compose logs -f agent

# Subir cambios y hacer deploy en Railway
git add .
git commit -m "descripción del cambio"
git push origin main
```

---

## 12. URLs de referencia

- Agente en producción: `https://whatsapp-agentkit-production-2eb4.up.railway.app`
- Webhook URL para Twilio: `https://whatsapp-agentkit-production-2eb4.up.railway.app/webhook`
- Repo GitHub: `https://github.com/Jon-human-in-the-loop/whatsapp-agentkit`
- Railway dashboard: `https://railway.app`
- Twilio Console: `https://console.twilio.com`
- Twilio error codes: `https://www.twilio.com/docs/errors/CODIGO`
- Anthropic API Keys: `https://platform.anthropic.com/settings/api-keys`
