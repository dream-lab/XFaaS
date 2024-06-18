import argparse
import json
import os
import sys
from datetime import datetime

import statistics



def cost_predict(user_wf_dir, wf_deployment_id, run_id, wf_name,region, csp,payload_size,inter_function_time_from_portal):
    
    user_wf_dir = user_wf_dir + "/workflow-gen"
    dag_path = user_wf_dir + '/dag.json'
    memory_map = get_memory_map(dag_path)
    logs_path = f"{user_wf_dir}/{wf_deployment_id}/{run_id}/logs/"
    time_map,num_entries = get_time_map(logs_path)
    if time_map == -1:
        print('No logs found')
        return
    cost_map = {}
    for id in time_map:
        if csp == 'azure' or csp == 'azure_v2':
            cost_map[id] = time_map[id] * memory_map[id] * 0.000016 * 80
        elif csp == 'aws':
            cost_map[id] = time_map[id] * memory_map[id] * 0.00001667 * 80

    single_exec_cost =  sum(cost_map.values()) / num_entries 
    single_inter_cost = inter_function_time_from_portal / num_entries
    # print(sum(time_map.values()),num_entries)
    if csp == 'aws':
        num_edges = get_num_edges(dag_path)
        single_inter_cost = num_edges * 0.0285 / 1000
        single_inter_cost = single_inter_cost * 80
    
    tot_single_cost = single_exec_cost + single_inter_cost
    print(wf_name,csp,payload_size,tot_single_cost)

def get_num_edges(dag_path):
    with open(dag_path, 'r') as f:
        dag = json.load(f)
    num_edges = 0
    ed = dag['Edges']
    for edge in ed:
            for key in edge:
                for val in edge[key]:
                    num_edges += 1
        
    return num_edges

def get_time_map(logs_path):
    time_map = {}
    inter_time_map = {}
    json_logs = []
    for file in os.listdir(logs_path):
        if file.endswith('.jsonl'):
            with open(f"{logs_path}/{file}", 'r') as f:
                logs = f.readlines()
            for log in logs:
                log = json.loads(log)
                json_logs.append(log)
    
    if len(json_logs) == 0:
        return -1,0
    for log in json_logs:
        fns = log['functions']
        for id in fns:
            if int(id) >0 and int(id) <= 100:
                start_delta = fns[id]['start_delta']
                end_delta = fns[id]['end_delta']
                if id not in inter_time_map:
                    inter_time_map[id] = []
                inter_time_map[id].append((end_delta - start_delta)/1000)
    for id in inter_time_map:
        time_map[id] = statistics.median(inter_time_map[id])

    num_nodes = len(time_map)
    time_map[0] = 0.01 * (num_nodes+1) 
    return time_map, len(json_logs)

def get_memory_map(dag_path):
    memory_map = {}
    memory_map[0] = 128 / 1024
    with open(dag_path, 'r') as f:
        dag = json.load(f)
    for node in dag['Nodes']:
        node_id  = node['NodeId']
        memory_map[node_id] = node['MemoryInMB'] / 1024
    return memory_map


if __name__ == '__main__':
    run_id = 'exp1'
    deployments_file = 'serwo/deployments.txt'

    with open(deployments_file, 'r') as f:
        deployments = f.readlines()
    for deployment in deployments:
        deployment = deployment.strip()
        user_wf_dir = deployment.split(',')[0]
        wf_deployment_id = deployment.split(',')[1]
        wf_name = deployment.split(',')[2]
        region = deployment.split(',')[3]
        csp = deployment.split(',')[4]
        payload_size = deployment.split(',')[5]
        inter_function_time_from_portal = float(deployment.split(',')[6])

        cost_predict(user_wf_dir, wf_deployment_id, run_id, wf_name, region, csp, payload_size, inter_function_time_from_portal)
