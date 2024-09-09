import argparse
import json
import os
import sys
from datetime import datetime
import math
import statistics
import matplotlib.pyplot as plt
import numpy as np

actual_func_exec = []
predicted_func_exec =  []

actual_inter_func = []
predicted_inter_func =  []

def get_az_cost(csp,payload_size,num_nodes,in_bytes,out_bytes,num_edges):
    if csp == 'azure':
        orch_cost = ((in_bytes+out_bytes)/(1024**3))*4.1256 + (num_nodes*2*5.8342)/10000 + (num_edges+1)*0.5835/10000
        if payload_size == 'small':
            cst = (num_nodes*2*0.0301)/10000 + orch_cost
        else:
            cst = (out_bytes/(1024**3))*1.6670 + (num_nodes*6.0009)/10000 + (num_nodes*0.5001)/10000 + orch_cost
        return cst
    elif csp == 'azure_v2':
        cst = (out_bytes+in_bytes)/((1024**2)*3600)*1.251 + (num_edges)/1000000*2.334
        tot_ops = math.ceil((out_bytes+in_bytes)/(64*1024))
        orch = (4*tot_ops*0.03001)/10000
        cst += orch
        return cst
    return 0

def plot():
    ## calculate msq error for func exec and inter func 
    func_exec_mse = 0
    inter_func_mse = 0
    for i in range(len(actual_func_exec)):
        func_exec_mse += (actual_func_exec[i] - predicted_func_exec[i])**2
        inter_func_mse += (actual_inter_func[i] - predicted_inter_func[i])**2
    func_exec_mse = func_exec_mse / len(actual_func_exec)
    inter_func_mse = inter_func_mse / len(actual_inter_func)
    print('func exec mse',func_exec_mse)
    print('inter func mse',inter_func_mse)

    func_exec_r2 = 0
    inter_func_r2 = 0
    actual_func_exec_mean = statistics.mean(actual_func_exec)
    actual_inter_func_mean = statistics.mean(actual_inter_func)
    for i in range(len(actual_func_exec)):
        func_exec_r2 += (actual_func_exec[i] - predicted_func_exec[i])**2
        inter_func_r2 += (actual_inter_func[i] - predicted_inter_func[i])**2
    func_exec_r2 = 1 - (func_exec_r2 / sum([(x - actual_func_exec_mean)**2 for x in actual_func_exec]))
    inter_func_r2 = 1 - (inter_func_r2 / sum([(x - actual_inter_func_mean)**2 for x in actual_inter_func]))
    print('func exec r2',func_exec_r2)
    print('inter func r2',inter_func_r2)

    print(len(actual_func_exec),len(predicted_func_exec),len(actual_inter_func),len(predicted_inter_func))
    ## plot a stacked bar graph with func exec in bottom and inter func on top, alternate bars for actual and predicted
    fig, ax = plt.subplots()
    fig.set_size_inches(2, 7)
    barWidth = 0.2
    r1 = np.arange(len(actual_func_exec))
    ax.minorticks_on()
    ax.grid(which='major', linestyle='-', linewidth='0.1', color='lightgrey')
    ax.grid(which='minor', linestyle='-', linewidth='0.1', color='lightgrey')
    
    r1 = [0,0.4,0.8,1.4,1.8,2.2,2.8,3.2,3.6]
    r1 = [x - 0.2 for x in r1]
    r2 = [x + barWidth for x in r1]
    labels = ['AWS S','AzS S','AzN S', 'AWS M','AzS M','AzN M', 'AWS L','AzS L','AzN L']
    ##add three lables for 3 groups of bars below x axis
    lab = ['Small','Medium','Large']
    


    
    xticks = [x + barWidth/2 for x in r1]
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels,fontsize=14,rotation=90)
    yticks = [0.000001,0.00001,0.0001,0.001,0.01,0.1,1]
    ax.set_yticks(yticks,minor=True,fontsize=16)

    ## if value is 0 then write NA  
    print(actual_func_exec)
    inds = [i for i, x in enumerate(actual_func_exec) if x == 0]
    for ind in inds:
        ax.text(r1[ind], 0.00001, 'NA', ha='center', va='bottom',rotation=90,c='red')
        ax.text(r2[ind], 0.00001, 'NA', ha='center', va='bottom', rotation=90,c='red')

    colors_func_exec = ['orange','blue','green','orange','blue','green','orange','blue','green']
    colors_inter_func = ['gold','cyan','green','gold','cyan','green','gold','cyan','green']
    ax.set_yscale('log')
    ax.bar(r1, actual_func_exec, width=barWidth, edgecolor='grey', label='Actual Func Exec',color = colors_func_exec)
    ax.bar(r2, predicted_func_exec, width=barWidth, edgecolor='grey', label='Predicted Func Exec',color = colors_func_exec, hatch='//')

    ax.bar(r1, actual_inter_func, width=barWidth, edgecolor='grey', label='Actual Inter Func', bottom=actual_func_exec,color = colors_inter_func)
    ax.bar(r2, predicted_inter_func, width=barWidth, edgecolor='grey', label='Predicted Inter Func', bottom=predicted_func_exec,color = colors_inter_func, hatch='\\')
    
    plt.legend(fontsize=11)
    # ax2 = ax.twinx()
    # ax2.set_xticks([0.4,2.4,3.4])
    # ax2.set_xticklabels(lab)
    fd = {'fontsize': 20}
    plt.xlabel('CSP / Payload Size',fontdict=fd)
    plt.ylabel('Cost(INR)',fontdict=fd)
    ##xtick labels fontsize

    plt.show()
    # plt.savefig('cost_analysis_graph.pdf', bbox_inches='tight' ,dpi=300)
def cost_predict(user_wf_dir, wf_deployment_id, run_id, wf_name,region, csp,payload_size,inter_function_time_from_portal):
    
    user_wf_dir = user_wf_dir + "/workflow-gen"
    directories = os.listdir(user_wf_dir)
    in_bytes =  0
    out_bytes = 0
    
    for directory in directories:
        ## if directory is a file and not a directory
        if not os.path.isdir(user_wf_dir + '/' + directory):
            continue
        d_dires = os.listdir(user_wf_dir + '/' + directory)
        if 'samples' in d_dires:
            in_path = user_wf_dir + '/' + directory + '/samples/' +payload_size + '/input/'
            out_path = user_wf_dir + '/' + directory + '/samples/' +payload_size + '/output/'
            if not os.path.exists(in_path) or not os.path.exists(out_path):
                continue
            in_size_in_bytes = 0
            out_size_in_bytes = 0
            for files in os.listdir(in_path):
                in_size_in_bytes = os.path.getsize(in_path + files)
            for files in os.listdir(out_path):   
                out_size_in_bytes = os.path.getsize(out_path + files)
            in_bytes += in_size_in_bytes
            out_bytes += out_size_in_bytes

    dag_path = user_wf_dir + '/dag.json'
    memory_map = get_memory_map(dag_path)
    logs_path = f"{user_wf_dir}/{wf_deployment_id}/{run_id}/logs/"
    print(logs_path)
    if not os.path.exists(logs_path):
        print('logs not found')
        actual_func_exec.append(0)
        actual_inter_func.append(0)
        predicted_func_exec.append(0)
        predicted_inter_func.append(0)
        return
    time_map,num_entries = get_time_map(logs_path)

    if time_map == -1:
       
        actual_func_exec.append(0)
        actual_inter_func.append(0)
        predicted_func_exec.append(0)
        predicted_inter_func.append(0)
        return
    cost_map = {}
    for id in time_map:
        if csp == 'azure' or csp == 'azure_v2':
            cost_map[id] = time_map[id] * memory_map[id] * 0.000016 * 80
        elif csp == 'aws':
            cost_map[id] = time_map[id] * memory_map[id] * 0.00001667 * 80

    single_exec_cost =  sum(cost_map.values()) / num_entries 
    single_inter_cost = inter_function_time_from_portal / num_entries
    num_edges = get_num_edges(dag_path)
    if csp == 'aws':
        
        single_inter_cost = num_edges * 0.0285 / 1000
        single_inter_cost = single_inter_cost * 80

  
    tot_single_cost = single_exec_cost + single_inter_cost
       
    
    
    # print('actual',wf_name,csp,payload_size,'exec--',single_exec_cost, 'inter--', single_inter_cost)
    if csp == 'aws':
        actual_func_exec.append(single_exec_cost)
        actual_inter_func.append(single_inter_cost)
        predicted_func_exec.append(single_exec_cost)
        predicted_inter_func.append(single_inter_cost)
        # print('predicted',wf_name,csp,payload_size,'exec--',single_exec_cost, 'inter--', single_inter_cost)
    else:
        az_single_inter_cost =  get_az_cost(csp,payload_size,len(time_map),in_bytes,out_bytes,num_edges)
        az_tot_single_cost = single_exec_cost + az_single_inter_cost
        actual_func_exec.append(single_exec_cost)
        actual_inter_func.append(single_inter_cost)
        predicted_func_exec.append(single_exec_cost)
        predicted_inter_func.append(az_single_inter_cost)

        # print('predicted',wf_name,csp,payload_size,'exec--',single_exec_cost, 'inter--', az_single_inter_cost)
        

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
    in_bytes = 0
    out_bytes = 0
    ff = 0
    for log in json_logs:
        fns = log['functions']
        for id in fns:
            if int(id) >0 and int(id) <= 100:
                start_delta = fns[id]['start_delta']
                end_delta = fns[id]['end_delta']
                if ff == 0:
                    in_bytes += fns[id]['in_payload_bytes']
                    out_bytes += fns[id]['out_payload_bytes']
                if id not in inter_time_map:
                    inter_time_map[id] = []
                inter_time_map[id].append((end_delta - start_delta)/1000)
        ff = 1
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
    plot()