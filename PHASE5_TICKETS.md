# Phase 5 — Sistema de Tickets de Soporte

## ¿Qué es?

Un sistema automático que:
1. **Crea un ticket** cuando el cliente agenda una cita
2. **Asigna número único** a cada reparación (ej: MER-20260328-001)
3. **Permite consultar estado** en cualquier momento ("¿Cómo va mi reparación?")
4. **Guarda historial** de cada reparación en la base de datos

## Flujo de ejemplo

```
Cliente:  "Se me rompió la pantalla del iPhone 14"
Agente:   "¿Cuándo querés que vengas? Tenemos disponible mañana a las 15:00"
Cliente:  "Perfecto!"

→ Sistema crea automáticamente:
  1. Evento en Google Calendar (mañana 15:00)
  2. Ticket de soporte: MER-20260328-001
  ↓
Cliente:  "¿Cómo va mi iPhone?"
Agente:   "📱 Estado: EN PROGRESO
           Ticket: MER-20260328-001
           Dispositivo: iPhone 14
           Estado: en_progreso
           Creado: 2026-03-29"
```

## Archivos modificados

### 1. **agent/memory.py** — Nueva tabla `Ticket`

```python
class Ticket(Base):
    id: int
    ticket_numero: str  # MER-20260328-001
    telefono: str
    nombre_cliente: str
    dispositivo: str
    problema: str
    estado: str  # "abierto", "en_progreso", "completado", "cerrado"
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    notas: str
    agente: str
```

**Funciones nuevas:**
- `crear_ticket(telefono, nombre, dispositivo, problema, agente)` → ticket_numero
- `consultar_ticket(ticket_numero)` → dict
- `buscar_tickets_por_telefono(telefono)` → list[dict]
- `actualizar_ticket(ticket_numero, estado, nota)` → bool

### 2. **agent/tools.py** — Funciones de negocio

```python
async def crear_ticket_desde_cita(nombre, telefono, dispositivo, problema) -> str:
    """Crea ticket cuando se agenda una cita."""

async def buscar_estado_reparacion(telefono, consulta="") -> str:
    """Busca tickets del cliente y retorna estado formateado."""
```

### 3. **agent/main.py** — Procesamiento de tickets en webhook

```python
# Cuando se detecta [CITA]...[/CITA]:
1. Crear evento en Google Calendar
2. Crear ticket de soporte
3. Eliminar tag del texto visible

# Cuando es pregunta de soporte:
1. Generar respuesta normal con Claude
2. Enriquecer con información de tickets del cliente
```

### 4. **config/mundo-electronico/prompts.yaml** — Filtro "soporte"

```yaml
soporte:
  keywords:
    - "estado"
    - "cómo va"
    - "mi reparación"
    - "ticket"
    - "cuando puedo retirar"
  instruccion_extra: |
    El cliente consulta por el estado de su reparación.
    Sé empático y proporciona el estado actual.
```

### 5. **tests/test_local.py** — Comandos de prueba

```
Nuevos comandos:
  'tickets'             — Muestra tus tickets
  'crear ticket [dispositivo]' — Crea ticket de prueba
```

## Estados de ticket

| Estado | Significado |
|--------|------------|
| `abierto` | Recién creado, esperando reparación |
| `en_progreso` | Se está reparando actualmente |
| `completado` | Reparación terminada, listo para retirar |
| `cerrado` | Cliente retiró el dispositivo |

## Formato de número de ticket

```
MER-20260328-001
│   │  │    │
│   │  │    └─── Número secuencial del día (001, 002, 003...)
│   │  └──────── Fecha (YYYYMMDD)
│   └─────────── Agente (primeras 3 letras de AGENTE_ACTIVO)
└────────────── Prefijo del agente
```

Ejemplos:
- `MER-20260328-001` — Primer ticket de Mundo Electronico el 28 de marzo 2026
- `MER-20260328-002` — Segundo ticket del mismo día
- `MER-20260329-001` — Primer ticket del 29 de marzo

## Flujos de usuario

### Flujo 1: Cliente agenda cita

```
Cliente: "Quiero agendar"
Agente: "¿Cuál es tu nombre y teléfono?"
Cliente: "Juan, 5491165689145"
Agente: "¿Cuándo querés venir?"
Cliente: "Mañana a las 3pm"

→ [CITA]Juan Pérez|5491165689145|iPhone 14 pantalla|2026-03-29|15:00[/CITA]
  (Tag invisible para el cliente)

Automáticamente:
✓ Crear evento Google Calendar
✓ Crear ticket MER-20260328-001
✓ Guardar en BD

Cliente recibe: "Perfecto Juan! Te agendé para mañana..."
```

### Flujo 2: Cliente consulta estado

```
Cliente: "¿Cómo va mi reparación?"

→ Sistema detecta tipo "soporte"
→ Busca tickets de este teléfono
→ Enriquece respuesta con estado actual

Cliente recibe:
"Hola! Tu reparación sigue en progreso.

📱 Estado de tu reparación:
Ticket: MER-20260328-001
Dispositivo: iPhone 14
Estado: EN PROGRESO
Problema: pantalla rota
Creado: 2026-03-29
Última actualización: 2026-03-29

Notas: Se está realizando el cambio de pantalla. Estará listo mañana a las 14:00"
```

### Flujo 3: Admin actualiza ticket

```
(En Railway o directamente en BD):
UPDATE tickets
SET estado = 'completado',
    notas = '[2026-03-29 14:00] Pantalla reemplazada. Dispositivo probado.'
WHERE ticket_numero = 'MER-20260328-001'
```

Próxima vez que el cliente pregunte: "Listo! Tu iPhone está completado. Podes pasar a buscarlo."

## Cómo probar en local

```bash
python tests/test_local.py
```

Comandos:
```
Tu: "Quiero agendar una cita"
Tu: "Me llamo Juan, 5491165689145"
Tu: "iPhone 14, pantalla rota"
Tu: "Mañana a las 15:00"
→ Se crea ticket automáticamente

Tu: "¿Cómo va mi reparación?"
→ Bot muestra el estado del ticket

Tu: "tickets"
→ Lista todos tus tickets

Tu: "crear ticket iPhone 15"
→ Crea un ticket de prueba manualmente
```

## Multi-agente

Cada agente tiene sus propios tickets en `data/{agente}/agentkit.db`:
- `MER-20260328-001` — Tickets de mundo-electronico
- `OTR-20260328-001` — Tickets de otro-agente
- `TEC-20260328-001` — Tickets de tech-support

Los números de ticket usan el prefijo del agente, así no colisiona.

## Próximas mejoras

- [ ] Endpoint `/tickets/{ticket_numero}` para consultar vía API
- [ ] Dashboard para admin ver todos los tickets y actualizar estado
- [ ] Notificaciones automáticas cuando cambio de estado
- [ ] Integración con CRM para tracking de leads
- [ ] Historial de cambios en cada ticket (quién cambió, cuándo, por qué)

## Base de datos

```sql
-- Ver todos los tickets
SELECT * FROM tickets;

-- Actualizar estado
UPDATE tickets SET estado='en_progreso' WHERE ticket_numero='MER-20260328-001';

-- Ver tickets abiertos de un cliente
SELECT * FROM tickets WHERE telefono='5491165689145' AND estado='abierto';

-- Agregar nota
UPDATE tickets
SET notas = notas || '\n[2026-03-29 14:00] Cambio de pantalla completado'
WHERE ticket_numero='MER-20260328-001';
```

---

**Phase 5 completada.** El sistema de tickets está integrado y listo para producción.

Ahora los clientes pueden:
1. ✅ Agendar citas (Phase 4)
2. ✅ Crear tickets automáticamente (Phase 5)
3. ✅ Consultar estado en cualquier momento (Phase 5)

Próximo: Dashboard admin para gestionar tickets y mandar notificaciones.
