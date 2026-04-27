"""Live handshake test against the real Pico W.

Mirrors the two legs in pi/camera.py:
  1. Pi → Pico: send TURN_PAGE\n, expect ACK
  2. Pico → Pi: listen for the PAGE_TURNED HTTP callback, reply 200 OK

Usage:
    python3 tests/test_pico_handshake.py

Reads PICO_HOST, PICO_PORT, and CAMERA_PORT from the environment.
Copy .env.example → .env and source it, or export them manually.
"""
import os
import socket
from pathlib import Path

# Load .env from project root if present (so plain `python3 tests/...` works)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

PICO_HOST = "10.42.0.190"
PICO_PORT = int(os.environ.get("PICO_PORT", "9999"))
CAMERA_PORT = int(os.environ.get("CAMERA_PORT", "9998"))

if not PICO_HOST:
    raise SystemExit("PICO_HOST is not set — export it or source your .env file")


def send_turn_page():
    print(f"[1/2] Connecting to Pico at {PICO_HOST}:{PICO_PORT} ...")
    with socket.create_connection((PICO_HOST, PICO_PORT), timeout=5) as sock:
        sock.sendall(b"TURN_PAGE\n")
        print("      Sent TURN_PAGE — waiting for ACK ...")
        sock.settimeout(10)
        ack = sock.recv(64)
        if b"ACK" not in ack:
            raise RuntimeError(f"Expected ACK from Pico, got: {ack!r}")
    print(f"      ACK received: {ack.strip()}")


def wait_for_page_turned():
    print(f"[2/2] Listening for PAGE_TURNED on port {CAMERA_PORT} ...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", CAMERA_PORT))
        srv.listen(1)
        srv.settimeout(15)
        conn, addr = srv.accept()
        with conn:
            conn.recv(1024)
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
    print(f"      PAGE_TURNED received from {addr[0]}")


send_turn_page()
wait_for_page_turned()
print("\nHandshake complete.")
