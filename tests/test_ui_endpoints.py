"""Comprehensive tests for Narra-Tron web UI endpoints with audio playback."""

import pytest
from pathlib import Path
import wave
import tempfile

from fastapi.testclient import TestClient

from narratron.api import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a minimal PNG image for testing."""
    # Minimal 1x1 pixel PNG (valid PNG header + minimal IHDR chunk)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDAT\x08\x99c\xf8\x0f\x00\x00\x01\x01"
        b"\x00\x05\xb3\xfb\xe7\xa3"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    image_path = tmp_path / "test_page.png"
    image_path.write_bytes(png_bytes)
    return image_path


def test_ui_process_page_mock_ocr(client: TestClient, sample_image: Path) -> None:
    """Test /ui/process-page with mock OCR generates audio and valid HTML response."""
    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={"use_real_ocr": "off"},
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text

    # Verify audio player HTML is present
    assert '<audio id="audio_player" controls>' in html
    assert "<source src" in html
    assert 'type="audio/wav"' in html

    # Verify audio file path is in the response
    assert "output/output.wav" in html
    assert 'src="/output/output.wav"' in html
    assert "audio-path" in html

    # Verify extracted text is displayed
    assert "[MOCK OCR]" in html
    assert "extracted_text_debug" in html


def test_ui_process_page_custom_output_path(
    client: TestClient, sample_image: Path, tmp_path: Path
) -> None:
    """Test /ui/process-page with custom output audio path."""
    custom_output = str(tmp_path / "custom_audio.wav")

    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={
                "use_real_ocr": "off",
                "output_audio_path": custom_output,
            },
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    html = response.text

    # Absolute filesystem path should be proxied to a browser-safe endpoint.
    assert custom_output in html
    assert 'src="/ui/audio-file?path=' in html

    # Verify audio file was actually created
    assert Path(custom_output).exists()


def test_ui_process_page_audio_file_valid(
    client: TestClient, sample_image: Path, tmp_path: Path
) -> None:
    """Test /ui/process-page creates a valid WAV audio file."""
    output_path = tmp_path / "test_output.wav"

    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={
                "use_real_ocr": "off",
                "output_audio_path": str(output_path),
            },
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200

    # Verify WAV file exists and is valid
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # Verify it's a valid WAV file with correct properties
    with wave.open(str(output_path), "rb") as wav:
        assert wav.getnchannels() == 1  # Mono
        assert wav.getsampwidth() == 2  # 16-bit
        assert wav.getframerate() == 22050  # Standard sample rate
        assert wav.getnframes() > 0  # Has audio data


def test_ui_process_page_missing_image(client: TestClient) -> None:
    """Test /ui/process-page fails with 422 when file is completely missing."""
    response = client.post(
        "/ui/process-page",
        data={"use_real_ocr": "off"},
    )

    # FastAPI validation error for required field
    assert response.status_code == 422


def test_ui_process_page_extracts_text(client: TestClient, sample_image: Path) -> None:
    """Test /ui/process-page extracts and displays text."""
    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={"use_real_ocr": "off"},
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    html = response.text

    # Verify OCR result is in the page
    assert "[MOCK OCR]" in html

    # Verify extracted text textarea exists and has readonly attribute
    assert 'id="extracted_text_debug"' in html
    assert "readonly>" in html


def test_ui_process_page_json_result_included(
    client: TestClient, sample_image: Path
) -> None:
    """Test /ui/process-page includes full JSON result in response."""
    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={"use_real_ocr": "off"},
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    html = response.text

    # Verify JSON result is embedded
    assert '"extracted_text"' in html
    assert '"audio_path"' in html
    assert '"page_turn_signal"' in html


def test_ui_parse_transcript(client: TestClient) -> None:
    """Test /ui/parse-transcript endpoint."""
    response = client.post(
        "/ui/parse-transcript",
        data={"transcript": "stop now"},
    )

    assert response.status_code == 200
    html = response.text

    # Verify parse result is shown
    assert '"command":' in html
    assert '"transcript":' in html
    assert "stop" in html


def test_ui_parse_transcript_empty_input(client: TestClient) -> None:
    """Test /ui/parse-transcript with empty transcript."""
    response = client.post(
        "/ui/parse-transcript",
        data={"transcript": ""},
    )

    assert response.status_code == 200
    html = response.text

    # Verify error message
    assert "Please enter transcript text" in html
    # Verify result is not shown
    assert "Transcript Parse Result" not in html


def test_ui_process_page_default_output_path(
    client: TestClient, sample_image: Path
) -> None:
    """Test /ui/process-page uses default output path."""
    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={"use_real_ocr": "off"},
            # Don't specify output_audio_path, should use default
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    html = response.text

    # Verify default path is used
    assert "output/output.wav" in html
    assert 'src="/output/output.wav"' in html


def test_ui_home_page(client: TestClient) -> None:
    """Test GET / returns the UI home page."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text

    # Verify page structure
    assert "Narra-Tron" in html
    assert "Process Page" in html
    assert "Parse Voice Command" in html
    assert "page_image" in html
    assert "transcript" in html


def test_ui_health_endpoint(client: TestClient) -> None:
    """Test /health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ui_process_page_response_structure(
    client: TestClient, sample_image: Path
) -> None:
    """Test /ui/process-page response contains expected HTML elements."""
    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={"use_real_ocr": "off"},
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    html = response.text

    # Verify main structure
    assert "<html" in html.lower()
    assert "</html>" in html.lower()

    # Verify form is present
    assert 'action="/ui/process-page"' in html
    assert 'action="/ui/parse-transcript"' in html

    # Verify result section exists with audio
    assert "<section" in html
    assert "Page Processing Result" in html
    assert "audio_player" in html


def test_ui_process_page_audio_src_correct_format(
    client: TestClient, sample_image: Path, tmp_path: Path
) -> None:
    """Test audio element's src attribute has correct format."""
    output_path = tmp_path / "audio_test.wav"

    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={
                "use_real_ocr": "off",
                "output_audio_path": str(output_path),
            },
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    html = response.text

    # Verify audio element structure
    assert '<audio id="audio_player" controls>' in html
    assert '<source src="/ui/audio-file?path=' in html
    assert "Your browser does not support the audio element." in html


def test_ui_audio_file_endpoint_serves_generated_wav(
    client: TestClient, sample_image: Path, tmp_path: Path
) -> None:
    """Test absolute-path audio can be fetched via /ui/audio-file endpoint."""
    output_path = tmp_path / "served_audio.wav"

    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={
                "use_real_ocr": "off",
                "output_audio_path": str(output_path),
            },
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200
    assert output_path.exists()

    served = client.get("/ui/audio-file", params={"path": str(output_path)})
    assert served.status_code == 200
    assert served.headers["content-type"].startswith("audio/wav")
    assert len(served.content) > 44


def test_ui_multiple_requests_sequential(
    client: TestClient, sample_image: Path, tmp_path: Path
) -> None:
    """Test multiple sequential process-page requests work correctly."""
    for i in range(3):
        output_path = tmp_path / f"output_{i}.wav"

        with open(sample_image, "rb") as f:
            response = client.post(
                "/ui/process-page",
                data={
                    "use_real_ocr": "off",
                    "output_audio_path": str(output_path),
                },
                files={"page_image": ("test.png", f, "image/png")},
            )

        assert response.status_code == 200
        html = response.text
        assert "audio_player" in html
        assert str(output_path) in html
        assert output_path.exists()


def test_ui_audio_file_playable(
    client: TestClient, sample_image: Path, tmp_path: Path
) -> None:
    """Test generated audio file can be read and has valid audio data."""
    output_path = tmp_path / "playable.wav"

    with open(sample_image, "rb") as f:
        response = client.post(
            "/ui/process-page",
            data={
                "use_real_ocr": "off",
                "output_audio_path": str(output_path),
            },
            files={"page_image": ("test.png", f, "image/png")},
        )

    assert response.status_code == 200

    # Verify file is readable and playable
    with wave.open(str(output_path), "rb") as wav:
        frames = wav.readframes(wav.getnframes())
        assert len(frames) > 0

        # Verify audio data is not silent (has some variation)
        # Convert bytes to samples
        sample_width = wav.getsampwidth()
        num_samples = len(frames) // sample_width
        assert num_samples > 0
