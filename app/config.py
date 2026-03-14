from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VoiceConfig(BaseModel):
    voice_id: str
    name: str
    language: str = "pt-BR"
    backend: str = "piper"
    # Piper fields
    model_path: Optional[str] = None
    config_path: Optional[str] = None
    speaker_id: Optional[int] = None
    # Kokoro fields
    kokoro_voice: Optional[str] = None


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
    tts_default_voice_id: Optional[str] = None
    piper_output_sample_rate: int = 22050
    piper_voices_json: List[VoiceConfig] = Field(default_factory=list)


@lru_cache
def get_settings() -> Settings:
    return Settings()
