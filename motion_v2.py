from picamera.array import PiRGBArray
from picamera import PiCamera
import imutils
import cv2
import argparse
import warnings
import json
import time
import datetime
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True, help="path to the json file")
ap.add_argument("-s", "--start-index", required=True, type=int, default=0, help="start index for file naming")
args = vars(ap.parse_args())
print(args)

warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))


def wait_for_motion():
    camera = PiCamera()
    camera.resolution = tuple(conf["resolution"])
    camera.framerate = conf["fps"]
    raw_capture = PiRGBArray(camera, size=tuple(conf["resolution"]))

    print("[INFO] warming up...")
    time.sleep(conf["camera_warmup_time"])
    avg = None
    motion_frames = 0

    for f in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
        frame = f.array
        frame_old = frame
        timestamp = datetime.datetime.now()
        text = "Unoccupied"

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
            motion_frames += 1
            if motion_frames >= conf["min_motion_frames"]:
                camera.close()
                return True

        else:
            motion_frames = 0

        if conf["show_video"]:
            cv2.imshow("Security Feed", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                camera.close()
                exit()

        raw_capture.truncate(0)

    camera.close()


def record_vid(i):
    name = "/home/pi/Desktop/vids/output_{}.h264".format(str(i).zfill(6))
    subprocess.run(["raspivid", '-v', '-o', name, '-t', str(conf["record_time"]), '-g', '4', '-fps', str(conf["fps"]), '-vf', '-a', '12',
                    '-n', '-hf'])


if __name__ == '__main__':
    i = args["start_index"]
    while True:
        if wait_for_motion():
            record_vid(i)
        i += 1
