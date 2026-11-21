"""Server-side narration drafts. Playback and Android exports never call a TTS API."""
import hashlib
import json
import math
from pathlib import Path
import secrets
import sqlite3
import threading
import wave
from functools import lru_cache

from flask import Blueprint, abort, jsonify, request
from kokoro_engine import MODEL, VOICES, VOICE_SETTINGS, VoiceError, readiness, synthesize_to_wav
LANGUAGES = {'pt', 'en', 'fr', 'it', 'es'}
BUNDLED_CATALOG = Path(__file__).parent / 'static/narration/catalog.json'


@lru_cache(maxsize=4)
def bundled_catalog(path, modified):
    return json.loads(path.read_text())['sessions']


def bundled_narration(item, lang):
    if not item.get('slug') or not BUNDLED_CATALOG.is_file():
        return None
    catalogue = bundled_catalog(BUNDLED_CATALOG, BUNDLED_CATALOG.stat().st_mtime_ns)
    manifest = catalogue.get(item['slug'], {}).get(lang)
    if manifest:
        root = BUNDLED_CATALOG.parent.parent
        if all((root / clip['audio_path'].lstrip('/')).is_file() for clip in manifest['segments']):
            return manifest
    return None


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
                 'model': MODEL, 'settings': VOICE_SETTINGS, 'version': 2}
    filename = 'voice-' + digest(signature) + '.wav'
    destination = uploads / filename
    if not destination.exists():
        temporary = uploads / ('.voice-' + secrets.token_hex(12) + '.tmp')
        try:
            synthesize_to_wav(temporary, text, lang, voice, speed)
            with wave.open(str(temporary), 'rb') as audio:
                length = audio.getnframes() / audio.getframerate()
            if not math.isfinite(length) or length <= 0:
                raise VoiceError('invalid_audio')
            temporary.replace(destination)
        except VoiceError:
            raise
        except (wave.Error, EOFError, ZeroDivisionError):
            raise VoiceError('invalid_audio') from None
        finally:
            temporary.unlink(missing_ok=True)
    try:
        with wave.open(str(destination), 'rb') as audio:
            length = audio.getnframes() / audio.getframerate()
    except Exception:
        raise VoiceError('invalid_audio') from None
    return {'audio_path': '/media/' + filename, 'duration': round(length, 3)}


def enrich_narration(db, item, lang):
    item['narration'] = {'kind': 'recorded'} if item.get('audio_path') else None
    if item.get('audio_path'):
        return item
    row = db.execute('SELECT source_hash, manifest FROM natural_narrations WHERE session_id=? AND lang=?',
                     (item['id'], lang)).fetchone()
    source_hash = digest(source_for(db, item['id'], lang)) if row else None
    if row and row['source_hash'] == source_hash:
        manifest = json.loads(row['manifest'])
    else:
        manifest = bundled_narration(item, lang)
        if manifest and manifest['source_hash'] != (source_hash or digest(source_for(db, item['id'], lang))):
            manifest = None
    if not manifest:
        return item
    # Existing recordings survive migration; their original provenance stays accurate.
    item['narration'] = {'kind': 'ai', 'provider': manifest.get('provider', 'elevenlabs'), 'voice': manifest['voice']}
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
            manifest = {'provider': 'kokoro', 'voice': voice, 'model': MODEL, 'speed': speed, 'segments': generated}
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
        status = readiness()
        return jsonify(configured=status['ready'], error=status['error'], provider='kokoro',
                       model=MODEL, voices=VOICES)

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
        if not isinstance(lang, str) or lang not in LANGUAGES or not isinstance(voice, str) or not any(v['id'] == voice and v['lang'] == lang for v in VOICES) or not .8 <= speed <= 1.05:
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
            status = readiness()
            if not status['ready']:
                return jsonify(error=status['error']), 503
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
