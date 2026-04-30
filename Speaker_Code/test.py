"""
Quick smoke-test: synthesise a short phrase with Piper TTS, then play it
through the Speaker (aplay).

Run from the project root:
    python Speaker_Code/test.py

Or pass custom text:
    python Speaker_Code/test.py "The quick brown fox"
"""

import os
import sys
import tempfile

# Allow running from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from Speaker_Code.speaker import Speaker
from src.narratron.services.tts import TTSService
from src.narratron.config import settings

TEXT = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello world"

print(f"[test] Synthesising: {TEXT!r}")

tts = TTSService(
    use_mock=settings.use_mock_services,
    piper_bin=settings.piper_bin,
    piper_model_path=settings.piper_model_path,
    piper_speaker_id=settings.piper_speaker_id,
)

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wav_path = f.name

try:
    audio_path = tts.synthesize(text=TEXT, output_audio_path=wav_path)
    print(f"[test] WAV written to {audio_path}")

    audio_device = os.environ.get("AUDIO_DEVICE", "plughw:2,0")
    speaker = Speaker(device=audio_device)
    if not speaker.is_available():
        print("[test] WARNING: aplay found no audio devices — playback may fail")

    print("[test] Playing...")
    speaker.play(audio_path)
    print("[test] Done.")
finally:
    os.unlink(wav_path)
