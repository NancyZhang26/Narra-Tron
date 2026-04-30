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

CAPTURED_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "captured_images"
)
NARRATRON_API = os.environ.get("NARRATRON_API", "http://127.0.0.1:8000")
PICO_HOST = os.environ.get("PICO_HOST", "")
PICO_PORT = int(os.environ.get("PICO_PORT", "9999"))
CAMERA_PORT = int(os.environ.get("CAMERA_PORT", "9998"))
PAGES_PER_SPREAD = int(os.environ.get("PAGES_PER_SPREAD", "1"))

os.makedirs(CAPTURED_DIR, exist_ok=True)

picam2 = Picamera2()
picam2.start()
time.sleep(2)  # warm-up


def capture():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CAPTURED_DIR, f"page_{ts}.jpg")
    picam2.capture_file(path)
    print(f"Captured: {path}")
    return path


def submit_to_pipeline(image_path):
    try:
        response = requests.post(
            f"{NARRATRON_API}/v1/pipeline/process-page",
            json={
                "image_path": image_path,
                "output_audio_path": f"output/page_{os.path.basename(image_path)}.wav",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(
            f"Failed to submit page to Narra-Tron API at {NARRATRON_API}: {e}"
        )


def capture_and_narrate(speaker: Speaker) -> bool:
    """Capture a page image, OCR it, synthesise speech, and play it.

    Returns False when the page is blank (end-of-book signal), True otherwise.
    Playback blocks until audio finishes — this is the implicit lock that
    prevents a page-flip signal from being sent while narration is running.
    """
    path = capture()
    result = submit_to_pipeline(path)
    text = result.get("extracted_text", "")
    if not text.strip():
        print("Empty page detected — end of book.")
        return False
    speaker.play(result.get("audio_path", ""))
    return True


def send_turn_page_to_pico():
    if not PICO_HOST:
        print("PICO_HOST not set — skipping TURN_PAGE signal")
        return
    try:
        with socket.create_connection((PICO_HOST, PICO_PORT), timeout=18000) as sock:
            sock.sendall(b"TURN_PAGE\n")
            sock.settimeout(10)  # motors take ~1.4 s; 10 s is generous
            ack = sock.recv(64)
            if b"ACK" not in ack:
                raise RuntimeError(f"Expected ACK from Pico, got: {ack!r}")
        print(f"TURN_PAGE acknowledged by Pico at {PICO_HOST}:{PICO_PORT}")
    except socket.timeout:
        raise RuntimeError(
            f"Pico at {PICO_HOST}:{PICO_PORT} did not ACK TURN_PAGE within timeout — "
            "check that the Pico is powered on and connected to WiFi"
        )
    except OSError as e:
        raise RuntimeError(
            f"ERROR: Could not reach Pico at {PICO_HOST}:{PICO_PORT}: {e}"
        )


def wait_for_page_turned(srv):
    """Block until the Pico sends its PAGE_TURNED HTTP notification."""
    print("Waiting for PAGE_TURNED signal from Pico...")
    conn, addr = srv.accept()
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


speaker = Speaker()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", CAMERA_PORT))
    srv.listen(1)
    print(f"Camera server listening on port {CAMERA_PORT}")
    end_of_book = False
    # Main loop: wait for Pico's page-turn confirmation, capture the next
    # spread, then signal the next turn. Exits cleanly on an empty page.
    while not end_of_book:
        try:
            time.sleep(0.5)  # mechanical settle after page turn
            for _ in range(PAGES_PER_SPREAD):
                res = capture_and_narrate(speaker)
                print(res)
                if not res:
                    end_of_book = True
                    break
            if not end_of_book:
                send_turn_page_to_pico()
        except RuntimeError as e:
            print(f"ERROR: {e}")
        wait_for_page_turned(srv)

    print("Book complete — shutting down.")
    picam2.stop()
