import json,wave,array,math,hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SoundAssetTests(unittest.TestCase):
 def test_stereo_levels_seams_and_variety(self):
  tracks=json.loads((ROOT/'static/audio/credits.json').read_text());self.assertEqual(len(tracks),10)
  hashes=set()
  for track in tracks:
   with self.subTest(track=track['key']):
    path=ROOT/'static'/track['audio_path'].lstrip('/')
    with wave.open(str(path)) as w:
     self.assertEqual(w.getnchannels(),2);self.assertEqual(w.getsampwidth(),2);self.assertEqual(w.getnframes()/w.getframerate(),32)
     raw=w.readframes(w.getnframes())
    samples=array.array('h',raw);self.assertEqual(samples[:2],samples[-2:]);self.assertLess(max(abs(v) for v in samples),16000)
    rms=math.sqrt(sum(v*v for v in samples)/len(samples))/32768;self.assertGreater(rms,.015);self.assertLess(rms,.1)
    self.assertTrue(track['license'] and track['license_url'] and track['attribution']);hashes.add(hashlib.sha256(raw).hexdigest())
  self.assertEqual(len(hashes),10)
