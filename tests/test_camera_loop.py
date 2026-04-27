"""Tests for the camera.py loop logic — no hardware needed.

Imports only the pure functions by patching hardware dependencies before
the module-level picamera2 initialisation runs.
"""
import socket
import sys
import os
import types
import importlib
import subprocess
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Stub out picamera2 and Speaker_Code so the module loads on non-Pi hardware
# ---------------------------------------------------------------------------

_fake_picamera2_mod = types.ModuleType("picamera2")
_fake_cam = MagicMock()
_fake_picamera2_mod.Picamera2 = MagicMock(return_value=_fake_cam)
sys.modules.setdefault("picamera2", _fake_picamera2_mod)

# Ensure project root is on path so Speaker_Code imports work
_root = os.path.join(os.path.dirname(__file__), "..")
if _root not in sys.path:
    sys.path.insert(0, _root)


# ---------------------------------------------------------------------------
# Helper: import camera module with time.sleep neutralised
# ---------------------------------------------------------------------------

def _import_camera():
    import time as _time
    _real_sleep = _time.sleep
    with patch("time.sleep"):          # skip warm-up sleep at module level
        # Force reimport each time so env vars take effect
        if "pi.camera" in sys.modules:
            del sys.modules["pi.camera"]
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pi.camera",
            os.path.join(os.path.dirname(__file__), "..", "pi", "camera.py"),
        )
        # We can't execute the module (it has top-level socket.bind) so just
        # test the functions in isolation by importing them directly.
    return None


# ---------------------------------------------------------------------------
# Unit-test the functions that carry the new logic
# ---------------------------------------------------------------------------

class FakeSpeaker:
    def __init__(self):
        self.played = []

    def play(self, path):
        self.played.append(path)


def make_submit_result(text="Hello world", audio="/tmp/out.wav"):
    return {"extracted_text": text, "audio_path": audio}


def _capture_and_narrate_fn():
    """Load and return just the capture_and_narrate function, with hardware stubs."""
    import importlib.util, types, time

    # Build a minimal fake module namespace
    ns = {
        "os": os,
        "datetime": __import__("datetime"),
        "socket": socket,
        "sys": sys,
        "time": time,
        "requests": MagicMock(),
        "Picamera2": _fake_picamera2_mod.Picamera2,
        "Speaker": __import__("Speaker_Code.speaker", fromlist=["Speaker"]).Speaker,
        "CAPTURED_DIR": "/tmp/narratron_test_captures",
        "NARRATRON_API": "http://127.0.0.1:8000",
        "PICO_HOST": "",
        "PICO_PORT": 9999,
        "CAMERA_PORT": 9998,
        "PAGES_PER_SPREAD": 2,
    }

    src = open(os.path.join(os.path.dirname(__file__), "..", "pi", "camera.py")).read()
    # Execute only the function definitions (stop before module-level socket code)
    fn_src = src.split("speaker = Speaker()")[0]
    exec(compile(fn_src, "pi/camera.py", "exec"), ns)
    return ns["capture_and_narrate"]


@pytest.fixture()
def capture_and_narrate():
    return _capture_and_narrate_fn()


def test_capture_and_narrate_returns_true_for_text_page(capture_and_narrate, tmp_path, monkeypatch):
    spk = FakeSpeaker()

    with patch("pi.camera.capture", return_value=str(tmp_path / "page.jpg"), create=True), \
         patch("pi.camera.submit_to_pipeline", return_value=make_submit_result("Some text"), create=True):

        # Call the extracted function directly using its own closure namespace
        import types
        fn = capture_and_narrate

        # We need to patch within the function's globals
        fn.__globals__["capture"] = lambda: str(tmp_path / "page.jpg")
        fn.__globals__["submit_to_pipeline"] = lambda p: make_submit_result("Some text")

        result = fn(spk)

    assert result is True
    assert len(spk.played) == 1


def test_capture_and_narrate_returns_false_for_empty_page(capture_and_narrate, tmp_path, capsys):
    spk = FakeSpeaker()

    capture_and_narrate.__globals__["capture"] = lambda: str(tmp_path / "page.jpg")
    capture_and_narrate.__globals__["submit_to_pipeline"] = lambda p: make_submit_result("   \n\t  ")

    result = capture_and_narrate(spk)

    assert result is False
    assert spk.played == []
    out = capsys.readouterr().out
    assert "Empty page" in out


def test_capture_and_narrate_returns_false_for_none_text(capture_and_narrate, tmp_path):
    spk = FakeSpeaker()

    capture_and_narrate.__globals__["capture"] = lambda: str(tmp_path / "page.jpg")
    capture_and_narrate.__globals__["submit_to_pipeline"] = lambda p: {"extracted_text": None, "audio_path": ""}

    result = capture_and_narrate(spk)
    assert result is False
