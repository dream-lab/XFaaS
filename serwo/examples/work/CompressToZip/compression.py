import io
import base64
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import zipfile

def compress_gifs_to_zip(gif1_base64):
    # Decode base64 encoded gifs
    gif1_bytes = base64.b64decode(gif1_base64)

    # Create a zip in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        zipf.writestr('gif1.gif', gif1_bytes)

    # Encode the zip content as base64
    zip_bytes = zip_buffer.getvalue()
    encoded_zip = base64.b64encode(zip_bytes).decode('utf-8')

    return encoded_zip

def user_function(xfaas_object):
    
    body = xfaas_object.get_body()
    gif = body["gif"]
    rt = compress_gifs_to_zip(gif)
    res = {"enc_zip":rt}
    s = SerWOObject(body=res)
    return s
