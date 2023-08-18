from azure.storage.queue import QueueService, QueueMessageFormat
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import os, uuid

connect_str = "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=serwoa65653;AccountKey=jlDlZ9paxWo8SOQ/LpkfAe6bpnh48KobRI+Clp7iMRvXubeE0jRgy+zdZ9HODFc9iWzu26dzxZK2+AStZDBnrg==;BlobEndpoint=https://serwoa65653.blob.core.windows.net/;FileEndpoint=https://serwoa65653.file.core.windows.net/;QueueEndpoint=https://serwoa65653.queue.core.windows.net/;TableEndpoint=https://serwoa65653.table.core.windows.net/"
queue_service = QueueService(connection_string=connect_str)
queue_name = "serwo-ingress"
# Setup Base64 encoding and decoding functions
queue_service.encode_function = QueueMessageFormat.binary_base64encode
queue_service.decode_function = QueueMessageFormat.binary_base64decode


def function(serwoObject) -> SerWOObject:
    try:
        fin_dict = dict()
        data = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        fin_dict["body"] = data
        fin_dict["metadata"] = metadata
        queue_service.put_message(queue_name, json.dumps(fin_dict).encode("utf-8"))
        return SerWOObject(body=data)
    except Exception as e:
        print(e)
        return SerWOObject(error=True)
