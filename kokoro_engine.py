"""Local CPU-only Kokoro inference. No downloads or remote calls during synthesis."""
import importlib.util
import os
from pathlib import Path
import threading
import wave

MODEL = 'kokoro-v1.0-onnx'
MODEL_FILE = 'kokoro-v1.0.onnx'
VOICES_FILE = 'voices-v1.0.bin'
VOICE_SETTINGS = {'sentence_pause': .65, 'clause_pause': .15, 'format': 'pcm16-24000'}
VOICES = [
    {'id': 'pf_dora', 'name': 'Dora · pt-BR', 'lang': 'pt', 'locale': 'pt-br'},
    {'id': 'pm_alex', 'name': 'Alex · pt-BR', 'lang': 'pt', 'locale': 'pt-br'},
    {'id': 'pm_santa', 'name': 'Santa · pt-BR', 'lang': 'pt', 'locale': 'pt-br'},
    {'id': 'af_heart', 'name': 'Heart · en-US', 'lang': 'en', 'locale': 'en-us'},
    {'id': 'af_bella', 'name': 'Bella · en-US', 'lang': 'en', 'locale': 'en-us'},
    {'id': 'af_nicole', 'name': 'Nicole · en-US', 'lang': 'en', 'locale': 'en-us'},
    {'id': 'am_michael', 'name': 'Michael · en-US', 'lang': 'en', 'locale': 'en-us'},
    {'id': 'bf_emma', 'name': 'Emma · en-GB', 'lang': 'en', 'locale': 'en-gb'},
    {'id': 'ff_siwis', 'name': 'Siwis · fr-FR', 'lang': 'fr', 'locale': 'fr-fr'},
    {'id': 'if_sara', 'name': 'Sara · it-IT', 'lang': 'it', 'locale': 'it'},
    {'id': 'im_nicola', 'name': 'Nicola · it-IT', 'lang': 'it', 'locale': 'it'},
    {'id': 'ef_dora', 'name': 'Dora · es-ES', 'lang': 'es', 'locale': 'es'},
    {'id': 'em_alex', 'name': 'Alex · es-ES', 'lang': 'es', 'locale': 'es'},
    {'id': 'em_santa', 'name': 'Santa · es-ES', 'lang': 'es', 'locale': 'es'},
]
_engine = None
_engine_path = None
_lock = threading.Lock()


class VoiceError(Exception):
    pass


def model_dir():
    return Path(os.getenv('KOKORO_MODEL_DIR', Path(__file__).parent / 'models/kokoro'))


def readiness():
    if importlib.util.find_spec('kokoro_onnx') is None:
        return {'ready': False, 'error': 'runtime_missing'}
    if not all((model_dir() / name).is_file() for name in (MODEL_FILE, VOICES_FILE)):
        return {'ready': False, 'error': 'models_missing'}
    return {'ready': True, 'error': None}


def get_engine():
    global _engine, _engine_path
    directory = model_dir().resolve()
    with _lock:
        if _engine is None or _engine_path != directory:
            status = readiness()
            if not status['ready']:
                raise VoiceError(status['error'])
            try:
                import onnxruntime as rt
                from kokoro_onnx import Kokoro
                threads = max(1, min(8, int(os.getenv('KOKORO_THREADS', '2'))))
                config = rt.SessionOptions()
                config.intra_op_num_threads = threads
                config.inter_op_num_threads = 1
                session = rt.InferenceSession(str(directory / MODEL_FILE), sess_options=config,
                                              providers=['CPUExecutionProvider'])
                _engine = Kokoro.from_session(session, str(directory / VOICES_FILE))
                _engine_path = directory
            except Exception:
                raise VoiceError('model_unavailable') from None
        return _engine


def synthesize_to_wav(destination, text, lang, voice, speed):
    selected = next((v for v in VOICES if v['id'] == voice and v['lang'] == lang), None)
    if not selected:
        raise VoiceError('voice_not_found')
    engine = get_engine()
    try:
        import numpy as np
        audio, sample_rate = engine.create(text, voice=voice, speed=speed, lang=selected['locale'],
                                          sentence_pause=.65, clause_pause=.15)
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if sample_rate != 24000 or not 0 < len(audio) <= sample_rate * 600 or not np.isfinite(audio).all():
            raise VoiceError('invalid_audio')
        peak = float(np.max(np.abs(audio)))
        if peak < .00001:
            raise VoiceError('invalid_audio')
        audio *= min(1.0, .9 / peak)
        pcm = (np.clip(audio, -1, 1) * 32767).astype('<i2')
        with wave.open(str(destination), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(pcm.tobytes())
    except VoiceError:
        raise
    except Exception:
        raise VoiceError('generation_failed') from None
