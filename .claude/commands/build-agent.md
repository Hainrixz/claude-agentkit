Lee el archivo CLAUDE.md completo. Contiene todas las instrucciones detalladas.

Ejecuta el flujo de onboarding de AgentKit siguiendo las 5 fases EN ORDEN:

FASE 1 — Bienvenida y verificación del entorno
- Muestra el mensaje de bienvenida
- Verifica Python >= 3.11
- Crea las carpetas necesarias (agent/, agent/providers/, config/, knowledge/, tests/)
- Genera requirements.txt e instala dependencias
- Crea .env base

FASE 2 — Entrevista del negocio
- Haz las 11 preguntas UNA POR UNA
- Espera respuesta antes de continuar a la siguiente
- PREGUNTA 9: el usuario elige su proveedor de WhatsApp (Meta/Twilio)
- PREGUNTA 10: pide las credenciales específicas del proveedor elegido
- PREGUNTA 11: el usuario decide si activa búsqueda web (You.com); si sí, pide YOU_API_KEY
- Guarda todas las respuestas para la Fase 3

FASE 3 — Generación del agente
- Genera config/business.yaml con datos del negocio
- Genera config/prompts.yaml con system prompt poderoso y específico
- Si hay archivos en /knowledge, léelos e incorpóralos al prompt
- Genera agent/providers/ con el proveedor elegido (base.py + __init__.py + adaptador)
- Genera agent/main.py (FastAPI + webhook provider-agnostic)
- Genera agent/brain.py (Claude API + ciclo de tool-use). Agrega el import de
  buscar_en_internet y su entrada en TOOLS solo si PREGUNTA 11 = Sí; si no, deja
  TOOLS = [] — el resto del archivo es igual en ambos casos.
- Genera agent/memory.py (SQLite + historial)
- Genera agent/tools.py (herramientas según caso de uso; incluye buscar_en_internet()
  solo si PREGUNTA 11 = Sí)
- Genera tests/test_local.py (simulador de chat)
- Genera Dockerfile y docker-compose.yml
- Configura .env con WHATSAPP_PROVIDER, YOU_API_KEY (si aplica) y las API keys del usuario

FASE 4 — Testing local
- Ejecuta python tests/test_local.py
- El usuario chatea con su agente en la terminal
- Si hay ajustes, modifica prompts.yaml y repite
- No avanza sin aprobación del usuario

FASE 5 — Deploy a Railway
- Solo si el usuario quiere
- Build Docker + instrucciones de Railway
- Configuración de webhook específica para el proveedor elegido

REGLAS:
- Habla siempre en español
- Una pregunta a la vez
- Nunca hardcodees API keys
- No avances de fase sin confirmación
- El agente debe funcionar antes de hablar de deploy
- Genera SOLO el adaptador del proveedor elegido (no los 3)
