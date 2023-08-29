import os
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import base64
import requests

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


def user_function(xfaas_object) -> SerWOObject:
   
    body = xfaas_object.get_body()
    basepath = xfaas_object.get_basepath()
    dep_path = basepath + "dependencies/"

    model_name = body["model_key"]
    video_url = body["video_url"]

    m = get_file_in_base64(dep_path + model_name)
    v = download_and_encode_video(video_url)

    res = {"model":m,
           "video":v}
    ret = SerWOObject(body=res)
    return ret