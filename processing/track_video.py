import cv2
import json
import os
import numpy as np
import csv
from datetime import datetime
from collections import defaultdict
from models.detector import YOLOv11Detector
from models.speed_estimator import SpeedEstimator
from models.tracker import Tracker

detector = YOLOv11Detector()
tracker = Tracker()

def load_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f)

def is_inside_polygon(point, polygon):
    return cv2.pointPolygonTest(np.array(polygon, np.int32), point, False) >= 0

def line_crossed(center, line):
    """Check if the center has crossed the virtual line (based on y-coordinates)."""
    (x1, y1), (x2, y2) = line
    return y1 <= center[1] <= y2 or y2 <= center[1] <= y1

def process_video(input_path, config_path, output_path):
    print("[INFO] process_video called")
    print(f"[INFO] Input: {input_path}")
    print(f"[INFO] Config: {config_path}")
    print(f"[INFO] Output: {output_path}")

    config = load_config(config_path)
    roi_polygon = config["polygon_roi"]
    line1 = config["line_1"]
    line2 = config["line_2"]
    real_dist = config["real_world_distance_m"]
    video_name = config["video_name"]

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    estimator = SpeedEstimator(real_dist)
    track_log = []

    frame_num = 0
    while cap.isOpened():
        print(f"[FRAME] Processing frame {frame_num}")
        ret, frame = cap.read()
        if not ret:
            break

        detections = detector.detect(frame)
        tracks = tracker.update([det[:4] for det in detections])

        for track in tracks:
            x1, y1, x2, y2 = map(int, track.box)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if not is_inside_polygon((cx, cy), roi_polygon):
                continue

            speed = estimator.update_and_get_speed(
                track.track_id, cy, frame_num / fps, line1[0][1], line2[0][1]
            )

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{track.track_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            if speed:
                track.speed = speed
                cv2.putText(frame, f"{speed} km/h", (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Log result
                track_log.append({
                    "video": video_name,
                    "track_id": track.track_id,
                    "speed_kmph": speed,
                    "timestamp": str(datetime.now()),
                    "frame": frame_num
                })

        # Draw ROI and lines
        cv2.polylines(frame, [np.array(roi_polygon, np.int32)], isClosed=True, color=(255, 0, 0), thickness=2)
        cv2.line(frame, line1[0], line1[1], (0, 255, 255), 2)
        cv2.line(frame, line2[0], line2[1], (0, 255, 255), 2)

        out.write(frame)
        yield frame

        frame_num += 1

    cap.release()
    out.release()

    # Save CSV log
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, f"speeds_{video_name}.csv")
    with open(log_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["video", "track_id", "speed_kmph", "timestamp", "frame"])
        writer.writeheader()
        for row in track_log:
            writer.writerow(row)
    print(f"Processing complete. Output saved to {output_path} and log saved to {log_path}")