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

SSID = "YOUR_WIFI"
PASSWORD = "YOUR_PASS"
CAMERA_HOST = "172.20.10.3"  # IP of the Pi running camera.py
CAMERA_PORT = 9998


def spin_roller():
    roller.duty_u16(65535)
    time.sleep(1)
    roller.duty_u16(0)
    print("roller finished")


def spin_finger():
    finger.duty_u16(5000)
    time.sleep(0.4)
    finger.duty_u16(0)
    print("finger finished")


def turn_page():
    spin_roller()
    spin_finger()


def notify_camera():
    try:
        r = urequests.get(f"http://{CAMERA_HOST}:{CAMERA_PORT}/")
        if r.status_code != 200:
            print(f"ERROR: camera did not ACK PAGE_TURNED (got status {r.status_code})")
        else:
            print("PAGE_TURNED acknowledged by camera")
        r.close()
    except Exception as e:
        print(f"ERROR: failed to notify camera at {CAMERA_HOST}:{CAMERA_PORT}: {e}")


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)
wlan.connect(SSID, PASSWORD)
while not wlan.isconnected():
    time.sleep(1)

print("Pico IP:", wlan.ifconfig()[0])

addr = socket.getaddrinfo("0.0.0.0", 9999)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print("Listening for TURN_PAGE signal on port 9999...")

while True:
    cl, addr = s.accept()
    request = cl.recv(1024)
    if b"TURN_PAGE" in request:
        print("TURN_PAGE received from", addr[0])
        turn_page()
        cl.send(b"ACK\n")
        time.sleep_ms(200)  # let TCP flush before close; immediate close can RST before ACK arrives
        cl.close()
        notify_camera()  # notify camera only after a real page turn
    else:
        print(f"ERROR: unknown signal from {addr[0]}: {request[:32]!r}")
        cl.send(b"UNKNOWN\n")
        cl.close()
        # do NOT notify camera — no page was turned
