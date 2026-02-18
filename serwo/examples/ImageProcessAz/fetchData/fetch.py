import requests
import base64
import logging

from python.src.utils.classes.commons.serwo_objects import SerWOObject


def download_file(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            return encoded_image
        else:
            logging.info(f"Failed to download image. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.info(f"An error occurred: {e}")
        return None


def user_function(xfaas_object: SerWOObject) -> SerWOObject:
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
