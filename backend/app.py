"""Serein content API. Run locally with: python app.py"""

import os
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
CORS(app, resources={r"/v1/*": {"origins": origins or "*"}})

# A lightweight local safeguard. Use a shared limiter such as Redis in production.
requests_by_ip: dict[str, deque[datetime]] = defaultdict(deque)
WINDOW = timedelta(minutes=10)
MAX_REQUESTS = 12
SUPPORTED_LANGUAGES = {"pt", "fr", "it", "en"}
SUPPORTED_INTENTIONS = {"respirar", "dormir", "pausa", "refletir"}


def is_rate_limited(ip: str) -> bool:
    now = datetime.now(timezone.utc)
    bucket = requests_by_ip[ip]
    while bucket and now - bucket[0] > WINDOW:
        bucket.popleft()
    if len(bucket) >= MAX_REQUESTS:
        return True
    bucket.append(now)
    return False


@app.get("/health")
def health():
    return {"status": "ok", "service": "serein-content-api"}


@app.post("/v1/relaxation-text")
def relaxation_text():
    if is_rate_limited(request.remote_addr or "unknown"):
        return jsonify(error="Muitas solicitações. Tente novamente em alguns minutos."), 429

    data = request.get_json(silent=True) or {}
    language = data.get("language", "pt")
    intention = data.get("intention", "pausa")
    feeling = str(data.get("feeling", "")).strip()

    if language not in SUPPORTED_LANGUAGES or intention not in SUPPORTED_INTENTIONS:
        return jsonify(error="Parâmetros inválidos."), 400
    if len(feeling) > 280:
        return jsonify(error="A sua mensagem deve ter no máximo 280 caracteres."), 400
    if not os.getenv("OPENAI_API_KEY"):
        return jsonify(error="O serviço de IA ainda não foi configurado."), 503

    prompt = f"""Create one short, gentle relaxation practice in {language}.
The chosen intention is: {intention}. The person optionally wrote: {feeling or 'no additional context'}.

Return plain text with: a warm title, 3 to 5 short guided sentences, and a final grounding sentence.
Tone: calm, inclusive, non-religious, and practical. Do not diagnose, prescribe, claim therapeutic effects,
mention Bach flower remedies as treatment, or make claims about healing frequencies. Do not give crisis advice.
If the person expresses immediate danger or self-harm, gently encourage contacting local emergency services
or a trusted person now. Keep the response below 150 words."""

    try:
        client = OpenAI()
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5"),
            input=prompt,
            store=False,
            max_output_tokens=280,
        )
        text = response.output_text.strip()
        if not text:
            raise RuntimeError("Empty model response")
        return jsonify(text=text)
    except Exception:
        app.logger.exception("Unable to create relaxation text")
        return jsonify(error="Não foi possível criar o texto agora. Tente novamente."), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
