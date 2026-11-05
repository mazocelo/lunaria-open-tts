
from pydantic import BaseModel, Field


class GenerateSpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    voices: int
