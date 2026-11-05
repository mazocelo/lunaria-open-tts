from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VoiceConfig(BaseModel):
    voice_id: str
    name: str
    language: str = "pt-BR"
    backend: str = "piper"
    # Piper fields
    model_path: str | None = None
    config_path: str | None = None
    speaker_id: int | None = None
    # Kokoro fields
    kokoro_voice: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    tts_service_name: str = "Open Source TTS"
    tts_host: str = "0.0.0.0"
    tts_port: int = 8002
    piper_executable: str = "piper"
    tts_default_voice_id: str | None = None
    piper_output_sample_rate: int = 22050
    piper_voices_json: list[VoiceConfig] = Field(default_factory=list)
    # Kokoro: synthesize a short phrase per voice at startup, so the first request is fast
    kokoro_warmup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
