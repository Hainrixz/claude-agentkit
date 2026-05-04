# Admin Dashboard — Gestión de Tickets

## ¿Qué es?

Una interfaz web donde el dueño del negocio puede:
- ✅ Ver TODOS los tickets de reparación
- ✅ Ver estado en tiempo real (abierto, en progreso, completado, cerrado)
- ✅ Cambiar estado con un dropdown
- ✅ Agregar notas sobre el progreso
- ✅ Ver fechas de creación y última actualización
- ✅ Estadísticas rápidas (total, abiertos, en progreso, completados)

## Acceso

**URL:** `https://tu-app.railway.app/admin`

**Contraseña:** Definida en `ADMIN_PASSWORD` (default: `admin123`)

Cambiar en `.env`:
```env
ADMIN_PASSWORD=tu-contraseña-segura
```

## Características

### 1. Login
```
Entra a /admin
↓
Sistema pide contraseña
↓
Si es correcta, sesión por 7 días (cookie httponly)
```

### 2. Dashboard principal

```
📊 Estadísticas:
  • Total de Tickets
  • Abiertos
  • En Progreso
  • Completados

📋 Tabla de tickets:
  • Ticket # | Cliente | Dispositivo | Problema | Estado | Creado | Acciones
```

### 3. Cambiar estado

Simplemente selecciona el nuevo estado en el dropdown:
```
🆕 Abierto → ⚙️ En progreso → ✅ Completado → ✓ Cerrado
```

Se guarda automáticamente y se muestra un confirmación.

### 4. Agregar notas

Click en botón "Notas" para abrir modal:
```
┌─────────────────────────────────────┐
│ Notas para MER-20260328-001         │
├─────────────────────────────────────┤
│ [textarea]                          │
│ Agregar cualquier actualización     │
│ sobre el progreso de la reparación  │
├─────────────────────────────────────┤
│ [Cancelar] [Guardar]                │
└─────────────────────────────────────┘
```

Las notas se guardan con timestamp automático:
```
[2026-03-29 14:00] Se está realizando cambio de pantalla
[2026-03-29 15:30] Pantalla reemplazada, probando funcionamiento
```

## Ejemplo de flujo

```
1. Cliente agenda cita por WhatsApp
   → Sistema crea ticket: MER-20260328-001

2. Dueño entra a /admin
   → Ve ticket nuevo en "Abierto"

3. Técnico inicia reparación
   → Dueño cambia estado a "En progreso"
   → Sistema notifica al cliente (futuro)

4. Se termina la reparación
   → Dueño cambia a "Completado"
   → Dueño agrega nota: "Pantalla reemplazada. Listo para retirar mañana 14:00"

5. Cliente pregunta por WhatsApp: "¿Está listo?"
   → Bot responde: "Sí! Tu iPhone está completado. Podes pasar mañana a las 14:00."
```

## Seguridad

- ✅ Contraseña protegida (ADMIN_PASSWORD en .env)
- ✅ Sesión por cookie httponly (7 días)
- ✅ Solo cambios autenticados
- ✅ No expone API keys o datos sensibles

## Styling

El dashboard tiene:
- Gradiente moderno (púrpura)
- Responsive (funciona en mobile)
- Dropdowns de estado con colores (rojo=abierto, azul=progreso, verde=completado, gris=cerrado)
- Modal elegante para notas
- Loading visual
- Mensajes de confirmación

## Archivos modificados

### agent/admin.py (nuevo)
- Ruta GET `/admin` — dashboard HTML
- Ruta POST `/admin/login` — validar contraseña
- Ruta POST `/admin/actualizar` — cambiar estado/notas
- Función `obtener_todos_los_tickets()` — query a BD
- Función `generar_html_dashboard()` — HTML + CSS + JS

### agent/main.py
- Agregar import: `from agent.admin import admin_router`
- Incluir router: `app.include_router(admin_router)`

### .env
- Nueva variable: `ADMIN_PASSWORD=admin123`

## Deploy a producción

En Railway ya está incluido. Solo:

1. Cambiar contraseña en Railway variables:
   ```
   ADMIN_PASSWORD = tu-contraseña-fuerte-aqui
   ```

2. Acceder a: `https://tu-app.railway.app/admin`

3. Login con la contraseña

4. ¡Usa el dashboard!

## Próximas mejoras

- [ ] Exportar tickets a CSV
- [ ] Filtrar por estado/cliente
- [ ] Búsqueda por nombre o ticket #
- [ ] Notificaciones automáticas al cliente cuando cambia estado
- [ ] Historial de quién cambió qué y cuándo
- [ ] Integración con WhatsApp (enviar mensajes directamente desde dashboard)

---

**Dashboard listo para usar.** No requiere configuración adicional.
