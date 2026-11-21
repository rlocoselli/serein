import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from flask import Flask, jsonify, session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Import production auth decorators without opening the user's database.
IMPORT_SANDBOX = tempfile.TemporaryDirectory(prefix='serein-voice-import-')
if 'app' not in sys.modules:
    os.environ['SEREIN_DB'] = str(Path(IMPORT_SANDBOX.name) / 'import.db')
    os.environ['SEREIN_UPLOADS'] = str(Path(IMPORT_SANDBOX.name) / 'uploads')
from app import admin_required, csrf_required
import natural_voice as voice

MP3 = (b'\xff\xfb\x90\x64' + bytes(413)) * 40


class InlineThread:
    def __init__(self, target, args, **kwargs):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


class NaturalVoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='serein-voice-test-')
        self.addCleanup(self.temp.cleanup)
        self.uploads = Path(self.temp.name) / 'uploads'
        self.uploads.mkdir()
        path = Path(self.temp.name) / 'test.db'

        def connect():
            db = sqlite3.connect(path)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            return db
        self.connect = connect
        with connect() as db:
            db.executescript('''CREATE TABLE sessions(id INTEGER PRIMARY KEY);
            INSERT INTO sessions VALUES(1);
            CREATE TABLE translations(session_id INTEGER, lang TEXT, script TEXT, audio_path TEXT);
            CREATE TABLE exercise_protocols(session_id INTEGER, lang TEXT, content TEXT);''')
            for lang in ('pt', 'en', 'fr', 'it', 'es'):
                db.execute('INSERT INTO translations VALUES(1,?,?,NULL)', (lang, 'Breathe. Rest.'))
                db.execute('INSERT INTO exercise_protocols VALUES(1,?,?)',
                    (lang, json.dumps({'steps': [{'text': 'Breathe.', 'seconds': 30}, {'text': 'Rest.', 'seconds': 30}]})))
        self.app = Flask(__name__)
        self.app.secret_key = 'test-only'
        voice.setup_natural_voice(self.app, connect, self.uploads, admin_required, csrf_required)
        self.client = self.app.test_client()
        self.key = patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only-provider-key'})
        self.key.start()
        self.addCleanup(self.key.stop)
        threads = patch.object(voice.threading, 'Thread', InlineThread)
        threads.start()
        self.addCleanup(threads.stop)
        with self.client.session_transaction() as s:
            s['admin'], s['csrf'] = True, 'test-csrf'

    def start(self, **changes):
        return self.client.post('/api/admin/narration',
            json={'session_id': 1, 'lang': 'pt', 'voice': 'testvoice', 'speed': .9, **changes},
            headers={'X-CSRF-Token': 'test-csrf'})

    def job(self, response):
        return self.client.get('/api/admin/narration/' + response.json['id']).json

    def publish(self, job):
        return self.client.post('/api/admin/narration/' + job['id'] + '/publish', headers={'X-CSRF-Token': 'test-csrf'})

    def item(self, lang='pt'):
        with self.connect() as db:
            protocol = json.loads(db.execute('SELECT content FROM exercise_protocols WHERE lang=?', (lang,)).fetchone()[0])
            return voice.enrich_narration(db, {'id': 1, 'audio_path': None, 'protocol': protocol}, lang)

    def test_admin_and_csrf_protect_paid_generation(self):
        with patch.object(voice, 'provider_request') as provider:
            self.assertEqual(self.client.post('/api/admin/narration', json={}).status_code, 403)
            with self.client.session_transaction() as s:
                s.clear()
            self.assertEqual(self.start().status_code, 401)
            self.assertEqual(self.client.get('/api/admin/narration/options').status_code, 401)
            provider.assert_not_called()

    def test_missing_key_and_invalid_inputs_make_no_provider_calls(self):
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}), patch.object(voice, 'provider_request') as provider:
            self.assertFalse(self.client.get('/api/admin/narration/options').json['configured'])
            self.assertEqual(self.start().status_code, 503)
            provider.assert_not_called()
        for changes in ({'lang': []}, {'voice': '../../bad'}, {'speed': 'nan'}, {'speed': .2}, {'session_id': 'bad'}):
            self.assertEqual(self.start(**changes).status_code, 400)

    def test_draft_is_not_public_until_review_and_repeated_requests_are_cached(self):
        with patch.object(voice, 'provider_request', return_value=MP3) as provider:
            response = self.start()
            self.assertEqual(response.status_code, 202)
            job = self.job(response)
            self.assertEqual(job['status'], 'ready')
            self.assertIsNone(self.item()['narration'])
            self.assertEqual(self.publish(job).status_code, 200)
            self.assertEqual(self.item()['narration']['kind'], 'ai')
            self.assertTrue(all(s.get('audio_path') for s in self.item()['protocol']['steps']))
            self.assertIsNone(self.item('fr')['narration'])
            self.assertEqual(self.start().status_code, 200)
            self.assertEqual(provider.call_count, 2)

    def test_failure_preserves_active_voice_and_retry_reuses_saved_clips(self):
        with patch.object(voice, 'provider_request', return_value=MP3):
            first = self.job(self.start())
            self.publish(first)
        old = self.item()['protocol']['steps'][0]['audio_path']
        with patch.object(voice, 'provider_request', side_effect=[MP3, voice.VoiceError('provider_quota')]) as provider:
            failed = self.job(self.start(speed=1))
            self.assertEqual(failed['status'], 'failed')
            self.assertEqual(failed['error'], 'provider_quota')
            self.assertEqual(self.item()['protocol']['steps'][0]['audio_path'], old)
            self.assertEqual(self.publish(failed).status_code, 409)
        with patch.object(voice, 'provider_request', return_value=MP3) as provider:
            ready = self.job(self.start(speed=1))
            self.assertEqual(ready['status'], 'ready')
            self.assertEqual(provider.call_count, 1)

    def test_changed_text_requires_new_recording(self):
        with patch.object(voice, 'provider_request', return_value=MP3):
            job = self.job(self.start())
        with self.connect() as db:
            protocol = {'steps': [{'text': 'Different guidance.', 'seconds': 30}]}
            db.execute('UPDATE exercise_protocols SET content=? WHERE lang=?', (json.dumps(protocol), 'pt'))
        self.assertEqual(self.publish(job).json['error'], 'source_changed')
        self.assertIsNone(self.item()['narration'])

    def test_overlong_or_invalid_audio_cannot_be_published(self):
        with self.connect() as db:
            db.execute('UPDATE exercise_protocols SET content=?', (json.dumps({'steps': [{'text': 'Breathe.', 'seconds': .1}]}),))
        with patch.object(voice, 'provider_request', return_value=MP3):
            job = self.job(self.start())
        self.assertEqual(job['error'], 'audio_too_long')
        self.assertEqual(self.publish(job).status_code, 409)
        with patch.object(voice, 'provider_request', return_value=b'not an mp3'):
            bad = self.job(self.start(speed=1))
        self.assertEqual(bad['error'], 'invalid_audio')
        self.assertFalse(list(self.uploads.glob('*.tmp')))

    def test_lost_media_can_be_regenerated(self):
        with patch.object(voice, 'provider_request', return_value=MP3):
            job = self.job(self.start())
        (self.uploads / Path(job['manifest']['segments'][0]['audio_path']).name).unlink()
        self.assertEqual(self.publish(job).json['error'], 'missing_audio')
        with patch.object(voice, 'provider_request', return_value=MP3) as provider:
            recovered = self.job(self.start())
            self.assertEqual(recovered['status'], 'ready')
            self.assertEqual(provider.call_count, 1)

    def test_provider_errors_do_not_expose_account_details_or_key(self):
        error = urllib.error.HTTPError('https://api.elevenlabs.io', 401, 'secret account details', {}, io.BytesIO(b'private'))
        with patch.object(voice.urllib.request, 'urlopen', side_effect=error):
            response = self.client.get('/api/admin/narration/options')
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json, {'error': 'provider_auth'})

    def test_only_one_paid_job_can_run_at_a_time(self):
        with self.connect() as db:
            db.execute("INSERT INTO narration_jobs(id,session_id,lang,signature,source_hash,status) VALUES('busy',1,'fr','other','other','running')")
        with patch.object(voice, 'provider_request') as provider:
            response = self.start()
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json['error'], 'generation_busy')
            provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
