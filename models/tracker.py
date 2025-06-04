from filterpy.kalman import KalmanFilter
import numpy as np

class Track:
    def __init__(self, bbox, track_id):
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.x[:4] = np.reshape(bbox, (4, 1))
        self.track_id = track_id
        self.hits = 0
        self.no_losses = 0
        self.box = bbox
        self.speed = None
    
    def predict(self):
        self.kf.predict()
        self.box = self.kf.x[:4].reshape(-1)
        return self.box

    def update(self, bbox):
        self.kf.update(np.reshape(bbox, (4, 1)))
        self.box = bbox
        self.hits += 1
        self.no_losses = 0

class Tracker:
    def __init__(self):
        self.tracks = []
        self.track_id = 0
    
    def update(self, detections):
        updated_tracks = []

        for det in detections:
            matched = False
            for track in self.tracks:
                iou_score = self.iou(track.box, det)
                if iou_score > 0.3:
                    track.update(det)
                    updated_tracks.append(track)
                    matched = True
                    break
            
            if not matched:
                new_track = Track(det, self.track_id)
                self.track_id += 1
                updated_tracks.append(new_track)
        
        self.tracks = updated_tracks
        return self.tracks
    
    @staticmethod
    def iou(box1, box2):
        x1, y1, x2, y2 = box1
        x1_p, y1_p, x2_p, y2_p = box2

        xi1, yi1 = max(x1, x1_p), max(y1, y1_p)
        xi2, yi2 = min(x2, x2_p), min(y2, y2_p)

        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = (x2 - x1) * (y2 - y1)
        box2_area = (x2_p - x1_p) * (y2_p - y1_p)

        return inter_area / float(box1_area + box2_area - inter_area)