from pathlib import Path

from narratron.services.ocr import OCRService


def test_extract_text_falls_back_when_cls_not_supported(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")

    class FakeEngine:
        def ocr(self, _path: str, **kwargs):
            if "cls" in kwargs:
                raise TypeError(
                    "PaddleOCR.predict() got an unexpected keyword argument 'cls'"
                )
            return [[[[[0, 0], [1, 0], [1, 1], [0, 1]], ["line one", 0.99]]]]

    svc = OCRService(use_mock=False)
    svc._engine = FakeEngine()

    text = svc.extract_text(str(image_path))

    assert text == "line one"


def test_extract_text_parses_legacy_paddleocr_shape(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")

    class FakeEngine:
        def ocr(self, _path: str, **_kwargs):
            return [
                [
                    [[[0, 0], [1, 0], [1, 1], [0, 1]], ["first", 0.99]],
                    [[[0, 2], [1, 2], [1, 3], [0, 3]], ["second", 0.95]],
                ]
            ]

    svc = OCRService(use_mock=False)
    svc._engine = FakeEngine()

    text = svc.extract_text(str(image_path))

    assert text == "first\nsecond"


def test_extract_text_parses_rec_texts_shape(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")

    class FakeEngine:
        def ocr(self, _path: str, **_kwargs):
            return [
                {"rec_texts": ["chapter 1", "the upheaval begins"]},
                {"rec_texts": [" ", "line 2"]},
            ]

    svc = OCRService(use_mock=False)
    svc._engine = FakeEngine()

    text = svc.extract_text(str(image_path))

    assert text == "chapter 1\nthe upheaval begins\nline 2"


def test_extract_text_converts_webp_to_png_before_ocr(tmp_path: Path) -> None:
    image_path = tmp_path / "page.webp"

    from PIL import Image

    Image.new("RGB", (4, 4), "white").save(image_path, format="WEBP")

    seen_path: dict[str, str] = {}

    class FakeEngine:
        def ocr(self, ocr_path: str, **_kwargs):
            seen_path["value"] = ocr_path
            return [[[[[0, 0], [1, 0], [1, 1], [0, 1]], ["converted", 0.99]]]]

    svc = OCRService(use_mock=False)
    svc._engine = FakeEngine()

    text = svc.extract_text(str(image_path))

    assert text == "converted"
    assert seen_path["value"].endswith(".png")


def test_extract_text_keeps_supported_png_path(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake")

    seen_path: dict[str, str] = {}

    class FakeEngine:
        def ocr(self, ocr_path: str, **_kwargs):
            seen_path["value"] = ocr_path
            return [[[[[0, 0], [1, 0], [1, 1], [0, 1]], ["native", 0.99]]]]

    svc = OCRService(use_mock=False)
    svc._engine = FakeEngine()

    text = svc.extract_text(str(image_path))

    assert text == "native"
    assert seen_path["value"] == str(image_path)
