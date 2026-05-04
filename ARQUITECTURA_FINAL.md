# Arquitectura Final — AgentKit + RIWEB.APP

## Visión General

Tienes **dos dashboards complementarios**:

1. **`/admin` (AgentKit)** — Gestión rápida de tickets para operadores
2. **RIWEB.APP dashboard** — Gestión comercial (clientes, pagos, analítica)

Ambos leen/escriben en la **misma Supabase**, así la data está centralizada y sincronizada.

---

## Flujo de Datos

```
CLIENTE VÍA WHATSAPP
    ↓
AgentKit (FastAPI) — Webhook de Whapi/Meta/Twilio
    ├─ Identifica al cliente por teléfono
    ├─ Lee su configuración desde Supabase (ai_prompts)
    ├─ Genera respuesta con Claude
    ├─ Guarda conversación en Supabase (conversations)
    ├─ Si agenda cita: crea ticket en Supabase (tickets)
    └─ Envía respuesta por WhatsApp

                        ↓

SUPABASE (DB centralizada)
    ├─ clients → quiénes son tus clientes
    ├─ ai_prompts → config de cada bot
    ├─ conversations → historial de chats
    ├─ tickets → citas/reparaciones agendadas
    └─ bot_leads → leads capturados

                        ↓

DOS FORMAS DE ACCEDER A LOS DATOS:

1. /admin (localhost:8000/admin) — para operadores
   - Ver todos los tickets en tiempo real
   - Cambiar estado (abierto → en_progreso → completado)
   - Agregar notas
   - Acceso rápido, UI simple

2. RIWEB.APP dashboard — para administración
   - Ver clientes, pagos, suscripciones
   - Analytics de bots (mensajes/mes, conversión)
   - Gestionar tickets si quieren
   - Dashboard profesional para el negocio
```

---

## Tablas en Supabase

### `clients`
```
id (UUID)
name (TEXT)                    — "Mundo Electronico"
business_type (TEXT)          — "reparación de celulares"
whatsapp (TEXT)               — número del dueño para el bot
active (BOOLEAN)
created_at (TIMESTAMPTZ)
```

### `ai_prompts`
```
id (UUID)
client_id (UUID)              — FK a clients
system_prompt (TEXT)          — instrucciones para Claude
tone (TEXT)                   — "amigable", "profesional", etc
business_type (TEXT)
objective (TEXT)              — "ventas", "soporte", etc
active (BOOLEAN)
created_at, updated_at (TIMESTAMPTZ)
```

### `conversations`
```
id (UUID)
client_id (UUID)              — FK a clients
telefono (TEXT)               — número del cliente
role (TEXT)                   — "user" o "assistant"
content (TEXT)                — mensaje
created_at (TIMESTAMPTZ)
```

### `tickets`
```
id (UUID)
client_id (UUID)              — FK a clients
ticket_numero (TEXT UNIQUE)   — "MUN-20260328-001"
nombre_cliente (TEXT)
telefono (TEXT)
dispositivo (TEXT)            — "iPhone 14 pantalla rota"
problema (TEXT)
estado (TEXT)                 — "abierto", "en_progreso", "completado", "cerrado"
notas (TEXT)
agente (TEXT)
fecha_creacion (TIMESTAMPTZ)
fecha_actualizacion (TIMESTAMPTZ)
```

### `bot_leads`
```
id (UUID)
client_id (UUID)              — FK a clients
name (TEXT)
phone (TEXT)
message (TEXT)
created_at (TIMESTAMPTZ)
```

---

## Cómo Funciona Paso a Paso

### Cuando un Cliente Manda Mensaje por WhatsApp

```
1. Llega webhook a AgentKit (/webhook POST)
   ├─ Whapi / Meta / Twilio normaliza el formato
   └─ MensajeEntrante(telefono="549...", texto="...", mensaje_id="...")

2. AgentKit identifica al cliente
   └─ Busca en Supabase.clients dónde whatsapp = telefono
   └─ client_id = UUID del cliente

3. Lee configuración del bot
   └─ SELECT * FROM ai_prompts WHERE client_id = UUID
   └─ Obtiene: system_prompt, tone, objetivo

4. Obtiene historial
   └─ SELECT * FROM conversations
      WHERE client_id = UUID AND telefono = "549..."
      ORDER BY created_at DESC LIMIT 20

5. Llama Claude API
   └─ system_prompt (del cliente, desde Supabase)
   └─ historial (conversaciones previas)
   └─ mensaje actual

6. Claude responde
   └─ Si incluye [CITA]datos[/CITA], crea ticket:
      - INSERT INTO tickets (client_id, ticket_numero, ...)
   └─ Respuesta se limpia (elimina tags) para el cliente

7. Guarda conversación
   └─ INSERT INTO conversations (client_id, telefono, "user", texto)
   └─ INSERT INTO conversations (client_id, telefono, "assistant", respuesta)

8. Envía por WhatsApp
   └─ Via Whapi / Meta / Twilio
```

### Cuando Abres `/admin`

```
1. GET /admin
   ├─ ¿Tiene sesión válida? (cookie admin_session)
   └─ No → mostrar login
   └─ Sí → continuar

2. Obtener tickets
   └─ SELECT * FROM tickets ORDER BY fecha_creacion DESC LIMIT 100

3. Mostrar tabla
   ├─ Ticket número
   ├─ Cliente (nombre, teléfono)
   ├─ Dispositivo + problema
   ├─ Estado (dropdown para cambiar)
   ├─ Fecha creación
   └─ Botón "Notas"

4. Cambiar estado
   └─ POST /admin/actualizar {id, estado: "en_progreso"}
   └─ UPDATE tickets SET estado='en_progreso' WHERE id=...

5. Agregar notas
   └─ POST /admin/actualizar {id, notas: "..."}
   └─ UPDATE tickets SET notas='...' WHERE id=...
```

### Cuando RIWEB.APP Accede a los Datos

```
1. Mostrar clientes
   └─ SELECT * FROM clients (tabla que maneja RIWEB)

2. Ver tickets de un cliente
   └─ SELECT * FROM tickets WHERE client_id = UUID

3. Analytics
   └─ SELECT COUNT(*) FROM conversations WHERE client_id=UUID
   └─ SELECT COUNT(*) FROM tickets WHERE estado='completado'
   └─ Calcular mensajes/mes, tasa de conversión, etc

4. Gestionar bot
   └─ UPDATE ai_prompts SET system_prompt='...' WHERE client_id=UUID
   └─ Cambiar tono, objetivo, instrucciones
```

---

## Ventajas de Esta Arquitectura

✅ **Una sola DB** — Supabase es fuente de verdad
✅ **Dos UIs especializadas** — Admin (rápido), RIWEB (comercial)
✅ **Multi-cliente** — Cada cliente = config + bot + tickets aislados
✅ **Sin sincronización** — Ambos dashboards leen de la misma DB
✅ **Escalable** — Agregar clientes es solo INSERT en `clients` + `ai_prompts`
✅ **Seguro** — RLS en Supabase para aislar datos por cliente (si lo necesitas)

---

## Próximos Pasos

### 1. Poblar Supabase con un Cliente de Prueba

```sql
-- Crear cliente
INSERT INTO clients (name, business_type, whatsapp, active)
VALUES ('Mundo Electronico', 'reparación', '549...número...', true)
RETURNING id;  -- Copiar este ID

-- Crear config del bot
INSERT INTO ai_prompts (client_id, system_prompt, tone, objective, active)
VALUES (
  'UUID-DEL-CLIENTE-ANTERIOR',
  'Eres Mundo Bot...',  -- tu system prompt
  'amigable',
  'ventas',
  true
);
```

### 2. Probar con WhatsApp Real
- Envía mensaje desde tu número
- El bot debería identificarte y usar tu config

### 3. Agregar a RIWEB.APP
- Dashboard para crear/editar clientes
- API para sincronizar pagos ↔ active en clients table
- Analytics de bots

---

## Configuración Actual

**En `.env`:**
```
ANTHROPIC_API_KEY=sk-ant-...
WHATSAPP_PROVIDER=whapi
WHAPI_TOKEN=...

SUPABASE_URL=https://xeqbapfjosgchkhqwzsh.supabase.co
SUPABASE_KEY=eyJhbGc...

ADMIN_PASSWORD=admin123
AGENTE_ACTIVO=mundo-electronico  # Para fallback local si quieren
```

**En código:**
- `agent/supabase_client.py` — Cliente de Supabase (conexión centralizada)
- `agent/brain.py` — Lee config desde Supabase
- `agent/memory.py` — Lee/escribe en Supabase (fallback SQLite)
- `agent/main.py` — Webhook que identifica cliente y usa su config
- `agent/admin.py` — Dashboard conectado a Supabase

---

## Diagrama Resumido

```
                    SUPABASE
                  (DB Central)
                    ↗     ↖
                   /       \
                  /         \
            AGENTKIT      RIWEB.APP
         (Ejecución)    (Dashboard)
              ↑              ↑
            🤖            👤
         Responde       Administra
```

---

## Seguridad

- `/admin` protegido con contraseña simple (cambiar en ADMIN_PASSWORD)
- Supabase con RLS enabled pero permisivo (solo admin puede acceder)
- Tokens en .env (NUNCA a GitHub)
- Service Role Key en SUPABASE_KEY (acceso total a la DB)

Si quieres RLS más estricto (cliente A no vea tickets de B), avísame.
