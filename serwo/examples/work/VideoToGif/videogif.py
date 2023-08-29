from python.src.utils.classes.commons.serwo_objects import SerWOObject
import base64
import io
import cv2
from PIL import Image
import logging

def convert_base64_video_to_gif(encoded_video):
    # Decode base64 video to bytes
    video_bytes = base64.b64decode(encoded_video)

    # Create an OpenCV VideoCapture object
    with open('/tmp/vid3.mp4', 'wb') as video_file:
        video_file.write(video_bytes)
    video_capture = cv2.VideoCapture(filename='/tmp/vid3.mp4')

    frames = []
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame_rgb))

    # Convert frames to GIF using PIL
    gif_io = io.BytesIO()
    frames[0].save(
        gif_io,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=100,  # Adjust the duration between frames as needed
        loop=0  # Loop indefinitely
    )

    # Encode GIF bytes to base64
    encoded_gif = base64.b64encode(gif_io.getvalue()).decode('utf-8')

    return encoded_gif


def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        v = body["video"]
        v = convert_base64_video_to_gif(v)
        r = {
            "gif":v
        }
        s = SerWOObject(body=r)
        return s
    except Exception as e:
        print("Error in selecting video path: ", e)
        return None
