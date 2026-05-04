# Setup: Integración con Google Calendar (Modo por Cliente)

⚠️ **NOTA IMPORTANTE:**

Si eres **proveedor** que vende bots a múltiples clientes, usa en cambio:
→ **[SETUP_MULTI_CLIENT_CALENDAR.md](SETUP_MULTI_CLIENT_CALENDAR.md)** ← RECOMENDADO PARA VENDER

Este documento es para si cada **cliente configura su propia cuenta de Google**.

---

Para que el agente cree citas automáticamente en tu Google Calendar, necesitas seguir estos pasos **UNA VEZ**.

---

## Paso 1: Crear un Proyecto en Google Cloud

1. Ve a **console.cloud.google.com**
2. Haz clic en el **selector de proyecto** (arriba a la izquierda)
3. Click **"NEW PROJECT"**
4. Nombre: `Mundo Electronico Bot` (o similar)
5. Click **"CREATE"**

Espera a que se cree el proyecto (~1 minuto).

---

## Paso 2: Habilitar Google Calendar API

1. En Google Cloud Console, ve a **APIs & Services** → **Library**
2. Busca: `Google Calendar API`
3. Click en el resultado
4. Click **"ENABLE"**

Espera a que se habilite (~1 minuto).

---

## Paso 3: Crear Service Account

1. Ve a **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** (arriba)
3. Selecciona **"Service Account"**
4. Completa:
   - **Service account name:** `mundo-bot` (cualquier nombre)
   - Click **"CREATE AND CONTINUE"**
5. En "Grant this service account access..." puedes saltarlo
6. Click **"CONTINUE"**
7. Click **"CREATE KEY"**
   - Selecciona **JSON**
   - Click **"CREATE"**

Se descargará un archivo `.json` con tus credenciales. **GUÁRDALO EN UN LUGAR SEGURO** — no lo subas a GitHub.

---

## Paso 4: Obtener el ID de tu Calendario

1. Ve a **Google Calendar** (calendar.google.com)
2. En el panel izquierdo, haz clic en los **⋮ (tres puntos)** junto a "Mi calendario"
3. Selecciona **"Settings"**
4. Busca **"Calendar ID"** en la sección de abajo
5. Copia ese ID (algo como: `tu-email@gmail.com`)

---

## Paso 5: Compartir el Calendario con el Service Account

1. En Google Calendar, ve a **Settings** → **Share with specific people**
2. Click **"Add people and groups"**
3. Pega el email del service account (está en el JSON descargado, búscalo como "client_email")
4. Otorga permiso **"Make changes to events"**
5. Click **"Send"**

---

## Paso 6: Configurar en Railway

1. Ve a **railway.app** → Tu proyecto
2. Click en la pestaña **"Variables"**
3. Agregalas:

### Variable 1: GOOGLE_CALENDAR_CREDENTIALS

- Abre el archivo JSON que descargaste en Paso 3
- **Copia TODO el contenido** (todo el JSON)
- En Railway, crea variable:
  - **Name:** `GOOGLE_CALENDAR_CREDENTIALS`
  - **Value:** (pega todo el JSON aquí)

### Variable 2: GOOGLE_CALENDAR_ID

- **Name:** `GOOGLE_CALENDAR_ID`
- **Value:** (el ID que copiaste en Paso 4)

4. Click **"SAVE"**

Railway hará redeploy automáticamente en 1-2 minutos.

---

## ¡Listo!

Ahora cuando el agente confirme una cita, aparecerá automáticamente en tu Google Calendar.

### Ejemplo:
```
Cliente: "¿Me agendás para mañana martes a las 3pm para cambiar la pantalla?"
Agente: "Perfecto Juan! Te agendé para el martes 29 de marzo a las 15:00."

👉 Google Calendar: Nuevo evento "Cita - iPhone 14 pantalla rota (Juan Pérez)"
   Martes 29 de marzo, 15:00-16:00
   Descripción: Cliente: Juan Pérez, Teléfono: 549..., Dispositivo: iPhone 14 pantalla rota
```

---

## Troubleshooting

**P: El evento no aparece en mi Google Calendar**

R: Verifica que:
1. Las variables `GOOGLE_CALENDAR_CREDENTIALS` y `GOOGLE_CALENDAR_ID` están configuradas en Railway
2. El JSON es válido (sin saltos de línea accidentales)
3. El service account está compartido en tu calendario (Paso 5)
4. Railway hizo redeploy (espera 2-3 minutos)

**P: ¿Mi API key de Google está segura?**

R: Sí. El service account:
- Solo puede crear eventos en tu calendario (no borrar, no modificar otros)
- Es específico de este proyecto
- Puedes revocarlo desde Google Cloud Console en cualquier momento

**P: Quiero dejar de usar Google Calendar**

R: Simplemente elimina las variables en Railway. El agente seguirá funcionando normalmente (solo que sin crear eventos en Calendar).

---

## Para nuevos agentes

Cada nuevo agente necesita su propio `GOOGLE_CALENDAR_CREDENTIALS` y `GOOGLE_CALENDAR_ID` en Railway.

O, si quieres compartir el mismo calendario para todos los agentes, usa los mismos valores en todos.

**Recomendación:** Un calendario por negocio (más organizado).
