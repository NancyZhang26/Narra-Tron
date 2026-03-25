from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    use_mock_services: bool = (
        os.getenv("NARRATRON_USE_MOCK_SERVICES", "true").lower() == "true"
    )
    stt_model_size: str = os.getenv("NARRATRON_STT_MODEL_SIZE", "tiny")
    piper_bin: str = os.getenv("NARRATRON_PIPER_BIN", "piper")
    piper_model_path: str = os.getenv("NARRATRON_PIPER_MODEL_PATH", "")
    piper_speaker_id: str = os.getenv("NARRATRON_PIPER_SPEAKER_ID", "")
    system_tts_voice: str = os.getenv("NARRATRON_SYSTEM_TTS_VOICE", "")
    host: str = os.getenv("NARRATRON_HOST", "127.0.0.1")
    port: int = int(os.getenv("NARRATRON_PORT", "8000"))


settings = Settings()
