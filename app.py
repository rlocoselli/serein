import os, sqlite3, secrets, json, re
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session, abort
from werkzeug.utils import secure_filename
from natural_voice import enrich_narration, setup_natural_voice

ROOT=Path(__file__).parent
DB=Path(os.getenv('SEREIN_DB', ROOT/'serein.db'))
UPLOADS=Path(os.getenv('SEREIN_UPLOADS', ROOT/'uploads'))
UPLOADS.mkdir(parents=True,exist_ok=True)
app=Flask(__name__,static_folder='static',static_url_path='')
app.secret_key=os.getenv('SEREIN_SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH']=100*1024*1024
LANGS={'pt','en','fr','it','es'}

def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c

def init():
 with conn() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, category TEXT NOT NULL, duration INTEGER NOT NULL, color TEXT NOT NULL, published INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS translations (session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, lang TEXT NOT NULL, title TEXT NOT NULL, subtitle TEXT NOT NULL, script TEXT NOT NULL, audio_path TEXT, PRIMARY KEY(session_id,lang));
 CREATE TABLE IF NOT EXISTS music (id INTEGER PRIMARY KEY, title TEXT NOT NULL, composer TEXT NOT NULL, performer TEXT NOT NULL, license TEXT NOT NULL, license_url TEXT NOT NULL, source_url TEXT NOT NULL, attribution TEXT NOT NULL, audio_path TEXT NOT NULL, published INTEGER NOT NULL DEFAULT 0);''')
  if 'video_path' not in [r[1] for r in c.execute('PRAGMA table_info(sessions)')]: c.execute('ALTER TABLE sessions ADD COLUMN video_path TEXT')
  for slug in ('respirar','soltar','sono'):
   c.execute('UPDATE sessions SET video_path=? WHERE slug=? AND video_path IS NULL',(f'/videos/{slug}.webm',slug))
  if c.execute('SELECT count(*) FROM sessions').fetchone()[0]: return
  seeds=[('respirar','breathing',5,'sage',{
   'pt':('Respire com calma','Um espaço para voltar ao presente','Encontre uma posição confortável. Sinta o apoio sob o seu corpo. Inspire lentamente pelo nariz. Perceba o ar entrando. Solte o ar sem pressa. Se a mente se afastar, apenas note e volte à próxima respiração. Não há nada para alcançar agora. Há apenas este momento. O que muda quando você permite uma pausa?'),
   'en':('Breathe gently','A space to return to the present','Find a comfortable position. Feel the support beneath your body. Breathe in slowly through your nose. Notice the air entering. Let it out without rushing. If your mind wanders, simply notice and return to the next breath. There is nothing to achieve right now. There is only this moment. What changes when you allow a pause?'),
   'fr':('Respirez doucement','Un espace pour revenir au présent','Installez-vous confortablement. Sentez le soutien sous votre corps. Inspirez lentement par le nez. Remarquez l’air qui entre. Expirez sans vous presser. Si votre esprit s’égare, constatez-le simplement et revenez au souffle suivant. Il n’y a rien à accomplir maintenant. Il y a seulement cet instant. Que change une pause que vous vous accordez ?'),
   'it':('Respira con calma','Uno spazio per tornare al presente','Trova una posizione comoda. Senti il sostegno sotto il corpo. Inspira lentamente dal naso. Nota l’aria che entra. Espira senza fretta. Se la mente vaga, accorgitene e torna al respiro successivo. Non c’è nulla da raggiungere adesso. C’è soltanto questo momento. Che cosa cambia quando ti concedi una pausa?'),
   'es':('Respira con calma','Un espacio para volver al presente','Busca una posición cómoda. Siente el apoyo bajo tu cuerpo. Inhala lentamente por la nariz. Nota cómo entra el aire. Exhala sin prisa. Si la mente se distrae, simplemente obsérvalo y vuelve a la siguiente respiración. No hay nada que lograr ahora. Solo existe este momento. ¿Qué cambia cuando te permites una pausa?')}),
   ('soltar','relaxation',8,'peach',{
   'pt':('Solte o peso do dia','Relaxe, uma parte de cada vez','Feche os olhos, se for confortável. Observe a testa e deixe-a suavizar. Solte a mandíbula. Permita que os ombros desçam. Sinta as mãos repousarem. A cada expiração, imagine que oferece um pouco mais de espaço ao corpo. Você pode estar exatamente como está. Qual parte de você pede mais gentileza hoje?'),
   'en':('Let the day soften','Relax, one part at a time','Close your eyes if that feels comfortable. Notice your forehead and let it soften. Release your jaw. Allow your shoulders to lower. Feel your hands resting. With each exhale, imagine giving your body a little more space. You may be exactly as you are. Which part of you asks for more kindness today?'),
   'fr':('Laissez la journée s’apaiser','Détendez-vous, une partie à la fois','Fermez les yeux si cela vous convient. Observez votre front et laissez-le se détendre. Relâchez la mâchoire. Laissez descendre les épaules. Sentez vos mains au repos. À chaque expiration, offrez un peu plus d’espace à votre corps. Vous pouvez être exactement comme vous êtes. Quelle part de vous a besoin de douceur aujourd’hui ?'),
   'it':('Lascia andare la giornata','Rilassati, una parte alla volta','Chiudi gli occhi, se ti fa stare bene. Nota la fronte e lasciala distendere. Rilassa la mandibola. Lascia scendere le spalle. Senti le mani a riposo. A ogni espirazione, immagina di offrire un po’ più di spazio al corpo. Puoi essere esattamente come sei. Quale parte di te chiede più gentilezza oggi?'),
   'es':('Suelta el peso del día','Relájate, una parte a la vez','Cierra los ojos si te resulta cómodo. Nota la frente y deja que se suavice. Relaja la mandíbula. Permite que los hombros bajen. Siente las manos descansando. Con cada exhalación, imagina que das un poco más de espacio al cuerpo. Puedes estar exactamente como estás. ¿Qué parte de ti necesita más amabilidad hoy?')}),
   ('sono','sleep',10,'lavender',{
   'pt':('Prepare-se para dormir','Um ritual para desacelerar','A noite chegou. Você pode deixar as tarefas de hoje para trás. Perceba a superfície que o acolhe. Inspire de forma natural. Ao expirar, solte uma pequena tensão. Deixe os pensamentos passarem como nuvens no céu escuro. Não precisa segui-los. Seu único convite agora é descansar. Como seria confiar neste momento de repouso?'),
   'en':('Ease into sleep','A ritual to slow down','Night has arrived. You can leave today’s tasks behind. Notice the surface supporting you. Breathe naturally. As you exhale, release a little tension. Let thoughts pass like clouds in a dark sky. You do not need to follow them. Your only invitation now is to rest. What would it feel like to trust this moment of rest?'),
   'fr':('Glissez vers le sommeil','Un rituel pour ralentir','La nuit est arrivée. Vous pouvez laisser les tâches du jour derrière vous. Sentez la surface qui vous soutient. Respirez naturellement. À l’expiration, relâchez une petite tension. Laissez passer les pensées comme des nuages dans le ciel sombre. Vous n’avez pas à les suivre. Votre seule invitation est de vous reposer. Que serait-ce de faire confiance à ce repos ?'),
   'it':('Verso il sonno','Un rituale per rallentare','È arrivata la notte. Puoi lasciare alle spalle le cose da fare oggi. Senti la superficie che ti sostiene. Respira naturalmente. Espirando, lascia andare una piccola tensione. Lascia passare i pensieri come nuvole nel cielo scuro. Non devi seguirli. Ora il tuo unico invito è riposare. Come sarebbe affidarti a questo momento di riposo?'),
   'es':('Descansa al dormir','Un ritual para bajar el ritmo','Ha llegado la noche. Puedes dejar atrás las tareas de hoy. Siente la superficie que te sostiene. Respira con naturalidad. Al exhalar, suelta una pequeña tensión. Deja pasar los pensamientos como nubes en el cielo oscuro. No tienes que seguirlos. Tu única invitación ahora es descansar. ¿Cómo sería confiar en este momento de reposo?')})]
  for slug,cat,dur,color,translations in seeds:
   cur=c.execute('INSERT INTO sessions(slug,category,duration,color) VALUES(?,?,?,?)',(slug,cat,dur,color))
   for lang,(title,subtitle,script) in translations.items(): c.execute('INSERT INTO translations(session_id,lang,title,subtitle,script) VALUES(?,?,?,?,?)',(cur.lastrowid,lang,title,subtitle,script))
   c.execute('UPDATE sessions SET video_path=? WHERE id=?',(f'/videos/{slug}.webm',cur.lastrowid))

def admin_required(fn):
 @wraps(fn)
 def wrapper(*a,**kw):
  if not session.get('admin'): return jsonify(error='Unauthorized'),401
  return fn(*a,**kw)
 return wrapper

def csrf_required():
 if request.headers.get('X-CSRF-Token')!=session.get('csrf'): abort(403)

@app.get('/')
def home(): return app.send_static_file('index.html')

@app.get('/api/sessions')
def list_sessions():
 lang=request.args.get('lang','pt'); lang=lang if lang in LANGS else 'pt'
 with conn() as c:
  rows=c.execute('SELECT s.*,t.title,t.subtitle,t.script,t.audio_path FROM sessions s JOIN translations t ON t.session_id=s.id AND t.lang=? WHERE s.published=1 ORDER BY s.id',(lang,)).fetchall()
 data=[]
 with conn() as c:
  for row in rows:
   item=dict(row)
   protocol=c.execute('SELECT content FROM exercise_protocols WHERE session_id=? AND lang=?',(row['id'],lang)).fetchone()
   item['protocol']=json.loads(protocol['content']) if protocol else None
   data.append(enrich_narration(c,item,lang))
 return jsonify(data)

@app.get('/api/music')
def list_music():
 with conn() as c: rows=c.execute('SELECT * FROM music WHERE published=1 ORDER BY id').fetchall()
 builtins=json.loads((ROOT/'static/audio/credits.json').read_text())
 return jsonify(builtins+[dict(r) for r in rows])

@app.get('/media/<path:name>')
def media(name): return send_from_directory(UPLOADS,name)

@app.post('/api/admin/login')
def login():
 password=os.getenv('SEREIN_ADMIN_PASSWORD')
 if not password: return jsonify(error='Configure SEREIN_ADMIN_PASSWORD'),503
 if not secrets.compare_digest(str(request.json.get('password','')),password): return jsonify(error='Invalid credentials'),401
 session['admin']=True; session['csrf']=secrets.token_urlsafe(24)
 return jsonify(csrf=session['csrf'])

@app.post('/api/admin/logout')
@admin_required
def logout(): csrf_required();session.clear();return jsonify(ok=True)

@app.get('/api/admin/sessions')
@admin_required
def admin_sessions():
 with conn() as c:
  rows=c.execute('SELECT * FROM sessions ORDER BY id DESC').fetchall()
  data=[]
  for r in rows:
   item=dict(r);item['translations']={t['lang']:dict(t) for t in c.execute('SELECT * FROM translations WHERE session_id=?',(r['id'],)).fetchall()};data.append(item)
 return jsonify(data)

@app.post('/api/admin/sessions')
@admin_required
def create_session():
 csrf_required();d=request.json or {}; translations=d.get('translations',{})
 if not all(lang in translations and all(translations[lang].get(k) for k in ('title','subtitle','script')) for lang in LANGS): return jsonify(error='Five complete translations required'),400
 if d.get('category') not in {'breathing','relaxation','sleep','focus'}: return jsonify(error='Invalid category'),400
 slug=re.sub('[^a-z0-9-]','-',str(d.get('slug','')).lower()).strip('-')
 if not slug:return jsonify(error='Slug required'),400
 try:
  with conn() as c:
   cur=c.execute('INSERT INTO sessions(slug,category,duration,color,published) VALUES(?,?,?,?,?)',(slug,d['category'],int(d.get('duration',5)),d.get('color','sage'),int(bool(d.get('published',False)))))
   for lang,t in translations.items():
    if lang in LANGS:c.execute('INSERT INTO translations(session_id,lang,title,subtitle,script) VALUES(?,?,?,?,?)',(cur.lastrowid,lang,t['title'],t['subtitle'],t['script']))
  return jsonify(id=cur.lastrowid),201
 except sqlite3.IntegrityError:return jsonify(error='Slug already exists'),409

@app.patch('/api/admin/sessions/<int:sid>')
@admin_required
def update_session(sid):
 csrf_required();d=request.json or {}
 with conn() as c:
  if not c.execute('SELECT id FROM sessions WHERE id=?',(sid,)).fetchone():abort(404)
  for key in ('published','duration','category','color'):
   if key in d:c.execute(f'UPDATE sessions SET {key}=? WHERE id=?',(d[key],sid))
  for lang,t in d.get('translations',{}).items():
   if lang not in LANGS:continue
   for key in ('title','subtitle','script'):
    if key in t:c.execute(f'UPDATE translations SET {key}=? WHERE session_id=? AND lang=?',(t[key],sid,lang))
 return jsonify(ok=True)

@app.post('/api/admin/upload')
@admin_required
def upload():
 csrf_required(); f=request.files.get('file'); sid=request.form.get('session_id');lang=request.form.get('lang')
 if not f or not sid or lang not in LANGS:return jsonify(error='File, session and language required'),400
 ext=Path(secure_filename(f.filename or '')).suffix.lower()
 if ext not in {'.mp3','.m4a','.ogg','.wav'}:return jsonify(error='Unsupported audio format'),400
 name=secrets.token_hex(16)+ext;f.save(UPLOADS/name)
 with conn() as c:
  cur=c.execute('UPDATE translations SET audio_path=? WHERE session_id=? AND lang=?',(f'/media/{name}',sid,lang))
  if not cur.rowcount:(UPLOADS/name).unlink(missing_ok=True);return jsonify(error='Session not found'),404
 return jsonify(audio_path=f'/media/{name}')

@app.post('/api/admin/video')
@admin_required
def upload_video():
 csrf_required(); f=request.files.get('file'); sid=request.form.get('session_id')
 if not f or not sid:return jsonify(error='File and session required'),400
 ext=Path(secure_filename(f.filename or '')).suffix.lower()
 if ext not in {'.mp4','.webm','.mov'}:return jsonify(error='Unsupported video format'),400
 name=secrets.token_hex(16)+ext;f.save(UPLOADS/name)
 with conn() as c:
  cur=c.execute('UPDATE sessions SET video_path=? WHERE id=?',(f'/media/{name}',sid))
  if not cur.rowcount:(UPLOADS/name).unlink(missing_ok=True);return jsonify(error='Session not found'),404
 return jsonify(video_path=f'/media/{name}')

@app.post('/api/admin/music')
@admin_required
def add_music():
 csrf_required();f=request.files.get('file'); fields=['title','composer','performer','license','license_url','source_url','attribution']
 if not f or not all(request.form.get(k) for k in fields):return jsonify(error='File and provenance fields required'),400
 ext=Path(secure_filename(f.filename or '')).suffix.lower()
 if ext not in {'.mp3','.m4a','.ogg','.wav'}:return jsonify(error='Unsupported audio format'),400
 name=secrets.token_hex(16)+ext;f.save(UPLOADS/name)
 with conn() as c:
  cur=c.execute('INSERT INTO music(title,composer,performer,license,license_url,source_url,attribution,audio_path,published) VALUES(?,?,?,?,?,?,?,?,0)',tuple(request.form[k] for k in fields)+(f'/media/{name}',))
 return jsonify(id=cur.lastrowid),201

@app.get('/api/admin/music')
@admin_required
def admin_music():
 with conn() as c: return jsonify([dict(r) for r in c.execute('SELECT * FROM music ORDER BY id DESC')])

@app.patch('/api/admin/music/<int:mid>')
@admin_required
def update_music(mid):
 csrf_required();d=request.json or {}
 with conn() as c:
  cur=c.execute('UPDATE music SET published=? WHERE id=?',(int(bool(d.get('published'))),mid))
  if not cur.rowcount:abort(404)
 return jsonify(ok=True)

def seed_exercises():
 with conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS exercise_protocols (session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, lang TEXT NOT NULL, content TEXT NOT NULL, PRIMARY KEY(session_id,lang))')
  for slug,exercise in json.loads((ROOT/'exercise_seed.json').read_text()).items():
   c.execute('INSERT OR IGNORE INTO sessions(slug,category,duration,color,published) VALUES(?,?,?,?,1)',(slug,exercise['category'],exercise['duration'],exercise['color']))
   sid=c.execute('SELECT id FROM sessions WHERE slug=?',(slug,)).fetchone()['id']
   for lang,local in exercise['locales'].items():
    script=' '.join(step['text'] for step in local['steps'])
    c.execute('INSERT OR IGNORE INTO translations(session_id,lang,title,subtitle,script) VALUES(?,?,?,?,?)',(sid,lang,local['title'],local['subtitle'],script))
    content={**local,'kind':exercise['kind'],'source':exercise['source'],'total_seconds':sum(step['seconds'] for step in local['steps'])}
    c.execute('INSERT OR IGNORE INTO exercise_protocols(session_id,lang,content) VALUES(?,?,?)',(sid,lang,json.dumps(content,ensure_ascii=False)))

def seed_stories():
 with conn() as c:
  for story in json.loads((ROOT/'story_seed.json').read_text()):
   c.execute('INSERT OR IGNORE INTO sessions(slug,category,duration,color,published) VALUES(?,?,?,?,1)',(story['slug'],story['category'],story['duration'],story['color']))
   sid=c.execute('SELECT id FROM sessions WHERE slug=?',(story['slug'],)).fetchone()['id']
   for lang,local in story['locales'].items():
    c.execute('INSERT OR IGNORE INTO translations(session_id,lang,title,subtitle,script) VALUES(?,?,?,?,?)',(sid,lang,local['title'],local['subtitle'],' '.join(s['text'] for s in local['steps'])))
    protocol={**local,'kind':'story','sound':story['sound'],'source':story['source'],'total_seconds':sum(s['seconds'] for s in local['steps'])}
    c.execute('INSERT OR IGNORE INTO exercise_protocols(session_id,lang,content) VALUES(?,?,?)',(sid,lang,json.dumps(protocol,ensure_ascii=False)))

init()
seed_exercises()
seed_stories()
setup_natural_voice(app,conn,UPLOADS,admin_required,csrf_required)
if __name__=='__main__':app.run(host='127.0.0.1',port=int(os.getenv('PORT',5000)),debug=False)
