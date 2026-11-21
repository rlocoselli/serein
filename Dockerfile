FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEREIN_DB=/data/serein.db \
    SEREIN_UPLOADS=/data/uploads \
    KOKORO_MODEL_DIR=/opt/kokoro \
    KOKORO_THREADS=2

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libstdc++6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY web-meditation/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt "gunicorn>=23,<24" \
    && groupadd --gid 10001 serein \
    && useradd --uid 10001 --gid serein --no-create-home serein \
    && mkdir -p /data/uploads \
    && chown -R serein:serein /data

COPY web-meditation/scripts/prepare_kokoro.py ./scripts/
COPY web-meditation/licenses/kokoro/ ./licenses/kokoro/
RUN python scripts/prepare_kokoro.py

COPY web-meditation/app.py web-meditation/seo.py web-meditation/natural_voice.py web-meditation/kokoro_engine.py web-meditation/exercise_seed.json web-meditation/story_seed.json ./
COPY web-meditation/templates/ ./templates/
COPY web-meditation/static/ ./static/

USER serein
VOLUME ["/data"]
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '5000') + '/api/sessions?lang=pt', timeout=3).read()"]

# One process initializes the SQLite seed; threads handle concurrent requests.
CMD ["sh", "-c", "exec gunicorn --bind \"0.0.0.0:${PORT:-5000}\" --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app"]
