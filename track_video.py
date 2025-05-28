import cv2
import json
from detector import YOLOv11Detector
from tracker import Tracker
from speed_estimator import SpeedEstimator
from logger_config import setup_logger

logger = setup_logger()

def process_video(video_path, config_path, output_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    
    (x1, y1), (x2, y2) = config["line1"]
    (x3, y3), (x4, y4) = config["line2"]
    LINE1_Y = int((y1 + y2) / 2)
    LINE2_Y = int((y3 + y4) / 2)
    REAL_DISTANCE_M = config["real_world_distance_m"]

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    detector = YOLOv11Detector()
    tracker = Tracker()
    speed_est = SpeedEstimator(real_distance_m=REAL_DISTANCE_M)
    
    speed_log = []
    logged_ids = set()
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        dets_raw = detector.detect(frame)
        timestamp = frame_idx / fps

        bboxes = [d[:4] for d in dets_raw]
        tracks = tracker.update(bboxes)

        for tr in tracks:
            x1, y1, x2, y2 = [int(v) for v in tr.box]
            track_id = tr.track_id
            y_center = (y1 + y2) // 2

            speed_kmph = speed_est.update_and_get_speed(
                track_id, y_center, timestamp, LINE1_Y, LINE2_Y
            )

            if speed_kmph is not None and track_id not in logged_ids:
                logged_ids.add(track_id)
                speed_log.append({
                    "track_id": track_id,
                    "speed_kmph": speed_kmph,
                    "timestamp": round(timestamp, 2)
                })

            if speed_kmph is not None:
                tr.speed = speed_kmph

            if tr.speed is not None and tr.speed >= 5:
                label = f"{tr.speed:.1f} km/h"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, label, ((x1 + x2) // 2 - 30, (y1 + y2) // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

        cv2.line(frame, (0, LINE1_Y), (width, LINE1_Y), (255,0,0), 2)
        cv2.line(frame, (0, LINE2_Y), (width, LINE2_Y), (0,0,255), 2)

        out.write(frame)
        yield frame

    cap.release()
    out.release()

    with open("speed_log.json", "w") as f_json:
        json.dump(speed_log, f_json, indent=2)
