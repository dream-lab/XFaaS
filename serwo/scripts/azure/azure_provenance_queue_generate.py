import os
import json
import shutil
from azure.storage.queue import QueueService, QueueMessageFormat

import os, uuid

connect_str = "DefaultEndpointsProtocol=https;AccountName=serwoprovenance;AccountKey=BaGZeTpyeEnO+9yd29yApEjFyzY1b4nR+3bW+mz8sJsSlBs3P29Gg8JzN4I0Lga12oefKWHI4pk3+AStD8AooA==;EndpointSuffix=core.windows.net"

queue_name = "serwo-provenance-queue"

print("Creating queue: " + queue_name)
queue_service = QueueService(connection_string=connect_str)
queue_service.create_queue(queue_name)
