import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote
import re
import ffmpeg
import numpy as np
import cv2

load_dotenv()
VDOINTEL_BASE_URL = os.getenv("VDOINTEL_BASE_URL")
VDOINTEL_USERNAME = os.getenv("VDOINTEL_USERNAME")
VDOINTEL_PASSWORD = os.getenv("VDOINTEL_PASSWORD")

def safe_rtsp_url(url: str) -> str:
    pattern = r'rtsp://([^:]+):(.+?)@([^:/]+)(?::(\d+))?(/.+)'
    match = re.match(pattern, url)
    if not match:
        print("⚠️ Could not parse RTSP URL. Using original.")
        return url

    username, password, host, port, path = match.groups()
    username = quote(username)
    password = quote(password)

    safe_url = f"rtsp://{username}:{password}@{host}"
    if port:
        safe_url += f":{port}"
    safe_url += path
    return safe_url

def get_rtsp_streams():
    try:
        token_resp = requests.post(
            f"{VDOINTEL_BASE_URL}/token",
            data={
                "username": VDOINTEL_USERNAME,
                "password": VDOINTEL_PASSWORD,
                "grant_type": "password"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        if token_resp.status_code != 200:
            print("❌ Failed to get token.")
            return []

        token = token_resp.json().get("access_token")
        if not token:
            print("❌ access_token missing in response.")
            return []

        headers = {"Authorization": f"Bearer {token}"}

        devices_resp = requests.get(
            f"{VDOINTEL_BASE_URL}/devices?status=1&limit=1&lastid=1",
            headers=headers
        )

        if devices_resp.status_code == 200:
            devices = devices_resp.json()
            return [
                (dev["devicename"], safe_rtsp_url(dev["substream"]))
                for dev in devices
                if dev.get("substream")
            ]
        else:
            print("❌ Failed to fetch device list.")
            return []
    except Exception as e:
        print("❌ Exception:", str(e))
        return []

def fetch_rtsp_frame_ffmpeg(rtsp_url: str, width: int = 640, height: int = 480, timeout: int = 5) -> np.ndarray:
    try:
        process = (
            ffmpeg
            .input(rtsp_url, rtsp_transport='tcp', t=timeout)
            .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1, s=f"{width}x{height}")
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        out, err = process.communicate()
        if err:
            print("FFmpeg stderr: ", err.decode(errors='ignore'))
        
        frame = (
            np
            .frombuffer(out, np.uint8)
            .reshape([height, width, 3])
        )
        return frame
    except Exception as e:
        print("❌ FFmpeg frame grab error:", str(e))
        return None