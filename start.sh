#!/bin/bash
# Produccion: arranca el servidor directamente
exec uvicorn agent.main:app --host 0.0.0.0 --port ${PORT:-8000}
