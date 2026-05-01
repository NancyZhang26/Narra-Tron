from machine import Pin, PWM
import time
import network
import socket
import urequests  # MicroPython built-in; not available in standard Python (IDE warning is expected)

roller = PWM(Pin(16))
# finger = Pin(20, Pin.OUT)
finger = PWM(Pin(18))

roller.freq(10000)
finger.freq(5000)

SSID = "nancy"
# PASSWORD = "YOUR_PASS"
CAMERA_HOST = "10.42.0.1"  # IP of the Pi running camera.py
CAMERA_PORT = 9998


def spin_roller():
    roller.duty_u16(65535)
    time.sleep(.21)
    roller.duty_u16(0)
    print("roller finished")


def spin_finger():
    finger.duty_u16(5000)
    time.sleep(1)
    finger.duty_u16(0)
    print("finger finished")


def turn_page():
    spin_roller()
    spin_finger()


def notify_camera(max_attempts=15, base_delay=3):
    for attempt in range(1, max_attempts + 1):
        try:
            r = urequests.get(f"http://{CAMERA_HOST}:{CAMERA_PORT}/")
            if r.status_code != 200:
                print(f"ERROR: camera did not ACK PAGE_TURNED (got status {r.status_code})")
            else:
                print("PAGE_TURNED acknowledged by camera")
            r.close()
            return
        except Exception as e:
            delay = min(base_delay * attempt, 30)
            if attempt < max_attempts:
                print(f"[{attempt}/{max_attempts}] Camera not ready ({e}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"ERROR: failed to notify camera at {CAMERA_HOST}:{CAMERA_PORT} after {max_attempts} attempts: {e}")

def connect_wifi():
    """Block until connected to SSID. Retries forever so order of startup doesn't matter."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xA11140)
    while True:
        if wlan.isconnected():
            print("Pico IP:", wlan.ifconfig()[0])
            return wlan
        print(f"Connecting to '{SSID}'... (status={wlan.status()})")
        try:
            wlan.connect(SSID)  # , PASSWORD)
        except Exception as e:
            print(f"  connect() raised: {e}")
        # Poll up to 15 s for the hotspot to accept us
        for _ in range(15):
            if wlan.isconnected():
                break
            time.sleep(1)
        if not wlan.isconnected():
            # Hotspot not up yet — disconnect cleanly and wait before retrying
            try:
                wlan.disconnect()
            except Exception:
                pass
            print(f"Hotspot '{SSID}' not available, waiting 5s before retry...")
            time.sleep(5)


def run():
    wlan = connect_wifi()

    while True:  # outer loop — re-entered on WiFi loss
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(socket.getaddrinfo("0.0.0.0", 9999)[0][-1])
        srv.listen(1)
        srv.settimeout(5)  # so we can check wlan.isconnected() periodically
        print("Listening for TURN_PAGE signal on port 9999...")

        try:
            while True:
                if not wlan.isconnected():
                    print("WiFi lost — closing socket and reconnecting...")
                    break  # drop to reconnect block below

                try:
                    cl, addr = srv.accept()
                except OSError:
                    # accept() timed out (every 5 s) — just loop and check WiFi
                    continue

                request = cl.recv(1024)
                if b"TURN_PAGE" in request:
                    print("TURN_PAGE received from", addr[0])
                    turn_page()
                    cl.send(b"ACK\n")
                    time.sleep_ms(
                        200
                    )  # let TCP flush before close; immediate close can RST before ACK arrives
                    cl.close()
                    notify_camera()  # notify camera only after a real page turn
                else:
                    print(f"ERROR: unknown signal from {addr[0]}: {request[:32]!r}")
                    cl.send(b"UNKNOWN\n")
                    cl.close()
                    # do NOT notify camera — no page was turned

        except Exception as e:
            print(f"Unexpected error in socket loop: {e}")
        finally:
            try:
                srv.close()
            except Exception:
                pass

        # Reconnect then fall through to re-bind the socket
        wlan = connect_wifi()


run()
# turn_page()
