from tracker import Tracker
import numpy as np

detections_frame1 = [np.array([100, 200, 150, 250]), np.array([300, 400, 350, 450])]
detections_frame2 = [np.array([105, 205, 155, 255]), np.array([305, 405, 355, 455])]

tracker = Tracker()

tracks1 = tracker.update(detections_frame1)
print("Frame 1: ")
for t in tracks1:
    print(f"Track ID: {t.id}, BBox: {t.box}")

tracks2 = tracker.update(detections_frame2)
print("\nFrame 2:")
for t in tracks2:
    print(f"Track ID: {t.id}, BBox: {t.box}")