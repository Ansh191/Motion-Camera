from pyimagesearch.tempimage import TempImage
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import dropbox
import imutils
import json
import time
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True, help="path to the json file")
args = vars(ap.parse_args())

warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None

# if conf["use_dropbox"]:
#     client = dropbox.Dropbox(conf["dropbox_access_token"])
#     print("[SUCCESS] dropbox account linked")

camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
raw_capture = PiRGBArray(camera, size=tuple(conf["resolution"]))

print("[INFO] warming up...")
time.sleep(conf["camera_warmup_time"])
avg = None
last_uploaded = datetime.datetime.now()
motion_counter = 0
occupied = False
inactive_counter = 0
counter = 0

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('/home/pi/Desktop/output.mp4', fourcc, conf["fps"] / 2, tuple(conf["resolution"]))

for f in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
    frame = f.array
    frame_old = frame
    timestamp = datetime.datetime.now()
    text = "Unoccupied"

    if occupied:
        if counter <= 48:
            counter += 1
            out.write(frame_old)
            raw_capture.truncate(0)
            continue

    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if avg is None:
        print("[INFO] starting background model...")
        avg = gray.copy().astype("float")
        raw_capture.truncate(0)
        continue

    cv2.accumulateWeighted(gray, avg, 0.5)
    frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frame_delta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    for c in cnts:
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupied"

    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(frame, f"Room Status: {text}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    if text == "Occupied":
        motion_counter += 1
        inactive_counter = 0

        if motion_counter >= conf["min_motion_frames"]:
            print("[INFO] started recording...")
            occupied = True

    else:
        inactive_counter += 1
        if inactive_counter >= 24:
            print("[INFO] stopped recording")
            occupied = False
            inactive_counter = 0
            motion_counter = 0
            counter = 0

    if conf["show_video"]:
        cv2.imshow("Security Feed", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    raw_capture.truncate(0)

out.release()
cv2.destroyAllWindows()
