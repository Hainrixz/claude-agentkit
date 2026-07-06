# AgentKit — WhatsApp AI Agent Builder

Construye tu propio agente de WhatsApp con inteligencia artificial en menos de 30 minutos.
No necesitas saber programar. Claude Code construye todo por ti.

<!-- ![AgentKit Demo](demo.gif) -->

---

## Que es AgentKit?

AgentKit es un proyecto que usa **Claude Code** (la herramienta de programacion de Anthropic)
para generar un agente de WhatsApp completo y personalizado para tu negocio.

Tu solo respondes preguntas sobre tu negocio. Claude Code se encarga de:
- Escribir todo el codigo
- Configurar la conexion con WhatsApp
- Crear un "cerebro" con IA que sabe sobre tu negocio
- Dejarlo listo para que tus clientes le escriban

---

## Como funciona? (El flujo completo)

### Paso 1: Tu clonas el repo y corres un comando

```bash
git clone https://github.com/Hainrixz/whatsapp-agentkit.git
cd whatsapp-agentkit
bash start.sh
```

`start.sh` solo verifica que tengas Python 3.11+ y Claude Code instalados.

### Paso 2: Abres Claude Code y escribes /build-agent

```bash
claude
# Dentro de Claude Code escribe:
/build-agent
```

Esto activa el sistema. Claude Code lee las instrucciones de `CLAUDE.md` y empieza
a guiarte paso a paso.

### Paso 3: Claude Code te entrevista (5 minutos)

Te hace 11 preguntas, una por una:

1. **Nombre de tu negocio** — ej: "Cafeteria El Buen Sabor"
2. **A que se dedica** — ej: "Vendemos cafe de especialidad y postres artesanales"
3. **Para que quieres el agente** — responder preguntas, agendar citas, tomar pedidos, etc.
4. **Nombre del agente** — ej: "Sofia" (el nombre que veran tus clientes)
5. **Tono de comunicacion** — profesional, amigable, vendedor, o empatico
6. **Horario de atencion** — ej: "Lunes a Viernes 9am a 6pm"
7. **Archivos de tu negocio** — menu, precios, FAQ (los pones en la carpeta /knowledge)
8. **API Key de Anthropic** — la llave para usar Claude AI (te guia a obtenerla)
9. **Proveedor de WhatsApp** — eliges entre Meta o Twilio
10. **Credenciales del proveedor** — el token o keys de tu servicio de WhatsApp
11. **Busqueda web (opcional)** — si quieres que el agente busque info actualizada en internet con You.com

### Paso 4: Claude Code construye tu agente (2-5 minutos)

Con tus respuestas, genera automaticamente estos archivos:

```
tu-proyecto/
├── agent/                     ← EL AGENTE COMPLETO
│   ├── main.py                Servidor web que recibe mensajes de WhatsApp
│   ├── brain.py               Conexion con Claude AI (el cerebro)
│   ├── memory.py              Guarda el historial de cada cliente
│   ├── tools.py               Herramientas especificas de tu negocio
│   └── providers/             Conexion con tu servicio de WhatsApp
│       ├── base.py            Interfaz comun
│       ├── __init__.py        Selecciona el proveedor automaticamente
│       └── twilio.py          Adaptador (o meta.py)
│
├── config/                    ← CONFIGURACION
│   ├── business.yaml          Datos de tu negocio
│   └── prompts.yaml           El "prompt" que define la personalidad del agente
│
├── knowledge/                 ← TUS ARCHIVOS
│   └── (menu.pdf, precios.txt, etc.)
│
├── tests/
│   └── test_local.py          Simulador de chat en tu terminal
│
├── requirements.txt           Dependencias de Python
├── Dockerfile                 Para produccion
├── docker-compose.yml         Orquestacion
└── .env                       Tus API keys (seguro, nunca se sube)
```

### Paso 5: Pruebas tu agente en la terminal (5 minutos)

Claude Code ejecuta un simulador de chat donde TU escribes como si fueras un cliente:

```
Tu: Hola, que horarios tienen?
Agente: Hola! Nuestro horario es de Lunes a Viernes de 9am a 6pm.
        Quieres que te ayude con algo mas?

Tu: Cuanto cuesta el cafe americano?
Agente: El cafe americano tiene un precio de $45 pesos.
        Te gustaria ordenar uno?
```

Si algo no te gusta, le dices a Claude Code y lo ajusta al momento.

### Paso 6: Deploy a produccion (opcional, 10 minutos)

Cuando estes satisfecho con tu agente, Claude Code te guia para ponerlo en linea:

1. **Claude Code prepara tu proyecto** para produccion (ajusta configuracion)
2. **Tu lo subes a GitHub** — Claude Code te da los comandos exactos para crear tu repo
3. **Conectas Railway** — entras a [railway.app](https://railway.app), le das tu repo de GitHub y Railway lo deployea automaticamente
4. **Configuras las variables** — Claude Code te dice exactamente cuales poner en Railway (las mismas API keys de tu .env)
5. **Configuras el webhook** — Claude Code te guia para conectar tu proveedor de WhatsApp con la URL de Railway

Despues de esto, cualquier persona que te escriba por WhatsApp sera atendida por tu agente.

**Nota:** No necesitas saber de servidores ni de deploy. Claude Code te dice cada paso, que escribir y donde hacer click.

---

## Como funciona el agente ya en produccion?

```
Un cliente escribe "Hola" por WhatsApp
         |
         v
Tu proveedor de WhatsApp (Meta/Twilio) recibe el mensaje
         |
         v
Envia el mensaje a tu servidor en Railway via webhook
         |
         v
agent/providers/ → Normaliza el mensaje (cada proveedor tiene formato diferente)
         |
         v
agent/memory.py → Busca el historial de ESE cliente (por numero de telefono)
         |
         v
agent/brain.py → Envia a Claude AI:
                 - El system prompt (personalidad + info de tu negocio)
                 - El historial de la conversacion
                 - El mensaje nuevo del cliente
         |
         v
Claude AI genera una respuesta inteligente
         |
         v
agent/providers/ → Envia la respuesta de vuelta por WhatsApp
         |
         v
El cliente recibe la respuesta en segundos
```

**Cosas importantes:**
- Cada cliente tiene su propio historial. Si alguien habla contigo y vuelve al dia siguiente, el agente recuerda la conversacion anterior.
- El agente NUNCA inventa informacion. Solo responde con lo que tu le diste.
- Si no sabe algo, responde: "No tengo esa informacion, dejame conectarte con alguien del equipo."

---

## Requisitos previos

Necesitas 4 cosas antes de empezar:

### 1. Python 3.11 o superior
- **Mac**: `brew install python` o descarga de [python.org](https://python.org/downloads)
- **Windows**: Descarga de [python.org](https://python.org/downloads) (marca "Add to PATH")
- **Linux**: `sudo apt install python3.11`
- Verifica: `python3 --version`

### 2. Claude Code
```bash
# Primero necesitas Node.js: https://nodejs.org
npm install -g @anthropic-ai/claude-code

# Autenticate (solo la primera vez)
claude
```

### 3. API Key de Anthropic
1. Ve a [platform.anthropic.com](https://platform.anthropic.com/settings/api-keys)
2. Crea una cuenta o inicia sesion
3. Ve a Settings → API Keys → Create Key
4. Copia la key (empieza con `sk-ant-...`)

### 4. Cuenta de WhatsApp API (elige una)

| Proveedor | Dificultad | Costo | Mejor para |
|-----------|-----------|-------|------------|
| [Twilio](https://twilio.com) | Media | Sandbox gratis / Pago por mensaje | Empezar rapido, probar, empresas |
| [Meta Cloud API](https://developers.facebook.com) | Media | Gratis por conversacion | Produccion seria |

**Si solo quieres probar rapido**, Twilio tiene sandbox gratis y no requiere verificacion. Para produccion seria, considera Meta Cloud API.

---

## Inicio rapido (3 comandos)

```bash
# 1. Clona el repositorio
git clone https://github.com/Hainrixz/whatsapp-agentkit.git
cd whatsapp-agentkit

# 2. Verifica tu entorno
bash start.sh

# 3. Abre Claude Code y construye tu agente
claude
# Escribe: /build-agent
```

Claude Code te guia desde ahi. Solo responde las preguntas.

---

## Proveedores de WhatsApp

AgentKit soporta 2 proveedores. Tu eliges cual usar durante el setup.

### Twilio (recomendado para empezar)
- Registrate en [twilio.com](https://twilio.com)
- Sandbox gratuito sin verificacion (ideal para probar)
- Muy confiable, excelente documentacion
- Necesitas: **Account SID** + **Auth Token** + **Phone Number**
- Pago por mensaje en produccion

### Meta Cloud API (oficial)
- Configura en [developers.facebook.com](https://developers.facebook.com)
- Es la API oficial de WhatsApp (de Meta/Facebook)
- Necesitas: **Access Token** + **Phone Number ID** + **Verify Token**
- Requiere cuenta de Facebook Business verificada
- Gratis por conversacion (pagas solo por conversaciones iniciadas por ti)

---

## Casos de uso

| Tipo de negocio | Que hace el agente | Ejemplo |
|-----------------|-------------------|---------|
| **Restaurante** | Responde sobre menu, horarios, ubicacion | "El platillo del dia es..." |
| **Clinica/Salon** | Agenda citas y reservaciones | "Tu cita quedo para el martes a las 3pm" |
| **Inmobiliaria** | Califica leads y envia info de propiedades | "Tenemos 3 departamentos en tu rango..." |
| **Tienda online** | Toma pedidos por WhatsApp | "Tu pedido de 2 pasteles quedo confirmado" |
| **SaaS/Software** | Soporte tecnico post-venta | "Para resetear tu contrasena, sigue estos pasos..." |
| **Cualquier negocio** | Responde preguntas frecuentes 24/7 | "Nuestro horario es..." |

---

## Comandos utiles (despues del setup)

```bash
# Probar el agente sin WhatsApp (chat en terminal)
python tests/test_local.py

# Arrancar el servidor localmente
uvicorn agent.main:app --reload --port 8000

# Build Docker para produccion
docker compose up --build

# Ver logs del agente
docker compose logs -f agent
```

---

## Personalizar tu agente despues

No necesitas tocar codigo. Abre Claude Code y pidele cambios en lenguaje natural:

```bash
# Cambiar como responde el agente
claude "El agente esta siendo muy formal. Hazlo mas amigable y casual."

# Agregar informacion nueva
claude "Agregamos un nuevo servicio de delivery. Actualiza el agente."

# Agregar una herramienta
claude "Quiero que el agente pueda consultar disponibilidad de citas."

# Cambiar de proveedor de WhatsApp
claude "Quiero migrar de Twilio a Meta Cloud API."
```

---

## Stack tecnico

Para los curiosos, esto es lo que se usa por debajo:

| Componente | Tecnologia | Para que sirve |
|-----------|-----------|----------------|
| IA | Claude AI (claude-sonnet-4-6) | Genera las respuestas inteligentes |
| Busqueda web (opcional) | You.com Search API | El agente busca info actualizada (precios, clima, noticias) cuando tu conocimiento de negocio no alcanza |
| Servidor | FastAPI + Uvicorn | Recibe los webhooks de WhatsApp |
| WhatsApp | Meta / Twilio | Conecta con WhatsApp (tu eliges) |
| Base de datos | SQLite (local) / PostgreSQL (prod) | Guarda historial de conversaciones |
| Deploy | Docker + Railway | Pone tu agente en internet |
| Config | python-dotenv + YAML | Maneja API keys y configuracion |

---

## Arquitectura (para desarrolladores)

```
WhatsApp (cliente)
    |
    v
Proveedor (Meta/Twilio) ←→ agent/providers/ (normaliza formato)
    |
    v
FastAPI (agent/main.py) ←→ agent/memory.py (historial SQLite)
    |
    v
Claude API (agent/brain.py) ←→ config/prompts.yaml (personalidad)
    |
    v
Respuesta enviada de vuelta por WhatsApp
```

El sistema usa un **patron adaptador** para proveedores de WhatsApp. Cada proveedor
(Meta, Twilio) implementa la misma interfaz, asi que `main.py` no sabe ni le
importa cual estas usando. Solo llama `proveedor.parsear_webhook()` y
`proveedor.enviar_mensaje()`.

---

## Preguntas frecuentes

**Necesito saber programar?**
No. Claude Code escribe todo el codigo por ti. Tu solo respondes preguntas.

**Cuanto cuesta?**
- AgentKit es gratis y open source
- Claude API: pagas por uso (~$3/millon de tokens, muy barato para un bot)
- WhatsApp: depende del proveedor (Twilio tiene sandbox gratis para probar)
- Railway: plan gratis disponible para proyectos pequenos

**Puedo usar esto con mi negocio real?**
Si. Despues de las pruebas locales, lo subes a Railway y cualquier cliente
que te escriba por WhatsApp sera atendido por tu agente.

**Y si el agente no sabe algo?**
Responde algo como: "No tengo esa informacion, dejame conectarte con alguien
de nuestro equipo." Nunca inventa datos.

**Puedo tener multiples agentes?**
Si. Clona el repo varias veces, uno por negocio. Cada agente es independiente.

**Puedo cambiar de proveedor de WhatsApp despues?**
Si. Abre Claude Code y dile: "Quiero cambiar de Twilio a Meta Cloud API."
El regenerara los archivos necesarios.

---

## Creditos

Creado por **Todo de IA** — [@soyenriquerocha](https://instagram.com/soyenriquerocha)

Construido con [Claude Code](https://claude.ai/claude-code) para builders de LATAM.

---

## Licencia

MIT — Usa este proyecto como quieras, para lo que quieras.
