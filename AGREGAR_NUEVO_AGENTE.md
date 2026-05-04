# Cómo agregar un nuevo agente — Guía rápida

Este repositorio soporta **múltiples agentes en un solo repo**. Aquí te mostramos cómo agregar uno nuevo.

---

## ⚡ Pasos rápidos (5 minutos)

### 1️⃣ Crear carpetas para el nuevo agente

```bash
mkdir -p config/nombre-negocio
mkdir -p knowledge/nombre-negocio
touch knowledge/nombre-negocio/.gitkeep
```

(Reemplaza `nombre-negocio` con el nombre real, ej: `clínica-dental`, `tienda-repuestos`, etc.)

---

### 2️⃣ Crear archivos de configuración

#### `config/nombre-negocio/business.yaml`

Copia y adapta este template:

```yaml
# Configuración del negocio
negocio:
  nombre: Tu Negocio
  descripcion: |
    Describe qué hace tu negocio aquí.
    Ejemplo: Somos una tienda de repuestos para autos...
  horario: "Lunes a Viernes 9am a 6pm, Sábados 10am a 2pm"
  ubicacion: "Tu ubicación"

agente:
  nombre: NombreBot
  tono: empático y cálido  # opciones: profesional, amigable, vendedor, empático
  casos_de_uso:
    - Responder preguntas frecuentes
    - Agendar citas
    - Tomar pedidos
    - Soporte post-venta

metadata:
  creado: 2026-03-28
  version: "1.0"
```

---

#### `config/nombre-negocio/prompts.yaml`

Copia y adapta el prompt desde `config/mundo-electronico/prompts.yaml`:

```yaml
system_prompt: |
  Eres [NombreBot], el asistente virtual de [Tu Negocio].

  ## Tu identidad
  - Te llamas [NombreBot]
  - Representas a [Tu Negocio]
  - Tu tono es [empático, cálido, etc.]

  ## Sobre el negocio
  [Descripción completa de qué hace tu negocio]

  ## Tus capacidades
  [Lista de qué puede hacer]

  ## Horario de atención
  [Tu horario]

  ## Reglas de comportamiento
  - SIEMPRE responde en español
  - Sé empático en cada mensaje
  - Si no sabes algo, di: "No tengo esa información, pero déjame conectarte con alguien que pueda ayudarte"
  - NUNCA inventes datos que no tengas confirmados

fallback_message: "Disculpa, no entendí tu mensaje. ¿Podrías reformularlo?"
error_message: "Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos minutos."
```

---

### 3️⃣ Agregar archivos de conocimiento (opcional)

Si tu negocio tiene documentos especiales (FAQ, precios, catálogo), colócalos en:

```
knowledge/nombre-negocio/
├── precios.txt
├── faq.md
├── politicas.txt
└── catalogo.pdf
```

El agente buscará automáticamente en estos archivos cuando responda.

---

### 4️⃣ Probar localmente

Antes de desplegar, prueba el agente en tu máquina:

```bash
# Establecer el agente activo
export AGENTE_ACTIVO=nombre-negocio

# Ejecutar test local
python tests/test_local.py
```

Escribe mensajes como si fueras un cliente. Si todo funciona, continúa al paso 5.

---

### 5️⃣ Hacer commit y push a GitHub

```bash
git add -A
git commit -m "feat: nuevo agente para nombre-negocio"
git push origin main
```

---

### 6️⃣ Desplegar en Railway

1. Ve a **railway.app** → Tu proyecto
2. Click **"New Service"** o **"Add Service"**
3. Selecciona el repo `whatsapp-agente` (el mismo)
4. En **Variables**, establece:
   ```
   AGENTE_ACTIVO=nombre-negocio
   WHATSAPP_PROVIDER=whapi
   WHAPI_TOKEN=tu-token-de-whapi
   ANTHROPIC_API_KEY=tu-key-de-anthropic
   PORT=8000
   ENVIRONMENT=production
   ```
5. Click **Deploy**
6. Espera 2-3 minutos
7. Copia la URL pública que te asigne Railway

---

### 7️⃣ Configurar webhook en Whapi.cloud

1. Ve a **whapi.cloud** → **Settings** → **Webhooks**
2. En **Webhook URL**, pega:
   ```
   https://tu-url-de-railway.up.railway.app/webhook
   ```
3. Método: **POST**
4. Activa el webhook
5. ¡Listo! El agente está en producción

---

## 📁 Estructura final

```
whatsapp-agente/
├── config/
│   ├── mundo-electronico/
│   │   ├── business.yaml
│   │   └── prompts.yaml
│   └── nombre-negocio/           ← TU NUEVO AGENTE
│       ├── business.yaml
│       └── prompts.yaml
├── knowledge/
│   ├── mundo-electronico/
│   └── nombre-negocio/           ← TU NUEVO AGENTE
│       ├── precios.txt (opcional)
│       └── .gitkeep
└── ...
```

---

## 🎯 Checklist antes de desplegar

- [ ] ✅ Carpetas creadas: `config/nombre-negocio/` y `knowledge/nombre-negocio/`
- [ ] ✅ Archivos creados: `business.yaml` y `prompts.yaml`
- [ ] ✅ El agente responde bien en `python tests/test_local.py`
- [ ] ✅ Commit y push a GitHub
- [ ] ✅ Nuevo servicio en Railway con `AGENTE_ACTIVO=nombre-negocio`
- [ ] ✅ Webhook configurado en Whapi.cloud
- [ ] ✅ Probaste desde WhatsApp real

---

## ❓ Preguntas frecuentes

**P: ¿Puedo tener múltiples agentes en un solo servicio de Railway?**
R: No. Un servicio = un `AGENTE_ACTIVO`. Si quieres 2 agentes, necesitas 2 servicios (ambos desde el mismo repo).

**P: ¿Cómo cambio la configuración de un agente que ya está en producción?**
R:
1. Edita `config/nombre-negocio/prompts.yaml` o `business.yaml`
2. Haz commit: `git add . && git commit -m "update: config para nombre-negocio"`
3. Push: `git push origin main`
4. Railway redeploy automáticamente en 1-2 minutos

**P: ¿Los historiales de cada agente están separados?**
R: Sí. Cada agente tiene su propia base de datos en `data/nombre-negocio/agentkit.db`

**P: ¿Puedo usar PostgreSQL en lugar de SQLite?**
R: Sí. En Railway, establece:
```
DATABASE_URL=postgresql+asyncpg://usuario:password@host:5432/database
```

---

## 🚀 Ejemplo completo

Para un nuevo negocio "Tienda Deportiva":

```bash
# 1. Crear carpetas
mkdir -p config/tienda-deportiva knowledge/tienda-deportiva
touch knowledge/tienda-deportiva/.gitkeep

# 2. Crear business.yaml y prompts.yaml en config/tienda-deportiva/

# 3. Probar localmente
export AGENTE_ACTIVO=tienda-deportiva
python tests/test_local.py

# 4. Guardar
git add .
git commit -m "feat: nuevo agente para Tienda Deportiva"
git push origin main

# 5. En Railway: nuevo servicio con AGENTE_ACTIVO=tienda-deportiva
```

¡Listo! Tu nuevo agente está en producción. 🎊
