import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import cv2
import json
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from logger_config import setup_logger
from processing.track_video import process_video
from config import INPUT_DIR, OUTPUT_DIR, TEMP_DIR
from tools.draw_roi import draw_polygon_with_opencv

logger = setup_logger()

st.set_page_config(layout="wide")
st.title("🚗 Vehicle Speed Detection with ROI and Virtual Lines")

uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
if uploaded_file:
    input_path = os.path.join(INPUT_DIR, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    logger.info("Video uploaded.")
    st.success("✅ Video uploaded successfully!")

    cap = cv2.VideoCapture(input_path)
    ret, frame = cap.read()
    cap.release()

    if ret:
        snapshot_path = os.path.join(TEMP_DIR, "snapshot.jpg")
        cv2.imwrite(snapshot_path, frame)
        img = Image.open(snapshot_path)

        st.subheader("Step 1⃣: Draw ROI Polygon Using OpenCV")

        roi_polygon = []
        if st.button("🖼️ Open ROI Drawer"):
            roi_polygon = draw_polygon_with_opencv(snapshot_path)
            if roi_polygon:
                st.session_state["roi_polygon"] = roi_polygon
                st.success("✅ ROI polygon drawn and captured successfully.")
            else:
                st.warning("❌ ROI drawing was cancelled or not completed.")

        roi_polygon = st.session_state.get("roi_polygon", [])

        if roi_polygon:
            st.subheader("Step 2⃣: Draw Two Virtual Lines Inside ROI")
            canvas_lines = st_canvas(
                fill_color="rgba(255, 255, 255, 0.3)",
                stroke_width=3,
                stroke_color="#ff0000",
                background_image=img,
                update_streamlit=True,
                height=img.height,
                width=img.width,
                drawing_mode="line",
                key="canvas_lines",
            )

            lines = []
            if canvas_lines.json_data:
                for obj in canvas_lines.json_data["objects"]:
                    if obj["type"] == "line":
                        x1 = int(obj["x1"] + obj["left"])
                        y1 = int(obj["y1"] + obj["top"])
                        x2 = int(obj["x2"] + obj["left"])
                        y2 = int(obj["y2"] + obj["top"])
                        lines.append([(x1, y1), (x2, y2)])

            if len(lines) >= 2:
                st.success("✅ Two virtual lines captured.")

                distance = st.number_input("Step 3⃣: Enter real-world distance between lines (in meters):", min_value=1.0)

                show_live = st.checkbox("Show video live during processing", value=True)

                if st.button("🚀 Start Processing"):
                    config = {
                        "polygon_roi": roi_polygon,
                        "line_1": lines[0],
                        "line_2": lines[1],
                        "real_world_distance_m": distance,
                        "video_name": uploaded_file.name,
                    }

                    config_path = os.path.join(TEMP_DIR, "config.json")
                    with open(config_path, "w") as f:
                        json.dump(config, f, indent=2)

                    st.success("🎥 Configuration saved. Starting processing...")

                    st_frame = st.empty()
                    output_path = os.path.join(OUTPUT_DIR, f"processed_{uploaded_file.name}")
                    for idx, frame in enumerate(process_video(input_path, config_path, output_path)):
                        if show_live and idx % 5 == 0:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            st_frame.image(frame_rgb, channels="RGB")

                    st.success("✅ Processing complete. Check output video and database.")
            else:
                st.warning("⚠️ Please draw at least two virtual lines inside the ROI.")
        else:
            st.warning("⚠️ Please draw ROI polygon first using the button above.")
