# Python base imports
from PIL import Image
import io
import base64

# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def rgb_to_grayscale(encoded_image):
    """image_data is the data read from image using read()"""
    image_data = base64.b64decode(encoded_image.encode('utf-8'))
    img = Image.open(io.BytesIO(image_data))
    img_grayscale = img.convert("L")
    img_byte_arr = io.BytesIO()
    img_grayscale.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')
    return encoded_image


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        encoded_image = body["encoded"]
        image_data = rgb_to_grayscale(encoded_image)

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
