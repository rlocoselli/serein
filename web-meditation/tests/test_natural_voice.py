import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

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

def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(24000)
        output.writeframes(bytes(48000))
    return buffer.getvalue()


AUDIO = wav_bytes()


def write_audio(destination, *args):
    Path(destination).write_bytes(AUDIO)


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
        self.ready = patch.object(voice, 'readiness', return_value={'ready': True, 'error': None})
        self.ready.start()
        self.addCleanup(self.ready.stop)
        threads = patch.object(voice.threading, 'Thread', InlineThread)
        threads.start()
        self.addCleanup(threads.stop)
        with self.client.session_transaction() as s:
            s['admin'], s['csrf'] = True, 'test-csrf'

    def start(self, **changes):
        return self.client.post('/api/admin/narration',
            json={'session_id': 1, 'lang': 'pt', 'voice': 'pf_dora', 'speed': .9, **changes},
            headers={'X-CSRF-Token': 'test-csrf'})

    def job(self, response):
        return self.client.get('/api/admin/narration/' + response.json['id']).json

    def publish(self, job):
        return self.client.post('/api/admin/narration/' + job['id'] + '/publish', headers={'X-CSRF-Token': 'test-csrf'})

    def item(self, lang='pt'):
        with self.connect() as db:
            protocol = json.loads(db.execute('SELECT content FROM exercise_protocols WHERE lang=?', (lang,)).fetchone()[0])
            return voice.enrich_narration(db, {'id': 1, 'audio_path': None, 'protocol': protocol}, lang)

    def test_admin_and_csrf_protect_generation(self):
        with patch.object(voice, 'synthesize_to_wav') as provider:
            self.assertEqual(self.client.post('/api/admin/narration', json={}).status_code, 403)
            with self.client.session_transaction() as s:
                s.clear()
            self.assertEqual(self.start().status_code, 401)
            self.assertEqual(self.client.get('/api/admin/narration/options').status_code, 401)
            provider.assert_not_called()

    def test_missing_models_and_invalid_inputs_do_not_synthesize(self):
        with patch.object(voice, 'readiness', return_value={'ready': False, 'error': 'models_missing'}), patch.object(voice, 'synthesize_to_wav') as provider:
            options = self.client.get('/api/admin/narration/options').json
            self.assertFalse(options['configured'])
            self.assertEqual(options['provider'], 'kokoro')
            self.assertEqual(self.start().status_code, 503)
            provider.assert_not_called()
        for changes in ({'lang': []}, {'voice': '../../bad'}, {'voice': 'ff_siwis'}, {'speed': 'nan'}, {'speed': .2}, {'session_id': 'bad'}):
            self.assertEqual(self.start(**changes).status_code, 400)

    def test_options_are_local_and_cover_the_five_languages(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('No HTTP allowed')):
            options = self.client.get('/api/admin/narration/options').json
        self.assertTrue(options['configured'])
        self.assertEqual({v['lang'] for v in options['voices']}, {'pt', 'en', 'fr', 'it', 'es'})
        self.assertTrue(all(v['locale']=='pt-br' for v in options['voices'] if v['lang']=='pt'))

    def test_draft_is_not_public_until_review_and_repeated_requests_are_cached(self):
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio) as provider:
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
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio):
            first = self.job(self.start())
            self.publish(first)
        old = self.item()['protocol']['steps'][0]['audio_path']
        calls = []
        def fail_second(destination, *args):
            calls.append(destination)
            if len(calls) == 2: raise voice.VoiceError('generation_failed')
            write_audio(destination)
        with patch.object(voice, 'synthesize_to_wav', side_effect=fail_second) as provider:
            failed = self.job(self.start(speed=1))
            self.assertEqual(failed['status'], 'failed')
            self.assertEqual(failed['error'], 'generation_failed')
            self.assertEqual(self.item()['protocol']['steps'][0]['audio_path'], old)
            self.assertEqual(self.publish(failed).status_code, 409)
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio) as provider:
            ready = self.job(self.start(speed=1))
            self.assertEqual(ready['status'], 'ready')
            self.assertEqual(provider.call_count, 1)

    def test_changed_text_requires_new_recording(self):
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio):
            job = self.job(self.start())
        with self.connect() as db:
            protocol = {'steps': [{'text': 'Different guidance.', 'seconds': 30}]}
            db.execute('UPDATE exercise_protocols SET content=? WHERE lang=?', (json.dumps(protocol), 'pt'))
        self.assertEqual(self.publish(job).json['error'], 'source_changed')
        self.assertIsNone(self.item()['narration'])

    def test_overlong_or_invalid_audio_cannot_be_published(self):
        with self.connect() as db:
            db.execute('UPDATE exercise_protocols SET content=?', (json.dumps({'steps': [{'text': 'Breathe.', 'seconds': .1}]}),))
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio):
            job = self.job(self.start())
        self.assertEqual(job['error'], 'audio_too_long')
        self.assertEqual(self.publish(job).status_code, 409)
        with patch.object(voice, 'synthesize_to_wav', side_effect=lambda path, *args: Path(path).write_bytes(b'not wav')):
            bad = self.job(self.start(speed=1))
        self.assertEqual(bad['error'], 'invalid_audio')
        self.assertFalse(list(self.uploads.glob('*.tmp')))

    def test_lost_media_can_be_regenerated(self):
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio):
            job = self.job(self.start())
        (self.uploads / Path(job['manifest']['segments'][0]['audio_path']).name).unlink()
        self.assertEqual(self.publish(job).json['error'], 'missing_audio')
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio) as provider:
            recovered = self.job(self.start())
            self.assertEqual(recovered['status'], 'ready')
            self.assertEqual(provider.call_count, 1)

    def test_generation_errors_do_not_expose_local_server_details(self):
        with patch.object(voice, 'synthesize_to_wav', side_effect=RuntimeError('private server details')):
            job = self.job(self.start())
        self.assertEqual(job['status'], 'failed')
        self.assertEqual(job['error'], 'generation_failed')
        self.assertNotIn('private server details', json.dumps(job))

    def test_kokoro_publication_sets_accurate_provenance(self):
        with patch.object(voice, 'synthesize_to_wav', side_effect=write_audio):
            job = self.job(self.start())
        self.publish(job)
        self.assertEqual(self.item()['narration']['provider'], 'kokoro')
        self.assertTrue(self.item()['protocol']['steps'][0]['audio_path'].endswith('.wav'))

    def test_only_one_generation_job_can_run_at_a_time(self):
        with self.connect() as db:
            db.execute("INSERT INTO narration_jobs(id,session_id,lang,signature,source_hash,status) VALUES('busy',1,'fr','other','other','running')")
        with patch.object(voice, 'synthesize_to_wav') as provider:
            response = self.start()
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json['error'], 'generation_busy')
            provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
