from __future__ import annotations

from dataclasses import dataclass

from narratron.config import settings
from narratron.models import CommandResult, CommandType, PageProcessResult
from narratron.services.ocr import OCRService
from narratron.services.stt import CommandParser, STTService
from narratron.services.tts import TTSService


@dataclass(slots=True)
class NarraTronPipeline:
    ocr: OCRService
    tts: TTSService
    stt: STTService
    parser: CommandParser

    @classmethod
    def build_default(cls) -> "NarraTronPipeline":
        return cls(
            ocr=OCRService(use_mock=settings.use_mock_services),
            tts=TTSService(
                use_mock=settings.use_mock_services,
                piper_bin=settings.piper_bin,
                piper_model_path=settings.piper_model_path,
                piper_speaker_id=settings.piper_speaker_id,
                system_tts_voice=settings.system_tts_voice,
            ),
            stt=STTService(
                model_size=settings.stt_model_size, use_mock=settings.use_mock_services
            ),
            parser=CommandParser(),
        )

    _NO_TEXT_FALLBACK = (
        "No text was extracted from the page. "
        "Please adjust the angle of the camera to ensure a better image, "
        "and restart the program."
    )

    @staticmethod
    def _flatten_to_sentences(text: str) -> str:
        """Join layout-broken lines so each output line is one complete sentence."""
        import re
        # Collapse runs of whitespace/newlines into single spaces, then split on
        # sentence-ending punctuation followed by whitespace or end-of-string.
        flat = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", flat)
        return "\n".join(s.strip() for s in sentences if s.strip())

    def process_page(
        self,
        image_path: str,
        output_audio_path: str,
        output_text_path: str | None = None,
        force_real_ocr: bool = True,
    ) -> PageProcessResult:
        ocr_service = OCRService(use_mock=False) if force_real_ocr else self.ocr
        text = ocr_service.extract_text(image_path)

        ocr_success = bool(text.strip())
        if not ocr_success:
            print(
                f"[NarraTron] OCR returned no text for image: {image_path}\n"
                f"[NarraTron] {self._NO_TEXT_FALLBACK}"
            )
            text = self._NO_TEXT_FALLBACK
        else:
            text = self._flatten_to_sentences(text)

        if output_text_path:
            from pathlib import Path
            Path(output_text_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_text_path).write_text(text, encoding="utf-8")

        audio_path = self.tts.synthesize(text=text, output_audio_path=output_audio_path)

        return PageProcessResult(
            extracted_text=text,
            audio_path=audio_path,
            ocr_success=ocr_success,
        )

    def transcribe_command(self, audio_path: str) -> CommandResult:
        transcript = self.stt.transcribe(audio_path)
        command = self.parser.parse(transcript)
        return CommandResult(command=command, transcript=transcript)

    def parse_transcript(self, transcript: str) -> CommandResult:
        command: CommandType = self.parser.parse(transcript)
        return CommandResult(command=command, transcript=transcript)
