FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=2

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 careerpilot \
    && mkdir -p /app/backend /app/.local/whisper \
    && chown -R careerpilot:careerpilot /app

WORKDIR /app/backend

COPY requirements.txt ./
RUN python -m pip install --requirement requirements.txt

COPY --chown=careerpilot:careerpilot app ./app
COPY --chown=careerpilot:careerpilot alembic ./alembic
COPY --chown=careerpilot:careerpilot alembic.ini ./alembic.ini

USER careerpilot

# Include the speech model so the first interview does not download it at runtime.
RUN python -c "from app.interview.transcription import whisper_model; whisper_model()"

EXPOSE 8000

# Check the process without repeatedly waking the Neon database.
HEALTHCHECK --interval=60s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), timeout=3).close()"

CMD ["sh", "-c", "python -m alembic upgrade head && exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
