import psycopg2
import csv
from dotenv import load_dotenv
import os
from logger_config import setup_logger

logger = setup_logger()

load_dotenv()
NEON_DB_URL = os.getenv("NEON_DB_URL")

def upload_csv_to_db(csv_path):
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()

        with open(csv_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                cursor.execute(
                    """
                        INSERT INTO vehicle_speed_logs (video, track_id, speed_kmph, timestamp, frame) VALUES (%s, %s, %s, %s, %s)
                    """, 
                    (
                        row["video"],
                        int(row["track_id"]),
                        float(row["speed_kmph"]),
                        row["timestamp"],
                        int(row["frame"])
                    )
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Uploaded data from {csv_path} to NeonDB")
    except Exception as e:
        logger.error(f"Error uploading CSV to DB: {e}")