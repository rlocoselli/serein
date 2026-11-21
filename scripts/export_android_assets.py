"""Snapshot only published content and local assets; no server, account or credentials."""
import sys,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import app,UPLOADS
OUT=ROOT/'android/app/src/main/assets/web'
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(parents=True,exist_ok=True)
shutil.copytree(ROOT/'static',OUT,dirs_exist_ok=True)
data=OUT/'data';data.mkdir(exist_ok=True)
client=app.test_client();media=set()
for lang in ['pt','en','fr','it','es']:
 response=client.get('/api/sessions?lang='+lang);assert response.status_code==200
 sessions=response.json
 (data/f'sessions-{lang}.json').write_text(json.dumps(sessions,ensure_ascii=False,indent=2))
 for item in sessions:
  for key in ['audio_path','video_path']:
   if item.get(key):media.add(item[key])
tracks=client.get('/api/music').json
(data/'music.json').write_text(json.dumps(tracks,ensure_ascii=False,indent=2))
for item in tracks:media.add(item['audio_path'])
for path in media:
 if path.startswith('/media/'):
  name=Path(path).name;source=UPLOADS/name
  if source.exists():
   (OUT/'media').mkdir(exist_ok=True);shutil.copy2(source,OUT/'media'/name)
 else:
  assert (OUT/path.lstrip('/')).is_file(),path
# Generated bundle contains no external font requests or server endpoints beyond intercepted reads.
print('Android offline assets:',len(sessions),'sessions,',len(tracks),'sound tracks, five languages')
