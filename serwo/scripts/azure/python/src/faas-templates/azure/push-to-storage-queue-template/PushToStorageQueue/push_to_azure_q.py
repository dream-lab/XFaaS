from azure.storage.queue import (
    QueueService,
    QueueMessageFormat
)
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import os, uuid

connect_str = '{{connection_string}}'
queue_service = QueueService(connection_string=connect_str)
queue_name = '{{queue_name}}'
# Setup Base64 encoding and decoding functions
queue_service.encode_function = QueueMessageFormat.binary_base64encode
queue_service.decode_function = QueueMessageFormat.binary_base64decode


def function(serwoObject) -> SerWOObject:
    try:
        fin_dict = dict()
        data = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        fin_dict['body'] = data
        fin_dict['metadata'] = metadata
        queue_service.put_message(queue_name, json.dumps(fin_dict).encode('utf-8'))
        return SerWOObject(body=data)
    except Exception as e:
        print(e)
        return SerWOObject(error=True)
