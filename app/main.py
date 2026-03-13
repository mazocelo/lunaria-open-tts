from fastapi import FastAPI
from fastapi.responses import Response

from app.config import get_settings
from app.models import GenerateSpeechRequest, HealthResponse
from app.services.piper_service import PiperService

settings = get_settings()
service = PiperService(settings)

app = FastAPI(title=settings.tts_service_name, version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def healthcheck():
    return HealthResponse(
        status="ok",
        service=settings.tts_service_name,
        voices=len(service.list_voices()),
    )


@app.get("/voices")
def list_voices():
    return {"success": True, "data": service.list_voices()}


@app.post("/generate")
def generate_speech(payload: GenerateSpeechRequest):
    audio_bytes = service.synthesize(payload.text, payload.voice_id)
    return Response(content=audio_bytes, media_type="audio/wav")
