import logging

import azure.functions as func
import azure.durable_functions as df
import time
import json
from time import time
func_id = 254
def get_delta(start_time):
    curr_time = int(time() * 1000)
    return (curr_time-start_time)

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    request = req.get_json()
    if 'metadata' not in request:
        job_id = request['workflow_instance_id']
        req_ts = request['request_timestamp']
        meta =  {'workflow_instance_id' : job_id,'functions' : [] ,'request_timestamp' :req_ts}
        request['metadata'] = meta

    metadata = request['metadata']
    body = request['body']
    if 'workflow_start_time' in metadata:
        start_delta = get_delta(metadata['workflow_start_time'])
    else:
        start_delta = get_delta(metadata['request_timestamp'])


    client = df.DurableOrchestrationClient(starter)

    logging.info(f'Request received== {request}')

    if 'workflow_start_time' in metadata:
        end_delta = get_delta(metadata['workflow_start_time'])
    else:
        end_delta = get_delta(metadata['request_timestamp'])

    func_json = {func_id : {'start_delta' : start_delta,'end_delta' : end_delta}}
    metadata['functions'].append(func_json)
    inp = dict(body=body,metadata=metadata)
    instance_id = await client.start_new(req.route_params["functionName"], None, inp)

    logging.info(f"Started orchestration with ID = '{instance_id}'.")

    return client.create_check_status_response(req, instance_id)