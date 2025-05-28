import cv2
import json
from detector import YOLOv11Detector
from tracker import Tracker
from speed_estimator import SpeedEstimator
from logger_config import setup_logger

logger = setup_logger()

line_config_path = "gui/line_config.json"
with open(line_config_path, "r") as f:
    config = json.load(f)

line1_pts = config["line1"]
line2_pts = config["line2"]
real_distance_m = config["real_world_distance_m"]

line1_y = int((line1_pts[0][1] + line1_pts[1][1]) / 2)
line2_y = int((line2_pts[0][1] + line2_pts[1][1]) / 2)
pixel_distance = abs(line2_y - line1_y)

VIDEO_PATH = "sample.mp4"
cap = cv2.VideoCapture(VIDEO_PATH)

fps = cap.get(cv2.CAP_PROP_FPS)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("result.mp4", fourcc, fps, (width, height))

detector = YOLOv11Detector()
tracker  = Tracker()
speed_est = SpeedEstimator(real_distance_m=real_distance_m)

speed_log = []
logged_ids = set()

frame_idx = 0

logger.info("Video processing started.")

while True:
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
            track_id, y_center, timestamp, line1_y, line2_y
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

        if tr.speed is not None and tr.speed >= 5:
            label = f"{tr.speed:.1f} km/h"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, ((x1 + x2) // 2 - 30, (y1 + y2) // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.line(frame, tuple(map(int, line1_pts[0])), tuple(map(int, line1_pts[1])), (255, 0, 0), 2)
    cv2.line(frame, tuple(map(int, line2_pts[0])), tuple(map(int, line2_pts[1])), (0, 0, 255), 2)

    cv2.imshow("Vehicles Speed Detection", frame)
    out.write(frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

with open("speed_log.json", "w") as f_json:
    json.dump(speed_log, f_json, indent=2)