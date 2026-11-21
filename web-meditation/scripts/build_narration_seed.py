"""Pre-render the original catalog with Kokoro so a fresh deployment has voices."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import multiprocessing
import os
import secrets
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEFAULT_VOICES = {'fr': 'ff_siwis', 'pt': 'pf_dora', 'en': 'af_heart', 'it': 'if_sara', 'es': 'ef_dora'}


def init_worker():
    os.environ['KOKORO_THREADS'] = '1'


def render(task):
    from kokoro_engine import synthesize_to_wav
    import imageio_ffmpeg
    text, lang, voice, target, cache, seconds = task
    target, cache = Path(target), Path(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.is_file():
        temporary = cache.with_name(cache.stem + '-' + secrets.token_hex(8) + '.tmp')
        try:
            synthesize_to_wav(temporary, text, lang, voice, .9)
            temporary.replace(cache)
        finally:
            temporary.unlink(missing_ok=True)
    with wave.open(str(cache), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate()
    if seconds is not None and duration + .1 > seconds:
        raise ValueError('Narration longer than step: ' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        temporary = target.with_suffix('.tmp.mp3')
        try:
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-loglevel', 'error', '-y',
                '-i', str(cache), '-map_metadata', '-1', '-ac', '1', '-ar', '24000',
                '-codec:a', 'libmp3lame', '-b:a', '64k', str(temporary)], check=True)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return round(duration + .1, 3)


def write_ready(manifest, languages, output):
    ready = {lang for lang in languages if all('duration' in clip
             for sessions in manifest['sessions'].values() for clip in sessions[lang]['segments'])}
    if not ready:
        return ready
    destination = output / 'catalog.json'
    existing = json.loads(destination.read_text()) if destination.is_file() else {**manifest, 'sessions': {}}
    for slug, values in manifest['sessions'].items():
        existing['sessions'].setdefault(slug, {}).update({lang: entry for lang, entry in values.items() if lang in ready})
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / 'catalog.tmp'
    temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    temporary.replace(destination)
    return ready


def build(languages, workers, index_only=False):
    from kokoro_engine import MODEL, VOICE_SETTINGS
    output = ROOT / 'static/narration'
    started = time.monotonic()
    manifest = {'version': 1, 'provider': 'kokoro', 'model': MODEL, 'sessions': {}}
    tasks = []
    # Render the shipped texts in a disposable database, preserving local admin edits.
    with tempfile.TemporaryDirectory(prefix='serein-voice-seed-') as directory:
        os.environ['SEREIN_DB'] = str(Path(directory) / 'seed.db')
        os.environ['SEREIN_UPLOADS'] = str(Path(directory) / 'uploads')
        from app import app, conn
        from natural_voice import digest, source_for
        client = app.test_client()
        for lang in languages:
            voice = DEFAULT_VOICES[lang]
            for item in client.get('/api/sessions?lang=' + lang).json:
                with conn() as db:
                    source = source_for(db, item['id'], lang)
                entry = {'provider': 'kokoro', 'model': MODEL, 'voice': voice,
                         'source_hash': digest(source), 'segments': []}
                manifest['sessions'].setdefault(item['slug'], {})[lang] = entry
                for index, segment in enumerate(source):
                    key = digest([segment['text'], lang, voice, .9, MODEL, VOICE_SETTINGS])
                    name = item['slug'] + '-' + str(index + 1).zfill(2) + '-' + key[:12] + '.mp3'
                    target = output / lang / name
                    clip = {'audio_path': '/narration/' + lang + '/' + name}
                    entry['segments'].append(clip)
                    task = (segment['text'], lang, voice, str(target),
                            str(ROOT / 'models/narration-seed-cache' / (key + '.wav')), segment['seconds'])
                    tasks.append((task, clip))
    if index_only:
        for task, clip in tasks:
            if Path(task[3]).is_file() and Path(task[4]).is_file():
                with wave.open(task[4], 'rb') as audio:
                    clip['duration'] = round(audio.getnframes() / audio.getframerate() + .1, 3)
        print('Languages ready:', ', '.join(sorted(write_ready(manifest, languages, output))), flush=True)
        return
    progress_file = ROOT / 'dist/narration-seed-progress.json'
    progress_file.parent.mkdir(exist_ok=True)
    completed_languages = set()
    groups = {}
    for task, clip in tasks:
        groups.setdefault(task[4], []).append((task, clip))
    with ProcessPoolExecutor(max_workers=workers, initializer=init_worker,
                             mp_context=multiprocessing.get_context('spawn')) as pool:
        futures = {pool.submit(render, entries[0][0]): entries for entries in groups.values()}
        completed = 0
        for future in as_completed(futures):
            entries = futures[future]
            duration = future.result()
            task = entries[0][0]
            for duplicate, clip in entries:
                if duplicate[5] is not None and duration > duplicate[5]:
                    raise ValueError('Narration longer than step: ' + duplicate[3])
                clip['duration'] = duration
                if duplicate[3] != task[3]:
                    destination = Path(duplicate[3])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary = destination.with_suffix('.copy.tmp')
                    shutil.copyfile(task[3], temporary)
                    temporary.replace(destination)
            completed += len(entries)
            progress = {'completed': completed, 'total': len(tasks), 'lang': task[1],
                        'elapsed_seconds': round(time.monotonic() - started)}
            progress_file.write_text(json.dumps(progress))
            print(json.dumps(progress), flush=True)
            ready = {lang for lang in languages if all('duration' in clip
                     for sessions in manifest['sessions'].values() for clip in sessions[lang]['segments'])}
            if ready != completed_languages:
                completed_languages = write_ready(manifest, languages, output)
                print('Languages ready:', ', '.join(sorted(ready)), flush=True)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / 'catalog.json'
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    temporary.replace(destination)
    print('Complete:', len(manifest['sessions']), 'sessions,', len(languages), 'languages,', len(tasks), 'clips', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--languages', nargs='+', choices=list(DEFAULT_VOICES), default=list(DEFAULT_VOICES))
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2)
    parser.add_argument('--index-only', action='store_true', help='Index complete languages from cached audio without synthesis')
    args = parser.parse_args()
    build(list(dict.fromkeys(args.languages)), args.workers, args.index_only)
