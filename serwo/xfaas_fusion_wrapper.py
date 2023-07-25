from serwo_function_fuse import fuse_graph
from python.src.utils.classes.commons.serwo_user_dag import SerWOUserDag
import pathlib
from copy import deepcopy
import xfaas_benchmark_reader as default_benchmark_reader
import xfaas_fusion_code_generator as xfaas_fusion_code_generator
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
import sys
import datetime
import networkx as nx
from distutils.dir_util import copy_tree
import json
import os
import shutil
import uuid

DAG_DEFINITION_FILE = sys.argv[2]
DAG_BENCHMARK_FILENAME = 'dag-benchmark.json'
MULTIPLIER = 100
PARENT_DIRECTORY = pathlib.Path(__file__).parent
USER_DIR = sys.argv[1]
DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
DAG_BENCHMARK_PATH = f'{USER_DIR}/{DAG_BENCHMARK_FILENAME}'
CSP = sys.argv[3]

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


def update_graph_with_benchmark_data(G, CSP):
    bm_dict = default_benchmark_reader.get_user_dag_benchmark_values(DAG_BENCHMARK_PATH)
    for node in G.nodes:
        G.nodes[node]['ExecDur'] = bm_dict['node_benchmarks'][node][CSP]['Latency']
    for edge in G.edges:
        G.edges[edge]['TransferTime'] = bm_dict['edge_benchmarks'][edge][CSP]
    return G

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def add_collect_logs_function(dag_path,G,csp):
    out_path = 'python/src/utils/CollectLogDirectories'

    node_name = 'CollectLogs'
    collect_dir =  out_path + '/'+node_name

    xd = list(nx.topological_sort(G))
    ind = len(xd)-1
    max_id = int(xd[ind])
    fnc_src = f'{USER_DIR}/src'

    dest = fnc_src+'/'+node_name

    copy_tree(collect_dir, dest)
    dagg = json.loads(open(f'{USER_DIR}/{dag_path}','r').read())
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
    outt = open(f'{USER_DIR}/{dag_path}','w')
    outt.write(json.dumps(dagg))
    outt.close()


def generate_refactored_workflow(refactored_wf_id,fused_dir,fused_dag,csp):
    print(refactored_wf_id,fused_dir,fused_dag)
    user_dag_path = f'{USER_DIR}/{DAG_DEFINITION_FILE}'
    dag_json = json.loads(open(user_dag_path,'r').read())
    fused_config = []
    dirs = os.listdir(fused_dir)
    node_id_map = dict()
    for nd in dag_json['Nodes']:
        node_id_map[nd['NodeName']] = nd['NodeId']
    for dir in dirs:
        if 'fused' in dir:
            pyth_path = fused_dir+'/'+dir+'/func.py'
            code = open(pyth_path,'r').readlines()
            fusedd = []
            for line in code:
                if '.function' in line:
                    fusedd.append(line.split()[2].split('.')[0])


            fused_func_id = node_id_map[fusedd[0]]
            original_func_ids = []
            for f in fusedd:
                original_func_ids.append(node_id_map[f])
            dct = dict()
            dct['fused_function_id'] = fused_func_id
            dct['original_function_ids'] = original_func_ids

            fused_config.append(dct)


    print(fused_config)
    print('======')
    dag_json['refactoring_strategy'] = 'Function fusion'
    dag_json['wf_refactored_id'] = refactored_wf_id
    dag_json['wf_partitions'] = []
    partition_label = csp
    function_ids = []
    fused_nodes = json.loads(open(f'{USER_DIR}/{fused_dag}','r').read())['Nodes']
    for fd in fused_nodes:
        function_ids.append(fd['NodeId'])

    obj = dict()
    obj["partition_label"] = partition_label
    obj['function_ids'] = function_ids
    dag_json['wf_partitions'].append(obj)
    # print(dag_json)

    try:
        #TODO - create table for refactored wf
        dynPartiQLWrapper = PartiQLWrapper('workflow_refactored_table')
        dynPartiQLWrapper.put(dag_json)
    except ClientError as e:
        print(e)
        exit()


def generate_deployment_logs(left,user_dir,wf_id,refactored_wf_id,csp):
    workflow_deployment_id = str(uuid.uuid4())

    dc = csp.lower()
    lpath = f"{user_dir}/{left}"
    print(lpath)
    js_left = json.loads(open(lpath,'r').read())

    lp = []


    for nd in js_left['Nodes']:
        lp.append(nd['NodeId'])




    d = dict()
    d['wf_id'] = wf_id
    d['refactored_wf_id'] = refactored_wf_id
    d["wf_dc_config"] = {
        'aws' : {"region": "ap-south-1", "csp": "AWS"},
        'azure' : {"region": "Central India", "csp": "Azure"}
    }
    d['wf_deployment_name'] = 'JPDC SMART GRID Fusion'

    d['wf_deployment_id'] = workflow_deployment_id
    d['wf_deployment_time'] = str(datetime.datetime.now())

    a=dict()
    for nd in js_left['Nodes']:
        a[nd['NodeId']] = {'dc_config_id' : dc ,"resource_id":'','endpoint':''}


    d['func_deployment_config'] = a
    try:
        dynPartiQLWrapper = PartiQLWrapper('workflow_deployment_table')
        dynPartiQLWrapper.put(d)
        print('====')
    except ClientError as e:
        print(e)
        exit()

    return workflow_deployment_id


def run(user_dag_input,user_dir,dag_definition_path,csp):
    global wf_id, wf_name
    wf_id = str(uuid.uuid4())
    # wf_name = push_user_dag_to_provenance(wf_id)
    wf_name = 'test'
    global G, node, god_list
    fin_g = deepcopy(user_dag_input)
    G = deepcopy(fin_g)
    user_og_graph = deepcopy(G)
    print(user_og_graph)
    G1 = deepcopy(G)
    fc, latency, user_graph_latency, cost, user_dag_cost = fuse_graph(G, csp,cost_factor=1.2)

    suffix_str = f'{csp}'
    fused_pth,dag_p,G = xfaas_fusion_code_generator.generate(G1, fc, user_og_graph, suffix_str,user_dir,dag_definition_path)
    add_collect_logs_function(dag_p,G,csp)
    refactored_wf_id  = str(uuid.uuid4())
    # generate_refactored_workflow(refactored_wf_id,fused_pth,dag_p,csp)
    # workflow_deployment_id = generate_deployment_logs(dag_p,user_dir,wf_id,refactored_wf_id,csp)
    workflow_deployment_id = 'test refactor'
    return wf_name, wf_id, refactored_wf_id, workflow_deployment_id,dag_p




if __name__ == "__main__":
    user_dag_input = SerWOUserDag(DAG_DEFINITION_PATH).get_dag()
    wf_name, wf_id, refactored_wf_id, wf_deployment_id,dag_path = run(user_dag_input,USER_DIR,DAG_DEFINITION_PATH,CSP)
