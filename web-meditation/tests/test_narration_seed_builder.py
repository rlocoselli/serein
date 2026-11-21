import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_narration_seed', ROOT / 'scripts/build_narration_seed.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class SeedCheckpointTests(unittest.TestCase):
    def test_only_complete_languages_are_published_and_existing_languages_survive(self):
        manifest = {'provider': 'kokoro', 'sessions': {
            'one': {'fr': {'segments': [{'duration': 2}]}, 'pt': {'segments': [{}]}},
            'two': {'fr': {'segments': [{'duration': 3}]}, 'pt': {'segments': [{'duration': 4}]}}}}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            catalog = output / 'catalog.json'
            catalog.write_text(json.dumps({'provider': 'kokoro', 'sessions': {'one': {'en': {'existing': True}}}}))
            self.assertEqual(builder.write_ready(manifest, ['fr', 'pt'], output), {'fr'})
            saved = json.loads(catalog.read_text())
            self.assertTrue(saved['sessions']['one']['en']['existing'])
            self.assertNotIn('pt', saved['sessions']['one'])
            manifest['sessions']['one']['pt']['segments'][0]['duration'] = 5
            builder.write_ready(manifest, ['fr', 'pt'], output)
            saved = json.loads(catalog.read_text())
            self.assertIn('pt', saved['sessions']['two'])
            self.assertTrue(saved['sessions']['one']['en']['existing'])

    def test_an_incomplete_language_cannot_create_a_published_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = {'sessions': {'one': {'fr': {'segments': [{}]}}}}
            self.assertEqual(builder.write_ready(manifest, ['fr'], output), set())
            self.assertFalse((output / 'catalog.json').exists())


if __name__ == '__main__':
    unittest.main()
