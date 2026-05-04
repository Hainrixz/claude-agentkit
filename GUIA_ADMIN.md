# Guía del Admin Dashboard
**Para clientes con Plan PRO**

---

## 🔐 Acceso

**URL:** `tudominio.com/admin`

**Credenciales** (te las pasaremos por email):
- Usuario: admin (o tu email)
- Password: [personalizado]

---

## 📊 Dashboard Principal

Al entrar ves un resumen de tu bot:

### Estadísticas (arriba)

- **🎫 Total**: Cantidad de tickets (citas agendadas)
- **🆕 Abiertos**: Tickets nuevos, sin iniciar reparación
- **⚙️ En progreso**: Reparaciones actualmente en proceso
- **✅ Completados**: Reparaciones terminadas

### Tabla de Tickets

| Columna | Qué es | Qué significa |
|---------|--------|---------------|
| **Ticket** | Número único | MER-20260329-001 = código del ticket |
| **Cliente** | Nombre | Quién agendó |
| **Dispositivo** | Qué repara | iPhone 14, Samsung S21, etc |
| **Problema** | Descripción | Pantalla rota, batería muerta, etc |
| **Estado** | Dropdown (cambiar) | 🆕 Abierto, ⚙️ En progreso, ✅ Completado, ✓ Cerrado |
| **Fecha** | Cuándo se creó | 29/03/2026 10:30 |
| **Acciones** | Botones | "Notas" para agregar información |

---

## 🎯 Cómo Usar

### Ver un Ticket

1. Busca en la tabla el ticket que quieres revisar
2. Lee: nombre cliente, dispositivo, problema, estado, fecha
3. Ejemplo:
   ```
   MER-20260329-001  | Juan García | iPhone 14 pantalla rota | Estado: 🆕 Abierto | 29/03/2026 10:30
   ```

---

### Cambiar Estado de un Ticket

**Cuándo hacer cambios:**

| Cambio | Cuándo |
|--------|--------|
| 🆕 Abierto → ⚙️ En progreso | Cuando EMPIEZA la reparación |
| ⚙️ En progreso → ✅ Completado | Cuando TERMINA la reparación |
| ✅ Completado → ✓ Cerrado | Cuando el cliente RETIRA el dispositivo |

**Cómo cambiar:**

1. Haz click en el dropdown del estado (columna Estado)
2. Selecciona el nuevo estado
3. Se guarda automáticamente
4. ¡Listo!

**Ejemplo:**
```
Cliente Juan agendó reparación de iPhone el 29/03
→ Estado: 🆕 Abierto

El 30/03 empezamos la reparación
→ Click en dropdown, selecciona "En progreso"
→ Estado: ⚙️ En progreso

El 02/04 terminamos
→ Click en dropdown, selecciona "Completado"
→ Estado: ✅ Completado

El 03/04 el cliente retira
→ Click en dropdown, selecciona "Cerrado"
→ Estado: ✓ Cerrado
```

---

### Agregar Notas a un Ticket

**Qué son las notas:**
- Información extra sobre la reparación
- Detalles técnicos
- Problemas encontrados
- Estado del cliente
- Lo que necesites recordar

**Cómo agregar:**

1. Haz click en botón **"Notas"** (columna Acciones)
2. Se abre una ventana (modal)
3. Escribe lo que necesites
4. Click en **"Guardar"**
5. Se guarda automáticamente

**Ejemplo de notas:**
```
"Encontramos daño de agua. Limpiamos la placa.
Batería debe ser reemplazada. Cliente avisado.
ETA: 3 días."
```

Después puedes leer esas notas cuando abras el ticket de nuevo.

---

### Ver Detalles Completos

Haz click en **número de ticket** para expandir y ver:
- Todas las notas
- Historial de cambios de estado
- Fecha de cada cambio

---

## 📈 Indicadores de Salud

### ¿Cómo sé si todo va bien?

**Buen signo:**
- ✅ Pocos tickets en "Abierto" (significa que atiendes rápido)
- ✅ Muchos en "Completado" (significa que trabajas rápido)
- ✅ Notas detalladas (organized, profesional)

**Mal signo:**
- ❌ Muchos tickets "Abiertos" viejos (no atiendes)
- ❌ Pocos "Completado" (lento)
- ❌ Sin notas (desorganizado)

---

## 🔄 Workflow Típico

### Un cliente agendó cita por WhatsApp

1. **Bot detecta** que quiere agendar
2. **Bot crea automáticamente** un ticket
3. **Aparece en /admin** como 🆕 Abierto
4. **Tú recibes notificación** (si la configuraste)

### Durante la reparación

1. **Cliente llega**: cambia a ⚙️ En progreso
2. **Mientras reparas**: agregas notas ("limpiando", "necesita batería", etc)
3. **Terminas**: cambias a ✅ Completado

### Cuando retira

1. **Cliente retira**: cambias a ✓ Cerrado
2. **Listo**: ticket archivado

---

## ⚙️ Configuración

### Cambiar contraseña

1. Footer del dashboard → "Mi perfil" o "Settings"
2. Click "Cambiar password"
3. Ingresa password vieja
4. Ingresa password nueva (2x)
5. Click "Guardar"

### Cambiar idioma

- Actualmente: Español
- Si necesitas otro idioma, contacta a RIWEB

### Descargar reporte

1. Top derecha → "Exportar"
2. Elige rango de fechas
3. Formato: PDF o Excel
4. Se descarga automaticamente

---

## 🔒 Seguridad

### ⚠️ IMPORTANTE

**NO HAGAS:**
- ❌ Compartas tu password
- ❌ Guardes password en Post-its
- ❌ Uses password que uses en otros lados
- ❌ Dejes sesión abierta en computadoras compartidas

**HAZLO:**
- ✅ Cambia password cada 3 meses
- ✅ Usa password fuerte (mayúscula, número, símbolo)
- ✅ Cierra sesión cuando terminas
- ✅ Usa 2FA si disponible

---

## 🚨 Troubleshooting

### "No veo el dashboard"
**Solución:**
1. Verifica que escribiste bien la URL (`tudominio.com/admin`)
2. Verifica que el dominio esté bien configurado
3. Contacta a RIWEB

### "No me deja loguear"
**Solución:**
1. Verifica que escribiste bien usuario y password
2. Verifica Caps Lock
3. Si no recuerdas, contacta a RIWEB para reset

### "No aparece un ticket"
**Solución:**
1. Recarga la página (Ctrl+R o Cmd+R)
2. Espera 10-20 segundos (a veces tarda)
3. Si sigue sin aparecer, contacta a RIWEB

### "No puedo cambiar estado"
**Solución:**
1. Recarga la página
2. Intenta de nuevo
3. Si sigue fallando, contacta a RIWEB

---

## 📞 Soporte

**¿Algo no funciona?**

Contacta a RIWEB:
- 📧 Email: soporte@riweb.app
- 📱 WhatsApp: +54 9 XXX XXXX
- ⏰ Respuesta: 12-24 horas

---

## 💡 Tips Profesionales

### Usa abreviaturas en notas
```
En lugar de: "El cliente llamó diciendo que es urgente"
Escribe: "URGENTE - cliente llamó"
```

### Agrega ETA (tiempo estimado)
```
"Esperando repuesto. ETA: 2 días"
```

### Documenta problemas raros
```
"Encontramos virus. Formateamos. Cliente sin respaldo = info perdida"
```

### Actualiza estado regularmente
No dejes tickets en "En progreso" por semanas.
Cambia a "Completado" cuando termines.

---

## 📱 Mobile

El dashboard funciona en celular también:
- Abre en navegador
- Escala automáticamente
- Puedes cambiar estado on-the-go

---

## ¿Preguntas?

Consulta **ONBOARDING.md** para más detalles.

---

**Guía v1.0 — Marzo 2026**
