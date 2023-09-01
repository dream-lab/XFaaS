import logging
import requests
import azure.functions as func
import json
from time import time
import azure.durable_functions as df

def get_delta(start_time):
    curr_time = int(time() * 1000)
    return (curr_time-start_time)


resources_path = '/home/site/wwwroot/QueueTrigger/azure_resources.json'
func_id = 253
def get_app_name():
    f = open(resources_path,'r')
    data = json.loads(f.read())
    return data['app_name']

app_name = '{{app_placeholder}}'

async def main(msg: func.QueueMessage,starter: str) -> None:
    logging.info('Python queue trigger function processed a queue item: %s', msg.get_body().decode('utf-8'))
    URL = f'https://{app_name}.azurewebsites.net/api/orchestrators/Orchestrate'
    metadata = json.loads(msg.get_body().decode('utf-8'))['metadata']
    body = json.loads(msg.get_body().decode('utf-8'))['body']

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

