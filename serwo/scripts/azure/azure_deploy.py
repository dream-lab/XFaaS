import os
import json
import shutil
import pathlib
import datetime
from botocore.exceptions import ClientError
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
from time import sleep
import sys
import uuid


def init_paths(user_workflow_dir, region , part_id):
    global resources_path, runtime, functions_version, runtime_version, os_type
    resources_path = f'{user_workflow_dir}/build/workflow/resources/azure-{region}-{part_id}.json'
    runtime = 'python'
    functions_version = 4
    runtime_version = 3.9
    os_type = 'linux'


def get_resources():
    f = open(resources_path, 'r')
    data = json.loads(f.read())
    return data['storage_account'],data['group'],data['app_name'],data['user_dir']


def deploy_to_azure(storage, group, app, user_dir, region):
    # print(f'Creating User app in azure: {app}')
    command = f'az functionapp create --consumption-plan-location {region} --runtime {runtime} --runtime-version {runtime_version} --functions-version {functions_version} --name {app} --os-type {os_type} --storage-account {storage} -g {group}'
    stream = os.popen(command)
    app_create_output = stream.read()
    # print(app_create_output)
    stream.close()
    ##TODO: check if function app exists instead of sleep
    sleep(30)
    os.chdir(user_dir)
    print(':' * 80,f'User app created, deploying {app}')
    stream = os.popen(f'func azure functionapp publish {app}')
    app_deploy_output = stream.read()
    # print(app_deploy_output)
    stream.close()


def deploy(user_dir , region , part_id):
    init_paths(user_dir,region,part_id)
    storage, group, app, user_dir = get_resources()
    deploy_to_azure(storage,group,app,user_dir,region)


if __name__ == '__main__':
    user_dir = sys.argv[1]
    region = sys.argv[2]
    part_id = sys.argv[3]
    deploy(user_dir,region,part_id)


