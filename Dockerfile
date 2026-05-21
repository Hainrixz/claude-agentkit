FROM python:3.11-slim

# Usuario no-root: si alguien comprometiera el contenedor no tendría root
RUN useradd --create-home --uid 1000 agentkit

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=agentkit:agentkit . .

USER agentkit

EXPOSE 8000

# Healthcheck para Railway/Docker — verifica que el server responde
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/').status == 200 else 1)"

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
