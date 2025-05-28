import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import json

st.set_page_config(layout="wide")
st.title("Draw Virtual Lines for Speed Detection")

image_path = "../frame_snapshot.jpg"
image = Image.open(image_path)

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=3,
    stroke_color="#ff0000",
    background_image=image,
    update_streamlit=True,
    height=image.height,
    width=image.width,
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
            st.write(f"Line {i+1}: From ({x1:.1f}, {y1:.1f}) to ({x2:.1f}, {y2:.1f})")
            line_coords.append(((x1, y1), (x2, y2)))

if len(line_coords) >= 2:
    distance = st.number_input("Enter real-world distance (in meters) between Line 1 and Line 2:", min_value=1.0)
    if st.button("Save Configuration"):
        config = {
            "line1": line_coords[0],
            "line2": line_coords[1],
            "real_world_distance_m": distance,
        }

        with open("line_config.json", "w") as f:
            json.dump(config, f, indent=2)
        st.success("Configuration saved as line_config.json")