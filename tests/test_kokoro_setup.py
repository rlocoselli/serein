import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import kokoro_engine

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_kokoro', ROOT / 'scripts/prepare_kokoro.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class KokoroSetupTests(unittest.TestCase):
    def test_preparation_checks_integrity_and_reuses_verified_files(self):
        payload = b'test model file'
        with tempfile.TemporaryDirectory() as directory, patch.object(setup, 'ASSETS', {'test.onnx': hashlib.sha256(payload).hexdigest()}):
            with patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(payload)) as network:
                setup.prepare(Path(directory))
                self.assertEqual(network.call_count, 1)
            with patch.object(setup.urllib.request, 'urlopen', side_effect=AssertionError('Must not redownload')):
                setup.prepare(Path(directory))
            self.assertTrue((Path(directory) / 'licenses/NOTICE.md').is_file())

    def test_bad_download_cannot_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(setup, 'ASSETS', {'test.onnx': '0' * 64}):
            path = Path(directory) / 'test.onnx'
            path.write_bytes(b'previous model')
            with patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(b'corrupt')):
                with self.assertRaises(ValueError):
                    setup.prepare(Path(directory))
            self.assertEqual(path.read_bytes(), b'previous model')
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_wrong_language_voice_is_rejected_before_loading_model(self):
        with patch.object(kokoro_engine, 'get_engine') as engine:
            with self.assertRaises(kokoro_engine.VoiceError):
                kokoro_engine.synthesize_to_wav('unused.wav', 'Bonjour.', 'fr', 'pf_dora', .9)
            engine.assert_not_called()


if __name__ == '__main__':
    unittest.main()
