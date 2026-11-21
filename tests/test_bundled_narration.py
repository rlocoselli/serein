"""A new deployment must serve voice files without admin activation or inference."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BundledNarrationTests(unittest.TestCase):
    def test_fresh_installation_has_playable_recordings_for_every_bundled_locale(self):
        catalog = json.loads((ROOT / 'static/narration/catalog.json').read_text())
        locales = sorted({locale for entry in catalog['sessions'].values() for locale in entry})
        self.assertEqual(set(locales), {'fr', 'pt', 'en', 'it', 'es'})
        self.assertEqual(len(catalog['sessions']), 16)
        for translations in catalog['sessions'].values():
            self.assertEqual(set(translations), set(locales))
        with tempfile.TemporaryDirectory(prefix='serein-bundled-voices-') as directory:
            env = {**os.environ, 'SEREIN_DB': str(Path(directory) / 'fresh.db'),
                   'SEREIN_UPLOADS': str(Path(directory) / 'uploads'),
                   'SEREIN_TEST_LOCALES': json.dumps(locales)}
            code = '''
import json, os, sys
from pathlib import Path
from unittest.mock import patch
from app import app
client=app.test_client()
with patch('natural_voice.synthesize_to_wav',side_effect=AssertionError('No inference for bundled audio')):
 for locale in json.loads(os.environ['SEREIN_TEST_LOCALES']):
  response=client.get('/api/sessions?lang='+locale)
  assert response.status_code==200
  assert len(response.json)==16
  for item in response.json:
   assert item['narration']['provider']=='kokoro',(locale,item['slug'])
   clips=item['protocol']['steps'] if item['protocol'] else [item]
   for clip in clips:
    assert clip['audio_path'].startswith('/narration/')
    assert (Path('static')/clip['audio_path'].lstrip('/')).is_file()
   audio=client.get(clips[0]['audio_path'],headers={'Range':'bytes=0-127'})
   assert audio.status_code==206,(locale,item['slug'])
   assert audio.content_type.startswith('audio/mpeg')
   assert len(audio.data)==128
assert 'onnxruntime' not in sys.modules,'Playback must not load the inference runtime'
'''
            result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
