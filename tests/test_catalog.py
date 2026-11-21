import json, os, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SANDBOX=tempfile.TemporaryDirectory(prefix='serein-catalog-')
os.environ['SEREIN_DB']=str(Path(SANDBOX.name)/'test.db')
os.environ['SEREIN_UPLOADS']=str(Path(SANDBOX.name)/'uploads')
from app import app, conn, seed_exercises

class CatalogTests(unittest.TestCase):
 def test_locales_and_timing(self):
  client=app.test_client()
  for lang in ['pt','en','fr','it','es']:
   with self.subTest(lang=lang):
    response=client.get('/api/sessions?lang='+lang)
    self.assertEqual(response.status_code,200)
    self.assertEqual(len(response.json),16)
    practices=[row for row in response.json if row['protocol'] and row['protocol']['kind']!='story']
    self.assertEqual(len(practices),11)
    self.assertEqual(len({row['title'] for row in response.json}),16)
    for row in practices:
     protocol=row['protocol'];self.assertEqual(sum(step['seconds'] for step in protocol['steps']),row['duration']*60)
     self.assertTrue(all(step['text'].strip() and step['seconds']>0 for step in protocol['steps']))
     self.assertTrue(protocol['source']['url'].startswith('https://'))
     self.assertTrue(protocol['safety'] and protocol['evidence'])
 def test_reseed_preserves_editorial_changes(self):
  with conn() as db:
   sid=db.execute("SELECT id FROM sessions WHERE slug='comecar-dia'").fetchone()['id']
   db.execute("UPDATE translations SET title='Edited title' WHERE session_id=? AND lang='en'",(sid,))
   db.execute("UPDATE sessions SET published=0 WHERE id=?",(sid,))
  seed_exercises();seed_exercises()
  with conn() as db:
   self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0],16)
   self.assertEqual(db.execute("SELECT title FROM translations WHERE session_id=? AND lang='en'",(sid,)).fetchone()[0],'Edited title')
   self.assertEqual(db.execute('SELECT published FROM sessions WHERE id=?',(sid,)).fetchone()[0],0)
   db.execute("UPDATE translations SET title='A more present beginning' WHERE session_id=? AND lang='en'",(sid,))
   db.execute('UPDATE sessions SET published=1 WHERE id=?',(sid,))

if __name__=='__main__':unittest.main()
