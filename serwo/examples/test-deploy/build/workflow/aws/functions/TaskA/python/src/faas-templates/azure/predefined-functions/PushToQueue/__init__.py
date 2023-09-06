from azure.storage.queue import (
    QueueService,
    QueueMessageFormat
)
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import os, uuid

connect_str = {{connection_str_placeholder}}
# connect_str = 'DefaultEndpointsProtocol=https;AccountName=serwoa551;AccountKey=vcVqEC4JNzuOQCJ4TpkGRDHKA0T18HVsvfhDcSH3/GjrXGDYplMVK8z4EeS0nQj2azpomsbUqcoc+AStDZ9tFg==;EndpointSuffix=core.windows.net'
queue_service = QueueService(connection_string=connect_str)
# queue_name = 'test-azure-dump'

queue_name = {{queue_name_placeholder}}

queue_service.encode_function = QueueMessageFormat.binary_base64encode
queue_service.decode_function = QueueMessageFormat.binary_base64decode

def main(serwoObject) -> SerWOObject:
    try:
        serwoObject = json.loads(serwoObject, object_hook=SerWOObject.from_json)
        fin_dict = dict()
        body = json.loads(serwoObject.get_body())
        metadata = json.loads(serwoObject.get_metadata())
        fin_dict['data'] = body
        fin_dict['metadata'] = metadata
        queue_service.put_message(queue_name, json.dumps(fin_dict).encode('utf-8'))

        return SerWOObject(body=json.dumps(body) , metadata=json.dumps(metadata)).to_json()


    except Exception as e:
        return SerWOObject(error=True)
