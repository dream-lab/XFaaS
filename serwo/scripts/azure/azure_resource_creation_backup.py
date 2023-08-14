import os
import json
import shutil
import pathlib
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
from random import randint
import sys

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
    print('Creating resources for ingress azure ')
    try:
        stream = os.popen(f'az group create --name {resource_group_name} --location {location}')
        stream.close()
    except BrokenPipeError as e:
        pass

    try:
        stream = os.popen(f'az storage account create --resource-group {resource_group_name} --name {storage_account_name} --location {location}')
        stream.close()
    except BrokenPipeError as e:
        pass

    try:
        stream = os.popen(f'az storage queue create -n {queue_name} --account-name {storage_account_name}')
        stream.close()
    except BrokenPipeError as e:
        pass

    try:
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