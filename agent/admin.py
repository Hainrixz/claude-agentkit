# agent/admin.py — Dashboard Admin para gestionar tickets
# Conectado a Supabase

"""
Interfaz web para que el dueño del negocio vea y actualice tickets de reparación.
Accesible en /admin (protegida con contraseña simple)
Lee y escribe en Supabase directamente.
"""

import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from agent.supabase_client import supabase_client, is_supabase_enabled

logger = logging.getLogger("agentkit")

admin_router = APIRouter()

# Contraseña admin (cambiar en .env: ADMIN_PASSWORD)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def verificar_sesion(request: Request) -> bool:
    """Verifica si el usuario tiene sesión admin válida."""
    session_cookie = request.cookies.get("admin_session")
    return session_cookie == ADMIN_PASSWORD


async def obtener_todos_los_tickets() -> list[dict]:
    """Obtiene todos los tickets de Supabase."""
    if not is_supabase_enabled():
        logger.warning("Supabase no está configurado — no hay tickets")
        return []

    try:
        result = supabase_client.table("tickets").select("*").order("fecha_creacion", desc=True).limit(100).execute()
        if result.data:
            tickets_formateados = []
            for t in result.data:
                # Convertir timestamps a formato legible
                fecha_creacion = t.get("fecha_creacion", "")
                fecha_actualizacion = t.get("fecha_actualizacion", "")

                if fecha_creacion:
                    try:
                        fecha_creacion = datetime.fromisoformat(fecha_creacion.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
                    except:
                        pass

                if fecha_actualizacion:
                    try:
                        fecha_actualizacion = datetime.fromisoformat(fecha_actualizacion.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
                    except:
                        pass

                tickets_formateados.append({
                    "id": t.get("id"),
                    "ticket_numero": t.get("ticket_numero"),
                    "nombre_cliente": t.get("nombre_cliente"),
                    "telefono": t.get("telefono"),
                    "dispositivo": t.get("dispositivo"),
                    "problema": t.get("problema"),
                    "estado": t.get("estado", "abierto"),
                    "fecha_creacion": fecha_creacion,
                    "fecha_actualizacion": fecha_actualizacion,
                    "notas": t.get("notas", ""),
                })

            return tickets_formateados
        return []
    except Exception as e:
        logger.error(f"Error obteniendo tickets: {e}")
        return []


def generar_html_dashboard(tickets: list[dict]) -> str:
    """Genera el HTML del dashboard."""

    estados = {
        "abierto": "🆕 Abierto",
        "en_progreso": "⚙️ En progreso",
        "completado": "✅ Completado",
        "cerrado": "✓ Cerrado",
    }

    # Estadísticas
    total = len(tickets)
    abiertos = len([t for t in tickets if t["estado"] == "abierto"])
    en_progreso = len([t for t in tickets if t["estado"] == "en_progreso"])
    completados = len([t for t in tickets if t["estado"] == "completado"])

    filas_html = ""
    for t in tickets:
        estado_label = estados.get(t["estado"], t["estado"])
        notas_preview = t["notas"][:50] + "..." if len(t["notas"]) > 50 else t["notas"]

        filas_html += f"""
        <tr>
            <td class="numero">{t['ticket_numero']}</td>
            <td>{t['nombre_cliente']}</td>
            <td>{t['dispositivo']}</td>
            <td>{t['problema'][:30]}</td>
            <td>
                <select name="estado" onchange="cambiarEstado('{t['id']}', this.value)" class="estado-select {t['estado']}">
                    <option value="abierto" {'selected' if t['estado'] == 'abierto' else ''}>🆕 Abierto</option>
                    <option value="en_progreso" {'selected' if t['estado'] == 'en_progreso' else ''}>⚙️ En progreso</option>
                    <option value="completado" {'selected' if t['estado'] == 'completado' else ''}>✅ Completado</option>
                    <option value="cerrado" {'selected' if t['estado'] == 'cerrado' else ''}>✓ Cerrado</option>
                </select>
            </td>
            <td>{t['fecha_creacion']}</td>
            <td>
                <button onclick="abrirNotas('{t['id']}', '{t['ticket_numero']}')" class="btn-notas">Notas</button>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard — Tickets</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}

            .header h1 {{
                font-size: 28px;
                margin-bottom: 8px;
            }}

            .header p {{
                opacity: 0.9;
                font-size: 14px;
            }}

            .content {{
                padding: 30px;
            }}

            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .stat-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}

            .stat-card h3 {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                margin-bottom: 8px;
            }}

            .stat-card .numero {{
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
            }}

            .tabla-wrapper {{
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background: #f8f9fa;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #e9ecef;
            }}

            td {{
                padding: 15px;
                border-bottom: 1px solid #e9ecef;
            }}

            tr:hover {{
                background: #f8f9fa;
            }}

            .numero {{
                font-weight: bold;
                color: #667eea;
            }}

            .estado-select {{
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
            }}

            .estado-select.abierto {{
                background-color: #fff3cd;
                color: #856404;
            }}

            .estado-select.en_progreso {{
                background-color: #cfe2ff;
                color: #084298;
            }}

            .estado-select.completado {{
                background-color: #d1e7dd;
                color: #0f5132;
            }}

            .estado-select.cerrado {{
                background-color: #e2e3e5;
                color: #383d41;
            }}

            .btn-notas {{
                padding: 8px 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
            }}

            .btn-notas:hover {{
                background: #764ba2;
            }}

            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }}

            .modal-content {{
                background-color: white;
                margin: 5% auto;
                padding: 30px;
                border-radius: 12px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }}

            .modal-header {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 20px;
                color: #333;
            }}

            .modal-close {{
                float: right;
                font-size: 24px;
                cursor: pointer;
                color: #999;
            }}

            .modal-close:hover {{
                color: #333;
            }}

            textarea {{
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                font-family: inherit;
                min-height: 120px;
                margin-bottom: 15px;
                resize: vertical;
            }}

            .btn-guardar {{
                background: #667eea;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            }}

            .btn-guardar:hover {{
                background: #764ba2;
            }}

            .btn-cancelar {{
                background: #e9ecef;
                color: #333;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                margin-left: 10px;
            }}

            .btn-cancelar:hover {{
                background: #dee2e6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎫 Dashboard de Tickets</h1>
                <p>Gestión de reparaciones en tiempo real</p>
            </div>

            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <h3>Total</h3>
                        <div class="numero">{total}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Abiertos</h3>
                        <div class="numero">{abiertos}</div>
                    </div>
                    <div class="stat-card">
                        <h3>En progreso</h3>
                        <div class="numero">{en_progreso}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Completados</h3>
                        <div class="numero">{completados}</div>
                    </div>
                </div>

                <div class="tabla-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Ticket</th>
                                <th>Cliente</th>
                                <th>Dispositivo</th>
                                <th>Problema</th>
                                <th>Estado</th>
                                <th>Fecha</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filas_html if filas_html else '<tr><td colspan="7" style="text-align: center; padding: 40px;">No hay tickets registrados</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="notasModal" class="modal">
            <div class="modal-content">
                <span class="modal-close" onclick="cerrarNotas()">&times;</span>
                <div class="modal-header">Notas — <span id="ticketNumero"></span></div>
                <textarea id="notasText" placeholder="Agregar notas sobre este ticket..."></textarea>
                <button class="btn-guardar" onclick="guardarNotas()">Guardar</button>
                <button class="btn-cancelar" onclick="cerrarNotas()">Cancelar</button>
            </div>
        </div>

        <script>
            let ticketId = null;

            function abrirNotas(id, numero) {{
                ticketId = id;
                document.getElementById('ticketNumero').textContent = numero;
                document.getElementById('notasModal').style.display = 'block';
                // Aquí podrías hacer fetch para cargar las notas existentes
            }}

            function cerrarNotas() {{
                document.getElementById('notasModal').style.display = 'none';
                ticketId = null;
            }}

            function guardarNotas() {{
                const notas = document.getElementById('notasText').value;
                fetch('/admin/actualizar', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{id: ticketId, notas: notas}})
                }})
                .then(r => r.json())
                .then(data => {{
                    if (data.success) {{
                        alert('Notas guardadas ✓');
                        cerrarNotas();
                        location.reload();
                    }} else {{
                        alert('Error al guardar');
                    }}
                }});
            }}

            function cambiarEstado(id, nuevoEstado) {{
                fetch('/admin/actualizar', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{id: id, estado: nuevoEstado}})
                }})
                .then(r => r.json())
                .then(data => {{
                    if (!data.success) {{
                        alert('Error al actualizar estado');
                        location.reload();
                    }}
                }});
            }}

            window.onclick = function(event) {{
                const modal = document.getElementById('notasModal');
                if (event.target == modal) {{
                    cerrarNotas();
                }}
            }}
        </script>
    </body>
    </html>
    """

    return html


@admin_router.get("/admin")
async def dashboard(request: Request):
    """Muestra el dashboard (requiere sesión válida)."""
    if not verificar_sesion(request):
        # Mostrar login
        html_login = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Admin Login</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .login-box {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    width: 100%;
                    max-width: 400px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                    margin-bottom: 30px;
                }
                input {
                    width: 100%;
                    padding: 12px;
                    margin-bottom: 20px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                button {
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    cursor: pointer;
                }
                button:hover {
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h1>🔐 Admin</h1>
                <form method="post" action="/admin/login">
                    <input type="password" name="password" placeholder="Contraseña" required autofocus>
                    <button type="submit">Ingresar</button>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html_login)

    # Obtener tickets y mostrar dashboard
    tickets = await obtener_todos_los_tickets()
    html = generar_html_dashboard(tickets)

    response = HTMLResponse(html)
    response.set_cookie("admin_session", ADMIN_PASSWORD, max_age=604800)  # 7 días
    return response


@admin_router.post("/admin/login")
async def admin_login(request: Request, password: str = Form(...)):
    """Valida la contraseña y crea sesión."""
    if password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie("admin_session", ADMIN_PASSWORD, max_age=604800)
        return response
    else:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")


@admin_router.post("/admin/actualizar")
async def admin_actualizar(request: Request):
    """Actualiza estado o notas de un ticket."""
    if not verificar_sesion(request):
        raise HTTPException(status_code=401, detail="No autorizado")

    if not is_supabase_enabled():
        return {"success": False, "error": "Supabase no configurado"}

    try:
        data = await request.json()
        ticket_id = data.get("id")
        nuevo_estado = data.get("estado")
        nuevas_notas = data.get("notas")

        update_data = {}
        if nuevo_estado:
            update_data["estado"] = nuevo_estado
        if nuevas_notas is not None:
            update_data["notas"] = nuevas_notas

        if update_data:
            supabase_client.table("tickets").update(update_data).eq("id", ticket_id).execute()
            logger.info(f"Ticket {ticket_id} actualizado: {update_data}")
            return {"success": True}

        return {"success": False, "error": "No hay datos para actualizar"}

    except Exception as e:
        logger.error(f"Error actualizando ticket: {e}")
        return {"success": False, "error": str(e)}
