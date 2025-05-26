import cv2
from detector import YOLOv11Detector

detector = YOLOv11Detector("yolo11n.pt")

image_path = "image.png"
image = cv2.imread(image_path)

detections = detector.detect(image)

for (x1, y1, x2, y2, label) in detections:
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

cv2.imwrite("vehicle_detection_result.png", image)
cv2.imshow("Detected Vehicles", image)
cv2.waitKey(0)
cv2.destroyAllWindows()