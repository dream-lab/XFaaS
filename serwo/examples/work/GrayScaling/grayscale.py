import cv2
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import base64
import logging

def grayscale_base64_video(encoded_video):
    # Decode the input base64 encoded video
    input_data = base64.b64decode(encoded_video)
    
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


def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        m = body["model"]
        v = body["video"]

        v = grayscale_base64_video(v)
        res = {"model":m,
               "video":v}
        s = SerWOObject(body=res)
        return s
    except Exception as e:
        print("Error in selecting video path : ", e)
        return None