# Narra-Tron

Software-first foundation for Narra-Tron: OCR -> TTS -> command parsing (STT) -> protocol signal for page turning.

This version is designed to run before hardware is available.

## What is implemented
- OCR service module with optional PaddleOCR backend.
- TTS service module using Piper CLI backend (with mock fallback).
- STT service module with optional Faster-Whisper backend.
- Command parser for voice commands: start, stop, turn page, go back.
- Software protocol bus that emits a turn-page signal after narration.
- FastAPI app and CLI for local development and integration testing.
- Local browser UI for uploading a page image and parsing command text.

## Project structure
- `src/narratron/services/ocr.py`: Image to text service.
- `src/narratron/services/tts.py`: Piper-based text to audio service.
- `src/narratron/services/stt.py`: Audio to text and command parsing.
- `src/narratron/services/protocol.py`: Placeholder protocol bus for hardware commands.
- `src/narratron/pipeline.py`: Orchestrates end-to-end software flow.
- `src/narratron/api.py`: HTTP API endpoints.
- `src/narratron/cli.py`: Command line interface.
- `templates/index.html`: Browser UI for software workflows.
- `tests/`: Unit tests for parser and pipeline behavior.

## Quick start
1. Install uv (if not already installed):

```bash
brew install uv
```

2. Create `.env` from template:

```bash
cp .env.example .env
```

3. Sync dependencies into the uv-managed environment:

```bash
uv sync --extra test
```

Optional ML dependencies:

```bash
uv sync --extra test --extra ml
```

## Run the dev server

Start the FastAPI development server:

```bash
uv run fastapi run src/narratron/api.py --port 8000
```

Or using the custom CLI:

```bash
uv run narra-tron serve --host 127.0.0.1 --port 8000
```

Then open the UI console in your browser:

```
http://127.0.0.1:8000/
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Process a page image:

```bash
curl -X POST http://127.0.0.1:8000/v1/pipeline/process-page \
	-H "Content-Type: application/json" \
	-d '{"image_path":"sample_page.png","output_audio_path":"output.wav"}'
```

Parse transcript text:

```bash
curl -X POST http://127.0.0.1:8000/v1/stt/parse-transcript \
	-H "Content-Type: application/json" \
	-d '{"transcript":"please turn to the next page"}'
```

## CLI usage
Process one page:

```bash
uv run narra-tron process-page sample_page.png output.wav
```

Parse transcript directly:

```bash
uv run narra-tron parse-transcript "stop reading"
```

Transcribe audio command and parse:

```bash
uv run narra-tron transcribe-command command.wav
```

## Enabling real ML backends
By default, mock mode is enabled to avoid blocking development.

1. Install ML dependencies:

```bash
uv sync --extra ml
```

2. Install Piper CLI and download a voice model (`.onnx`).

3. Set in `.env`:

```env
NARRATRON_USE_MOCK_SERVICES=false
NARRATRON_STT_MODEL_SIZE=tiny
NARRATRON_PIPER_BIN=piper
NARRATRON_PIPER_MODEL_PATH=/absolute/path/to/voice-model.onnx
# Optional for multi-speaker voices
NARRATRON_PIPER_SPEAKER_ID=0
```

### Mock mode spoken audio on macOS

When `NARRATRON_USE_MOCK_SERVICES=true`, Narra-Tron tries macOS `say` before falling back to a generated tone.
If your default macOS voice returns near-empty audio, pin a voice explicitly in `.env`:

```env
NARRATRON_SYSTEM_TTS_VOICE=Samantha
```

If performance on Raspberry Pi is limited, run selected components remotely and keep API contracts unchanged.

## Run tests
```bash
uv run pytest
```
