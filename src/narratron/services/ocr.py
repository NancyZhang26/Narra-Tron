from __future__ import annotations

from pathlib import Path


_SAMPLE_DOSTOYEVSKY_PASSAGE = (
    "I am a sick man... I am a spiteful man. I am an unattractive man. "
    "I think there is something wrong with my liver."
)


class OCRService:
    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock

    def extract_text(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if self.use_mock:
            return f"[MOCK OCR] {_SAMPLE_DOSTOYEVSKY_PASSAGE}"

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "pytesseract or Pillow is not installed. Run: uv add pytesseract Pillow"
            ) from exc

        try:
            image = Image.open(path)
            return pytesseract.image_to_string(image)
        except Exception as exc:
            raise RuntimeError(f"OCR failed: {exc}") from exc
