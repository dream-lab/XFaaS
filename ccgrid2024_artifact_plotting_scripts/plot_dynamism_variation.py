import argparse
from collections import defaultdict
import os
import json
import statistics
import numpy as np


from matplotlib import pyplot as plt
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
parser.add_argument("--wf-user-directory", help="Path to the user directory")


def read_log_file(log_file_path):
    with open(log_file_path, "r") as file:
            loglines = [json.loads(line) for line in file.readlines()]
    return loglines

def init_dict(logs):
    distribution_dict = dict(
        client_overheads=[],
        functions=defaultdict(list),
        edges=defaultdict(list),
        wf_invocation_id = []
    )
    nodes = ["1","2","3","4","5"]
    edges = [("1","2"),("1","3"),("1","4"),("2","5"),("3","5"),("4","5")]
    for log in logs:
        wf_invocation_id = log["workflow_invocation_id"]
        distribution_dict["wf_invocation_id"].append(wf_invocation_id)
        distribution_dict["client_overheads"].append((int(log["invocation_start_time_ms"]) - int(log["client_request_time_ms"]))/1000)
        for u in [v for v in nodes]:
            exec_time = (log["functions"][u]["end_delta"] - log["functions"][u]["start_delta"])/1000 # seconds
            distribution_dict["functions"][u].append(exec_time)
        for v1,v2 in [e for e in edges]:
            edge_key = f"{v1}-{v2}"
            comm_time = (log["functions"][v2]["start_delta"] - log["functions"][v1]["end_delta"])/1000 # seconds
            distribution_dict["edges"][edge_key].append(comm_time)
    
    return distribution_dict

def plot_stacked_bar(a,b):
    ##keep a in the bottom and b on top
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    ##show major grid lines
    ax.grid(True)
    xlables = ["AWS Step","AZ Step","AWS Sawtooth","AZ Sawtooth","AWS Alibaba","AZ ALibaba"]
    ax.set_xticks(np.arange(len(a)))
    ax.set_xticklabels(xlables)
    ## add vertical text at the 5th x tick saying NA
    colors_bottom = ['orange','blue','orange','blue','orange','blue']
    colors_top = ['gold','cyan','gold','cyan','gold','cyan']
    ax.bar(np.arange(len(a)), a, 0.35, label='Execution Time',color=colors_bottom)
    ax.bar(np.arange(len(b)), b, 0.35, bottom=a, label='Communication Time',color=colors_top)
    ax.set_ylabel('Time (sec)')
    ax.set_xlabel('Dynamism Variation')
    ax.legend()
    xfaas_dir = os.getenv('XFAAS_DIR')
    plt.savefig(f"{xfaas_dir}/ccgrid2024_artifact_plotting_scripts/dynamism_variation.pdf",bbox_inches='tight')


def get_cumm_time(function_times, edge_times, num_iters):
    source = "1"
    sink = "5"
    paths = [["1","2","5"],["1","3","5"],["1","4","5"]]

    cumm_function_exec = []
    for i in range(num_iters):
        temp = []
        for path in paths:
            tm = 0
            for node in path:
                tm += function_times[node][i]
            temp.append((tm,path))
        a,b = max(temp)
        cumm_function_exec.append(a)
    
    cumm_comm_time = []
    for i in range(num_iters):
        temp = []
        for path in paths:
            tm = 0
            for j in range(0,len(path)-1):
                tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
            temp.append((tm,path))
        a,b = max(temp)
        cumm_comm_time.append(a)

    e2e_time = []
    for i in range(num_iters):
        temp = []
        for path in paths:
            tm = 0
            
            for j in range(0,len(path)-1):
                tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                tm += function_times[path[j]][i]
            tm += function_times[path[-1]][i]
            temp.append((tm,path))
        a,b = max(temp)
        e2e_time.append(a)

    return cumm_function_exec,cumm_comm_time,e2e_time



if __name__ == "__main__":
    wf_user_directory = parser.parse_args().wf_user_directory + '/workflow-gen'

    xfaas_dir = os.getenv('XFAAS_DIR')
    deployments_file_path = f"{xfaas_dir}/deployments.txt"

    deployments = []
    with open(deployments_file_path, 'r') as f:
        deployments = f.readlines()
        deployments = [x.strip() for x in deployments]


    cumm_execs = []
    cumm_comms = []
    i = 0
    for deployment in deployments:
        log_file_dir = f"{wf_user_directory}/{deployment}/exp1/logs/"
        ## list all files in the directory
        files = os.listdir(log_file_dir)
        log_file_path = f"{log_file_dir}/{files[0]}"
        print(log_file_path)
        logs = read_log_file(log_file_path)
        dist_dict = init_dict(logs)
        cumm_function_exec,cumm_comm_time,e2e_time = get_cumm_time(dist_dict["functions"],
                                                                   dist_dict["edges"],
                                                                   num_iters=len(logs))
        cumm_execs.append(statistics.median(cumm_function_exec))
        cumm_comms.append(statistics.median(cumm_comm_time))
        i += 1
        
    print(cumm_execs)
    print(cumm_comms)

    plot_stacked_bar(cumm_execs, cumm_comms)





