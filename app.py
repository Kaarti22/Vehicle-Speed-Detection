import streamlit as st
import os
import cv2
import json
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from track_video import process_video
from logger_config import setup_logger

logger = setup_logger()

INPUT_DIR = "inputs"
OUTPUT_DIR = "outputs"
TEMP_DIR = "temp"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

st.title("Vehicle Speed Detection with Virtual Line UI")

uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
if uploaded_file:
    input_path = os.path.join(INPUT_DIR, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())
    
    logger.info("Video uploaded successfully.")
    st.success("Video uploaded successfully.")

    cap = cv2.VideoCapture(input_path)
    ret, frame = cap.read()
    cap.release()

    if ret:
        frame_path = os.path.join(TEMP_DIR, "snapshot.jpg")
        cv2.imwrite(frame_path, frame)
        logger.info("Snapshot captured from video.")

        st.subheader("Draw virtual lines")
        img = Image.open(frame_path)
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color="#ff0000",
            background_image=img,
            update_streamlit=True,
            height=img.height,
            width=img.width,
            drawing_mode="line",
            key="canvas",
        )

        line_coords = []
        if canvas_result.json_data is not None:
            for i, obj in enumerate(canvas_result.json_data["objects"]):
                if obj["type"] == "line":
                    x1 = obj["x1"] + obj["left"]
                    y1 = obj["y1"] + obj["top"]
                    x2 = obj["x2"] + obj["left"]
                    y2 = obj["y2"] + obj["top"]

                    logger.info(f"Line {i+1}: From ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})")
                    st.write(f"Line {i+1}: From ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})")
                    line_coords.append(((x1, y1), (x2, y2)))
        
        if len(line_coords) >= 2:
            distance = st.number_input("Enter real-world distance (in meters) between Line 1 and Line 2:", min_value=1.0)
            if st.button("Start Processing"):
                config = {
                    "line1": line_coords[0],
                    "line2": line_coords[1],
                    "real_world_distance_m": distance,
                }

                config_path = os.path.join(TEMP_DIR, "line_config.json")
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

                logger.info("Virtual lines configuration updated.")

                st_frame = st.empty()
                st.info("Processing and streaming video...")

                output_path = os.path.join(OUTPUT_DIR, f"processed_{uploaded_file.name}")

                for frame in process_video(input_path, config_path, output_path):
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st_frame.image(frame_rgb, channels="RGB")
                    time.sleep(0.03)
                
                logger.info("Video processing complete.")
                st.success("Video processing complete")