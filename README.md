# Narra-Tron

Automated book-reading robot: camera captures a page → OCR extracts text → TTS narrates it → after 2 pages, signals a Raspberry Pi Pico W to physically turn the page.

## System overview

```
Pi (this repo)                          Pico W (pi/main.py)
──────────────────────────────          ──────────────────────
camera.py captures page image
  → OCR (PaddleOCR)
  → TTS (Piper) generates audio
  → aplay plays audio (blocking)
  → after 2 pages:
      TURN_PAGE ──────────────────────→ receives signal
                                        runs roller + finger motors
      ←───────────────────────── ACK    motors done
  → wait for PAGE_TURNED
      ←──────────────── PAGE_TURNED    notifies camera
  → capture next page
```

## Project structure

```
src/narratron/
  pipeline.py        Orchestrates OCR → TTS per page
  api.py             FastAPI HTTP endpoints
  cli.py             Command-line interface
  config.py          Settings loaded from .env
  models.py          Pydantic data models
  services/
    ocr.py           PaddleOCR backend (mock available)
    tts.py           Piper TTS backend (mock available)
    stt.py           Faster-Whisper backend (mock available)
    protocol.py      TCP protocol bus (software placeholder)
pi/
  camera.py          Runs on Pi: capture loop, audio playback, page-turn coordination
  main.py            Runs on Pico W: motor control, WiFi listener
  captured_images/   Runtime image output (gitignored)
templates/           Browser UI (Jinja2)
tests/               Unit and integration tests
```

## Quick start

1. Install uv (if not already installed):

```bash
brew install uv
```

2. Create `.env` from template and fill in your values:

```bash
cp .env.example .env
```

3. Sync dependencies:

```bash
uv sync --extra test
```

Optional ML dependencies (PaddleOCR, Faster-Whisper):

```bash
uv sync --extra test --extra ml
```

## Run the Narra-Tron server (Pi)

```bash
uv run narra-tron serve --host 127.0.0.1 --port 8000
```

Or via FastAPI directly:

```bash
uv run fastapi run src/narratron/api.py --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Run the camera loop (Pi)

This starts the full automated capture → narrate → page-turn cycle.

```bash
set -a && source .env && set +a && python pi/camera.py
```

Before running, make sure `.env` has `PICO_HOST` set to the Pico W's IP address (see below).

## Configure the Pico W

Open [pi/main.py](pi/main.py) and set these three values at the top:

```python
SSID = "your_wifi_network"
from picamera2.previews import previews
PASSWORD = "your_wifi_password"
CAMERA_HOST = "192.168.x.x"  # IP of the Pi running camera.py
```

Flash `pi/main.py` onto the Pico W using Thonny or `mpremote`. On boot it will connect to WiFi and print its IP address to the serial console — that IP is your `PICO_HOST` value for `.env`.

### Getting the Pico W's IP address

The Pico W prints its IP when it connects to WiFi. To read it:

**Option A — Thonny (easiest):**
1. Open Thonny, connect to the Pico W
2. Run `pi/main.py` (or it auto-runs on boot)
3. The Shell panel prints: `Pico IP: 192.168.x.x`

**Option B — mpremote (terminal):**
```bash
pip install mpremote
mpremote connect auto run pi/main.py
# Output: Pico IP: 192.168.x.x
```

**Option C — router admin page:**
Log into your router (usually `192.168.1.1`) and look for a device named `Pico` or `raspberrypi-pico` in the connected devices list.

Once you have the IP, add it to `.env`:

```env
PICO_HOST=192.168.x.x
```

## Browser UI (development)

```
http://127.0.0.1:8000/
```

Upload a page image and test OCR + TTS without the camera loop.

## API usage

Process a page image:

```bash
curl -X POST http://127.0.0.1:8000/v1/pipeline/process-page \
  -H "Content-Type: application/json" \
  -d '{"image_path":"sample_page.png","output_audio_path":"output.wav"}'
```

Parse a voice transcript:

```bash
curl -X POST http://127.0.0.1:8000/v1/stt/parse-transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript":"please turn to the next page"}'
```

## CLI usage

```bash
uv run narra-tron process-page sample_page.png output.wav
uv run narra-tron parse-transcript "stop reading"
uv run narra-tron transcribe-command command.wav
```

## Enabling real ML backends

By default, mock mode is on so development works without hardware.

1. Install ML dependencies:

```bash
uv sync --extra ml
```

2. Install Piper CLI and download a voice model (`.onnx`).

3. Set in `.env`:

```env
NARRATRON_USE_MOCK_SERVICES=false
NARRATRON_PIPER_BIN=piper
NARRATRON_PIPER_MODEL_PATH=/absolute/path/to/voice-model.onnx
```

### Mock mode spoken audio on macOS

When `NARRATRON_USE_MOCK_SERVICES=true`, Narra-Tron tries macOS `say` before falling back to a generated tone. Pin a voice explicitly if needed:

```env
NARRATRON_SYSTEM_TTS_VOICE=Samantha
```

## Run tests

```bash
uv run pytest
```
