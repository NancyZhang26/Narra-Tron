from picamera2 import Picamera2
import time

picam2 = Picamera2()
picam2.start()

time.sleep(2)

picam2.capture_file("Pierce.jpg")
# save the captured file into the directory
print("Image saved!")