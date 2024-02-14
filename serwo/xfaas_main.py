import xfaas_init as xfaas_init
import xfaas_optimizer as xfaas_optimizer
import xfaas_provenance as xfaas_provenance
import xfaas_resource_generator as xfaas_resource_generator
import xfaas_build as xfaas_build
import xfaas_deploy as xfaas_deploy
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient
import os
import string
import random
import sys
import json
import pathlib
project_dir = pathlib.Path(__file__).parent.resolve()

USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]

DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
BENCHMARK_FILE = sys.argv[3]
benchmark_path = f'{USER_DIR}/{BENCHMARK_FILE}'
csp = sys.argv[4]
region = sys.argv[5]
part_id = "test"
def get_user_pinned_nodes():

    config = json.loads(open(f'{project_dir}/config/xfaas_user_config.json', 'r').read())
    if "user_pinned_nodes" in config:
        return config['user_pinned_nodes']
    else:
        return None

def randomString(stringLength):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def add_collect_logs(dag_definition_path,user_wf_dir, xfaas_user_dag,region):
    if region == 'us-east-1':
        region = 'eastus'
    elif region == 'ap-southeast-1':
        region = 'southeastasia'
    
    region = 'centralindia'
    
    collect_logs_dir = f'{project_dir}/templates/azure/predefined-functions/CollectLogs'
    new_collect_logs_dir = f'{user_wf_dir}/CollectLogs'
   

    print('creating xfaas logging queue')
    resource_group_name = "xfaasGlobalLogger"
    storage_account_name = "xfaasgloballogger"
   
    queue_name = randomString(5)
    
    credential = DefaultAzureCredential()
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_client = ResourceManagementClient(credential, subscription_id)
    try:
        rg_result = resource_client.resource_groups.create_or_update(
            f"{resource_group_name}", {"location": f"{region}"}
        )
    except Exception as e:
        print(e)
    
    try:
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
    except Exception as e:
        print(e)

    try:
        queue_service_client = QueueServiceClient(account_url=f"https://{storage_account_name}.queue.core.windows.net", credential=credential)
        queue_service_client.create_queue(queue_name)
    except Exception as e:
        print(e)

    try:
        #TODO Need a native call to get connection string
        stream = os.popen(f'az storage account show-connection-string --name {storage_account_name} --resource-group {resource_group_name}')
        json_str = stream.read()
        stream.close()
    except Exception as e:
        print(e)

    jsson = json.loads(json_str)
    fin_dict = {'queue_name' : queue_name, 'connection_string' : jsson['connectionString'] , 'storage_account' : storage_account_name, 'group':resource_group_name}
    
    
    ## copy collect_logs_dir to user_wf_dir using shutil copytree

    os.system(f'cp -r {collect_logs_dir} {user_wf_dir}')
    
    connection_string_template = 'CONNECTION_STRING'
    queue_name_template = 'QUEUE_NAME'
    
    ##open the file and replace the connection string and queue name
    with open(f'{new_collect_logs_dir}/func.py', 'r') as file :
        filedata = file.read()
    
    filedata = filedata.replace(connection_string_template, fin_dict['connection_string'])
    filedata = filedata.replace(queue_name_template, fin_dict['queue_name'])

    with open(f'{new_collect_logs_dir}/func.py', 'w') as file:
        file.write(filedata)
    
    node_dict = {
        "NodeId": "253",
        "NodeName": "CollectLogs",
        "Path": new_collect_logs_dir,
        "EntryPoint": "func.py",
        "CSP": "NA",
        "MemoryInMB": 128
    }

    ##open dag definition file and add the node to the dag
    with open(dag_definition_path, 'r') as file :
        filedata = file.read()
    dag = json.loads(filedata)

    dag['Nodes'].append(node_dict)
    
    nx_dag = xfaas_user_dag.get_dag()
    ## find sink node with out degree 0
    sink_node = None
    for node in nx_dag.nodes:
        if nx_dag.out_degree(node) == 0:
            sink_node = node
            break
    
    node_name = node_dict['NodeName']
    sink_node_name = nx_dag.nodes[sink_node]['NodeName']
    dag['Edges'].append({f"{sink_node_name}":[f"{node_name}"]})
    
    
    with open(f'{user_wf_dir}/refactored-dag.json', 'w') as file:
        file.write(json.dumps(dag, indent=4))
    nx_dag.add_node(node_dict['NodeId'], **node_dict)
    nx_dag.add_edge(sink_node,node_dict['NodeId'])

    
    return fin_dict
    
def run(user_wf_dir, dag_definition_file, benchmark_file, csp,region):
    # user_wf_dir += "/workflow-gen"
    dag_definition_path = f"{user_wf_dir}/{dag_definition_file}"
    user_pinned_nodes = get_user_pinned_nodes()
    xfaas_user_dag = xfaas_init.init(dag_definition_path)
    # partition_config = xfaas_optimizer.optimize(xfaas_user_dag,
    #                                             user_pinned_nodes, benchmark_path)

    partition_config = [PartitionPoint("function_name", 2, csp, None, part_id, region)]

    wf_id = xfaas_provenance.push_user_dag(dag_definition_path)
    queue_details = add_collect_logs(dag_definition_path,user_wf_dir,xfaas_user_dag,region)
    dag_definition_path = f'{user_wf_dir}/refactored-{dag_definition_file}'
    refactored_wf_id = xfaas_provenance.push_refactored_workflow("refactored-dag.json", user_wf_dir, wf_id,csp)
    wf_deployment_id = xfaas_provenance.push_deployment_logs("refactored-dag.json",user_wf_dir,wf_id,refactored_wf_id,csp)
    xfaas_resource_generator.generate(user_wf_dir, dag_definition_path, partition_config,"refactored-dag.json")
    xfaas_provenance.generate_provenance_artifacts(user_wf_dir,wf_id,refactored_wf_id,wf_deployment_id,csp,region,part_id,queue_details)

    return wf_id, refactored_wf_id, wf_deployment_id
   

if __name__ == '__main__':

    wf_id, refactored_wf_id, wf_deployment_id = run(f'{USER_DIR}', DAG_DEFINITION_FILE, BENCHMARK_FILE, csp,region)
    
