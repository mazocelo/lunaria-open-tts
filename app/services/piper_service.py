import os
import subprocess
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app.config import Settings, VoiceConfig


class PiperService:
    def __init__(self, settings: Settings, voices: list = None):
        self.settings = settings
        voice_list = voices if voices is not None else settings.piper_voices_json
        self.voice_map = {voice.voice_id: voice for voice in voice_list}

    def list_voices(self):
        return [
            {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "language": voice.language,
                "provider": "piper",
            }
            for voice in self.voice_map.values()
        ]

    def resolve_voice(self, voice_id: str | None) -> VoiceConfig:
        target_voice_id = voice_id or self.settings.tts_default_voice_id
        if not target_voice_id:
            raise HTTPException(status_code=500, detail="Nenhuma voz padrao configurada")

        voice = self.voice_map.get(target_voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail=f"Voz '{target_voice_id}' nao encontrada")

        if not Path(voice.model_path).exists():
            raise HTTPException(status_code=500, detail=f"Modelo nao encontrado: {voice.model_path}")

        if voice.config_path and not Path(voice.config_path).exists():
            raise HTTPException(status_code=500, detail=f"Config do modelo nao encontrada: {voice.config_path}")

        return voice

    def synthesize(self, text: str, voice_id: str | None) -> bytes:
        voice = self.resolve_voice(voice_id)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            output_path = tmp_file.name

        command = [
            self.settings.piper_executable,
            "--model",
            voice.model_path,
            "--output_file",
            output_path,
        ]

        if voice.config_path:
            command.extend(["--config", voice.config_path])

        if voice.speaker_id is not None:
            command.extend(["--speaker", str(voice.speaker_id)])

        try:
            result = subprocess.run(
                command,
                input=text,
                text=True,
                capture_output=True,
                check=False,
                env=os.environ.copy(),
            )
            if result.returncode != 0:
                error_message = result.stderr.strip() or result.stdout.strip() or "Falha ao executar Piper"
                raise HTTPException(status_code=500, detail=error_message)

            with open(output_path, "rb") as audio_file:
                return audio_file.read()
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
