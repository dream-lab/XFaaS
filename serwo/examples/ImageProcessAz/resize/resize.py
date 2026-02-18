import cv2
import base64
import numpy as np
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def decode(image_json):
    decoded_image = base64.b64decode(image_json.encode('utf-8'))
    jpeg_as_np = np.frombuffer(decoded_image, dtype=np.uint8)
    image = cv2.imdecode(jpeg_as_np, flags=1)
    return image


def resize(img_from_request):
    resized_img = cv2.resize(img_from_request, (224, 224))
    return resized_img


def encode(image):
    retval, buffer = cv2.imencode('.jpg', image)
    encoded_im = base64.b64encode(buffer)
    image = encoded_im.decode('utf-8')
    return image


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        encoded_image = body["encoded"]
        image_data = encode(resize(decode(encoded_image)))

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)