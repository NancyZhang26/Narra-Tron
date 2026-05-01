import datetime
import os
import socket
import sys
import time

import requests
from picamera2 import Picamera2

# Speaker_Code lives one level up from this file (project root)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from Speaker_Code.speaker import Speaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURED_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "captured_images"
)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
NARRATRON_API = os.environ.get("NARRATRON_API", "http://127.0.0.1:8000")
PICO_HOST = os.environ.get("PICO_HOST", "")
PICO_PORT = int(os.environ.get("PICO_PORT", "9999"))
CAMERA_PORT = int(os.environ.get("CAMERA_PORT", "9998"))
AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE", "plughw:2,0")

os.makedirs(CAPTURED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    requests.post(f"{NARRATRON_API}/camera/release", timeout=5)
    print("Released preview camera from API server.")
except Exception as e:
    print(f"Warning: could not release camera from API server: {e}")

picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (4608, 2592)})
picam2.configure(config)
picam2.start()
time.sleep(2)  # warm-up


def capture():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CAPTURED_DIR, f"page_{ts}.jpg")
    picam2.capture_file(path)
    print(f"Captured: {path}")
    return path


def submit_to_pipeline(image_path, half):
    base = os.path.basename(image_path)
    try:
        response = requests.post(
            f"{NARRATRON_API}/v1/pipeline/process-page",
            json={
                "image_path": image_path,
                "output_audio_path": os.path.join(OUTPUT_DIR, f"page_{base}_{half}.wav"),
                "output_text_path": os.path.join(OUTPUT_DIR, "text", f"page_{base}_{half}.txt"),
                "half": half,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(
            f"Failed to submit page to Narra-Tron API at {NARRATRON_API}: {e}"
        )


def capture_and_narrate(speaker: Speaker) -> None:
    """Capture one spread, then narrate left page then right page.

    A single image is captured and submitted twice — once cropped to the left
    half, once to the right — so both pages are read before the page turner
    is signalled.  Each play() call blocks until that page's audio finishes.
    """
    path = capture()
    for half in ("left", "right"):
        result = submit_to_pipeline(path, half=half)
        if not result.get("ocr_success", True):
            print(f"OCR returned no text for {half} page — narrating error message.")
        speaker.play(result.get("audio_path", ""))


def send_turn_page_to_pico(max_attempts=15, base_delay=3):
    if not PICO_HOST:
        print("PICO_HOST not set — skipping TURN_PAGE signal")
        return
    for attempt in range(1, max_attempts + 1):
        try:
            with socket.create_connection((PICO_HOST, PICO_PORT), timeout=5) as sock:
                sock.sendall(b"TURN_PAGE\n")
                sock.settimeout(10)  # motors take ~1.4 s; 10 s is generous
                ack = sock.recv(64)
                if b"ACK" not in ack:
                    raise RuntimeError(f"Expected ACK from Pico, got: {ack!r}")
            print(f"TURN_PAGE acknowledged by Pico at {PICO_HOST}:{PICO_PORT}")
            return
        except (OSError, socket.timeout) as e:
            delay = min(base_delay * attempt, 30)
            if attempt < max_attempts:
                print(f"[{attempt}/{max_attempts}] Pico not ready ({e}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"Could not reach Pico at {PICO_HOST}:{PICO_PORT} after {max_attempts} attempts: {e}"
                )


def wait_for_page_turned(srv, timeout=300):
    """Block until the Pico sends its PAGE_TURNED HTTP notification.

    Raises RuntimeError after `timeout` seconds so the main loop can retry
    instead of hanging forever if the Pico disconnects mid-turn.
    """
    print(f"Waiting for PAGE_TURNED signal from Pico (timeout {timeout}s)...")
    srv.settimeout(timeout)
    try:
        conn, addr = srv.accept()
    except socket.timeout:
        raise RuntimeError(
            f"Timed out waiting {timeout}s for PAGE_TURNED — Pico may have disconnected"
        )
    finally:
        srv.settimeout(None)
    with conn:
        conn.recv(1024)
        # Send a complete HTTP response so MicroPython's urequests client
        # can reliably read the status and finish the request cleanly.
        conn.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: 2\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            b"OK"
        )
    print(f"PAGE_TURNED received from {addr[0]}")


speaker = Speaker(device=AUDIO_DEVICE)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", CAMERA_PORT))
    srv.listen(1)
    print(f"Camera server listening on port {CAMERA_PORT}")
    while True:
        try:
            time.sleep(0.5)  # mechanical settle after page turn
            # 1. Narrate left then right page (both block until audio finishes).
            capture_and_narrate(speaker)
            # 2. Only reached after both pages are fully narrated.
            send_turn_page_to_pico()
            # 3. Wait for the physical page turn before looping.
            wait_for_page_turned(srv)
        except RuntimeError as e:
            print(f"ERROR: {e}")
            time.sleep(5)  # back off before retrying to avoid hot-spinning

    print("Shutting down.")
    picam2.stop()
    sys.exit(0)
