import cv2

cam = cv2.VideoCapture(8, cv2.CAP_V4L2)

if not cam.isOpened():
    print("Camera not opened")
    exit()

while True:
    ret, frame = cam.read()

    if not ret:
        print("Failed to grab frame")
        break

    # show live preview
    cv2.imshow("Preview - Press S to take photo, Q to quit", frame)

    key = cv2.waitKey(1)

    if key == ord('s'):
        cv2.imwrite("picture.jpg", frame)
        print("Picture saved!")

    elif key == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()