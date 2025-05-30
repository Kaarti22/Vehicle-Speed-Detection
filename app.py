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

        st.subheader("Draw ROI Polygon (Region of Interest)")
        img = Image.open(frame_path)
        canvas_result = st_canvas(
            fill_color="rgba(0, 255, 0, 0.3)",
            stroke_width=3,
            stroke_color="#00ff00",
            background_image=img,
            update_streamlit=True,
            height=img.height,
            width=img.width,
            drawing_mode="polygon",
            key="canvas",
        )

        polygon_coords = []

        if canvas_result.json_data is not None:
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "polygon" and "path" in obj:
                    polygon_coords = []
                    for p in obj["path"]:
                        if isinstance(p, list) and len(p) == 2:
                            px, py = p
                            polygon_coords.append((int(px + obj["left"]), int(py + obj["top"])))


        if polygon_coords:
            st.write("Polygon ROI points:")
            for pt in polygon_coords:
                st.write(f"({pt[0]}, {pt[1]})")

            distance = st.number_input("Enter real-world distance (in meters) between two lines:", min_value=1.0)

            if st.button("Start Processing"):
                # Save config
                config = {
                    "polygon_roi": polygon_coords,
                    "real_world_distance_m": distance,
                }

                config_path = os.path.join(TEMP_DIR, "line_config.json")
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

                # Show feedback
                st.success("Configuration saved. Processing video...")

                st_frame = st.empty()
                output_path = os.path.join(OUTPUT_DIR, f"processed_{uploaded_file.name}")

                for frame in process_video(input_path, config_path, output_path):
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st_frame.image(frame_rgb, channels="RGB")
