import ctypes
import ctypes.util
import io
import logging
import threading
from typing import List

import numpy as np
from fastapi import HTTPException

from app.config import VoiceConfig

KOKORO_SAMPLE_RATE = 24000
WARMUP_TEXT = "Olá, aventureiros."

logger = logging.getLogger(__name__)

try:
    _libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6")
    _malloc_trim = _libc.malloc_trim
except (OSError, AttributeError):
    _malloc_trim = None


def release_freed_memory():
    # A synthesis of ~13 s of audio allocates about 1 GB of intermediate tensors. Once freed,
    # glibc keeps that memory in its arenas (one per threadpool thread), so RSS only grows.
    # malloc_trim hands the free pages back to the OS (~20 ms).
    if _malloc_trim is not None:
        _malloc_trim(0)


class KokoroService:
    def __init__(self, voices: List[VoiceConfig]):
        self.voice_map = {v.voice_id: v for v in voices}
        self._pipelines: dict = {}
        # The warm-up thread and the first request must not load the model twice.
        self._load_lock = threading.Lock()

    def _get_pipeline(self, lang_code: str = "p"):
        with self._load_lock:
            if lang_code not in self._pipelines:
                from kokoro import KPipeline
                self._pipelines[lang_code] = KPipeline(lang_code=lang_code)
        return self._pipelines[lang_code]

    def list_voices(self):
        return [
            {
                "voice_id": v.voice_id,
                "name": v.name,
                "language": v.language,
                "provider": "kokoro",
            }
            for v in self.voice_map.values()
        ]

    def warmup(self):
        """Loads the pipeline and every configured voice, so the first request is not slow."""
        try:
            for voice_id in self.voice_map:
                self.synthesize(WARMUP_TEXT, voice_id)
        except Exception:
            logger.exception("Kokoro warm-up failed")

    def synthesize(self, text: str, voice_id: str) -> bytes:
        import soundfile as sf

        voice = self.voice_map.get(voice_id)
        if not voice or not voice.kokoro_voice:
            raise HTTPException(status_code=404, detail=f"Voz Kokoro '{voice_id}' nao encontrada")

        pipeline = self._get_pipeline("p")

        chunks = []
        try:
            for _, _, audio in pipeline(text, voice=voice.kokoro_voice, speed=1.0):
                if audio is not None:
                    chunks.append(audio)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Kokoro erro: {e}")
        finally:
            release_freed_memory()

        if not chunks:
            raise HTTPException(status_code=500, detail="Kokoro nao gerou audio")

        audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]

        buf = io.BytesIO()
        sf.write(buf, audio, KOKORO_SAMPLE_RATE, format="WAV")
        buf.seek(0)
        return buf.read()
