import argparse
import json
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
parser.add_argument("--region",dest='region',type=str,help="Region")
parser.add_argument("--wf",dest='wf',type=str,help="WF ")

args = parser.parse_args()
og = args.wf_user_directory
wf_user_directory = args.wf_user_directory +'/workflow-gen'
wf = args.wf
region = args.region

## list all directories in the wf_user_directory

import os

## a uuid looks like 539357a1-b680-4cfa-b26f-6560fbeadd0a
dirs = os.listdir(wf_user_directory)
run_id = 'exp1'
god_list = []
for dir in dirs:
    ## check if the directory is a uuid
    if len(dir.split('-')) == 5:
        ## read artifact.json from the directory/run_id
        artifacts_file = wf_user_directory+'/'+dir+'/'+run_id+'/artifact.json'
        if not os.path.exists(artifacts_file):
            continue
        with open(artifacts_file,'r') as f:
            artifacts = json.load(f)
        if 'experiment_conf' not in artifacts.keys():
            continue
        exp_conf = artifacts['experiment_conf']
        ## find max rps in the experiment_conf
        max_rps = -1
        tot_duration = 0
        for k in exp_conf.keys():
            tot_duration += int(exp_conf[k]['duration'])
            max_rps = max(max_rps,int(exp_conf[k]['rps']))
        first_key = list(exp_conf.keys())[0]
        csp = artifacts['experiment_conf'][first_key]["csp"]
        rps = max_rps
        duration = tot_duration
        payload_size = artifacts['experiment_conf'][first_key]["payload_size"]
        dynamism = artifacts['experiment_conf'][first_key]["dynamism"]
        god_list.append([dir,csp,region,rps,duration,payload_size,dynamism])
        # print(dir,csp,region,rps,duration,payload_size,dynamism)

        ## write to serwo/custom_deployments.txt

f = open('serwo/custom_deployments.txt','w')      
for dir,csp,region,rps,duration,payload_size,dynamism in god_list:

    f.write(dir+','+csp+','+region+','+str(rps)+','+str(duration)+','+payload_size+','+dynamism+'\n')

f.close()
cmd = f'python3 serwo/azure_function_container_drilldown.py --wf-user-directory {og} --wf {wf_user_directory}'


# os.system(cmd)
