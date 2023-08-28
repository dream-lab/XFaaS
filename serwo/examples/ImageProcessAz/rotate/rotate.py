# Python base imports
from PIL import Image
import io
import base64

# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def rotate(encoded_image):
    try:
        image_data = base64.b64decode(encoded_image.encode('utf-8'))
        # Create a BytesIO object to simulate a file-like object
        image_io = io.BytesIO(image_data)

        # Open the image as a PIL Image object
        image = Image.open(image_io)

        # Rotate the image
        rotated_image = image.rotate(-90, expand=True)

        # Create a new BytesIO object to store the flipped image
        rotated_image_io = io.BytesIO()

        # Save the flipped image as PNG format to the new BytesIO object
        rotated_image.save(rotated_image_io, format='PNG')

        # Get the bytes of the flipped image
        rotated_image_bytes = rotated_image_io.getvalue()

        # Encode the flipped image as base64
        encoded_rotated_image = base64.b64encode(rotated_image_bytes).decode('utf-8')

        return encoded_rotated_image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def savetofile(image_data, filename):
    with open(filename, "wb") as f:
        f.write(image_data)


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        image_data = body["encoded"]
        image_data = rotate(image_data)

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
