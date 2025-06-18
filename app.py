import sys
import os
import streamlit as st
import cv2
import numpy as np
import json
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from logger_config import setup_logger
from processing.track_video import process_video
from config import INPUT_DIR, OUTPUT_DIR, TEMP_DIR
from tools.draw_roi import draw_polygon_with_opencv
from tools.rtsp_helper import get_rtsp_streams, safe_rtsp_url, fetch_rtsp_frame_ffmpeg

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

logger = setup_logger()

st.set_page_config(layout="wide")
st.title("🚗 Vehicle Speed Detection with ROI and Virtual Lines")

st.sidebar.title("📡 RTSP Camera Stream")
use_rtsp = st.sidebar.checkbox("Use RTSP stream instead of uploaded video")

input_path = None
video_name = None

if use_rtsp:
    try:
        streams = get_rtsp_streams()
        
        stream_dict = {name: url for name, url in streams if url}
        if stream_dict:
            selected_name = st.sidebar.selectbox("Select Camera Stream", list(stream_dict.keys()))
            selected_rtsp_url = stream_dict.get(selected_name)

            # Encode RTSP URL safely
            input_path = safe_rtsp_url(selected_rtsp_url)
            video_name = selected_name.replace(" ", "_") + ".mp4"

            st.write(f"📽️ Using stream: {selected_name}")
            st.text(f"Input path: {input_path}")
        else:
            st.warning("No RTSP streams available or API failed.")
    except Exception as e:
        logger.error(f"RTSP stream fetch failed: {e}")
        st.warning("Failed to fetch RTSP streams. Check connection or credentials.")
else:
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
    if uploaded_file:
        input_path = os.path.join(INPUT_DIR, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        logger.info(f"Video saved to {input_path}")
        st.success("✅ Video uploaded successfully!")
        video_name = uploaded_file.name

if input_path:
    logger.info(f"Trying to open: {input_path}")
    st.text(f"Trying to open: {input_path}")
    
    frame = None
    if use_rtsp:
        frame = fetch_rtsp_frame_ffmpeg(input_path, width=704, height=576)
    else:
        cap = cv2.VideoCapture(input_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            frame = None

    if frame is None:
        st.error("❌ Failed to open video stream or read frame. Check RTSP URL, credentials, or camera status.")
        logger.error(f"Failed to read frame from input: {input_path}")
    else:
        snapshot_path = os.path.join(TEMP_DIR, "snapshot.jpg")
        cv2.imwrite(snapshot_path, frame)
        img = Image.open(snapshot_path)

        logger.info("Extracted first frame for ROI drawing.")

        st.subheader("Step 1⃣: Draw ROI Polygon Using OpenCV")

        roi_polygon = []
        if st.button("🖼️ Open ROI Drawer"):
            roi_polygon = draw_polygon_with_opencv(snapshot_path)
            if roi_polygon:
                st.session_state["roi_polygon"] = roi_polygon
                logger.info("ROI polygon drawn successfully.")
                st.success("✅ ROI polygon drawn and captured successfully.")
            else:
                logger.warning("ROI drawing was not completed.")
                st.warning("❌ ROI drawing was cancelled or not completed.")

        roi_polygon = st.session_state.get("roi_polygon", [])

        if roi_polygon:
            st.subheader("Step 2⃣: Draw Two Virtual Lines Inside ROI")

            img_cv = np.array(img.convert('RGB'))
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

            pts = np.array(roi_polygon, np.int32).reshape((-1, 1, 2))
            cv2.polylines(img_cv, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

            for point in roi_polygon:
                cv2.circle(img_cv, tuple(point), 5, (0, 0, 255), -1)

            img_with_roi = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            img_with_roi_pil = Image.fromarray(img_with_roi)

            canvas_lines = st_canvas(
                fill_color="rgba(255, 255, 255, 0.3)",
                stroke_width=3,
                stroke_color="#ff0000",
                background_image=img_with_roi_pil,
                update_streamlit=True,
                height=img_with_roi_pil.height,
                width=img_with_roi_pil.width,
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
                logger.info(f"Virtual lines captured: {lines[:2]}")
                st.success("✅ Two virtual lines captured.")

                distance = st.number_input("Step 3⃣: Enter real-world distance between lines (in meters):", min_value=1.0)

                show_live = st.checkbox("Show video live during processing", value=True)

                if st.button("🚀 Start Processing"):
                    config = {
                        "polygon_roi": roi_polygon,
                        "line_1": lines[0],
                        "line_2": lines[1],
                        "real_world_distance_m": distance,
                        "video_name": video_name,
                    }

                    config_path = os.path.join(TEMP_DIR, "config.json")
                    with open(config_path, "w") as f:
                        json.dump(config, f, indent=2)

                    logger.info(f"Processing started for {config['video_name']} with config: {config_path}")
                    st.success("🎥 Configuration saved. Starting processing...")

                    st_frame = st.empty()
                    output_path = os.path.join(OUTPUT_DIR, f"processed_{config['video_name']}")

                    for idx, frame in enumerate(process_video(input_path, config_path, output_path)):
                        if show_live and idx % 5 == 0:
                            logger.debug(f"Displaying frame {idx}")
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            st_frame.image(frame_rgb, channels="RGB")

                    logger.info("Processing completed.")
                    st.success("✅ Processing complete. Check output video and database.")
            else:
                st.warning("⚠️ Please draw at least two virtual lines inside the ROI.")
        else:
            st.warning("⚠️ Please draw ROI polygon first using the button above.")
