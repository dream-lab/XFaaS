# Python base imports
from PIL import Image
import io
import base64

# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def flip(encoded_image):
    try:
        image_data = base64.b64decode(encoded_image.encode('utf-8'))

        # Create a BytesIO object to simulate a file-like object
        image_io = io.BytesIO(image_data)

        # Open the image as a PIL Image object
        image = Image.open(image_io)

        # Flip the image vertically (top to bottom)
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # Create a new BytesIO object to store the flipped image
        flipped_image_io = io.BytesIO()

        # Save the flipped image as PNG format to the new BytesIO object
        flipped_image.save(flipped_image_io, format='PNG')

        # Get the bytes of the flipped image
        flipped_image_bytes = flipped_image_io.getvalue()

        # Encode the flipped image as base64
        encoded_flipped_image = base64.b64encode(flipped_image_bytes).decode('utf-8')

        return encoded_flipped_image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        image_data = body["encoded"]
        image_data = flip(image_data)

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
