import os
import sys
import json
import pathlib
import networkx as nx
import uuid
from python.src.utils.classes.commons.serwo_user_dag import SerWOUserDag
from distutils.dir_util import copy_tree
from python.src.utils.classes.commons.serwo_user_dag import SerWOUserDag
from python.src.utils.classes.commons.csp import CSP
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from jinja2 import Environment, FileSystemLoader
from botocore.exceptions import ClientError

import python.src.utils.generators.commons.jmx_generator as JMXGenerator
import datetime
import subprocess


USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]
csp = sys.argv[3]

def push_user_dag_to_provenance(wf_id):
    global dynPartiQLWrapper, e
    # convert this to an api call
    print(":" * 80)
    print(f"Pushing workflow configuration to Dynamo DB")

    workflow_name = ""
    try:
        # print(f"{USER_DIR}/{DAG_DEFINITION_FILE}")
        f = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
        js = open(f,'r').read()
        user_workflow_item = json.loads(js)

        user_workflow_item['wf_id'] = wf_id
        workflow_name = user_workflow_item["WorkflowName"]

        dynPartiQLWrapper = PartiQLWrapper('workflow_user_table')
        dynPartiQLWrapper.put(user_workflow_item)
    except ClientError as e:
        print(e)
    print(":" * 80)
    return workflow_name

def generate_refactored_workflow(left,user_dir,refactored_wf_id,wf_id):
    lpath = f"{user_dir}/{left}"

    js_left = json.loads(open(lpath,'r').read())

    lp = []


    for nd in js_left['Nodes']:
        lp.append(nd['NodeId'])


    js_left['wf_fusion_config'] = ''
    js_left['wf_id'] = wf_id
    js_left['wf_refactored_id'] =refactored_wf_id
    dc = csp

    fin_parts = [{'partition_label':dc,'function_ids':lp}]


    js_left['wf_partitions'] = fin_parts

    js_left['refactoring_strategy'] = 'Single Cloud'

    try:
        #TODO - create table for refactored wf
        dynPartiQLWrapper = PartiQLWrapper('workflow_refactored_table')
        dynPartiQLWrapper.put(js_left)
    except ClientError as e:
        print(e)



def generate_deployment_logs(left,user_dir,wf_id,refactored_wf_id):

    lpath = f"{user_dir}/{left}"

    js_left = json.loads(open(lpath,'r').read())

    lp = []


    for nd in js_left['Nodes']:
        lp.append(nd['NodeId'])
    dc = csp



    d = dict()
    d['wf_id'] = wf_id
    d['wf_refacored_id'] = refactored_wf_id
    d["wf_dc_config"] = {
        'aws' : {"region": "ap-south-1", "csp": "AWS"},
        'azure' : {"region": "Central India", "csp": "Azure"}
    }
    d['wf_deployment_name'] = 'JPDC SMART GRID SINGLE CLOUD'

    workflow_deployment_id = str(uuid.uuid4())
    d['wf_deployment_id'] = workflow_deployment_id
    d['wf_deployment_time'] = str(datetime.datetime.now())

    a=dict()
    for nd in js_left['Nodes']:
        a[nd['NodeId']] = {'dc_config_id' : dc ,"resource_id":'','endpoint':''}


    d['func_deployment_config'] = a

    try:
        dynPartiQLWrapper = PartiQLWrapper('workflow_deployment_table')
        dynPartiQLWrapper.put(d)
        print(d)
    except ClientError as e:
        print(e)
    
    return workflow_deployment_id

def deploy():
    if csp == 'aws':
        subprocess.call(['python3', 'aws_create_statemachine.py',USER_DIR ,f'transformed-{DAG_DEFINITION_FILE}', 'REST'])
    elif csp == 'azure':
        os.chdir('..')
        subprocess.call(['sh', f'./azure_build.sh',USER_DIR ,f'transformed-{DAG_DEFINITION_FILE}'])
        # stream = os.popen(f"./azure_build.sh {USER_DIR} transformed-{DAG_DEFINITION_FILE}")
        # stream.close()


def add_collect_logs_function():
    out_path = 'python/src/utils/CollectLogDirectories'

    node_name = 'CollectLogs'
    collect_dir =  out_path + '/'+node_name



    fnc_src = f'{USER_DIR}/src'

    dest = fnc_src+'/'+node_name

    copy_tree(collect_dir, dest)
    dagg = json.loads(open(f'{USER_DIR}/{DAG_DEFINITION_FILE}','r').read())
    G = SerWOUserDag(f'{USER_DIR}/{DAG_DEFINITION_FILE}').get_dag()
    xd = list(nx.topological_sort(G))
    ind = len(xd)-1
    max_id = int(xd[ind])
    print(max_id)
    collect = dict()

    node_name_max= ''
    for nd in dagg['Nodes']:
        if int(nd['NodeId']) == max_id:
            node_name_max = nd['NodeName']

    edge = {node_name_max :[node_name]}

    collect['NodeId'] = '256'
    collect['NodeName'] = node_name
    collect['Path'] = fnc_src + '/'+node_name
    collect['EntryPoint'] = 'func.py'
    collect['CSP'] = csp
    collect['MemoryInMB'] = 256
    dagg['Nodes'].append(collect)
    dagg['Edges'].append(edge)
    outt = open(f'{USER_DIR}/transformed-{DAG_DEFINITION_FILE}','w')
    outt.write(json.dumps(dagg))
    outt.close()


if __name__ == "__main__":
    wf_id = str(uuid.uuid4())
    wf_name = push_user_dag_to_provenance(wf_id)
    add_collect_logs_function()
    refactored_wf_id  = str(uuid.uuid4())
    generate_refactored_workflow(DAG_DEFINITION_FILE,USER_DIR,refactored_wf_id,wf_id)
    wf_deployment_id = generate_deployment_logs(DAG_DEFINITION_FILE,USER_DIR,refactored_wf_id,wf_id)
    deploy()

    # # generate JMX post deployment
    # try:
    #     JMXGenerator.generate_jmx_files(
    #         workflow_name=wf_name,
    #         workflow_deployment_id=wf_deployment_id,
    #         user_dir=USER_DIR,
    #         template_root_dir="python/src/jmx-templates",
    #         csp=csp
    #     )
    # except Exception as e:
    #     print(e)


    # resources dir
    cwd = os.getcwd()
    user_dir = USER_DIR
    if 'serwo' not in cwd:
        user_dir = f"serwo/{USER_DIR}"
    
    resources_dir=pathlib.Path.joinpath(pathlib.Path(user_dir), "build/workflow/resources")
    provenance_artifacts = {
        "workflow_id": wf_id,
        "refactored_workflow_id": refactored_wf_id,
        "deployment_id": wf_deployment_id
    }

    print("::Provenance Artifacts::")
    print(provenance_artifacts)

    print("::Writing provenance artifacts output to JSON file::")
    json_output = json.dumps(provenance_artifacts, indent=4)
    with open(pathlib.Path.joinpath(resources_dir, "provenance-artifacts.json"), "w+") as out:
        out.write(json_output)


    print("::Adding deployment structure JSON::")
    deployment_structure = {
        "entry_csp": csp
    }    
    deployment_struct_json = json.dumps(deployment_structure, indent=4)
    with open(pathlib.Path.joinpath(resources_dir, "deployment-structure.json"), "w+") as out:
        out.write(deployment_struct_json)