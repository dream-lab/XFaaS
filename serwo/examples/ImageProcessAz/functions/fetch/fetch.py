from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import base64
import requests

def download_file(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            return encoded_image
        else:
            with open ('/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/MgrsE2G.jpg', 'rb') as file:
                img_data = file.read()
            encoded_image = base64.b64encode(img_data).decode('utf-8')
            return encoded_image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def FetchData(xfaas_object: SerWOObject) -> SerWOObject:
    try:
        # body contains the input json data given in postman
        metadata = xfaas_object.get_metadata()
        body = xfaas_object.get_body()
        url = body["url"]

        encoded = download_file(url)
        body["encoded"] = encoded

        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/fetch/inputs/input.json'
req = build_req_from_file(path)
img = FetchData(req)