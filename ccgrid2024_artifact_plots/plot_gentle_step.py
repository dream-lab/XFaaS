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
    nodes = ["1"]
    for log in logs:
        wf_invocation_id = log["workflow_invocation_id"]
        distribution_dict["wf_invocation_id"].append(wf_invocation_id)
        distribution_dict["client_overheads"].append((int(log["invocation_start_time_ms"]) - int(log["client_request_time_ms"]))/1000)
        for u in [v for v in nodes]:
            exec_time = (log["functions"][u]["end_delta"] - log["functions"][u]["start_delta"])/1000 # seconds
            distribution_dict["functions"][u].append(exec_time)
        
    
    return distribution_dict


def plot_violin(god_list):
    god_of_gods = []
    for god in god_list:
        ninteeth_percentile = np.percentile(god,90)
        #filter out the 90th percentile
        god1 = [x for x in god if x < ninteeth_percentile]
        god2 = [x for x in god if x >= ninteeth_percentile]
        god_of_gods.append(god1)
        god_of_gods.append(god2)


    fig, ax = plt.subplots()
    fig.set_dpi(400)
    ax.grid(True)
    ax.violinplot(god_of_gods, showmeans=False, showmedians=True)
    xlabels = ["AWS Cold Starts","AWS Warm Starts", "AZ Cold Starts" ,"AZ Warm Starts"]
    ax.set_xticks(np.arange(1,5))
    ax.set_xticklabels(xlabels)

    ax.set_ylabel('Execution Time (sec)')
    xfaas_dir = os.getenv('XFAAS_DIR')
    plt.savefig(f"{xfaas_dir}/ccgrid2024_artifact_plots/gentle_step_violin.pdf",bbox_inches='tight')



if __name__ == "__main__":
    wf_user_directory = parser.parse_args().wf_user_directory + '/workflow-gen'

    xfaas_dir = os.getenv('XFAAS_DIR')
    deployments_file_path = f"{xfaas_dir}/deployments.txt"

    deployments = []
    with open(deployments_file_path, 'r') as f:
        deployments = f.readlines()
        deployments = [x.strip() for x in deployments]


    god_list = []
    i = 0
    for deployment in deployments:
        log_file_dir = f"{wf_user_directory}/{deployment}/exp1/logs/"
        ## list all files in the directory
        files = os.listdir(log_file_dir)
        log_file_path = f"{log_file_dir}/{files[0]}"
        print(log_file_path)
        logs = read_log_file(log_file_path)
        dist_dict = init_dict(logs)
        node_execs = dist_dict['functions']
        lstt = node_execs["1"]
        god_list.append(lstt)

        i += 1
        
    

    plot_violin(god_list)





