import cv2
import numpy as np
import json
from detector import YOLOv11Detector
from tracker import Tracker
from speed_estimator import SpeedEstimator
from logger_config import setup_logger

logger = setup_logger()

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

speed_log = []
logged_ids = set()

frame_idx = 0

while True:
    logger.info("Video processing started.")

    ret, frame = cap.read()
    if not ret:
        logger.info("End of video reached or failed to read frame.")
        break

    frame_idx += 1
    timestamp = frame_idx / fps

    logger.info(f"Processing frame {frame_idx}")

    dets_raw = detector.detect(frame)
    bboxes = [d[:4] for d in dets_raw]
    tracks = tracker.update(bboxes)

    logger.info(f"Detections: {len(dets_raw)} vehicles")

    for tr in tracks:
        x1, y1, x2, y2 = [int(v) for v in tr.box]
        track_id = tr.track_id
        y_center = (y1 + y2) // 2

        speed_kmph = speed_est.update_and_get_speed(
            track_id, y_center, timestamp, LINE1_Y, LINE2_Y
        )

        if speed_kmph is not None and track_id not in logged_ids:
            logger.info(f"Speed detected - Track ID: {track_id}, Speed: {speed_kmph} km/h at timestamp {timestamp:.2f}")
            logged_ids.add(track_id)
            speed_log.append({
                "track_id": track_id,
                "speed_kmph": speed_kmph,
                "timestamp": round(timestamp, 2)
            })

        if speed_kmph is not None:
            tr.speed = speed_kmph

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        label = f"ID {track_id}"
        if tr.speed is not None:
            label += f" | {tr.speed:.1f} km/h"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

    cv2.line(frame, (0, LINE1_Y), (width, LINE1_Y), (255,0,0), 2)
    cv2.line(frame, (0, LINE2_Y), (width, LINE2_Y), (0,0,255), 2)

    cv2.imshow("Vehicles Speed Detection", frame)

    out.write(frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

with open("speed_log.json", "w") as f_json:
    json.dump(speed_log, f_json, indent=2)