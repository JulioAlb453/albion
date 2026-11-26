# API del gremio (FastAPI + SQLite). Se construye desde la carpeta backend/.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Las dependencias salen de pyproject.toml (una sola fuente de verdad) y van en su propia capa:
# solo se reinstalan cuando cambian, no con cada cambio del código.
COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > requisitos.txt \
    && pip install -r requisitos.txt

COPY src ./src
COPY scripts ./scripts

# Sin permisos de administrador dentro del contenedor.
RUN useradd --create-home --uid 10001 gremio \
    && mkdir -p /app/data /app/respaldos \
    && chown -R gremio:gremio /app/data /app/respaldos
USER gremio

# La base y las copias viven en carpetas que el compose monta desde tu PC.
ENV GREMIO_DB=/app/data/gremio.db \
    GREMIO_RESPALDOS_DIR=/app/respaldos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/salud', timeout=3)"

CMD ["python", "-m", "uvicorn", "src.bootstrap.produccion:crear_app_desde_entorno", "--factory", "--host", "0.0.0.0", "--port", "8000"]
