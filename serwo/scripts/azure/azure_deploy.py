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
user_input_1 = sys.argv[1]
user_input_2 = sys.argv[2]

#az functionapp create --consumption-plan-location centralindia --runtime python --runtime-version 3.9 --functions-version 4 --name testdeploymentserwo  --os-type linux --storage-account serwoa553 -g serWO
#func azure functionapp publish testdeploymentserwo

parent_directory = pathlib.Path(__file__).parent.absolute().parent.absolute().parent
user_json_dir=f"{parent_directory}/{user_input_1}"
json_path = f'{user_json_dir}/build/workflow/resources/azure_resources.json'
runtime = 'python'
functions_version = 4
runtime_version = 3.9
os_type = 'linux'
location = 'centralindia'

def get_resources():
    f = open(json_path,'r')
    data = json.loads(f.read())
    return data['storage_account'],data['group'],data['app_name'],data['user_dir']

def deploy(storage,group,app,user_dir):
    print(f'Creating User app: {app}')
    command = f'az functionapp create --consumption-plan-location {location} --runtime {runtime} --runtime-version {runtime_version} --functions-version {functions_version} --name {app} --os-type {os_type} --storage-account {storage} -g {group}'
    stream = os.popen(command)
    stream.close()
    sleep(30)
    os.chdir(user_dir)
    print(f'User app created, deploying {app}')
    stream = os.popen(f'func azure functionapp publish {app}')
    stream.close()


def generate_deployment_logs():

    path = user_json_dir+'/'+user_input_2

    js_left = json.loads(open(path,'r').read())

    lp = []


    for nd in js_left['Nodes']:
        lp.append(nd['NodeId'])


    dc = 'azure'

    d = dict()
    d['wf_id'] = wf_id
    d['refactored_wf_id'] = refactored_wf_id
    d["wf_dc_config"] = {
        'aws' : {"region": "ap-south-1", "csp": "AWS"},
        'azure' : {"region": "Central India", "csp": "Azure"}
    }
    d['wf_deployment_name'] = 'JPDC SMART GRID Azure only'

    d['wf_deployment_id'] = str(uuid.uuid4())
    d['wf_deployment_time'] = str(datetime.datetime.now())

    a=dict()
    for nd in js_left['Nodes']:
        a[nd['NodeId']] = {'dc_config_id' : dc ,"resource_id":'','endpoint':''}

    d['func_deployment_config'] = a

    try:
        dynPartiQLWrapper = PartiQLWrapper('workflow_deployment_table')
        dynPartiQLWrapper.put(d)
    except ClientError as e:
        print(e)


if __name__ == '__main__':
    storage, group, app, user_dir = get_resources()
    # generate_deployment_logs()
    deploy(storage,group,app,user_dir)


