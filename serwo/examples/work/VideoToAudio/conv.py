from python.src.utils.classes.commons.serwo_objects import SerWOObject
import base64
from io import BytesIO
import logging
import imageio
import tempfile
import os
from moviepy.video.io.VideoFileClip import VideoFileClip

def get_audio_from_base64_video(encoded_video_base64):
    # Convert base64 to bytes
    video_bytes = base64.b64decode(encoded_video_base64)

    # Create a temporary file to save the video bytes
    with tempfile.NamedTemporaryFile(delete=False) as temp_video_file:
        temp_video_file.write(video_bytes)
        temp_video_file_path = temp_video_file.name

    # Create a VideoFileClip object from the temporary video file
    video_clip = VideoFileClip(temp_video_file_path)

    # Check if the video has an audio track
    if video_clip.audio is None:
        raise ValueError("The video does not have an audio track.")

    # Extract the audio from the video clip
    audio_clip = video_clip.audio

    # Write the audio to a temporary file
    temp_audio_file = "/tmp/temp_audio.wav"
    audio_clip.write_audiofile(temp_audio_file)

    # Read the temporary audio file as bytes
    with open(temp_audio_file, "rb") as f:
        audio_bytes = f.read()

    # Encode the audio bytes into base64
    base64_audio = base64.b64encode(audio_bytes).decode("utf-8")

    # Clean up the temporary files
    # audio_clip.close()
    # video_clip.close()
    os.remove(temp_video_file_path)
    os.remove(temp_audio_file)

    return base64_audio

def user_function(xfaas_object) -> SerWOObject:

    body = xfaas_object.get_body()
    video = body["video"]
    audio = get_audio_from_base64_video(video)

    res = {"audio":audio}
    ret = SerWOObject(body=res)
    return ret
