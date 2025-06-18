import subprocess
import numpy as np

def read_frames_ffmpeg(rtsp_url, width=704, height=576):
    cmd = [
        'ffmpeg',
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
        '-f', 'image2pipe',
        '-pix_fmt', 'bgr24',
        '-vcodec', 'rawvideo', '-'
    ]

    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)

    while True:
        raw_frame = pipe.stdout.read(width * height * 3)
        if len(raw_frame) != width * height * 3:
            break
        frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3)).copy()
        yield frame

    pipe.stdout.close()
    pipe.terminate()
