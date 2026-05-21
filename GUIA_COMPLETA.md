# Guía completa: Agente WhatsApp con IA para HELIX · AI

**Sofía — Agente de WhatsApp con Claude AI + Twilio + Railway**

---

## Qué se construyó

Un agente de WhatsApp con inteligencia artificial que:
- Recibe mensajes de clientes por WhatsApp
- Responde automáticamente 24/7 con el perfil de HELIX · AI
- Recuerda el historial de cada conversación
- Tiene delays humanos y divide respuestas largas en mensajes cortos
- Valida la autenticidad de cada mensaje (seguridad HMAC)
- Corre en producción en Railway con deploy automático desde GitHub

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Servidor web | FastAPI + Uvicorn |
| IA | Claude claude-sonnet-4-6 (Anthropic) |
| WhatsApp | Twilio (sandbox gratuito / producción de pago) |
| Base de datos | SQLite en /tmp (desarrollo) / PostgreSQL (producción real) |
| Variables de entorno | python-dotenv |
| Deploy | Railway (conectado a GitHub, deploy automático) |

---

## Estructura de archivos generada

```
whatsapp-agentkit/
├── agent/
│   ├── __init__.py
│   ├── main.py          — Servidor FastAPI + lógica del webhook + delays + split de mensajes
│   ├── brain.py         — Conexión con Claude API
│   ├── memory.py        — Historial de conversaciones por número de teléfono (SQLite)
│   ├── security.py      — Rate limiting, idempotencia, sanitización de mensajes
│   ├── tools.py         — Herramientas del negocio (búsqueda en knowledge base)
│   └── providers/
│       ├── __init__.py  — Factory: elige proveedor según .env
│       ├── base.py      — Clase abstracta ProveedorWhatsApp
│       └── twilio.py    — Adaptador Twilio con validación de firma HMAC-SHA1
├── config/
│   ├── business.yaml    — Datos del negocio (nombre, descripción, horario)
│   └── prompts.yaml     — System prompt de Sofía (personalidad + reglas de escritura WhatsApp)
├── knowledge/           — Carpeta para subir documentos del negocio (PDFs, CSVs, etc.)
├── tests/
│   ├── test_local.py    — Simulador de chat en terminal (sin WhatsApp)
│   └── test_security.py — 20 tests automáticos de seguridad
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                 — API keys (NUNCA va a GitHub)
```

---

## Pasos realizados en las sesiones

### Sesión 1 — Infraestructura base y seguridad

1. Se detectó que el repo tenía un `.gitignore` que excluía todo el código generado
2. Se verificó el entorno (Python 3.11, dependencias)
3. Se crearon las carpetas necesarias: `agent/`, `config/`, `knowledge/`, `tests/`
4. Se instalaron todas las dependencias de Python
5. Se preparó el `.env` base

### Sesión 2 — Onboarding completo de HELIX · AI

**Entrevista del negocio (respuestas recopiladas):**

- Nombre: HELIX · AI — Agencia de Crecimiento Digital e IA
- Descripción: Agencia de automatización con IA para empresas B2B, e-commerce y consultorías
- Casos de uso: Ventas, agendamiento de citas, soporte, FAQ, auditoría de crecimiento
- Nombre del agente: Sofía
- Tono: Amigable y empático
- Horario: Lunes a viernes 8:00 a 18:00 hs
- Proveedor WhatsApp: Twilio

**Credenciales configuradas:**
- Anthropic API Key: guardada en `.env` (nunca en el repo)
- Twilio Account SID: guardado en `.env`
- Twilio Auth Token: guardado en `.env`
- Twilio Phone Number: `+16083524676`

**Archivos generados:**

- `config/business.yaml` — perfil del negocio
- `config/prompts.yaml` — system prompt con identidad de Sofía, servicios de HELIX · AI, reglas de seguridad
- Todo el código en `agent/`
- Tests de seguridad (20 tests, todos pasaron)
- `.gitignore` reemplazado por versión de producción (incluye `agent/`, `config/`, etc.)

**Deploy:**

- Merge a `main` → Railway detectó el push y deployó automáticamente
- Error inicial: `DATABASE_URL` apuntaba a `./agentkit.db` (sin permisos en Railway)
- Fix: cambiar `DATABASE_URL` a `sqlite+aiosqlite:////tmp/agentkit.db`
- Deploy exitoso — servicio Online en `whatsapp-agentkit-production-2eb4.up.railway.app`
- Variables de entorno cargadas en Railway (ANTHROPIC_API_KEY, WHATSAPP_PROVIDER, TWILIO_*)

**Humanización del agente:**

- System prompt actualizado: prohibido markdown, bullets, listas, firmas, guiones largos
- Estilo conversacional: informal, muletillas, máximo 2-3 oraciones por mensaje
- Delay humano antes de responder: entre 2 y 8 segundos según largo del mensaje
- Split automático de respuestas largas en múltiples mensajes con pausa entre ellos

---

## Montar esto de cero — paso a paso

### Prerequisitos

- Python 3.11 instalado (`python3 --version`)
- Cuenta en GitHub
- Cuenta en Anthropic (platform.anthropic.com) con API key
- Cuenta en Twilio (twilio.com) con sandbox de WhatsApp activado
- Cuenta en Railway (railway.app)

### Paso 1 — Clonar y preparar el repo

```bash
git clone https://github.com/Jon-human-in-the-loop/whatsapp-agentkit.git
cd whatsapp-agentkit
mkdir -p agent/providers config knowledge tests
pip install -r requirements.txt
cp .env.example .env
```

### Paso 2 — Configurar el .env

Editar `.env` con los valores reales:

```env
ANTHROPIC_API_KEY=sk-ant-...
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
TWILIO_VALIDATE_SIGNATURE=false   # false para pruebas locales
PORT=8000
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./agentkit.db
```

### Paso 3 — Personalizar el agente

Editar `config/business.yaml` con los datos del negocio del cliente.

Editar `config/prompts.yaml` con:
- Nombre del agente
- Descripción del negocio
- Servicios y precios
- Horario de atención
- Tono y personalidad

### Paso 4 — Probar localmente

```bash
# Tests de seguridad
python3 -m pytest tests/test_security.py -v

# Chat en terminal (simula WhatsApp sin necesitar número real)
python tests/test_local.py
```

### Paso 5 — Deploy en Railway

1. Subir el código a GitHub (`git add . && git commit -m "..." && git push origin main`)
2. Ir a railway.app → New Project → Deploy from GitHub repo
3. Seleccionar el repo
4. En Variables, agregar todas las del `.env` (excepto DATABASE_URL si se usa PostgreSQL de Railway)
5. Cambiar `ENVIRONMENT=production` y `TWILIO_VALIDATE_SIGNATURE=true`
6. Railway hace el build y deploy automáticamente
7. Copiar la URL pública que asigna Railway (ej: `mi-agente.up.railway.app`)

### Paso 6 — Configurar webhook en Twilio

1. Ir a Twilio Console → Messaging → Try it Out → Send a WhatsApp message
2. En "Sandbox Settings", campo "When a message comes in":
   ```
   https://mi-agente.up.railway.app/webhook
   ```
3. Método: HTTP POST → Guardar
4. Mandar un mensaje al número de sandbox desde WhatsApp → el agente responde

---

## Lo que falta para estar 100% en producción y vender a un cliente

### Crítico (sin esto no funciona bien en producción)

**1. Número de WhatsApp real (no sandbox)**

El sandbox de Twilio solo permite mensajes a números verificados manualmente. Para clientes reales se necesita:
- Twilio WhatsApp Business API (requiere aprobación de Meta, tarda 1-7 días)
- O migrar a Meta Cloud API directamente (gratis por conversación, requiere cuenta de Facebook Business verificada)

**2. Base de datos persistente**

El SQLite en `/tmp` en Railway se borra cada vez que el servidor se reinicia. Los clientes pierden el historial de conversación.

Solución: agregar PostgreSQL en Railway (un clic) y cambiar `DATABASE_URL` al que Railway provee automáticamente. El código ya está preparado para esto.

**3. Validación de firma Twilio**

Si `TWILIO_VALIDATE_SIGNATURE=true` está activo y el agente corre detrás del proxy de Railway, la validación puede fallar porque la URL firmada por Twilio no coincide con la que ve el servidor.

Solución: agregar en `agent/providers/twilio.py` el header `X-Forwarded-Proto` para reconstruir la URL correcta, o deshabilitar temporalmente la validación hasta confirmar que funciona.

### Importante (mejora la experiencia)

**4. Manejo de medios (imágenes, audios, documentos)**

Actualmente el agente solo procesa texto. Los clientes por WhatsApp suelen mandar fotos de productos, audios, PDFs. Hay que agregar manejo de estos tipos en `parsear_webhook`.

**5. Escalamiento a humano**

Cuando el agente no puede resolver algo, debería notificar a un humano (por email, Slack o Notion). Se puede agregar una herramienta en `agent/tools.py`.

**6. Panel de conversaciones**

Para que el cliente pueda ver qué le preguntan a su agente, necesita algún tipo de dashboard. Opciones simples: Notion, Airtable, o una tabla en la misma base de datos con una interfaz.

**7. Monitoreo y alertas**

Si el agente cae o da error, nadie se entera. Agregar Sentry o al menos un webhook de alerta a Slack/email cuando hay errores 500.

### Opcional (para escalar el producto)

**8. Multiples clientes / multitenancy**

Si se va a vender a varios clientes, el sistema actual sirve para uno solo. Para múltiples clientes se necesita una arquitectura multi-tenant con una instancia por cliente o un sistema de routing por número de teléfono.

**9. Knowledge base dinámica**

Actualmente el agente solo busca en archivos de texto en `/knowledge`. Para clientes con catálogos grandes o precios que cambian, se puede conectar a una base de vectores (Pinecone, Supabase Vector) para búsqueda semántica.

**10. Métricas de uso**

Cuántos mensajes se procesan, cuánto cuesta por cliente, cuáles son las preguntas más frecuentes. Importante para cobrar y para mejorar el agente.

---

## Checklist de lanzamiento para un cliente nuevo

- [ ] Datos del negocio recopilados (nombre, descripción, servicios, precios, horario)
- [ ] `config/business.yaml` y `config/prompts.yaml` personalizados
- [ ] Archivos del negocio en `/knowledge` (menú, FAQ, catálogo)
- [ ] Tests locales pasando (`python tests/test_local.py`)
- [ ] Número de WhatsApp real aprobado por Meta/Twilio
- [ ] PostgreSQL configurado en Railway (no SQLite en /tmp)
- [ ] Variables de entorno en Railway completas y correctas
- [ ] `ENVIRONMENT=production` en Railway
- [ ] `TWILIO_VALIDATE_SIGNATURE=true` funcionando correctamente
- [ ] Webhook configurado en Twilio apuntando a la URL de Railway
- [ ] Test end-to-end: mensaje real desde WhatsApp → respuesta del agente
- [ ] Monitoreo de errores configurado (Sentry o similar)
- [ ] Cliente entrenado: cómo ver las conversaciones, cómo escalar a humano

---

## Comandos útiles

```bash
# Correr localmente
uvicorn agent.main:app --reload --port 8000

# Chat de prueba sin WhatsApp
python tests/test_local.py

# Tests de seguridad
python3 -m pytest tests/test_security.py -v

# Build Docker local
docker compose up --build

# Ver logs en Railway
# Railway dashboard → tu servicio → View logs

# Subir cambios y hacer deploy
git add .
git commit -m "descripción del cambio"
git push origin main
# Railway detecta el push y hace deploy automático
```

---

## URLs importantes

- Agente en producción: `https://whatsapp-agentkit-production-2eb4.up.railway.app`
- Webhook URL para Twilio: `https://whatsapp-agentkit-production-2eb4.up.railway.app/webhook`
- Repo GitHub: `https://github.com/Jon-human-in-the-loop/whatsapp-agentkit`
- Railway dashboard: `https://railway.app`
- Twilio Console: `https://console.twilio.com`
- Anthropic API Keys: `https://platform.anthropic.com/settings/api-keys`
