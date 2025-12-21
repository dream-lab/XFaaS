import logging
import requests
import azure.functions as func
import json
from time import time
import azure.durable_functions as df


def get_delta(start_time):
    curr_time = int(time() * 1000)
    return (curr_time-start_time)


func_id = 253

app_name = '{{app_placeholder}}'


async def main(msg: func.QueueMessage,starter: str) -> None:
    logging.info('Python queue trigger function processed a queue item: %s', msg.get_body().decode('utf-8'))
    URL = f'https://{app_name}.azurewebsites.net/api/orchestrators/Orchestrate'
    msg_dict = json.loads(msg.get_body().decode('utf-8'))

    # If the message is a pointer to a large payload, fetch it from Blob
    if msg_dict.get('large_payload') == 1 and "azure" in msg_dict:
        blob_url = msg_dict["azure"]["blob_url"]
        resp = requests.get(blob_url)
        if resp.status_code == 200:
            payload = json.loads(resp.content) 
            body = payload.get("body") 
            metadata = payload.get("metadata")
        else:
            raise Exception(f"Could not retrieve blob from {blob_url} - status code: {resp.status_code}")
        
    else:
        metadata = msg_dict['metadata']
        body = msg_dict['body']

    start_delta = get_delta(metadata['workflow_start_time'])
    end_delta = get_delta(metadata['workflow_start_time'])
    func_json = {func_id : {'start_delta' : start_delta,'end_delta' : end_delta}}
    metadata['functions'].append(func_json)
    inp = dict(body=body,metadata=metadata)

    client = df.DurableOrchestrationClient(starter)
    instance_id = await client.start_new("Orchestrate", None, inp)
    logging.info(f"Started orchestration with ID = '{instance_id}'.")

    # response = requests.post(url = URL,json = inp)
    # logging.info("Received Response In Q Trigger = "+str(response.json()))

