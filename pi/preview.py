"""
DEBUG ONLY — live camera preview for physical alignment.
Run with: python pi/preview.py
Press Ctrl+C to exit.
"""
import time
from picamera2 import Picamera2
from picamera2.previews import QtPreview

cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": (1280, 720)}))
cam.start_preview(QtPreview())
cam.start()
print("Preview running — press Ctrl+C to exit.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    cam.stop_preview()
    cam.stop()
    cam.close()
    print("Preview closed.")
