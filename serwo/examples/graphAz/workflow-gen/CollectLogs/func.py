from azure.storage.queue import QueueClient
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import os, uuid


connect_str = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=xfaasgloballogger;AccountKey=J+c6RYphlZYQDAd9+EJ7o5kh0YL6KdvUHLhif69N+iQfd52hQPrgty8DMwN5pU7CrAIjfdkiYCVM+AStHItmpg==;BlobEndpoint=https://xfaasgloballogger.blob.core.windows.net/;FileEndpoint=https://xfaasgloballogger.file.core.windows.net/;QueueEndpoint=https://xfaasgloballogger.queue.core.windows.net/;TableEndpoint=https://xfaasgloballogger.table.core.windows.net/'
queue_name = 'sqymx'

queue = QueueClient.from_connection_string(conn_str=connect_str, queue_name=queue_name)


def user_function(serwoObject) -> SerWOObject:
    try:
        fin_dict = dict()
        data = serwoObject.get_body()
        print("Data to push - ", data)
        metadata = serwoObject.get_metadata()
        fin_dict["data"] = "success: OK"
        fin_dict["metadata"] = metadata
        print("Fin dict - ", fin_dict)
        queue.send_message(json.dumps(fin_dict))
        return SerWOObject(body=data)
    except Exception as e:
        return SerWOObject(error=True)
