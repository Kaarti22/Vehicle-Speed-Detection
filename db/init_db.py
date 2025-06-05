import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
NEON_DB_URL = os.getenv("NEON_DB_URL")

def create_table_if_not_exists():
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS vehicle_speed_logs (
                    id SERIAL PRIMARY KEY,
                    video TEXT,
                    track_id INTEGER,
                    speed_kmph FLOAT,
                    timestamp TIMESTAMPTZ,
                    frame INTEGER
                );
            """
        )

        conn.commit()
        cursor.close()
        conn.close()
        print("Table 'vehicle_speed_logs' created or already exists.")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_table_if_not_exists()