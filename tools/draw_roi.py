import cv2
import os
import numpy as np

roi_points = []
drawing_complete = False
CLOSE_THRESHOLD = 10

def is_close_to_start(pt, start_pt):
    return np.linalg.norm(np.array(pt) - np.array(start_pt)) < CLOSE_THRESHOLD

def mouse_callback(event, x, y, flags, param):
    global roi_points, drawing_complete

    if drawing_complete:
        return

    if event == cv2.EVENT_LBUTTONDOWN:
        current_point = (x, y)
        if len(roi_points) >= 3 and is_close_to_start(current_point, roi_points[0]):
            drawing_complete = True
        else:
            roi_points.append(current_point)

def draw_polygon_with_opencv(image_path):
    global roi_points, drawing_complete
    roi_points = []
    drawing_complete = False

    img = cv2.imread(image_path)
    clone = img.copy()
    cv2.namedWindow("Draw ROI - Left-click to draw, click near start to close")
    cv2.setMouseCallback("Draw ROI - Left-click to draw, click near start to close", mouse_callback)

    while True:
        temp_img = clone.copy()
        for pt in roi_points:
            cv2.circle(temp_img, pt, 5, (0, 255, 0), -1)

        if len(roi_points) > 1:
            cv2.polylines(temp_img, [np.array(roi_points)], False, (255, 0, 0), 2)

        if len(roi_points) >= 3 and not drawing_complete:
            cv2.line(temp_img, roi_points[-1], roi_points[0], (100, 100, 255), 1)

        if drawing_complete:
            cv2.polylines(temp_img, [np.array(roi_points)], True, (0, 255, 255), 2)

        cv2.imshow("Draw ROI - Left-click to draw, click near start to close", temp_img)

        key = cv2.waitKey(1) & 0xFF
        if drawing_complete:
            break
        if key == 27:
            roi_points = []
            break

    cv2.destroyAllWindows()
    return roi_points
