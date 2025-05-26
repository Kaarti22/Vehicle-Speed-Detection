from ultralytics import YOLO

class YOLOv11Detector:
    def __init__(self, model_path="yolo11n.pt"):
        self.model = YOLO(model_path)
    
    def detect(self, image):
        results = self.model.predict(source=image, save=False, conf=0.3, verbose=False)
        detections = []
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                label = result.names[cls]
                if label in ["car", "bus", "truck", "motorbike", "bicycle"]:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detections.append((x1, y1, x2, y2, label))
        return detections