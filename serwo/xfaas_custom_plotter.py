from xfbench_plotter import XFBenchPlotter
import argparse
import os
from datetime import datetime
import shutil
import time
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")


args = parser.parse_args()
wf_user_directory = args.wf_user_directory +'/workflow-gen'


deployments_filename = 'serwo/custom_deployments.txt'

data = []
with open(deployments_filename,'r') as f:
    for line in f:
        data.append(line.strip().split(','))



def plot_metrics(user_wf_dir, wf_deployment_id, run_id):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot_e2e_timeline(xticks=[], yticks=[],is_overlay=False)
    plotter.plot_stagewise( yticks=[])
    


run_id = 'exp1'

print('==================PLOTTING METRICS===========================')

for d in data:

    wf_deployment_id = d[0]
    csp = d[1]
    region = d[2]
    max_rps = d[3]
    duration = d[4]
    payload_size = d[5]
    dynamism = d[6]
    print(f"Plotting for {wf_deployment_id} {csp} {region} {max_rps} {duration} {payload_size} {dynamism}")

    plot_metrics(wf_user_directory,wf_deployment_id,run_id)
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    exp_conf = f"{csp}-{region}-{max_rps}-{duration}-{payload_size}-{dynamism}-{timestamp}"
    src = f"{wf_user_directory}/{wf_deployment_id}"
    dst = f"{wf_user_directory}/{exp_conf}"
    
    shutil.copytree(src, dst)
    