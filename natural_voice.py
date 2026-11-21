"""Server-side narration drafts. Playback and Android exports never call a TTS API."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import urllib.error
import urllib.request

from flask import Blueprint, abort, jsonify, request
from mutagen.mp3 import MP3

MODEL = 'eleven_multilingual_v2'
VOICE_SETTINGS = {'stability': .7, 'similarity_boost': .75, 'style': 0,
                  'use_speaker_boost': True}
LANGUAGES = {'pt', 'en', 'fr', 'it', 'es'}


class VoiceError(Exception):
    pass


def provider_request(path, payload=None):
    key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    if not key:
        raise VoiceError('not_configured')
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request('https://api.elevenlabs.io' + path, data=data,
        headers={'xi-api-key': key, 'Content-Type': 'application/json',
                 'Accept': 'audio/mpeg' if data else 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            body = response.read(20 * 1024 * 1024 + 1)
            if len(body) > 20 * 1024 * 1024:
                raise VoiceError('invalid_audio')
            return body
    except urllib.error.HTTPError as error:
        # Provider responses may include account details: never return them to clients.
        code = {401: 'provider_auth', 403: 'provider_auth', 404: 'voice_not_found',
                429: 'provider_quota'}.get(error.code, 'provider_unavailable')
        raise VoiceError(code) from None
    except (OSError, TimeoutError):
        raise VoiceError('provider_unavailable') from None


def source_for(db, sid, lang):
    row = db.execute('SELECT script FROM translations WHERE session_id=? AND lang=?',
                     (sid, lang)).fetchone()
    if not row:
        raise VoiceError('session_not_found')
    protocol = db.execute('SELECT content FROM exercise_protocols WHERE session_id=? AND lang=?',
                          (sid, lang)).fetchone()
    if protocol:
        steps = json.loads(protocol['content'])['steps']
        return [{'text': step['text'], 'seconds': step['seconds']} for step in steps]
    return [{'text': row['script'], 'seconds': None}]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def cached_segment(uploads, text, lang, voice, speed):
    signature = {'text': text, 'lang': lang, 'voice': voice, 'speed': speed,
                 'model': MODEL, 'settings': VOICE_SETTINGS, 'version': 1}
    filename = 'voice-' + digest(signature) + '.mp3'
    destination = uploads / filename
    if not destination.exists():
        audio = provider_request('/v1/text-to-speech/' + voice + '?output_format=mp3_44100_128',
            {'text': text, 'model_id': MODEL,
             'voice_settings': {**VOICE_SETTINGS, 'speed': speed}})
        temporary = uploads / ('.voice-' + secrets.token_hex(12) + '.tmp')
        try:
            temporary.write_bytes(audio)
            length = MP3(temporary).info.length
            if not math.isfinite(length) or length <= 0:
                raise VoiceError('invalid_audio')
            temporary.replace(destination)
        except VoiceError:
            raise
        except Exception:
            raise VoiceError('invalid_audio') from None
        finally:
            temporary.unlink(missing_ok=True)
    try:
        length = MP3(destination).info.length
    except Exception:
        raise VoiceError('invalid_audio') from None
    return {'audio_path': '/media/' + filename, 'duration': round(length, 3)}


def enrich_narration(db, item, lang):
    item['narration'] = {'kind': 'recorded'} if item.get('audio_path') else None
    if item.get('audio_path'):
        return item
    row = db.execute('SELECT source_hash, manifest FROM natural_narrations WHERE session_id=? AND lang=?',
                     (item['id'], lang)).fetchone()
    if not row or row['source_hash'] != digest(source_for(db, item['id'], lang)):
        return item
    manifest = json.loads(row['manifest'])
    item['narration'] = {'kind': 'ai', 'provider': 'elevenlabs', 'voice': manifest['voice']}
    if item.get('protocol'):
        for step, segment in zip(item['protocol']['steps'], manifest['segments']):
            step.update(segment)
    else:
        item['audio_path'] = manifest['segments'][0]['audio_path']
    return item


def setup_natural_voice(app, connect, uploads, admin_required, csrf_required):
    uploads = Path(uploads)
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS natural_narrations (
          session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
          lang TEXT NOT NULL, source_hash TEXT NOT NULL, manifest TEXT NOT NULL,
          PRIMARY KEY(session_id, lang));
        CREATE TABLE IF NOT EXISTS narration_jobs (
          id TEXT PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
          lang TEXT NOT NULL, signature TEXT NOT NULL, source_hash TEXT NOT NULL,
          status TEXT NOT NULL, error TEXT, manifest TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE UNIQUE INDEX IF NOT EXISTS narration_one_active_job
          ON narration_jobs((1)) WHERE status='running';
        ''')
        # The supported server uses one worker. A restart must not leave an eternal job.
        db.execute("UPDATE narration_jobs SET status='failed', error='interrupted' WHERE status='running'")
    bp = Blueprint('natural_voice', __name__)

    def job_data(row):
        return {'id': row['id'], 'session_id': row['session_id'], 'lang': row['lang'],
                'status': row['status'], 'error': row['error'],
                'manifest': json.loads(row['manifest']) if row['manifest'] else None}

    def generate(job_id, segments, lang, voice, speed):
        try:
            generated = []
            for segment in segments:
                clip = cached_segment(uploads, segment['text'], lang, voice, speed)
                if segment['seconds'] is not None and clip['duration'] > segment['seconds']:
                    raise VoiceError('audio_too_long')
                generated.append(clip)
            manifest = {'voice': voice, 'model': MODEL, 'speed': speed, 'segments': generated}
            with connect() as db:
                db.execute("UPDATE narration_jobs SET status='ready', manifest=? WHERE id=?",
                           (json.dumps(manifest), job_id))
        except Exception as error:
            code = str(error) if isinstance(error, VoiceError) else 'generation_failed'
            with connect() as db:
                db.execute("UPDATE narration_jobs SET status='failed', error=? WHERE id=?", (code, job_id))

    @bp.get('/api/admin/narration/options')
    @admin_required
    def options():
        configured = bool(os.getenv('ELEVENLABS_API_KEY', '').strip())
        voices = []
        if configured:
            try:
                data = json.loads(provider_request('/v2/voices?page_size=100&voice_type=default'))
                voices = [{'id': v['voice_id'], 'name': v['name']} for v in data.get('voices', [])]
            except (VoiceError, ValueError) as error:
                return jsonify(error=str(error) if isinstance(error, VoiceError) else 'provider_unavailable'), 502
        return jsonify(configured=configured, provider='elevenlabs', model=MODEL, voices=voices)

    @bp.post('/api/admin/narration')
    @admin_required
    def start():
        csrf_required()
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify(error='invalid_request'), 400
        try:
            sid = int(data.get('session_id', 0))
            speed = float(data.get('speed', .9))
        except (TypeError, ValueError):
            return jsonify(error='invalid_request'), 400
        lang, voice = data.get('lang'), data.get('voice')
        if not isinstance(lang, str) or lang not in LANGUAGES or not isinstance(voice, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', voice) or not .8 <= speed <= 1.05:
            return jsonify(error='invalid_request'), 400
        with connect() as db:
            try:
                segments = source_for(db, sid, lang)
            except VoiceError:
                return jsonify(error='session_not_found'), 404
            if not segments or any(not s['text'].strip() or len(s['text']) > 10000 for s in segments):
                return jsonify(error='text_too_long'), 400
            signature = digest([segments, lang, voice, speed, MODEL, VOICE_SETTINGS])
            existing = db.execute("SELECT * FROM narration_jobs WHERE signature=? AND status IN ('running','ready','published') ORDER BY created_at DESC LIMIT 1", (signature,)).fetchone()
            if existing and existing['status'] != 'running':
                saved = json.loads(existing['manifest'])
                if any(not (uploads / Path(s['audio_path']).name).is_file() for s in saved['segments']):
                    db.execute("UPDATE narration_jobs SET status='failed', error='missing_audio' WHERE id=?", (existing['id'],))
                    existing = None
            if existing:
                return jsonify(job_data(existing)), 202 if existing['status'] == 'running' else 200
            if not os.getenv('ELEVENLABS_API_KEY', '').strip():
                return jsonify(error='not_configured'), 503
            job_id = secrets.token_hex(16)
            try:
                db.execute("INSERT INTO narration_jobs(id,session_id,lang,signature,source_hash,status) VALUES(?,?,?,?,?,'running')",
                           (job_id, sid, lang, signature, digest(segments)))
            except sqlite3.IntegrityError:
                return jsonify(error='generation_busy'), 409
        worker = threading.Thread(target=generate, args=(job_id, segments, lang, voice, speed), daemon=True)
        worker.start()
        return jsonify(id=job_id, session_id=sid, lang=lang, status='running', error=None, manifest=None), 202

    @bp.get('/api/admin/narration/<job_id>')
    @admin_required
    def status(job_id):
        with connect() as db:
            row = db.execute('SELECT * FROM narration_jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                abort(404)
            return jsonify(job_data(row))

    @bp.post('/api/admin/narration/<job_id>/publish')
    @admin_required
    def publish(job_id):
        csrf_required()
        with connect() as db:
            row = db.execute('SELECT * FROM narration_jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                abort(404)
            if row['status'] not in ('ready', 'published'):
                return jsonify(error='not_ready'), 409
            if row['source_hash'] != digest(source_for(db, row['session_id'], row['lang'])):
                return jsonify(error='source_changed'), 409
            manifest = json.loads(row['manifest'])
            if any(not (uploads / Path(s['audio_path']).name).is_file() for s in manifest['segments']):
                return jsonify(error='missing_audio'), 409
            db.execute('INSERT OR REPLACE INTO natural_narrations(session_id,lang,source_hash,manifest) VALUES(?,?,?,?)',
                       (row['session_id'], row['lang'], row['source_hash'], row['manifest']))
            db.execute('UPDATE translations SET audio_path=NULL WHERE session_id=? AND lang=?',
                       (row['session_id'], row['lang']))
            db.execute("UPDATE narration_jobs SET status='published' WHERE id=?", (job_id,))
        return jsonify(ok=True)

    app.register_blueprint(bp)
