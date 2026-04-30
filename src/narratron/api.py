from __future__ import annotations

import io
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi import File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

from narratron.models import (
    CommandResult,
    PageProcessRequest,
    PageProcessResult,
    ParseTranscriptRequest,
    TranscribeRequest,
)
from narratron.pipeline import NarraTronPipeline

app = FastAPI(title="Narra-Tron API", version="0.1.0")
pipeline = NarraTronPipeline.build_default()
templates = Jinja2Templates(directory="templates")
Path("output").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")


def _audio_source_url(audio_path: str) -> str:
    path = Path(audio_path)

    # Absolute filesystem paths are not directly web-accessible; proxy them via endpoint.
    if path.is_absolute():
        return f"/ui/audio-file?path={quote(audio_path, safe='')}"

    if audio_path.startswith(("http://", "https://", "/")):
        return audio_path

    return f"/{audio_path.lstrip('/')}"


def _base_context(request: Request) -> dict[str, object]:
    return {
        "request": request,
        "process_result": None,
        "parse_result": None,
        "error": None,
    }


@app.get("/", response_class=HTMLResponse)
def ui_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", _base_context(request))


@app.post("/ui/process-page", response_class=HTMLResponse)
async def ui_process_page(
    request: Request,
    page_image: UploadFile = File(...),
    output_audio_path: str = Form("output/output.wav"),
    use_real_ocr: bool = Form(True),
) -> HTMLResponse:
    ctx = _base_context(request)

    if not page_image.filename:
        ctx["error"] = "Please select an image file."
        return templates.TemplateResponse("index.html", ctx)

    suffix = Path(page_image.filename).suffix or ".png"
    tmp_dir = Path(tempfile.gettempdir()) / "narra-tron-ui"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    saved_path = tmp_dir / f"{uuid4().hex}{suffix}"
    saved_path.write_bytes(await page_image.read())

    try:
        result = pipeline.process_page(
            image_path=str(saved_path),
            output_audio_path=output_audio_path,
            force_real_ocr=use_real_ocr,
        )
        payload = result.model_dump()
        payload["audio_url"] = _audio_source_url(payload["audio_path"])
        ctx["process_result"] = payload
    except Exception as exc:
        details = str(exc)
        if "PaddleOCR is not installed" in details:
            details = f"{details} Install it with: uv sync --extra ml"
        ctx["error"] = details

    return templates.TemplateResponse("index.html", ctx)


@app.post("/ui/parse-transcript", response_class=HTMLResponse)
def ui_parse_transcript(request: Request, transcript: str = Form("")) -> HTMLResponse:
    ctx = _base_context(request)

    if not transcript.strip():
        ctx["error"] = "Please enter transcript text."
        return templates.TemplateResponse("index.html", ctx)

    result = pipeline.parse_transcript(transcript=transcript)
    ctx["parse_result"] = result.model_dump()
    return templates.TemplateResponse("index.html", ctx)


@app.post("/ui/capture-and-ocr", response_class=HTMLResponse)
async def ui_capture_and_ocr(
    request: Request,
    half: str = Form("left"),
    output_audio_path: str = Form("output/output.wav"),
) -> HTMLResponse:
    ctx = _base_context(request)
    try:
        saved_path = _capture_full_res_image(half)
        result = pipeline.process_page(
            image_path=str(saved_path),
            output_audio_path=output_audio_path,
            force_real_ocr=True,
        )
        payload = result.model_dump()
        payload["audio_url"] = _audio_source_url(payload["audio_path"])
        ctx["process_result"] = payload
    except Exception as exc:
        ctx["error"] = str(exc)
    return templates.TemplateResponse("index.html", ctx)


@app.get("/ui/audio-file")
def ui_audio_file(path: str) -> FileResponse:
    audio_path = Path(path)
    if not audio_path.exists() or not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(str(audio_path), media_type="audio/wav")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/pipeline/process-page", response_model=PageProcessResult)
def process_page(req: PageProcessRequest) -> PageProcessResult:
    try:
        return pipeline.process_page(
            image_path=req.image_path, output_audio_path=req.output_audio_path, force_real_ocr=True
        )
    except FileNotFoundError as exc:
        print(f"File not found during page processing: {exc}")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        print(f"File not found during page processing: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/stt/transcribe-command", response_model=CommandResult)
def transcribe_command(req: TranscribeRequest) -> CommandResult:
    try:
        return pipeline.transcribe_command(audio_path=req.audio_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/stt/parse-transcript", response_model=CommandResult)
def parse_transcript(req: ParseTranscriptRequest) -> CommandResult:
    return pipeline.parse_transcript(transcript=req.transcript)


_camera_lock = threading.Lock()
_camera = None


def _get_preview_camera():
    global _camera
    with _camera_lock:
        if _camera is not None:
            return _camera
        try:
            from picamera2 import Picamera2
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration(main={"size": (640, 480)}))
            cam.start()
            time.sleep(1)
            _camera = cam
            return cam
        except Exception as exc:
            raise RuntimeError(f"Camera unavailable: {exc}") from exc


def _capture_full_res_image(half: str) -> Path:
    """Capture full-resolution still, rotate 180°, crop to the requested half."""
    global _camera

    with _camera_lock:
        # Stop and release the preview camera so we can reconfigure for a still.
        if _camera is not None:
            try:
                _camera.stop()
                _camera.close()
            except Exception:
                pass
            _camera = None

        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError("picamera2 is not installed") from exc

        cam = Picamera2()
        cam.configure(cam.create_still_configuration())
        cam.start()
        time.sleep(0.5)

        tmp_dir = Path(tempfile.gettempdir()) / "narra-tron-ui"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        raw_path = tmp_dir / f"{uuid4().hex}_raw.jpg"
        cam.capture_file(str(raw_path))
        cam.stop()
        cam.close()

    img = Image.open(str(raw_path))
    img = img.rotate(180)

    w, h = img.size
    if half == "left":
        img = img.crop((0, 0, w // 2, h))
    else:
        img = img.crop((w // 2, 0, w, h))

    out_path = tmp_dir / f"{uuid4().hex}.jpg"
    img.save(str(out_path), quality=95)
    return out_path


def _mjpeg_frames():
    cam = _get_preview_camera()
    while True:
        buf = io.BytesIO()
        cam.capture_file(buf, format="jpeg")
        buf.seek(0)
        frame = buf.read()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
        time.sleep(0.2)  # 5 fps


@app.get("/camera/stream")
def camera_stream():
    try:
        return StreamingResponse(
            _mjpeg_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
