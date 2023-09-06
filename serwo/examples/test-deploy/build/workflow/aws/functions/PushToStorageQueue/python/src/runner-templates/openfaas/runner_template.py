import importlib
import json
import sys
import time
import random
import string
import logging
import os
import psutil
from USER_FUNCTION_PLACEHOLDER import function as USER_FUNCTION_PLACEHOLDER_function
from copy import deepcopy
from python.src.utils.classes.commons.serwo_objects import build_serwo_object
from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def handle(serwoObject):
    start_time = round(time.time()*1000)

    if isinstance(serwoObject, list):
        print('hi')
    elif isinstance(serwoObject, dict):
        print('hey')
        if 'metadata' not in serwoObject:
            new_serwo_object = deepcopy(serwoObject)
        event = dict(body=new_serwo_object)
        wf_instance_id = event.get("workflow_instance_id")
        request_timestamp = event.get("request_timestamp")
        overheads = start_time - request_timestamp
        event['metadata'] = dict(
            workflow_instance_id=wf_instance_id,
            workflow_start_time=start_time,
            request_timestamp=request_timestamp,
            overheads=overheads,
            functions=[]
        )
        serwo_request_object = build_serwo_object(event)
    else:
        pass
    serwo_request_object.set_basepath('')
    status_code = 200
    try:
        print('')
    except Exception as e:
        logging.info("excep= "+str(e))
        return None

    return serwoObject