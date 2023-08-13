import os
import json
import shutil
import pathlib
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
from random import randint
import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient


user_input_1 = sys.argv[1]
user_input_2 = sys.argv[2]
json_file_name=user_input_2
# parent_directory = pathlib.Path(__file__).parent.parent.parent.absolute().resolve()
parent_directory = pathlib.Path(__file__).parent.absolute().parent.absolute().parent
print("Parent directory", parent_directory)
user_json_dir = f"{parent_directory}/{user_input_1}"

location = 'centralindia'
queue_name = 'serwo-ingress'

resource_dir=f"{user_json_dir}/build/workflow/resources"
out_file_path = f'{resource_dir}/azure_resources.json'

def get_user_workflow_name():
    json_path = f'{user_json_dir}/{json_file_name}'
    data = json.load(open(json_path))
    user_app_name = data['WorkflowName']
    return user_app_name

def create_resources():
    credential = DefaultAzureCredential()
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_client = ResourceManagementClient(credential, subscription_id)
    print('Creating resources for ingress azure ')
    try:
        rg_result = resource_client.resource_groups.create_or_update(
            "{resource_group_name}", {"location": "{location}"}
        )
    except BrokenPipeError as e:
        pass

    try:
        storage_client = StorageManagementClient(credential, subscription_id)
        poller = storage_client.storage_accounts.begin_create(resource_group_name, storage_account_name,
            {
                "location" : location,
                "kind": "StorageV2",
                "sku": {"name": "Standard_LRS"}
            }
        )
        account_result = poller.result()
        print(f"Provisioned storage account {account_result.name}")
    except BrokenPipeError as e:
        pass

    try:
        queue_service_client = QueueServiceClient(account_url=f"https://{storage_account_name}.queue.core.windows.net", credential=credential)
        queue_service_client.create_queue(queue_name)
    except BrokenPipeError as e:
        pass

    try:
        #TODO Need a native call to get connection string
        stream = os.popen(f'az storage account show-connection-string --name {storage_account_name} --resource-group {resource_group_name}')
        json_str = stream.read()
        stream.close()
    except BrokenPipeError as e:
        pass

    jsson = json.loads(json_str)
    fin_dict = {'queue_name' : queue_name, 'connection_string' : jsson['connectionString'] , 'storage_account' : storage_account_name, 'group':resource_group_name}

    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
    with open(out_file_path, 'w') as f:
        json.dump(fin_dict, f)


def create():
    global resource_group_name, storage_account_name
    if os.path.exists(out_file_path):
        return
    user_app_name = get_user_workflow_name()
    resource_group_name = f'{user_app_name}SerwoTest'
    xd = randint(10000, 99999)
    storage_account_name = f'serwoa{xd}'
    try:
        create_resources()
    except Exception as e:
        print(f'Exception thrown: {e}')


if __name__ == '__main__':

    create()