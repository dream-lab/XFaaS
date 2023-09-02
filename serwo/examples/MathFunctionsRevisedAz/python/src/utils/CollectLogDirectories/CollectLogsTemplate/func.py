from azure.storage.queue import QueueService, QueueMessageFormat
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import os, uuid


connect_str = "CONNECTION_STRING_PLACEHOLDER"
queue_name = "QUEUE_NAME_PLACEHOLDER"


queue_service = QueueService(connection_string=connect_str)

queue_service.encode_function = QueueMessageFormat.binary_base64encode
queue_service.decode_function = QueueMessageFormat.binary_base64decode


def function(serwoObject) -> SerWOObject:
    try:
        fin_dict = dict()
        data = serwoObject.get_body()
        print("Data to push - ", data)
        metadata = serwoObject.get_metadata()
        fin_dict["data"] = data
        fin_dict["metadata"] = metadata
        print("Fin dict - ", fin_dict)
        queue_service.put_message(queue_name, json.dumps(fin_dict).encode("utf-8"))
        return SerWOObject(body=data)
    except Exception as e:
        return SerWOObject(error=True)
