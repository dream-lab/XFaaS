import os, uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging

connect_str = 'DefaultEndpointsProtocol=https;AccountName=serwoblob;AccountKey=zlh7mkvbpULFGuNU6mcFpScw4vk87PpD3E3C3IGssHsz4GEGLuOqWjfqDGVz8PBlrCTe4bO+3MKj+ASttmqULA==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_name = 'serwo-multicloud-container'

def function(serwoObject) -> SerWOObject:
    try:
        fin_dict = dict()
        data = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        fin_dict['data'] = data
        str_data = json.dumps(fin_dict)
        local_path = "/tmp/serwo-data"
        if not os.path.exists(local_path):
            os.mkdir(local_path)
        local_file_name = str(uuid.uuid4()) + ".txt"
        upload_file_path = os.path.join(local_path, local_file_name)
        file = open(file=upload_file_path, mode='w')
        file.write(str_data)
        file.close()
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
        with open(file=upload_file_path, mode="rb") as data:
            blob_client.upload_blob(data)

        return SerWOObject(body=data)
    except Exception as e:
        logging.info(f'Excetion in push to blob: {e}')
        return SerWOObject(error=True)
