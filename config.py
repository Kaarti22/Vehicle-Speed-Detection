import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(ROOT_DIR, "inputs")
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")
TEMP_DIR = os.path.join(ROOT_DIR, "temp")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
