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

    def process_page(
        self,
        image_path: str,
        output_audio_path: str,
        force_real_ocr: bool = True,
    ) -> PageProcessResult:
        print("using ocr", force_real_ocr)
        if force_real_ocr:
            text = OCRService(use_mock=False).extract_text(image_path)
        else:
            text = self.ocr.extract_text(image_path)

        audio_path = self.tts.synthesize(text=text, output_audio_path=output_audio_path)

        return PageProcessResult(
            extracted_text=text,
            audio_path=audio_path,
        )

    def transcribe_command(self, audio_path: str) -> CommandResult:
        transcript = self.stt.transcribe(audio_path)
        command = self.parser.parse(transcript)
        return CommandResult(command=command, transcript=transcript)

    def parse_transcript(self, transcript: str) -> CommandResult:
        command: CommandType = self.parser.parse(transcript)
        return CommandResult(command=command, transcript=transcript)
