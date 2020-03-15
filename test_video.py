import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
raw_capture = PiRGBArray(camera, size=(640, 480))

time.sleep(0.1)

# cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('/home/pi/Desktop/output.mp4', fourcc, 16, (640, 480))
# out = cv2.VideoWriter('output.avi', -1, 20.0, (640, 480))

count = 0

for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
    image = frame.array

    out.write(image)

    if count == 240:
        break

    count += 1

    # cv2.imshow('frame', image)

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

    raw_capture.truncate(0)


# Release everything if job is finished

out.release()
cv2.destroyAllWindows()
