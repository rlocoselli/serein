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
    def test_published_step_audio_is_bundled_without_the_inference_engine(self):
        with tempfile.TemporaryDirectory(prefix='serein-voice-export-') as directory:
            root = Path(directory)
            for name in ('app.py', 'natural_voice.py', 'kokoro_engine.py', 'exercise_seed.json', 'story_seed.json'):
                shutil.copy2(ROOT / name, root / name)
            (root / 'scripts').mkdir()
            shutil.copy2(ROOT / 'scripts/export_android_assets.py', root / 'scripts/export_android_assets.py')
            shutil.copytree(ROOT / 'static', root / 'static')
            env = {**os.environ, 'SEREIN_DB': str(root / 'test.db'),
                   'SEREIN_UPLOADS': str(root / 'uploads')}
            code = r'''
import json, runpy, io, wave
from pathlib import Path
from unittest.mock import patch
from app import app
import natural_voice
buffer=io.BytesIO()
with wave.open(buffer,'wb') as out:
 out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000);out.writeframes(bytes(48000))
audio=buffer.getvalue()
def synthesize(path,*args):Path(path).write_bytes(audio)
class InlineThread:
 def __init__(self,target,args,**kw):self.target,self.args=target,args
 def start(self):self.target(*self.args)
client=app.test_client()
with client.session_transaction() as session:session['admin']=True;session['csrf']='test-csrf'
item=next(x for x in client.get('/api/sessions?lang=fr').json if x['slug']=='respiracao-suave')
with patch.object(natural_voice,'synthesize_to_wav',side_effect=synthesize) as provider, patch.object(natural_voice,'readiness',return_value={'ready':True,'error':None}), patch.object(natural_voice.threading,'Thread',InlineThread):
 response=client.post('/api/admin/narration',json={'session_id':item['id'],'lang':'fr','voice':'ff_siwis','speed':.9},headers={'X-CSRF-Token':'test-csrf'})
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
assert published['narration']['provider']=='kokoro'
for step in published['protocol']['steps']:assert (out/step['audio_path'].lstrip('/')).read_bytes()==audio
others=json.loads((out/'data/sessions-pt.json').read_text())
other=next(x for x in others if x['id']==item['id'])
assert other['narration'] is None or all(s['audio_path'].startswith('/narration/') for s in other['protocol']['steps'])
assert not (out/'models').exists()
assert not (out/'kokoro_engine.py').exists()
print('Published French step narration bundled; other locales unchanged; no inference engine bundled.')
'''
            result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
