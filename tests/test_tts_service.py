from pathlib import Path
import wave

from narratron.services.tts import TTSService


def test_mock_tts_synthesize_perfect_scan_to_valid_wav(
    tmp_path: Path, monkeypatch
) -> None:
    source_text = (Path(__file__).parent / "perfect_scan.txt").read_text(
        encoding="utf-8"
    )
    output_audio_path = tmp_path / "perfect_scan.wav"

    service = TTSService(use_mock=True)
    # Force the deterministic pure-Python fallback so duration checks are stable.
    monkeypatch.setattr(service, "_try_system_tts", lambda text, path: False)
    result_path = service.synthesize(
        text=source_text, output_audio_path=str(output_audio_path)
    )

    assert result_path == str(output_audio_path)
    assert output_audio_path.exists()
    assert output_audio_path.stat().st_size > 44

    with wave.open(str(output_audio_path), "rb") as wav_file:
        assert wav_file.getnchannels() >= 1
        assert wav_file.getsampwidth() >= 1
        assert wav_file.getframerate() >= 8000
        assert wav_file.getnframes() > 0

        duration_seconds = wav_file.getnframes() / wav_file.getframerate()
        assert duration_seconds >= 1.0
        assert duration_seconds <= 4.0


def test_mock_tts_synthesize_perfect_scan_not_near_zero_duration(
    tmp_path: Path,
) -> None:
    source_text = (Path(__file__).parent / "perfect_scan.txt").read_text(
        encoding="utf-8"
    )
    output_audio_path = tmp_path / "perfect_scan_system_or_fallback.wav"

    service = TTSService(use_mock=True)
    service.synthesize(text=source_text, output_audio_path=str(output_audio_path))

    with wave.open(str(output_audio_path), "rb") as wav_file:
        duration_seconds = wav_file.getnframes() / wav_file.getframerate()
        assert duration_seconds >= 0.25
