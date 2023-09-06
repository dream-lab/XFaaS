#!/usr/bin/env python
import contextlib as __stickytape_contextlib

@__stickytape_contextlib.contextmanager
def __stickytape_temporary_dir():
    import tempfile
    import shutil
    dir_path = tempfile.mkdtemp()
    try:
        yield dir_path
    finally:
        shutil.rmtree(dir_path)

with __stickytape_temporary_dir() as __stickytape_working_dir:
    def __stickytape_write_module(path, contents):
        import os, os.path

        def make_package(path):
            parts = path.split("/")
            partial_path = __stickytape_working_dir
            for part in parts:
                partial_path = os.path.join(partial_path, part)
                if not os.path.exists(partial_path):
                    os.mkdir(partial_path)
                    with open(os.path.join(partial_path, "__init__.py"), "wb") as f:
                        f.write(b"\n")

        make_package(os.path.dirname(path))

        full_path = os.path.join(__stickytape_working_dir, path)
        with open(full_path, "wb") as module_file:
            module_file.write(contents)

    import sys as __stickytape_sys
    __stickytape_sys.path.insert(0, __stickytape_working_dir)

    __stickytape_write_module('push_to_azure_q.py', b"from azure.storage.queue import (\n    QueueService,\n    QueueMessageFormat\n)\nimport json\nfrom python.src.utils.classes.commons.serwo_objects import SerWOObject\nimport os, uuid\n\nconnect_str = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=serwoa65653;AccountKey=jlDlZ9paxWo8SOQ/LpkfAe6bpnh48KobRI+Clp7iMRvXubeE0jRgy+zdZ9HODFc9iWzu26dzxZK2+AStZDBnrg==;BlobEndpoint=https://serwoa65653.blob.core.windows.net/;FileEndpoint=https://serwoa65653.file.core.windows.net/;QueueEndpoint=https://serwoa65653.queue.core.windows.net/;TableEndpoint=https://serwoa65653.table.core.windows.net/'\nqueue_service = QueueService(connection_string=connect_str)\nqueue_name = 'serwo-ingress'\n# Setup Base64 encoding and decoding functions\nqueue_service.encode_function = QueueMessageFormat.binary_base64encode\nqueue_service.decode_function = QueueMessageFormat.binary_base64decode\n\n\ndef function(serwoObject) -> SerWOObject:\n    try:\n        fin_dict = dict()\n        data = serwoObject.get_body()\n        metadata = serwoObject.get_metadata()\n        fin_dict['body'] = data\n        fin_dict['metadata'] = metadata\n        queue_service.put_message(queue_name, json.dumps(fin_dict).encode('utf-8'))\n        return SerWOObject(body=data)\n    except Exception as e:\n        print(e)\n        return SerWOObject(error=True)")
    # TODO - !! MOVE THIS OUT TO A DIFFERENT MODULE #
    # SerwoObject - single one
    # SerwoListObject - [SerwoObject] 
    import importlib
    import json
    import sys
    import time
    import random
    import string
    import logging
    import os
    import psutil
    from push_to_azure_q import function as push_to_azure_q_function
    from copy import deepcopy
    from python.src.utils.classes.commons.serwo_objects import build_serwo_object
    from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object
    from python.src.utils.classes.commons.serwo_objects import SerWOObject
    downstream = 0
    '''
    NOTE - creating a serwo wrapper object from cloud events
    * a different wrapper object will be constructed for different event types
    * for one particular event type one object will be constructed
        - we will need to find common keys in the event object for one event type across different FaaS service providers
        - objective is to create a list of common keys, access patterns which will be used to create a common object to pass around
        - 
    '''
    # Get time delta function
    def get_delta(timestamp):
        return round(time.time()*1000) - timestamp
    # AWS Handler
    def lambda_handler(event, context):
        start_time = round(time.time()*1000)
        # Unmarshal from lambda handler
        if isinstance(event, list):
            # TODO: exception handling
            serwo_request_object = build_serwo_list_object(event)
        elif isinstance(event, dict):
            # # NOTE - this is a sample if condition for the pilot jobs
            # if "body" in event:
            #     if "is_warmup" in event["body"]:
            #         print("Warmup code")
            #         return dict(status_code=200, body="Warmed up")
            if 'metadata' not in event:
                new_event = deepcopy(event)
                event = dict(body=new_event)
                wf_instance_id = event["body"].get("workflow_instance_id")
                request_timestamp = event["body"].get("request_timestamp")
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
            # TODO: Report error and return
            pass
        serwo_request_object.set_basepath('')
        # user function exec
        status_code = 200
        try:
            start_epoch_time = serwo_request_object.get_metadata().get('workflow_start_time')
            start_time_delta = get_delta(start_epoch_time)
            wf_instance_id = serwo_request_object.get_metadata().get('workflow_instance_id')
            function_id = '251'
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            print(f'SerWOMemUsage::Before::{wf_instance_id},{function_id},{memory}')
            response_object = push_to_azure_q_function(serwo_request_object)
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            print(f'SerWOMemUsage::After::{wf_instance_id},{function_id},{memory}')
            # Sanity check for user function response
            if not isinstance(response_object, SerWOObject):
                status_code = 500
                return dict(statusCode=status_code,
                            body="Response Object Must be of type SerWOObject",
                            metadata="None")
            end_time_delta = get_delta(start_epoch_time)
            # Get current metadata here
            metadata = serwo_request_object.get_metadata()
            function_metadata_list = metadata.get("functions")
            # NOTE - the template for generated function id
            function_metadata_list.append({function_id: dict(start_delta=start_time_delta, end_delta=end_time_delta)})
            metadata.update(dict(functions=function_metadata_list))
        except Exception as e:
            # if user compute fails then default to status code as 500 and no response body
            print(e)
            status_code = 500
            return dict(statusCode=status_code,
                        body="Error in user compute",
                        metadata="None")
        # post function handler
        # NOTE - leaving empty for now and returning a response is.
        # Send service bus/ storage queue
        body = response_object.get_body()
        response = dict(statusCode=status_code,
                        body=body,
                        metadata=metadata)
        if downstream == 0:
            # TODO - change while doing egress
            return response
        return response
    if __name__ == "__main__":
        print("Main Method")
        # lambda_handler(event, context)