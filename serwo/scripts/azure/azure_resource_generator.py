import os
import json
import shutil
import pathlib
import subprocess
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
from random import randint
import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient
import string
import random
import time

queue_name = 'serwo-ingress'

def get_user_workflow_name(dag_definition_path):
    if not os.path.exists(dag_definition_path):
        raise FileNotFoundError(f"DAG definition file not found: {dag_definition_path}")
    data = json.load(open(dag_definition_path))
    user_app_name = data['WorkflowName']
    return user_app_name

def create_resources(resource_dir, out_file_path, region,is_netherite):
    credential = DefaultAzureCredential()
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_client = ResourceManagementClient(credential, subscription_id)
    # print('Creating resources for ingress azure ')

    rg_result = resource_client.resource_groups.create_or_update(
        f"{resource_group_name}", {"location": f"{region}"}
    )

    storage_client = StorageManagementClient(credential, subscription_id)
    poller = storage_client.storage_accounts.begin_create(resource_group_name, storage_account_name,
        {
            "location" : region,
            "kind": "StorageV2",
            "sku": {"name": "Standard_LRS"}
        }
    )
    account_result = poller.result()
    # print(f"Provisioned storage account {account_result.name}")

    # Retry logic for queue creation (DNS propagation delay)
    max_retries = 10
    for attempt in range(max_retries):
        try:
            queue_service_client = QueueServiceClient(account_url=f"https://{storage_account_name}.queue.core.windows.net", credential=credential)
            queue_service_client.create_queue(queue_name)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Queue creation failed (attempt {attempt+1}/{max_retries}). Retrying in 10s...")
                time.sleep(10)
            else:
                raise e

    # Retry logic for connection string
    json_str = ""
    for attempt in range(max_retries):
        stream = os.popen(f'az storage account show-connection-string --name {storage_account_name} --resource-group {resource_group_name} --subscription {subscription_id}')
        json_str = stream.read()
        ret_code = stream.close()
        if ret_code is None and json_str.strip(): # Success
            break
        
        print(f"Failed to get connection string (attempt {attempt+1}/{max_retries}). Retrying in 5s...")
        time.sleep(5)
    
    if not json_str.strip():
        raise Exception("Failed to retrieve storage account connection string after multiple attempts.")

    jsson = json.loads(json_str)
    if is_netherite:
        netherite_namespace = randomString(12)
        ## create eventhubs namespace
        
        stream = os.popen(f'az eventhubs namespace create --name {netherite_namespace} --resource-group {resource_group_name} --location {region} --subscription {subscription_id}')
        json_str = stream.read()
        stream.close()

        ## get connection string for eventhubs namespace
        stream = os.popen(f'az eventhubs namespace authorization-rule keys list --name RootManageSharedAccessKey --namespace-name {netherite_namespace} --resource-group {resource_group_name} --subscription {subscription_id}')
        json_str = stream.read()
        stream.close()
        
        event_hubs_connection_string = json.loads(json_str)['primaryConnectionString']
        fin_dict = {'queue_name' : queue_name, 'connection_string' : jsson['connectionString'] , 'storage_account' : storage_account_name, 'group':resource_group_name,'event_hub_namespace':netherite_namespace,'event_hubs_connection_string': event_hubs_connection_string}
    else:
        fin_dict = {'queue_name' : queue_name, 'connection_string' : jsson['connectionString'] , 'storage_account' : storage_account_name, 'group':resource_group_name}

    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
    with open(out_file_path, 'w') as f:
        json.dump(fin_dict, f)


def randomString(stringLength):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def generate(user_dir, dag_definition_path,region,part_id, is_netherite):
    global resource_group_name, storage_account_name

    resource_dir = f"{user_dir}/build/workflow/resources"
    if is_netherite:
        out_file_path = f'{resource_dir}/azure_v2-{region}-{part_id}.json'
    else:
        out_file_path = f'{resource_dir}/azure-{region}-{part_id}.json'

    if os.path.exists(out_file_path):
        return
    user_app_name = get_user_workflow_name(dag_definition_path)
    ##generate 4 length random string
    st = randomString(4)
    resource_group_name = f'{user_app_name}{st}SerwoTest'
    xd = randint(10000, 99999)
    storage_account_name = f'serwoa{xd}'
    create_resources(resource_dir,out_file_path,region,is_netherite)
