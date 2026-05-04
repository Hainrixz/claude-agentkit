# Setup: Modo Multi-Cliente con Google Calendar

## Visión general

Como proveedor, TÚ manejas UNA cuenta de Google con múltiples calendarios (uno por cliente).

```
Mi Cuenta Google (agentkit@miempresa.com)
├─ Calendario: Mundo Electronico
├─ Calendario: Tech Support
├─ Calendario: Otro Negocio
└─ Calendario: etc...

Mi app whatsapp-agente
├─ Agente: mundo-electronico → citas → Calendario Mundo Electronico
├─ Agente: tech-support → citas → Calendario Tech Support
└─ Agente: otro-negocio → citas → Calendario Otro Negocio
```

Cada cliente recibe un agente configurado. **Ellos NUNCA tocan Google.** Las citas aparecen en TU calendario automáticamente.

---

## Paso 1: Crear cuenta de Google para el proveedor

1. Ve a **gmail.com**
2. Crea una cuenta profesional: `agentkit@tuempresa.com` (o similar)
3. Esta será tu cuenta MAESTRA

---

## Paso 2: Crear proyecto en Google Cloud (UNA SOLA VEZ)

1. Ve a **console.cloud.google.com**
2. Selector de proyecto (arriba) → **NEW PROJECT**
3. Nombre: `AgentKit Multi-Client`
4. Click **CREATE**

---

## Paso 3: Habilitar Google Calendar API

1. **APIs & Services** → **Library**
2. Busca: `Google Calendar API`
3. Click en el resultado → **ENABLE**

---

## Paso 4: Crear Service Account (UNA SOLA VEZ)

1. **APIs & Services** → **Credentials**
2. **+ CREATE CREDENTIALS** → **Service Account**
3. **Service account name:** `agentkit-provider`
4. Click **CREATE AND CONTINUE**
5. Skip "Grant access" → **CONTINUE**
6. **CREATE KEY** → **JSON** → **CREATE**

Se descarga un `.json` con tus credenciales. **GUARDA ESTE ARCHIVO.**

---

## Paso 5: En Google Calendar, crear calendarios para cada cliente

1. Ve a **calendar.google.com** (conectado con tu cuenta agentkit@...)
2. Izquierda, junto a "+ Crear" → click en **+**
3. **Crear nuevo calendario**
4. Nombre: `Mundo Electronico` (nombre del negocio)
5. Descripción: `Reparaciones y citas` (opcional)
6. **CREATE**
7. Repite para cada cliente/negocio

Ahora tienes varios calendarios bajo una sola cuenta.

---

## Paso 6: Obtener Calendar IDs

Para cada calendario que creaste:

1. **Settings** (ícono de engranaje) → **Settings**
2. Izquierda, selecciona el calendario (ej: "Mundo Electronico")
3. Busca **"Calendar ID"** (en la sección de abajo)
4. Cópialo (algo como: `c_abc123def456@group.calendar.google.com`)
5. **Guarda cada uno en un lugar seguro**

---

## Paso 7: Compartir calendarios con el Service Account

El service account necesita permisos WRITE en cada calendario.

Para cada calendario:

1. Abre el calendario en **calendar.google.com**
2. Click en **⋮ (puntos)** → **Settings**
3. **Share with specific people**
4. **Add people and groups**
5. Email: busca en el `.json` el campo `"client_email"` y cópialo
   (algo como: `agentkit-provider@project-123.iam.gserviceaccount.com`)
6. Permiso: **Make changes to events**
7. **SEND**

Repite para cada calendario.

---

## Paso 8: Configurar en Railway (Centro de Control)

### Variable global (credenciales del proveedor)

En Railway, proyecto → **Variables**, agrega:

**Name:** `GOOGLE_CALENDAR_CREDENTIALS`
**Value:** (Abre el `.json` descargado, copia TODO el contenido)

Esto es una sola vez para todas tus aplicaciones.

---

## Paso 9: Configurar cada cliente

Para cada agente que vendas, edita su `config/{agente}/business.yaml`:

```yaml
negocio:
  nombre: "Mundo Electronico"
  # ... otros datos ...
  calendar_id: "c_abc123def456@group.calendar.google.com"  # ← Agrega esta línea

agente:
  nombre: "Mundo Bot"
  # ...
```

Reemplaza `c_abc123def456@group.calendar.google.com` con el Calendar ID que copiaste en Paso 6.

---

## Ejemplo completo

```yaml
# config/mundo-electronico/business.yaml

negocio:
  nombre: Mundo Electronico
  descripcion: |
    Reparación de electrónica...
  horario: "L-V 11-19, Sáb 11-14"
  ubicacion: "Argentina"
  calendar_id: "c_abc123def456@group.calendar.google.com"  # ← AQUÍ

agente:
  nombre: Mundo Bot
  tono: empático y cálido
  # ...
```

Cuando un cliente agenda cita:
```
Cliente: "Me agendás para mañana a las 15:00?"
Bot: "Perfecto! Te agendé para mañana."

→ Sistema crea evento en TU calendario "Mundo Electronico"
→ Cita aparece en tu Google Calendar personal
```

---

## Flujo de venta

```
TÚ (como proveedor)

1. Vendés el agente a "Mundo Electronico"
2. Copias la carpeta config/mundo-electronico
3. Cambias el nombre, prompts, precios, etc.
4. Agregas el calendar_id en business.yaml
5. Deployás a Railway
6. Listo — el cliente solo usa WhatsApp

→ Las citas aparecen en TU Google Calendar
→ TÚ manejas todos los calendarios centralmente
```

---

## Diferencia: Modo Antiguo vs Nuevo

### Modo Antiguo (no recomendado)
```
CLIENTE 1 → Configura su Google
CLIENTE 2 → Configura su Google
CLIENTE 3 → Configura su Google
TÚ → Sin visibilidad
```

### Modo Nuevo (RECOMENDADO - ¡lo que acabamos de hacer!)
```
TÚ → Una cuenta Google con múltiples calendarios

         ├─ Mundo Electronico
         ├─ Tech Support
         ├─ Otro Negocio
         └─ etc...

CLIENTES → Solo usan WhatsApp, no tocan Google
```

---

## Ventajas

✅ **Escalable:** Agrega clientes sin que ellos hagan nada de Google
✅ **Centralizado:** Todos los calendarios en un solo lugar
✅ **Profesional:** El cliente NO ve tu cuenta de Google
✅ **Fácil de vender:** "No necesitas hacer nada de Google"
✅ **Seguro:** Los clientes nunca tienen acceso a tus credenciales
✅ **Auditable:** TÚ ves todas las citas de todos tus clientes

---

## Cambios en el código

El código ya soporta esto automáticamente:

1. `crear_evento_calendario()` en `agent/tools.py` busca:
   - Primero: `calendar_id` en `config/{agente}/business.yaml`
   - Segundo: Variable `GOOGLE_CALENDAR_ID` en .env
   - Si tampoco encuentra, descarta silenciosamente

2. `GOOGLE_CALENDAR_CREDENTIALS` es global (una sola vez en Railway)

3. Cada agente define su `calendar_id` en su `business.yaml`

---

## Troubleshooting

**P: Creé el calendar pero no aparecen las citas**

R: Verifica:
1. El `calendar_id` en `business.yaml` es correcto
2. El service account está compartido en el calendario (Paso 7)
3. Espera 1-2 minutos después de compartir (Google tarda)

**P: ¿Puedo agregar más calendarios después?**

R: Sí, en cualquier momento:
1. Crea el calendario en tu Google Calendar
2. Obtén el Calendar ID
3. Agrega el `calendar_id` en el `business.yaml` del cliente
4. Deploy a Railway
5. Listo

**P: ¿Y si necesito mover un cliente a otro calendario?**

R: Solo cambia el `calendar_id` en su `business.yaml` y redeploya. Las nuevas citas irán al nuevo calendario.

---

## Próximo paso

Ahora que está configurado en modo multi-cliente:

1. Copia `config/mundo-electronico` para crear `config/otro-agente`
2. Edita su `business.yaml` con otro nombre y `calendar_id`
3. Deploy
4. ¡Nuevo cliente listo!

Sin tocar Google ni credenciales nuevas.

---

**¿Listo?** Avísame cuando tengas la carpeta de otro cliente y ayudo con el setup.
