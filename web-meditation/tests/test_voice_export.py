"""Exercise the real Flask catalog and APK exporter with isolated, simulated audio."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VoiceExportTests(unittest.TestCase):
    def test_published_step_audio_is_bundled_without_provider_credentials(self):
        with tempfile.TemporaryDirectory(prefix='serein-voice-export-') as directory:
            root = Path(directory)
            for name in ('app.py', 'natural_voice.py', 'exercise_seed.json', 'story_seed.json'):
                shutil.copy2(ROOT / name, root / name)
            (root / 'scripts').mkdir()
            shutil.copy2(ROOT / 'scripts/export_android_assets.py', root / 'scripts/export_android_assets.py')
            shutil.copytree(ROOT / 'static', root / 'static')
            env = {**os.environ, 'SEREIN_DB': str(root / 'test.db'),
                   'SEREIN_UPLOADS': str(root / 'uploads'),
                   'ELEVENLABS_API_KEY': 'test-provider-key-do-not-export'}
            code = r'''
import json, runpy
from pathlib import Path
from unittest.mock import patch
from app import app
import natural_voice
audio=(b'\xff\xfb\x90\x64'+bytes(413))*40
class InlineThread:
 def __init__(self,target,args,**kw):self.target,self.args=target,args
 def start(self):self.target(*self.args)
client=app.test_client()
with client.session_transaction() as session:session['admin']=True;session['csrf']='test-csrf'
item=next(x for x in client.get('/api/sessions?lang=fr').json if x['slug']=='respiracao-suave')
with patch.object(natural_voice,'provider_request',return_value=audio) as provider, patch.object(natural_voice.threading,'Thread',InlineThread):
 response=client.post('/api/admin/narration',json={'session_id':item['id'],'lang':'fr','voice':'testvoice','speed':.9},headers={'X-CSRF-Token':'test-csrf'})
 assert response.status_code==202,response.json
 job=client.get('/api/admin/narration/'+response.json['id']).json
 assert job['status']=='ready',job
 assert client.post('/api/admin/narration/'+job['id']+'/publish',headers={'X-CSRF-Token':'test-csrf'}).status_code==200
 runpy.run_path('scripts/export_android_assets.py')
 assert provider.call_count==len(item['protocol']['steps'])
out=Path('android/app/src/main/assets/web')
sessions=json.loads((out/'data/sessions-fr.json').read_text())
published=next(x for x in sessions if x['id']==item['id'])
assert published['narration']['kind']=='ai'
for step in published['protocol']['steps']:assert (out/step['audio_path'].lstrip('/')).read_bytes()==audio
others=json.loads((out/'data/sessions-pt.json').read_text())
assert next(x for x in others if x['id']==item['id'])['narration'] is None
assert not any('test-provider-key-do-not-export' in p.read_text() for p in out.rglob('*') if p.suffix in ('.js','.json','.html'))
print('Published French step narration bundled; other locales unchanged; no provider key exported.')
'''
            result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
