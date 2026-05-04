# Schema de Supabase — Estructura Completa
**Con soporte para Planes, Pagos y Extras**

---

## Tablas

### 1. `clients` (Actualizada)
Clientes y su información de suscripción

```sql
CREATE TABLE IF NOT EXISTS clients (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- Información básica
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  business_type TEXT,
  whatsapp TEXT,

  -- Plan
  plan TEXT DEFAULT 'starter',  -- 'starter', 'pro', 'custom'

  -- Precios
  precio_base NUMERIC(10,2),     -- 65 o 120
  precio_total NUMERIC(10,2),    -- incluyendo extras

  -- Pagos
  estado_pago TEXT DEFAULT 'pending',  -- 'pending', 'pagado', 'vencido'
  pago_50_percent NUMERIC(10,2) DEFAULT 0,
  pago_final NUMERIC(10,2) DEFAULT 0,

  -- Fechas
  fecha_contratacion DATE,
  fecha_entrega_estimada DATE,
  fecha_entrega_real DATE,
  fecha_expiracion_soporte DATE,  -- 3 meses (Starter) o 6 (Pro) desde entrega

  -- Hosting y Dominio
  hosting_proveedor TEXT,         -- 'vercel', 'netlify', 'hostinger', etc
  hosting_url TEXT,               -- URL del hosting
  dominio TEXT,                   -- ejemplo.com
  dominio_propio BOOLEAN DEFAULT false,

  -- Créditos/Uso
  creditos_disponibles NUMERIC DEFAULT 0,
  mensajes_usados_este_mes NUMERIC DEFAULT 0,
  leads_capturados NUMERIC DEFAULT 0,

  -- Status
  active BOOLEAN DEFAULT true,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_clients_plan ON clients(plan);
CREATE INDEX idx_clients_estado_pago ON clients(estado_pago);
CREATE INDEX idx_clients_whatsapp ON clients(whatsapp);
```

---

### 2. `extras_contratados` (Nueva)
Extras que el cliente contrató (Analytics, Soporte prioritario, etc)

```sql
CREATE TABLE IF NOT EXISTS extras_contratados (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  nombre TEXT NOT NULL,          -- 'analytics_avanzados', 'soporte_prioritario', 'integracion_crm'
  descripcion TEXT,
  costo_mensual NUMERIC(10,2),
  costo_unico NUMERIC(10,2),

  -- Estado del extra
  estado TEXT DEFAULT 'activo',  -- 'activo', 'cancelado', 'pausado'
  fecha_inicio DATE,
  fecha_vencimiento DATE,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_extras_client_id ON extras_contratados(client_id);
CREATE INDEX idx_extras_estado ON extras_contratados(estado);
```

---

### 3. `pagos` (Nueva)
Historial de transacciones de pago

```sql
CREATE TABLE IF NOT EXISTS pagos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  concepto TEXT NOT NULL,        -- 'Pago 50% Starter', 'Pago final Pro', 'Extra Analytics', etc
  monto NUMERIC(10,2) NOT NULL,
  moneda TEXT DEFAULT 'USD',     -- 'USD', 'ARS'

  -- Estado del pago
  estado TEXT DEFAULT 'pendiente',  -- 'pendiente', 'pagado', 'rechazado'
  metodo_pago TEXT,              -- 'transferencia', 'stripe', 'efectivo'
  referencia_transaccion TEXT,   -- ID de transacción del banco/Stripe

  -- Fechas
  fecha_vencimiento DATE,
  fecha_pagado DATE,

  -- Notas
  notas TEXT,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pagos_client_id ON pagos(client_id);
CREATE INDEX idx_pagos_estado ON pagos(estado);
CREATE INDEX idx_pagos_fecha ON pagos(fecha_pagado);
```

---

### 4. `proyectos` (Nueva)
Tracking de cada proyecto (desarrollo)

```sql
CREATE TABLE IF NOT EXISTS proyectos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  -- Información del proyecto
  nombre TEXT NOT NULL,
  descripcion TEXT,

  -- Estado
  estado TEXT DEFAULT 'en_desarrollo',  -- 'en_desarrollo', 'en_testing', 'entregado', 'en_soporte'
  progreso_porcentaje NUMERIC(3,0) DEFAULT 0,  -- 0-100

  -- Timeline
  fecha_inicio DATE,
  fecha_entrega_estimada DATE,
  fecha_entrega_real DATE,

  -- Team
  project_manager TEXT,
  frontend_dev TEXT,
  backend_dev TEXT,

  -- Notas
  notas TEXT,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_proyectos_client_id ON proyectos(client_id);
CREATE INDEX idx_proyectos_estado ON proyectos(estado);
```

---

### 5. `ai_prompts` (Actualizada)
Configuración del bot (sin cambios, pero referencia)

```sql
CREATE TABLE IF NOT EXISTS ai_prompts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  system_prompt TEXT,
  tone TEXT DEFAULT 'amigable',
  business_type TEXT,
  objective TEXT DEFAULT 'ventas',

  active BOOLEAN DEFAULT true,

  updated_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ai_prompts_client_id ON ai_prompts(client_id);
```

---

### 6. `tickets` (Sin cambios)
Sistema de tickets (ya existe)

```sql
CREATE TABLE IF NOT EXISTS tickets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  ticket_numero TEXT NOT NULL UNIQUE,
  nombre_cliente TEXT NOT NULL,
  telefono TEXT NOT NULL,
  dispositivo TEXT NOT NULL,
  problema TEXT NOT NULL,

  estado TEXT DEFAULT 'abierto',
  notas TEXT,
  agente TEXT,

  fecha_creacion TIMESTAMPTZ DEFAULT now(),
  fecha_actualizacion TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tickets_client_id ON tickets(client_id);
CREATE INDEX idx_tickets_telefono ON tickets(telefono);
CREATE INDEX idx_tickets_estado ON tickets(estado);
```

---

### 7. `conversations` (Sin cambios)
Historial de chats (ya existe)

```sql
CREATE TABLE IF NOT EXISTS conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  telefono TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,

  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conversations_client_id ON conversations(client_id);
CREATE INDEX idx_conversations_telefono ON conversations(telefono);
```

---

### 8. `bot_leads` (Sin cambios)
Leads capturados por el bot

```sql
CREATE TABLE IF NOT EXISTS bot_leads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

  name TEXT,
  phone TEXT,
  message TEXT,

  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_bot_leads_client_id ON bot_leads(client_id);
```

---

## RLS (Row Level Security)

```sql
-- Todos los usuarios autenticados pueden ver todo (para MVP)
-- Después implementar isolamiento por cliente

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE extras_contratados ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos ENABLE ROW LEVEL SECURITY;
ALTER TABLE proyectos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin_all" ON clients FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON extras_contratados FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON pagos FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON proyectos FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON ai_prompts FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON tickets FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON conversations FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "admin_all" ON bot_leads FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

## Queries Útiles

### Obtener cliente con todos sus datos
```sql
SELECT
  c.*,
  COUNT(DISTINCT t.id) as tickets_totales,
  COUNT(DISTINCT b.id) as leads_totales,
  SUM(p.monto) as ingresos_totales
FROM clients c
LEFT JOIN tickets t ON c.id = t.client_id
LEFT JOIN bot_leads b ON c.id = b.client_id
LEFT JOIN pagos p ON c.id = p.client_id AND p.estado = 'pagado'
WHERE c.id = 'UUID-DEL-CLIENTE'
GROUP BY c.id;
```

### Ver clientes con soporte vencido
```sql
SELECT id, name, plan, fecha_expiracion_soporte
FROM clients
WHERE fecha_expiracion_soporte < NOW()
AND active = true
ORDER BY fecha_expiracion_soporte ASC;
```

### Ver pagos pendientes
```sql
SELECT c.name, p.concepto, p.monto, p.fecha_vencimiento
FROM pagos p
JOIN clients c ON p.client_id = c.id
WHERE p.estado = 'pendiente'
AND p.fecha_vencimiento < NOW()
ORDER BY p.fecha_vencimiento ASC;
```

### Ver uso de mensajes este mes
```sql
SELECT name, mensajes_usados_este_mes, creditos_disponibles
FROM clients
WHERE plan = 'pro'
AND mensajes_usados_este_mes > creditos_disponibles
ORDER BY mensajes_usados_este_mes DESC;
```

---

## Cómo usar desde Python (agent/supabase_client.py)

Próximamente agregaremos funciones para:
- Crear cliente con plan
- Agregar extra
- Registrar pago
- Actualizar uso de mensajes
- Checar si soporte venció
- Checar si plan permite esta acción

---

## Ejemplo: Crear Cliente PRO

```sql
-- 1. Crear cliente
INSERT INTO clients (
  name, email, phone, plan, precio_base, precio_total,
  estado_pago, fecha_contratacion, fecha_entrega_estimada,
  fecha_expiracion_soporte
)
VALUES (
  'Juan García - Electrónica',
  'juan@electronica.com',
  '+54 9 1234567890',
  'pro',
  120.00,
  120.00,
  'pending',
  '2026-03-29',
  '2026-04-13',
  '2026-10-13'  -- 6 meses después
)
RETURNING id;  -- Guardar este UUID

-- 2. Crear su configuración de bot
INSERT INTO ai_prompts (client_id, system_prompt, tone, objective)
VALUES (
  'UUID-RETORNADO-ARRIBA',
  'Eres Mundo Bot...',
  'amigable',
  'ventas'
);

-- 3. Crear registro de pago (50%)
INSERT INTO pagos (client_id, concepto, monto, fecha_vencimiento, estado)
VALUES (
  'UUID-DEL-CLIENTE',
  'Pago 50% Plan Pro',
  60.00,
  '2026-03-29',
  'pagado'
);

-- 4. (Más tarde) Crear pago final
INSERT INTO pagos (client_id, concepto, monto, fecha_vencimiento, estado)
VALUES (
  'UUID-DEL-CLIENTE',
  'Pago 50% final Plan Pro',
  60.00,
  '2026-04-13',
  'pending'
);

-- 5. Si contrató extra
INSERT INTO extras_contratados (client_id, nombre, costo_mensual, fecha_inicio)
VALUES (
  'UUID-DEL-CLIENTE',
  'analytics_avanzados',
  20.00,
  '2026-04-14'
);
```

---

## Próxima Migración

Ejecuta el SQL abajo en Supabase SQL Editor.
