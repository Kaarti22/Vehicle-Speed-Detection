import cv2
import numpy as np
from detector import YOLOv11Detector
from tracker import Tracker
from speed_estimator import SpeedEstimator

VIDEO_PATH = "sample.mp4"
LINE1_Y = 415
LINE2_Y = 450
REAL_DISTANCE_M = 20.0

cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
pixel_distance = abs(LINE2_Y - LINE1_Y)

meters_per_pixel = REAL_DISTANCE_M / pixel_distance

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("result.mp4", fourcc, fps, (width, height))

detector = YOLOv11Detector()
tracker  = Tracker()
speed_est = SpeedEstimator(real_distance_m=REAL_DISTANCE_M)

frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_idx += 1
    timestamp = frame_idx / fps

    dets_raw = detector.detect(frame)
    bboxes = [d[:4] for d in dets_raw]
    tracks = tracker.update(bboxes)

    for tr in tracks:
        x1, y1, x2, y2 = [int(v) for v in tr.box]
        track_id = tr.track_id
        y_center = (y1 + y2) // 2

        speed_kmh = speed_est.update_and_get_speed(
            track_id, y_center, timestamp, LINE1_Y, LINE2_Y
        )

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        label = f"ID {track_id}"
        if speed_kmh is not None:
            label += f" | {speed_kmh:.1f} km/h"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

    cv2.line(frame, (0, LINE1_Y), (width, LINE1_Y), (255,0,0), 2)
    cv2.line(frame, (0, LINE2_Y), (width, LINE2_Y), (0,0,255), 2)

    cv2.imshow("Speed Demo", frame)

    out.write(frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()