# HELIX · AI — Sofía (Agente WhatsApp)
## Documentación técnica completa

**Última actualización:** 21 de mayo de 2026
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

### 2.2. Configuración de Twilio Sandbox (modo desarrollo)

Twilio ofrece un sandbox gratuito de WhatsApp para desarrollo. El número del sandbox es `+1 415 523 8886`.

Pasos:
1. Iniciar sesión en Twilio Console
2. Ir a Messaging → Try it out → Send a WhatsApp message
3. Anotar el código de unión (formato `join <dos-palabras>`, ejemplo: `join run-chance`)
4. Desde tu WhatsApp personal, enviar ese código al `+1 415 523 8886`
5. Tu número queda registrado como participante del sandbox
6. Anotar también: Account SID (`ACxxxxxxxx...`) y Auth Token

**Limitaciones del sandbox:**
- No soporta typing indicators
- Cada persona que quiera hablar con el bot tiene que enviar el `join` primero
- El número es compartido, no exclusivo
- No sirve para producción comercial

### 2.3. Configuración del webhook en Twilio

En Twilio Console → Sandbox Settings:

- **When a message comes in:** `https://TU-APP.up.railway.app/webhook` (método POST)
- Status callback URL: opcional

Sin este paso, Twilio nunca le avisa al servidor que llegó un mensaje.

### 2.4. Variables de entorno en Railway

| Variable | Valor de ejemplo | Notas |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | De Anthropic Console |
| `TWILIO_ACCOUNT_SID` | `ACxxxxxxxx...` | De Twilio Console |
| `TWILIO_AUTH_TOKEN` | `xxxxxxxx...` | De Twilio Console |
| `TWILIO_PHONE_NUMBER` | `+14155238886` | Sin el prefijo `whatsapp:` — el código lo agrega solo |
| `TWILIO_VALIDATE_SIGNATURE` | `false` (en sandbox) | En producción cambiar a `true` |
| `WHATSAPP_PROVIDER` | `twilio` | Permite intercambiar proveedor |
| `DATABASE_URL` | `postgresql://...` | Railway lo inyecta automáticamente con PostgreSQL |
| `ENVIRONMENT` | `production` | Para logging y comportamiento condicional |
| `PORT` | `8000` | Railway lo inyecta solo |

**Punto crítico descubierto:** el código agrega el prefijo `whatsapp:` automáticamente al construir el `From`. Por lo tanto `TWILIO_PHONE_NUMBER` debe contener solo el número en formato E.164 sin prefijo. Si se pone `whatsapp:+14155238886`, el código termina enviando `whatsapp:whatsapp:+14155238886` y Twilio responde con error 21212 ("Invalid From Number").

### 2.5. Deploy en Railway

1. Crear nuevo proyecto en Railway
2. Conectar el repositorio de GitHub (`whatsapp-agentkit`)
3. Railway detecta automáticamente el builder (Railpack v0.23.0)
4. Cargar las variables de entorno listadas arriba
5. Deploy automático en cada push a `main`
6. Railway genera una URL pública del tipo `https://TU-APP-production-xxxx.up.railway.app`

**Fix importante aplicado durante setup:** `DATABASE_URL` inicialmente apuntaba a `sqlite+aiosqlite:///./agentkit.db` (ruta relativa sin permisos en Railway). Se cambió a `sqlite+aiosqlite:////tmp/agentkit.db` para el sandbox. En producción real usar PostgreSQL.

### 2.6. Estructura del repositorio

```
whatsapp-agentkit/
├── agent/
│   ├── __init__.py
│   ├── main.py          — Servidor FastAPI + lógica del webhook + delays + split de mensajes
│   ├── brain.py         — Conexión con Claude API (claude-sonnet-4-6)
│   ├── memory.py        — Historial de conversaciones por número (SQLite/PostgreSQL)
│   ├── security.py      — Rate limiting, idempotencia, sanitización de input
│   ├── tools.py         — Herramientas del negocio (búsqueda en knowledge base)
│   └── providers/
│       ├── __init__.py  — Factory: elige proveedor según .env
│       ├── base.py      — Clase abstracta ProveedorWhatsApp
│       └── twilio.py    — Adaptador Twilio con validación de firma HMAC-SHA1
├── config/
│   ├── business.yaml    — Datos del negocio (nombre, descripción, horario)
│   └── prompts.yaml     — System prompt de Sofía (personalidad + reglas de escritura)
├── knowledge/           — Carpeta para documentos del negocio (PDFs, CSVs, etc.)
├── tests/
│   ├── test_local.py    — Simulador de chat en terminal (sin WhatsApp real)
│   └── test_security.py — 20 tests automáticos de seguridad (todos pasan)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                 — API keys (NUNCA va a GitHub)
```

**Dependencias principales (`requirements.txt`):**

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

## 3. Personalización del agente Sofía

### 3.1. Identidad de Sofía

Sofía es la asistente virtual de HELIX · AI. Su rol es atender consultas iniciales por WhatsApp, calificar leads y orientar sobre qué solución de HELIX hace sentido para cada caso.

Perfil configurado:
- Tono amigable y empático: primero entiende el problema, luego ofrece soluciones
- Nunca vende por vender
- Conoce los 4 pilares: Estrategia e Identidad, Crecimiento Digital, Automatización IA, Infraestructura Web
- El servicio de entrada que ofrece es la Auditoría de Crecimiento
- Horario: Lunes a Viernes 8:00 a 18:00 hs

### 3.2. System prompt — estilo de escritura

Después de las primeras pruebas se detectó que Sofía respondía como asistente técnico (markdown, bullets, guiones largos), lo que la hacía sentir muy "IA" y rompía la ilusión de WhatsApp. Se agregó al system prompt la siguiente sección de estilo:

```
ESTILO DE ESCRITURA (CRÍTICO):
- Estás escribiendo en WhatsApp, NO en Slack ni en un email.
- NUNCA uses markdown: prohibido negrita, cursiva, títulos, citas, código.
- NUNCA uses listas con guiones ni con asteriscos.
- NUNCA uses bullets ni numeración.
- Si necesitás enumerar algo, hacelo en prosa: "primero X, después Y, y por último Z".
- Mensajes cortos. Máximo 2-3 oraciones por mensaje.
- Si tenés que decir algo largo, partilo en VARIOS mensajes cortos.
- Emojis con moderación: máximo uno cada 3-4 mensajes.
- Hablás como persona real desde el celular: contracciones, informal.
- No saludes en cada mensaje. Solo al inicio de la conversación.
- No firmes los mensajes con "Sofía HELIX".
- No uses guion largo ( — ). Reemplazalo con comas o puntos.
```

### 3.3. Delay humano antes de enviar

Para que no se sienta robótico, antes de cada envío a Twilio el código aplica una pausa proporcional al largo del mensaje:

```python
import asyncio, random

delay = min(2 + len(respuesta) / 80, 8) + random.uniform(0, 1.5)
await asyncio.sleep(delay)
```

Esto simula una persona escribiendo a ~80 caracteres por segundo, con un piso de 2s, techo de 8s y variabilidad natural.

### 3.4. Partición de respuestas largas

Si la respuesta supera 280 caracteres o contiene saltos de párrafo dobles (`\n\n`), se parte en bloques. Entre cada bloque se aplica un delay de `random.uniform(1.5, 3)` segundos. Si no hay saltos de párrafo, se corta por oraciones intentando mantener bloques de menos de 280 caracteres.

Para personalizar el agente a un cliente nuevo editar:
- `config/business.yaml` — nombre, descripción, horario
- `config/prompts.yaml` — system prompt completo con los servicios y tono del negocio
- `knowledge/` — subir archivos con información del negocio (PDFs, CSVs, menú, FAQ, etc.)

---

## 4. Diagnóstico de problemas que ya resolvimos

### 4.1. Síntoma: el bot no responde a mensajes

Causas posibles, en orden de probabilidad:

1. **Webhook de Twilio no configurado o apuntando a URL vieja.** Verificar en Sandbox Settings que la URL sea la del último deploy de Railway.

2. **`TWILIO_PHONE_NUMBER` con prefijo `whatsapp:` (esto nos pasó).** Twilio responde con código 21212. Solución: dejar solo `+14155238886`.

3. **`TWILIO_PHONE_NUMBER` apuntando a un número que no es canal de WhatsApp.** Twilio responde con código 63007. Solución: usar el del sandbox o un sender de WhatsApp aprobado en producción.

4. **El número del usuario no hizo el `join` al sandbox.** Solución: enviar primero el código `join <dos-palabras>` al número del sandbox.

5. **Variables de entorno faltantes o mal cargadas** (ANTHROPIC_API_KEY, credenciales de Twilio).

6. **`TWILIO_VALIDATE_SIGNATURE=true` con Railway detrás de proxy.** En sandbox conviene `false` mientras se prueba; en producción se puede activar con configuración cuidadosa.

7. **`DATABASE_URL` apuntando a ruta relativa sin permisos en Railway.** Fix: usar `/tmp/agentkit.db` o PostgreSQL.

### 4.2. Cómo leer logs en Railway

- Railway → Proyecto → Servicio `whatsapp-agentkit`
- Pestaña Deployments → click en "View logs" del deploy activo
- Buscar líneas con `ERROR:agentkit:` o `ERROR:`
- Para errores de Twilio, buscar el código numérico en `https://www.twilio.com/docs/errors/CODIGO`

---

## 5. Lo que falta para estar 100% en producción

### Crítico (sin esto no funciona bien en producción real)

**Número de WhatsApp real (no sandbox)**

El sandbox solo permite mensajes a números verificados manualmente. Para clientes reales:
- Twilio WhatsApp Business API (requiere aprobación de Meta, tarda 1-7 días)
- O migrar a Meta Cloud API directamente (gratis por conversación, requiere Facebook Business verificada)

**Base de datos persistente**

El SQLite en `/tmp` se borra cada vez que Railway reinicia el contenedor. Los clientes pierden el historial. Solución: agregar PostgreSQL en Railway (un clic) y usar el `DATABASE_URL` que Railway provee automáticamente. El código ya está preparado.

**Validación de firma Twilio en producción**

Con `TWILIO_VALIDATE_SIGNATURE=true` y Railway detrás de un proxy, la validación puede fallar porque la URL firmada por Twilio no coincide con la que ve el servidor. Hay que reconstruir la URL usando el header `X-Forwarded-Proto` o verificar que Railway pase los headers correctamente.

### Importante

**Manejo de medios (imágenes, audios, documentos)**

Actualmente el agente solo procesa texto. Los clientes suelen mandar fotos de productos, audios, PDFs. Hay que agregar manejo en `parsear_webhook`.

**Escalamiento a humano**

Cuando el agente no puede resolver algo, debería notificar a alguien (email, Slack, Notion). Se agrega como herramienta en `agent/tools.py`.

**Monitoreo de errores**

Si el agente cae, nadie se entera. Agregar Sentry o un webhook de alerta a Slack/email cuando hay errores 500.

**Panel de conversaciones**

Para que el cliente vea qué le preguntan a su agente: Notion, Airtable, o una interfaz sobre la base de datos.

### Para escalar el producto

**Múltiples clientes (multitenancy)**

El sistema actual sirve para un negocio. Para vender a varios clientes: una instancia por cliente (más simple) o routing por número de teléfono con configs separadas por tenant.

**Knowledge base dinámica**

Para clientes con catálogos grandes o precios que cambian frecuentemente: conectar a una base de vectores (Pinecone, Supabase Vector) para búsqueda semántica en lugar de búsqueda por texto plano.

**Métricas de uso**

Cuántos mensajes se procesan, cuánto cuesta por cliente, cuáles son las preguntas más frecuentes. Importante para cobrar y para mejorar el agente.

---

## 6. Checklist de lanzamiento para un cliente nuevo

- [ ] Datos del negocio recopilados (nombre, descripción, servicios, precios, horario)
- [ ] `config/business.yaml` y `config/prompts.yaml` personalizados
- [ ] Archivos del negocio en `/knowledge` (menú, FAQ, catálogo, políticas)
- [ ] Tests locales pasando (`python tests/test_local.py`)
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

## 7. Comandos útiles

```bash
# Correr localmente
uvicorn agent.main:app --reload --port 8000

# Chat de prueba sin WhatsApp
python tests/test_local.py

# Tests de seguridad (20 tests, todos deben pasar)
python3 -m pytest tests/test_security.py -v

# Build Docker local
docker compose up --build

# Subir cambios y hacer deploy
git add .
git commit -m "descripción del cambio"
git push origin main
# Railway detecta el push y hace deploy automático
```

---

## 8. URLs de referencia

- Agente en producción: `https://whatsapp-agentkit-production-2eb4.up.railway.app`
- Webhook URL para Twilio: `https://whatsapp-agentkit-production-2eb4.up.railway.app/webhook`
- Repo GitHub: `https://github.com/Jon-human-in-the-loop/whatsapp-agentkit`
- Railway dashboard: `https://railway.app`
- Twilio Console: `https://console.twilio.com`
- Twilio error codes: `https://www.twilio.com/docs/errors/CODIGO`
- Anthropic API Keys: `https://platform.anthropic.com/settings/api-keys`
