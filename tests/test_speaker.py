"""Tests for Speaker_Code/speaker.py — runs without hardware via subprocess mocks."""
import subprocess
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Speaker_Code.speaker import Speaker


def test_play_skips_missing_file(capsys):
    s = Speaker()
    s.play("/nonexistent/path/audio.wav")
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "not found" in out


def test_play_calls_aplay(tmp_path, monkeypatch):
    wav = tmp_path / "test.wav"
    wav.write_bytes(b"\x00" * 44)  # minimal placeholder

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    s = Speaker(device="hw:0,0")
    s.play(str(wav))

    assert len(calls) == 1
    assert calls[0] == ["aplay", "-D", "hw:0,0", str(wav)]


def test_play_warns_on_nonzero_exit(tmp_path, monkeypatch, capsys):
    wav = tmp_path / "test.wav"
    wav.write_bytes(b"\x00" * 44)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1),
    )

    s = Speaker()
    s.play(str(wav))

    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "returncode" in out or "code" in out


def test_is_available_true(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0),
    )
    assert Speaker().is_available() is True


def test_is_available_false(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1),
    )
    assert Speaker().is_available() is False
