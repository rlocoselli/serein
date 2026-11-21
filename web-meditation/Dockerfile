FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEREIN_DB=/data/serein.db \
    SEREIN_UPLOADS=/data/uploads

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt "gunicorn>=23,<24" \
    && groupadd --gid 10001 serein \
    && useradd --uid 10001 --gid serein --no-create-home serein \
    && mkdir -p /data/uploads \
    && chown -R serein:serein /data

COPY app.py natural_voice.py exercise_seed.json story_seed.json ./
COPY static/ ./static/

USER serein
VOLUME ["/data"]
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '5000') + '/api/sessions?lang=pt', timeout=3).read()"]

# One process initializes the SQLite seed; threads handle concurrent requests.
CMD ["sh", "-c", "exec gunicorn --bind \"0.0.0.0:${PORT:-5000}\" --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:app"]
