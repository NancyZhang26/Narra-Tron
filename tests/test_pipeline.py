from pathlib import Path

from narratron.pipeline import NarraTronPipeline


def test_process_page_mock_pipeline(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")

    output_audio_path = tmp_path / "out.wav"

    pipeline = NarraTronPipeline.build_default()
    result = pipeline.process_page(str(image_path), str(output_audio_path))

    assert result.extracted_text.startswith("[MOCK OCR]")
    assert output_audio_path.exists()
    assert result.page_turn_signal is None


def test_parse_transcript_pipeline() -> None:
    pipeline = NarraTronPipeline.build_default()
    result = pipeline.parse_transcript("stop now")

    assert result.command.value == "stop"
    assert result.transcript == "stop now"
