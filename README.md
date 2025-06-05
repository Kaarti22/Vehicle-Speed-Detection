# 🚗 Vehicle Speed Detection System using YOLOv11 + Streamlit + NeonDB

This project detects moving vehicles in a video, tracks them, and calculates their speed based on how long they take to cross a known real-world distance between two virtual lines. The system uses the **YOLOv11 object detection model**, **Kalman filter tracking**, a custom **speed estimation module**, and a **Streamlit-based UI** with **NeonDB (PostgreSQL)** integration.

---

## 📌 Problem Statement

Given a road surveillance video:

* Detect vehicles.
* Track them as they move.
* Estimate and log their speed when they cross two predefined virtual lines.
* Display the tracked vehicles with speed on video.
* Store speed logs in both CSV and a cloud PostgreSQL (NeonDB) database.

---

## ✅ Key Features

* 🖼️ Web UI to draw ROI polygon and virtual lines.
* ⚡ Real-time vehicle detection using **YOLOv11**.
* 🧠 Tracking using **Kalman Filter** + simple IOU-based matching.
* 📏 Speed estimation using timestamped line crossing.
* 📄 Logs speed data in CSV + NeonDB.
* 📹 Annotated output saved as processed video.
* 🛠️ Logging system integrated.
* ❌ Ignores 2-wheelers and persons.
* ❌ Filters out slow vehicles (< 5 km/h).

---

## 🔄 Streamlit Workflow

1. **Upload Video** → Streamlit UI allows video upload.
2. **Draw ROI Polygon** → First frame shown to draw region of interest (OpenCV UI).
3. **Draw Virtual Lines** → Two lines drawn inside ROI using Streamlit canvas.
4. **Set Real-world Distance** → User enters distance between lines (in meters).
5. **Processing** → Vehicle detection, tracking, speed calculation.
6. **Live Output Display** → Frames shown live while processing (optional).
7. **CSV & DB Logging** → Speed logs written to CSV and pushed to NeonDB.

---

## 🧠 Backend Strategy

### 1. **Detection (YOLOv11)**
- Using `ultralytics` YOLOv11n.
- Only detects `car`, `bus`, `truck` classes.

### 2. **Tracking**
- Kalman filter tracks objects frame-to-frame.
- IOU matching for association.

### 3. **Speed Estimation**
- Time `t1` at line 1, `t2` at line 2.
- Speed = `distance / (t2 - t1)` → converted to km/h.
- Persistent display until object exits frame.

### 4. **NeonDB Integration**
- Logs pushed from CSV to NeonDB PostgreSQL via `psycopg2`.
- `init_db.py` initializes schema:

```sql
CREATE TABLE IF NOT EXISTS vehicle_speed_logs (
    id SERIAL PRIMARY KEY,
    video TEXT,
    track_id INTEGER,
    speed_kmph FLOAT,
    timestamp TIMESTAMPTZ,
    frame INTEGER
);
```

---

## 🗂️ Folder Structure

```
vehicle-speed-detector/
├── app.py                  # Streamlit UI main app
├── config.py               # Configurations of app directories
├── logger_config.py        # Custom logging module
├── db/
│   ├── init_db.py          # Initialize database schema
├── models/
│   ├── detector.py         # YOLOv11 object detection
│   └── speed_estimator.py  # Speed calculation
│   └── tracker.py          # Kalman tracking logic
├── processing/
│   ├── track_video.py      # Video processing pipeline
├── tools/
│   ├── db_uploader.py      # Insert logs to NeonDB (PostgreSQL) database
│   ├── draw_roi.py         # Draw polygon lines
├── .env                    # Contains NeonDB connection string
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 📽️ Sample Output

* Annotated video with bounding boxes, speed, ROI and virtual lines.
* CSV + NeonDB log entry per vehicle.

```csv
video,track_id,speed_kmph,timestamp,frame
sample.mp4,17,39.3,2025-06-05 14:32:10.321,317
```

---

## 🚀 How to Run

1. **Install dependencies**:

```bash
pip install -r requirements.txt
```

2. **Set up `.env` file**:

```env
NEON_DB_URL=postgresql://<user>:<password>@<host>/<dbname>?sslmode=require
```

3. **Run app**:

```bash
streamlit run app.py
```

4. **Optional: Initialize DB Table**:

```bash
python db/init_db.py
```

---

## 🧾 Logging Example

```
[INFO] Detected 3 vehicles.
[INFO] Track ID 17 crossed Line 1 at 52.8s
[INFO] Track ID 17 crossed Line 2 at 53.17s
[INFO] Speed = 39.3 km/h → Logged to CSV and DB.
```

---

## 🙌 Maintainer

**Mondi Venkata Kartikeya**  
SWE Intern @ Precistat IT Solutions

Feel free to fork, contribute, or raise issues for improvements.
