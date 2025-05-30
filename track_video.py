import cv2
import json
import os
from ultralytics import YOLO
from collections import defaultdict
from datetime import datetime
import numpy as np

model = YOLO("yolo11n.pt")

def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

def is_inside_polygon(point, polygon):
    return cv2.pointPolygonTest(np.array(polygon, np.int32), point, False) >= 0

def process_video(input_path, config_path, output_path):
    config = load_config(config_path)
    polygon_pts = config.get("polygon_roi", [])
    distance_m = config.get("real_world_distance_m", 20)

    if not polygon_pts:
        raise ValueError("No polygon ROI defined in config.")

    polygon_np = [(int(x), int(y)) for x, y in polygon_pts]

    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    vehicle_lo = defaultdict(dict)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        detections = results[0].boxes.xyxy.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()

        for i, box in enumerate(detections):
            class_id = int(classes[i])
            conf = confidences[i]

            if class_id not in [2, 5, 7]:
                continue

            x1, y1, x2, y2 = map(int, box)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if not is_inside_polygon((cx, cy), polygon_np):
                continue

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

        cv2.polylines(frame, [np.array(polygon_np, np.int32)], isClosed=True, color=(255, 0, 0), thickness=2)

        out.write(frame)
        yield frame

        frame_count += 1

    cap.release()
    out.release()
