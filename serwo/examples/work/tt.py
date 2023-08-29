import os
import base64
import requests
import cv2
import io
import zipfile
from PIL import Image
from moviepy.editor import VideoFileClip, TextClip
import tempfile
import speech_recognition as sr
from textblob import TextBlob
import json
import nltk

def get_file_in_base64(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            return encoded_content
    else:
        return None

def download_and_encode_video(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        video_content = response.content
        encoded_content = base64.b64encode(video_content).decode('utf-8')
        return encoded_content
    else:
        return None

def video_processing_base64(model_base64, video_base64):
    model_bytes = base64.b64decode(model_base64)
    video_bytes = base64.b64decode(video_base64)

    model_path = 'temp_model.xml'  # Temporary model path
    with open(model_path, 'wb') as model_file:
        model_file.write(model_bytes)
    
    with open('/tmp/avid.mp4', 'wb') as video_file:
        video_file.write(video_bytes)

    # video = cv2.VideoCapture(io.BytesIO(video_bytes))
    video = cv2.VideoCapture('/tmp/avid.mp4')

    width = int(video.get(3))
    height = int(video.get(4))

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('aoutput.avi', fourcc, 20.0, (width, height))

    face_cascade = cv2.CascadeClassifier(model_path)

    count = 0
    while video.isOpened():
        ret, frame = video.read()

        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)
            print("Found {0} faces!".format(len(faces)))
            if len(faces) == 1:
                count += 1

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            out.write(frame)
        else:
            break

    video.release()
    out.release()

    result_video_bytes = open('aoutput.avi', 'rb').read()
    result_video_base64 = base64.b64encode(result_video_bytes).decode('utf-8')

    return result_video_base64, count

def convert_to_grayscale_base64(input_base64):
    # Decode the input base64 encoded video
    input_data = base64.b64decode(input_base64)
    
    with open('/tmp/gr_vid.mp4', 'wb') as video_file:
        video_file.write(input_data)
    # Create a VideoCapture object from the decoded data
    cap = cv2.VideoCapture('/tmp/gr_vid.mp4')
        
    # Initialize an empty list to store processed frames
    processed_frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert the frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Encode the grayscale frame to base64
        _, encoded_frame = cv2.imencode(".jpg", gray_frame)
        base64_frame = base64.b64encode(encoded_frame).decode("utf-8")
        
        processed_frames.append(base64_frame)
    
    # Release the VideoCapture object
    cap.release()
    
    # Convert the processed frames list back to a single base64 encoded video
    output_frames = "".join(processed_frames)
    
    return output_frames


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

def compress_gifs_to_zip(gif1_base64, gif2_base64):
    # Decode base64 encoded gifs
    gif1_bytes = base64.b64decode(gif1_base64)
    gif2_bytes = base64.b64decode(gif2_base64)

    # Create a zip in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        zipf.writestr('gif1.gif', gif1_bytes)
        zipf.writestr('gif2.gif', gif2_bytes)

    # Encode the zip content as base64
    zip_bytes = zip_buffer.getvalue()
    encoded_zip = base64.b64encode(zip_bytes).decode('utf-8')

    return encoded_zip

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
    temp_audio_file = "temp_audio.wav"
    audio_clip.write_audiofile(temp_audio_file)

    # Read the temporary audio file as bytes
    with open(temp_audio_file, "rb") as f:
        audio_bytes = f.read()

    # Encode the audio bytes into base64
    base64_audio = base64.b64encode(audio_bytes).decode("utf-8")

    # Clean up the temporary files
    audio_clip.close()
    video_clip.close()
    os.remove(temp_video_file_path)
    os.remove(temp_audio_file)

    return base64_audio

def audio_text(base64_wav_audio):
    finalData = ''
    try:
        r = sr.Recognizer()
        audio_binary = base64.b64decode(base64_wav_audio)
        audio_bytesio = io.BytesIO(audio_binary)
        with sr.AudioFile(audio_bytesio) as source:
            audio_data = r.listen(source)
            finalData = r.recognize_google(audio_data)

    except Exception as e:
        print("Following error was observed:", e)
        print("Exiting the code.")
        exit(0)
    
    return finalData

def text_sentiment(text):
    nltk.download('punkt')

    blob = TextBlob(text)
    res = {
        "polarity": 0,
        "subjectivity": 0
    }

    for sentence in blob.sentences:
        res["subjectivity"] = res["subjectivity"] + sentence.sentiment.subjectivity
        res["polarity"] = res["polarity"] + sentence.sentiment.polarity

    total = len(blob.sentences)

    res["sentence_count"] = total
    res["polarity"] = res["polarity"] / total
    res["subjectivity"] = res["subjectivity"] / total

    return json.dumps(res)  

def overlay_text_on_base64_gif(base64_gif, text, font_size=20, duration=None):
    from PIL import Image, ImageDraw, ImageSequence
    import io

    gif_bytes = base64.b64decode(base64_gif)

    with open('/tmp/vid3.gif', 'wb') as gif_file:
        gif_file.write(gif_bytes)

    im = Image.open('/tmp/vid3.gif')
    frames = []
    for frame in ImageSequence.Iterator(im):
        # Draw the text on the frame
        d = ImageDraw.Draw(frame)
        d.text((10,100), "Sub : ")
        del d
        
        b = io.BytesIO()
        frame.save(b, format="GIF")
        frame = Image.open(b)
        
        frames.append(frame)
    gif_io = io.BytesIO()
    frames[0].save(
        gif_io,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=100,  # Adjust the duration between frames as needed
        loop=0  # Loop indefinitely
    )
    encoded_gif = base64.b64encode(gif_io.getvalue()).decode('utf-8')

    return encoded_gif
    
file_path = "/home/nikhil/work/XFaaS/serwo/examples/work/DownloadFromS3/dependencies/haarcascade_eye.xml"
# video_url = "https://assets.mixkit.co/videos/preview/mixkit-surprised-man-with-hands-on-head-4508-large.mp4"
video_url = "https://i.imgur.com/aHaUuk1.mp4"

# m = get_file_in_base64(file_path)
v = download_and_encode_video(video_url)
# v, c = video_processing_base64(m,v)
l = convert_to_grayscale_base64(v)
# print(l)
g = convert_base64_video_to_gif(v)
# r = compress_gifs_to_zip(g,g)
a = get_audio_from_base64_video(v)
t = audio_text(a)
r = text_sentiment(t)
res = overlay_text_on_base64_gif(g, t, 10)

# print(t)

print(res)