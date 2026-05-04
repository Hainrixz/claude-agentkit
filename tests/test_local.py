# tests/test_local.py — Simulador de chat en terminal
# Generado por AgentKit

"""
Prueba tu agente sin necesitar WhatsApp.
Simula una conversación en la terminal.
"""

import asyncio
import sys
import os
import io

# Configurar stdout para UTF-8 (soluciona problemas con emojis en Windows)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.brain import generar_respuesta
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial, limpiar_historial, obtener_tickets_por_telefono
from agent.tools import detectar_tipo_pregunta, crear_ticket_desde_cita
import re
import asyncio as aio

TELEFONO_TEST = "test-local-001"


async def main():
    """Loop principal del chat de prueba."""
    await inicializar_db()

    print()
    print("=" * 55)
    print("   AgentKit — Test Local (Phase 5: Tickets)")
    print("=" * 55)
    print()
    print("  Escribe mensajes como si fueras un cliente.")
    print("  Comandos especiales:")
    print("    'limpiar'     — borra el historial")
    print("    'tickets'     — muestra tus tickets (simula búsqueda de BD)")
    print("    'crear ticket [dispositivo]' — crea un ticket de prueba")
    print("    'salir'       — termina el test")
    print()
    print("  Prueba estos flujos:")
    print("  1. Pregunta por reparación y pide agendar cita")
    print("  2. Luego pregunta '¿cómo va mi reparación?'")
    print("  3. Mira cómo el bot te muestra el estado del ticket")
    print()
    print("-" * 55)
    print()

    while True:
        try:
            mensaje = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nTest finalizado.")
            break

        if not mensaje:
            continue

        if mensaje.lower() == "salir":
            print("\nTest finalizado.")
            break

        if mensaje.lower() == "limpiar":
            await limpiar_historial(TELEFONO_TEST)
            print("[Historial borrado]\n")
            continue

        if mensaje.lower() == "tickets":
            # En modo local sin Supabase, los tickets no persisten
            print("[Nota: En modo local sin Supabase, los tickets no se guardan]")
            print("[Para ver tickets, configura SUPABASE_URL y SUPABASE_KEY en .env]\n")
            continue

        if mensaje.lower().startswith("crear ticket"):
            # Comando de prueba: crear ticket manualmente
            dispositivo = mensaje.replace("crear ticket", "").strip() or "Dispositivo test"
            ticket_numero = await crear_ticket_desde_cita(
                "Cliente Test",
                TELEFONO_TEST,
                dispositivo,
                "Prueba de sistema de tickets"
            )
            print(f"[Ticket creado: {ticket_numero}]\n")
            continue

        # Obtener historial ANTES de guardar (brain.py agrega el mensaje actual)
        historial = await obtener_historial(TELEFONO_TEST)

        # Generar respuesta
        print("\nMundo Bot: ", end="", flush=True)
        respuesta = await generar_respuesta(mensaje, historial)
        print(respuesta)

        # Procesar tag [CITA] — soporta dos formatos
        nombre, telefono_cita, dispositivo, fecha, hora = None, None, None, None, None

        # Intentar formato pipe: [CITA]nombre|tel|disp|fecha|hora[/CITA]
        patron_pipe = r'\[CITA\](.*?)\[/CITA\]'
        match = re.search(patron_pipe, respuesta)
        if match:
            datos = match.group(1).split("|")
            if len(datos) == 5:
                nombre, telefono_cita, dispositivo, fecha, hora = [d.strip() for d in datos]
        else:
            # Intentar formato JSON (flexible)
            patron_json = r'\[CITA:\s*(.*?)\]'
            match = re.search(patron_json, respuesta)
            if match:
                datos_raw = match.group(1)
                # Buscar campos flexiblemente
                nombre_m = re.search(r'(?:nombre|cliente)\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)
                tel_m = re.search(r'(?:telefono|contacto|teléfono)\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)
                disp_m = re.search(r'dispositivo\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)
                prob_m = re.search(r'problema\s*=\s*["\']?([^"\',\[\]]+)["\']?', datos_raw)
                fecha_m = re.search(r'fecha\s*=\s*["\']?(\d{4}-\d{2}-\d{2})["\']?', datos_raw)
                hora_m = re.search(r'hora\s*=\s*["\']?(\d{2}:\d{2})["\']?', datos_raw)
                if all([nombre_m, tel_m, disp_m, prob_m, fecha_m, hora_m]):
                    nombre = nombre_m.group(1).strip()
                    telefono_cita = tel_m.group(1).strip()
                    dispositivo = f"{disp_m.group(1).strip()} {prob_m.group(1).strip()}"
                    fecha = fecha_m.group(1).strip()
                    hora = hora_m.group(1).strip()

        # Si encontramos datos, crear ticket
        if nombre and telefono_cita and dispositivo and fecha and hora:
            try:
                # Limpiar símbolos del teléfono
                telefono_limpio = re.sub(r'[^\d]', '', telefono_cita)
                ticket_numero = await crear_ticket_desde_cita(nombre, telefono_limpio, dispositivo, "Reparación agendada")
                # Limpiar tags de la respuesta
                respuesta_clean = re.sub(patron_pipe, "", respuesta)
                respuesta_clean = re.sub(patron_json, "", respuesta_clean)
                respuesta = respuesta_clean.strip()
                print(f"\n[✓ Ticket creado: {ticket_numero}]")
            except Exception as e:
                print(f"\n[Error creando ticket: {e}]")

        print()

        # Guardar mensaje del usuario y respuesta del agente
        await guardar_mensaje(TELEFONO_TEST, "user", mensaje)
        await guardar_mensaje(TELEFONO_TEST, "assistant", respuesta)


if __name__ == "__main__":
    asyncio.run(main())
