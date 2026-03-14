from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from app.config import get_settings
from app.models import GenerateSpeechRequest, HealthResponse
from app.services.piper_service import PiperService
from app.services.kokoro_service import KokoroService

settings = get_settings()

_piper_voices = [v for v in settings.piper_voices_json if v.backend == "piper"]
_kokoro_voices = [v for v in settings.piper_voices_json if v.backend == "kokoro"]

piper_service = PiperService(settings, _piper_voices)
kokoro_service = KokoroService(_kokoro_voices)

_all_voice_map = {v.voice_id: v for v in settings.piper_voices_json}

app = FastAPI(title=settings.tts_service_name, version="2.0.0")


@app.get("/health", response_model=HealthResponse)
def healthcheck():
    return HealthResponse(
        status="ok",
        service=settings.tts_service_name,
        voices=len(settings.piper_voices_json),
    )


@app.get("/voices")
def list_voices():
    return {"success": True, "data": piper_service.list_voices() + kokoro_service.list_voices()}


@app.post("/generate")
def generate_speech(payload: GenerateSpeechRequest):
    target_id = payload.voice_id or settings.tts_default_voice_id
    voice_config = _all_voice_map.get(target_id)
    if not voice_config:
        raise HTTPException(status_code=404, detail=f"Voz '{target_id}' nao encontrada")

    if voice_config.backend == "kokoro":
        audio_bytes = kokoro_service.synthesize(payload.text, target_id)
    else:
        audio_bytes = piper_service.synthesize(payload.text, target_id)

    return Response(content=audio_bytes, media_type="audio/wav")
