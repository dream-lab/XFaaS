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
import objsize
# from USER_FUNCTION_PLACEHOLDER import function as USER_FUNCTION_PLACEHOLDER_function - NOTE - !!! TK - STANDARDISE THIS!!! IMPORTANT
from USER_FUNCTION_PLACEHOLDER import user_function as USER_FUNCTION_PLACEHOLDER_function
from copy import deepcopy
from python.src.utils.classes.commons.serwo_objects import build_serwo_object
from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object
from python.src.utils.classes.commons.serwo_objects import SerWOObject

downstream = 0
"""
NOTE - creating a serwo wrapper object from cloud events
* a different wrapper object will be constructed for different event types
* for one particular event type one object will be constructed
    - we will need to find common keys in the event object for one event type across different FaaS service providers
    - objective is to create a list of common keys, access patterns which will be used to create a common object to pass around
    - 
"""


# Get time delta function
def get_delta(timestamp):
    return round(time.time() * 1000) - timestamp


# AWS Handler
def lambda_handler(event, context):
    start_time = round(time.time() * 1000)
    # Unmarshal from lambda handler
    # capturing input payload size
    input_payload_size_bytes = None

    if isinstance(event, list):
        # TODO: exception handling
        serwo_request_object = build_serwo_list_object(event)

        # Calculate input payload size
        input_payload_size_bytes = sum([objsize.get_deep_size(x.get_body()) for x in serwo_request_object.get_objects()])
    
    elif isinstance(event, dict):
        # # NOTE - this is a sample if condition for the pilot jobs
        # if "body" in event:
        #     if "is_warmup" in event["body"]:
        #         print("Warmup code")
        #         return dict(status_code=200, body="Warmed up")
        if "metadata" not in event:
            new_event = deepcopy(event)
            event = dict(body=new_event)
            wf_instance_id = event["body"].get("workflow_instance_id")
            request_timestamp = event["body"].get("request_timestamp")
            session_id = event["body"].get("session_id") # NOTE - new variable to keep track of requests
            deployment_id = event["body"].get("deployment_id")
            overheads = start_time - request_timestamp
            event["metadata"] = dict(
                workflow_instance_id=wf_instance_id,
                workflow_start_time=start_time,
                request_timestamp=request_timestamp,
                session_id=session_id,
                overheads=overheads,
                deployment_id=deployment_id,
                functions=[],
            )
        serwo_request_object = build_serwo_object(event)
        input_payload_size_bytes = objsize.get_deep_size(serwo_request_object.get_body())
    else:
        # TODO: Report error and return
        pass
    serwo_request_object.set_basepath("")
    # user function exec
    status_code = 200
    try:
        start_epoch_time = serwo_request_object.get_metadata().get(
            "workflow_start_time"
        )
        start_time_delta = get_delta(start_epoch_time)
        wf_instance_id = serwo_request_object.get_metadata().get("workflow_instance_id")
        function_id = "{{function_id_placeholder}}"
        process = psutil.Process(os.getpid())
        
        memory_before = process.memory_info().rss
        print(f"SerWOMemUsage::Before::{wf_instance_id},{function_id},{memory_before}")
        response_object = USER_FUNCTION_PLACEHOLDER_function(serwo_request_object)
        process = psutil.Process(os.getpid())
        memory_after = process.memory_info().rss
        print(f"SerWOMemUsage::After::{wf_instance_id},{function_id},{memory_after}")
        
        # Sanity check for user function response
        if not isinstance(response_object, SerWOObject):
            status_code = 500
            return dict(
                statusCode=status_code,
                body="Response Object Must be of type SerWOObject",
                metadata="None",
            )
        end_time_delta = get_delta(start_epoch_time)
        
        # Get current metadata here
        metadata = serwo_request_object.get_metadata()
        function_metadata_list = metadata.get("functions")
        # NOTE - the template for generated function id
        function_metadata_list.append(
            {
                function_id: dict(
                    start_delta=start_time_delta,
                    end_delta=end_time_delta,
                    mem_before=memory_before,
                    mem_after=memory_after,
                    in_payload_bytes=input_payload_size_bytes,
                    out_payload_bytes=objsize.get_deep_size(response_object.get_body())
                )
            }
        )
        metadata.update(dict(functions=function_metadata_list))
    except Exception as e:
        # if user compute fails then default to status code as 500 and no response body
        print(e)
        status_code = 500
        return dict(
            statusCode=status_code, body="Error in user compute", metadata="None"
        )
    # post function handler
    # NOTE - leaving empty for now and returning a response is.
    # Send service bus/ storage queue
    body = response_object.get_body()
    response = dict(statusCode=status_code, body=body, metadata=metadata)
    if downstream == 0:
        # TODO - change while doing egress
        return response
    return response


if __name__ == "__main__":
    print("Main Method")
    # lambda_handler(event, context)
