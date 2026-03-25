from __future__ import annotations

from pathlib import Path
import tempfile


_SAMPLE_DOSTOYEVSKY_PASSAGE = (
    "I am a sick man... I am a spiteful man. I am an unattractive man. "
    "I think there is something wrong with my liver."
)


class OCRService:
    def __init__(self, use_mock: bool = True) -> None:
        self.use_mock = use_mock
        self._engine = None

    def _ensure_engine(self) -> None:
        if self.use_mock or self._engine is not None:
            return

        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Install requirements-ml.txt or set NARRATRON_USE_MOCK_SERVICES=true."
            ) from exc

        self._engine = PaddleOCR(use_angle_cls=True, lang="en")

    def _run_ocr(self, image_path: str):
        assert self._engine is not None

        try:
            # PaddleOCR 2.x supports cls; some newer paths do not.
            return self._engine.ocr(image_path, cls=True)
        except TypeError as exc:
            if "cls" not in str(exc):
                raise
            return self._engine.ocr(image_path)

    def _normalize_input_path(self, path: Path) -> tuple[str, Path | None]:
        supported_suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".pdf"}
        if path.suffix.lower() in supported_suffixes:
            return str(path), None

        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Unsupported image format for PaddleOCR. Install Pillow or upload jpg/png/jpeg/bmp/pdf."
            ) from exc

        with Image.open(path) as img:
            converted = img.convert("RGB")
            with tempfile.NamedTemporaryFile(
                prefix="narra-tron-ocr-",
                suffix=".png",
                delete=False,
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
            converted.save(tmp_path, format="PNG")

        return str(tmp_path), tmp_path

    def _extract_lines(self, result) -> list[str]:
        lines: list[str] = []

        if not isinstance(result, list):
            return lines

        # PaddleOCR 2.x legacy format: [[[[x,y],...], ["text", score]], ...]
        for block in result:
            if not isinstance(block, list):
                continue

            for entry in block:
                if not isinstance(entry, (list, tuple)):
                    continue
                if len(entry) < 2:
                    continue

                rec = entry[1]
                if (
                    isinstance(rec, (list, tuple))
                    and len(rec) >= 1
                    and isinstance(rec[0], str)
                ):
                    text = rec[0].strip()
                    if text:
                        lines.append(text)

        if lines:
            return lines

        # PaddleOCR newer format can include dict items with rec_texts.
        for item in result:
            if not isinstance(item, dict):
                continue
            rec_texts = item.get("rec_texts")
            if isinstance(rec_texts, list):
                for text in rec_texts:
                    if isinstance(text, str):
                        stripped = text.strip()
                        if stripped:
                            lines.append(stripped)

        return lines

    def extract_text(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if self.use_mock:
            return f"[MOCK OCR] {_SAMPLE_DOSTOYEVSKY_PASSAGE}"

        self._ensure_engine()
        assert self._engine is not None

        ocr_input_path, tmp_path = self._normalize_input_path(path)
        try:
            result = self._run_ocr(ocr_input_path)
            lines = self._extract_lines(result)
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

        return "\n".join(lines)
