from picamera2 import Preview, Picamera2
import time

picam2 = Picamera2()

def preview():
    camera_config = picam2.create_preview_configuration()
    picam2.configure(camera_config)
    picam2.start_preview(Preview.QTGL)

def capture(imgName):
    picam2.start()
    time.sleep(2)
    picam2.autofocus_cycle()
    time.sleep(1)
    picam2.capture_file(imgName)
    picam2.stop()