import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker

model = YOLO("yolo11n.pt")

cap = cv2.VideoCapture("sample.mp4")
width = int(cap.get(3))
height = int(cap.get(4))
fps = int(cap.get(cv2.CAP_PROP_FPS))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("result.mp4", fourcc, fps, (width, height))

tracker = Tracker()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame, verbose=False)[0]
    detections = []

    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = result
        class_id = int(class_id)
        if class_id in [2, 5, 7]:
            detections.append([int(x1), int(y1), int(x2), int(y2)])
    
    tracks = tracker.update(detections)

    for track in tracks:
        x1, y1, x2, y2 = track.box
        track_id = track.track_id
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    out.write(frame)

    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()