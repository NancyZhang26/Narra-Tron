from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CommandType(str, Enum):
    START = "start"
    STOP = "stop"
    TURN = "turn_page"
    BACK = "go_back"
    UNKNOWN = "unknown"


class OCRResult(BaseModel):
    text: str = Field(default="")


class STTResult(BaseModel):
    transcript: str = Field(default="")


class CommandResult(BaseModel):
    command: CommandType
    transcript: str


class PageProcessRequest(BaseModel):
    image_path: str
    output_audio_path: str = "output.wav"
    output_text_path: str | None = None
    half: str | None = None  # "left" or "right" — rotate 180° and crop if provided


class PageProcessResult(BaseModel):
    extracted_text: str
    audio_path: str
    ocr_success: bool = True
    # Only populated on every 2nd page (both pages of an open book narrated).
    page_turn_signal: str | None = None


class TranscribeRequest(BaseModel):
    audio_path: str


class ParseTranscriptRequest(BaseModel):
    transcript: str
