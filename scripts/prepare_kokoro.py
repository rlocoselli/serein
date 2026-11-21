"""Fetch the pinned public Kokoro assets once; synthesis itself stays offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
ASSETS = {
    'kokoro-v1.0.onnx': 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
    'voices-v1.0.bin': 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',
}


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def prepare(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in ASSETS.items():
        destination = directory / name
        if destination.is_file() and checksum(destination) == expected:
            print('Verified:', name, flush=True)
            continue
        print('Downloading:', name, flush=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix='.' + name, dir=directory)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                req = urllib.request.Request(BASE + name, headers={'User-Agent': 'Serein-Kokoro-Setup/1.0'})
                with urllib.request.urlopen(req, timeout=120) as response:
                    shutil.copyfileobj(response, output, length=1024 * 1024)
            if checksum(temporary) != expected:
                raise ValueError('SHA256 verification failed: ' + name)
            temporary.chmod(0o644)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        print('Verified:', name, flush=True)
    shutil.copytree(ROOT / 'licenses/kokoro', directory / 'licenses', dirs_exist_ok=True)
    (directory / 'manifest.json').write_text(json.dumps({'source': BASE, 'sha256': ASSETS}, indent=2))
    print('Kokoro ready:', directory, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(os.getenv('KOKORO_MODEL_DIR', ROOT / 'models/kokoro')))
    prepare(parser.parse_args().output)
