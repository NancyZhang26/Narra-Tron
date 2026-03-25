from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi import File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
            image_path=req.image_path, output_audio_path=req.output_audio_path
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
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
