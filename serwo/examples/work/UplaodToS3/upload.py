import datetime
import os
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from boto3 import client
import base64
import tempfile


secret_key=os.environ['AWS_SECRET_ACCESS_KEY']
access_key=os.environ['AWS_ACCESS_KEY_ID']


s3_client = client(
    service_name='s3',
    region_name='ap-south-1',  
    aws_access_key_id=access_key,  
    aws_secret_access_key=secret_key
)

def handler(event):


    output_bucket = event.get('bucket')
    encoded_zip = event.get('encoded_zip')
    print("OUTPUT_BUCKET:",output_bucket)
    decoded_video=base64.b64decode(encoded_zip)
    temp_video_file = tempfile.NamedTemporaryFile(delete=False,suffix='.zip')
    temp_video_file.write(decoded_video)
    temp_video_file.close()

    filename = temp_video_file.name
    s3_client.upload_file(Bucket=output_bucket, Key=filename, Filename=filename)

    return {
        'bucket': output_bucket,
        'result': "Zip folder uploaded successfully"
    }
    

def user_function(xfaas_object) -> SerWOObject:
    """
    Function that takes an input SerWOObject and returns a SerWOObject.

    Args:
        xfaas_object (SerWOObject): Input SerWOObject containing event data.

    Returns:
        SerWOObject: Output SerWOObject containing the processing result.
    """
    body = xfaas_object.get_body()
    #print("BODY:",body)   
    result = handler(body)
    ret_str={'result_of_upload':result}
    ret=SerWOObject(body=ret_str)
    return ret