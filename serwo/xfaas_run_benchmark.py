import json
import argparse
import subprocess
import pathlib
import os
import shutil
import sys
import time
from datetime import datetime
from xfaas_main import run as xfaas_deployer
import time
from xfbench_plotter import XFBenchPlotter
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
parser.add_argument("--csp",dest='csp',type=str,help="CSP name")
parser.add_argument("--region",dest='region',type=str,help="Region name")
parser.add_argument("--max-rps",dest='max_rps',type=int,help="Max RPS")
parser.add_argument("--duration",dest='duration',type=int,help="Duration(sec)")
parser.add_argument("--payload-size",dest='payload_size',type=str,help="Payload size: Values: Small/Medium/Large")
parser.add_argument("--dynamism",dest='dynamism',type=str,help="Dynamism: Values: staic/alibaba/step_function")
parser.add_argument("--wf-name",dest='wf_name',type=str,help="Workflow name")
parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
parser.add_argument("--path-to-client-config",dest='client_config_path',type=str,help="Path to client config file")
parser.add_argument("--client-key",dest='client_key',type=str,help="Key of client to pick from client config file")
parser.add_argument("--dag-file-name",dest='dag_filename',type=str,help="DAG FILE NAME")
parser.add_argument("--teardown-flag",dest='teardown_flag',type=str,help="Tear down application by default true")
parser.add_argument("--is_singleton_wf",dest='is_singleton_wf',type=str,help="Is singleton workflow",default=0)
parser.add_argument("--function-class",dest='function_class',type=str,help="Function class")
parser.add_argument("--function-name",dest='function_name',type=str,help="Function name")
parser.add_argument("--function-code",dest='function_code',type=str,help="Function code")
parser.add_argument("--node_name",dest='node_name',type=str,help="Node name")

artifact_suffix = 'artifact.json'
args = parser.parse_args()
provenance_artifact_filename = None
deployment_id = ''
server_ip = None
server_user_id  = None
server_pem_file_path = None
def get_client_login_details(config_path):
    global server_ip, server_user_id, server_pem_file_path
    with open(config_path) as f:
        data = json.load(f)
    data = data[args.client_key]
    server_ip = data['server_ip']
    server_user_id = data['server_user_id']
    if 'server_pem_file_path' in data:
        server_pem_file_path = data['server_pem_file_path']

shell_script_commands = []
aws_shell_script_commands = []


def get_aws_payload(payload):
    payload = json.dumps(payload)
    payload = payload.replace('"', '\&quot;')
    payload = payload[1:-1]
    return payload

def get_azure_payload(payload):
    payload = json.dumps(payload)
    payload = payload.replace('"', '&quot;')
    return payload



def read_dynamism_file(dynamism,duration, max_rps):
    file_path = os.getenv("XFBENCH_DIR") + f"/workloads/{dynamism}-{max_rps}-{duration}.csv"
    with open(file_path) as f:  
        data = f.readlines()
    data = [x.strip() for x in data]
    final_data = []
    for d in data:
        vals = [float(x) for x in d.split(",") if x != "" ] # '''and 'KB' not in x'''
        # size = d.split(",")[-1]
        
        final_data.append((vals[0],vals[1]))
    return final_data


def get_azure_resources(csp,region,part_id,wf_user_directory):
    resources = read_resources(csp, region, part_id, wf_user_directory)
    app_name = resources['app_name']
    url = f"https://{app_name}.azurewebsites.net/api/orchestrators/Orchestrate"
    return url


def read_resources(csp, region, part_id, wf_user_directory):
    resources_file_path = f'{wf_user_directory}/build/workflow/resources/{csp}-{region}-{part_id}.json'
    with open(resources_file_path) as f:
        resources = json.load(f)
    return resources


def get_aws_resources(csp,region,part_id,wf_user_directory):
    resources = read_resources(csp, region, part_id, wf_user_directory)
    for r in resources:
        if r['OutputKey'] == 'ExecuteApi':
            execute_url = r['OutputValue']
        elif r['Description'] == 'Serwo CLI State machine ARN':
            state_machine_arn = r['OutputValue']
        
    return execute_url, state_machine_arn


def template_azure_jmx_file(rps, duration, execute_url, payload_size, input_jmx, output_path, session_id,payload):
    rps_keyword = "RPS"
    execute_url_keyword = "URL"
    duration_keyword = "DURATION"
    payload_size_keyword = "PAYLOAD"
    session_id_keyword = "SESSION"
    deployment_id_keyword = "DEPLOYMENT_ID"
    azure_payload_keyword = "AZURE_PAYLOAD_TO_REPLACE"

    with open(input_jmx) as f:
        data = f.read()
    data = data.replace(rps_keyword, str(rps))
    data = data.replace(execute_url_keyword, execute_url)
    data = data.replace(duration_keyword, str(int(duration)))
    # data = data.replace(payload_size_keyword, payload_size)
    data = data.replace(session_id_keyword, str(session_id))
    data = data.replace(deployment_id_keyword, deployment_id)
    data = data.replace(azure_payload_keyword, get_azure_payload(payload))
    to_replace = '"ThreadGroup.num_threads">2'
    if rps == 1020.0 or rps == 840.0: 
        data = data.replace(to_replace, f'"ThreadGroup.num_threads">17')
    elif rps == 1920.0 or rps == 3840.0 or rps == 7680.0:
        data = data.replace(to_replace, f'"ThreadGroup.num_threads">64')
    
    with open(output_path, "w") as f:
        f.write(data)


def template_aws_jmx_file(rps, duration, execute_url, state_machine_arn, payload_size, input_jmx, output_path, session_id,payload):
    global deployment_id
    rps_keyword = "RPS"
    execute_url_keyword = "URL"
    duration_keyword = "DURATION"
    payload_size_keyword = "PAYLOAD"
    state_machine_arn_keyword = "STATE_MACHINE_ARN"
    session_id_keyword = "SESSION"
    deployment_id_keyword = "DEPLOYMENT_ID"
    aws_payload_keyword = "AWS_PAYLOAD_TO_REPLACE"


    with open(input_jmx) as f:
        data = f.read() 
    data = data.replace(rps_keyword, str(rps))
    data = data.replace(execute_url_keyword, f'{execute_url}/execute')
    data = data.replace(duration_keyword, str(int(duration)))
    # data = data.replace(payload_size_keyword, payload_size)
    data = data.replace(state_machine_arn_keyword, state_machine_arn)
    data = data.replace(session_id_keyword, str(session_id))
    data = data.replace(deployment_id_keyword, deployment_id)
    data = data.replace(aws_payload_keyword, get_aws_payload(payload))
    to_replace = '"ThreadGroup.num_threads">2'
    if rps == 1020.0 or rps == 840.0: 
        data = data.replace(to_replace, f'"ThreadGroup.num_threads">17')
    elif rps == 1920.0 or rps == 3840.0 or rps == 7680.0:
        data = data.replace(to_replace, f'"ThreadGroup.num_threads">64')

    with open(output_path, "w") as f:
        f.write(data)


def make_jmx_file(csp, rps, duration, payload_size, wf_name, execute_url,state_machine_arn, dynamism, session_id, wf_user_directory, part_id, region, wf_deployment_id,run_id, payload,is_localhost):
    jmx_template_path, jmx_output_path,jmx_output_filename = get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism,session_id,region)
    if 'azure' in csp:
       template_azure_jmx_file(rps, duration, execute_url, payload_size, jmx_template_path, jmx_output_path, session_id,payload)
    else:
        template_aws_jmx_file(rps, duration, execute_url, state_machine_arn, payload_size, jmx_template_path, jmx_output_path, session_id,payload)
    send_jmx_file_to_server(jmx_output_path,jmx_output_filename,rps,duration,is_localhost)
    dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region, wf_deployment_id,run_id)



def dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region,wf_deployment_id,run_id):
   
    provenance_artefacts_updated_path = f"{wf_user_directory}/{wf_deployment_id}/{run_id}/{artifact_suffix}"
    with open(provenance_artefacts_updated_path) as f:
        provenance_artefacts = json.load(f)
    experiment_conf =  {
            "jmx_output_filename": jmx_output_filename,
            "csp": csp,
            "rps": int(rps/60),
            "duration": duration,
            "payload_size": payload_size,
            "wf_name": wf_name,
            "dynamism": dynamism
    }
    
    if "experiment_conf" in provenance_artefacts:
        provenance_artefacts['experiment_conf'][session_id] = experiment_conf
    else:
        provenance_artefacts['experiment_conf'] = {}
        provenance_artefacts['experiment_conf'][session_id] = experiment_conf


    with open(f"{provenance_artefacts_updated_path}", "w") as f:
        json.dump(provenance_artefacts, f,indent=4)
    

def send_jmx_file_to_server(jmx_output_path,jmx_output_filename,rps,duration,is_localhost):
    if not is_localhost:
        if rps != 0:
            server_jmx_files_dir = f"/home/{server_user_id}/jmx-files"
            if server_pem_file_path is not None:
                remote_copy_command = f"scp -i {server_pem_file_path} {jmx_output_path} {server_user_id}@{server_ip}:{server_jmx_files_dir}"
                remote_mkdir_command = f"ssh -i {server_pem_file_path} {server_user_id}@{server_ip} mkdir -p /home/{server_user_id}/jmx-files"
            else:
                remote_mkdir_command = f"ssh {server_user_id}@{server_ip} mkdir -p /home/{server_user_id}/jmx-files"
                remote_copy_command = f"scp {jmx_output_path} {server_user_id}@{server_ip}:{server_jmx_files_dir}"

            os.system(remote_mkdir_command)
            os.system(remote_copy_command)
            experiment_begin_command = f"/home/{server_user_id}/apache-jmeter-5.6.2/bin/jmeter -n -t {server_jmx_files_dir}/{jmx_output_filename}  -l {server_jmx_files_dir}/{jmx_output_filename}.jtl"
            shell_script_commands.append(experiment_begin_command)
        else:
            cmd = f"sleep {int(duration)}"
            shell_script_commands.append(cmd)
    else:
        experiment_begin_command = f"jmeter -n -t {jmx_output_path}  -l {jmx_output_path}.jtl"
        shell_script_commands.append(experiment_begin_command)
    

def get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism, session_id,region):
    ## use pathlib to get the path of the current file
   
    cur_path = os.getenv("XFAAS_DIR")+ "/serwo"
    jmx_template_path = f"{cur_path}/benchmark_resources/{csp.split('_')[0]}_jmx_template.jmx"
    jmx_output_filename = f"{csp}-{region}-{wf_name}-{payload_size}-{dynamism}-{int(rps/60)}-{int(duration)}-session-{session_id}.jmx"
    make_jmx_resources_dir = f"{cur_path}/benchmark_resources/generated_jmx_resources"
    os.makedirs(make_jmx_resources_dir, exist_ok=True)
    jmx_output_path  = f"{cur_path}/benchmark_resources/generated_jmx_resources/{jmx_output_filename}"
    return jmx_template_path,jmx_output_path,jmx_output_filename


def generate_shell_script_and_scp(csp,payload_size, wf_name, rps, duration,dynamism,region,is_localhost):
    shell_file_name  = f"{csp}-{region}-{payload_size}-{wf_name}-{rps}-{duration}-{dynamism}.sh"
    make_shell_scripts_dir = f"{pathlib.Path(__file__).parent}/benchmark_resources/generated_shell_scripts"
    os.makedirs(make_shell_scripts_dir, exist_ok=True)
    output_path = pathlib.Path(__file__).parent / f"benchmark_resources/generated_shell_scripts/{shell_file_name}"
    code = "#!/bin/sh\n"
    for command in shell_script_commands:
        code += command + "\n"
        # code += "sleep 20\n"
    with open(output_path, "w") as f:
        f.write(code)
    
    if not is_localhost:
        if server_pem_file_path is not None:
            # mkdir if not exists
            os.system(f"ssh -i {server_pem_file_path} {server_user_id}@{server_ip} mkdir -p shell_scripts")
            os.system(f"scp -i {server_pem_file_path} {output_path} {server_user_id}@{server_ip}:shell_scripts/")
            os.system(f"ssh -i {server_pem_file_path} {server_user_id}@{server_ip} 'chmod +x shell_scripts/{shell_file_name}'")
            os.system(f"ssh -i {server_pem_file_path} {server_user_id}@{server_ip} ./shell_scripts/{shell_file_name}")
        else:
            # mkdir if not exists
            os.system(f"ssh {server_user_id}@{server_ip} mkdir -p shell_scripts")
            os.system(f"scp {output_path} {server_user_id}@{server_ip}:shell_scripts/")
            os.system(f"ssh {server_user_id}@{server_ip} 'chmod +x shell_scripts/{shell_file_name}'")
            os.system(f"ssh {server_user_id}@{server_ip} ./shell_scripts/{shell_file_name}")
    else:
        os.system(f"chmod +x {output_path}")
        os.system(f"./{output_path}")
    
def load_payload(wf_user_directory,payload_size):
    payload_path = f"{wf_user_directory}/samples/{payload_size}/input/input.json"
    with open(payload_path) as f:
        payload = json.load(f)

    return payload


def run_workload(csp,region,part_id,max_rps,duration,payload_size,dynamism,wf_name, wf_user_directory, wf_deployment_id,run_id, is_localhost):

    copy_provenance_artifacts(csp, region, part_id, wf_user_directory, wf_deployment_id,max_rps,run_id)
    
    dynamism_data = read_dynamism_file(dynamism, duration, max_rps)
    if 'azure' in csp:
        execute_url = get_azure_resources(csp,region,part_id,wf_user_directory)
        state_machine_arn = ''
    elif csp == 'aws':
        execute_url, state_machine_arn = get_aws_resources(csp,region,part_id,wf_user_directory)


    dynamism_updated = dynamism

    if dynamism == 'sawtooth':
        dynamism_updated = "st"
    elif dynamism == 'alibaba':
        dynamism_updated = "a"
    elif dynamism == 'step-up':
        dynamism_updated = "su"
    elif dynamism == 'google':
        dynamism_updated = "g"

    payload = load_payload(wf_user_directory,payload_size)

    session_id = dynamism_updated + payload_size
    i = 1
    for d in dynamism_data:
        duration = d[0]
        rps = d[1]
        # payload_size = d[2]
        # payload = load_payload(wf_user_directory,payload_size)
        ne_session_id = session_id + str(i)
        
        make_jmx_file(csp, rps * 60.0, duration, payload_size, wf_name, execute_url,state_machine_arn, dynamism, ne_session_id, wf_user_directory, part_id, region , wf_deployment_id, run_id,payload,is_localhost)
        i += 1
    generate_shell_script_and_scp(csp,payload_size, wf_name,   max_rps, duration,dynamism,region,is_localhost)
    


def copy_provenance_artifacts(csp, region, part_id, wf_user_directory,wf_deployment_id,rps,run_id):
    
    global deployment_id
    
    os.makedirs(f"{wf_user_directory}/{wf_deployment_id}/{run_id}", exist_ok=True)
    provenance_artefacts_path = f"{wf_user_directory}/build/workflow/resources/provenance-artifacts-{csp}-{region}-{part_id}.json"
    with open(provenance_artefacts_path) as f:
        provenance_artifact = json.load(f)
    deployment_id = provenance_artifact['deployment_id']

    provenance_artefacts_updated_path = f"{wf_user_directory}/{wf_deployment_id}/{run_id}/{artifact_suffix}"
   
    shutil.copyfile(provenance_artefacts_path, provenance_artefacts_updated_path)
        

def build_workflow(user_wf_dir):
    root_dir = os.getenv("XFBENCH_DIR")
    wf_builder_code = f'{root_dir}/workflows/build_wf.py'
    sys.path.append(wf_builder_code)
    args_to_send = '--wf-user-directory ' + user_wf_dir
    os.system(f'python3 {wf_builder_code} {args_to_send}')
    
def deploy_workflow(user_wf_dir,dag_filename, region,csp):
    wf_id, refactored_wf_id, wf_deployment_id = xfaas_deployer(user_wf_dir, dag_filename ,'dag-benchmark-revised.json',csp,region)
    return wf_id, refactored_wf_id, wf_deployment_id

def plot_metrics(user_wf_dir, wf_deployment_id, run_id, wf_name,region):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot_e2e_timeline(xticks=[], yticks=[],is_overlay=True,region=region)
    figwidth = 7
    if wf_name == 'fileProcessing' or wf_name == 'math':
        figwidth = 20   
    plotter.plot_stagewise( yticks=[],figwidth=figwidth)
    plotter.plot_cumm_e2e(yticks=[])
    # plotter.plot_e2e_invocations_wnwo_containers(csp="azure", yticks=[])



def remote_teardown(wf_user_directory,csp,region,part_id):
    if csp == 'aws':
        pass
    elif 'azure' in csp:
        resource_path = f"{wf_user_directory}/build/workflow/resources/{csp}-{region}-{part_id}.json"
        with open(resource_path) as f:
            resource = json.load(f)
        resource_group_name = resource['group']
        remove_resource_group_command = f"az group delete --name {resource_group_name} --yes"
        os.system(remove_resource_group_command)


def build_singleton_wf(function_class, function_name,function_code,node_name):
    root_dir = os.getenv("XFBENCH_DIR")
    wf_builder_code = f'{root_dir}/workflows/build_singleton_wf.py'
    sys.path.append(wf_builder_code)
    args_to_send = f"--function-class {function_class} --function-name {function_name} --function-code {function_code} --node_name {node_name}"
    os.system(f'python3 {wf_builder_code} {args_to_send}')

def local_teardown(wf_user_directory):
    remove_build_command = f"rm -rf {wf_user_directory}/build"
    remove_collect_logs_command = f"rm -rf {wf_user_directory}/CollectLogs"
    remove_refactored_dag_command = f"rm -rf {wf_user_directory}/refactored-dag.json"
    remove_orchestrator_command = f"rm -rf {wf_user_directory}/orchestrator.py"

    if os.path.exists(f"{wf_user_directory}/build"):
        os.system(remove_build_command)
    if os.path.exists(f"{wf_user_directory}/CollectLogs"):    
        os.system(remove_collect_logs_command)
    if os.path.exists(f"{wf_user_directory}/refactored-dag.json"):
        os.system(remove_refactored_dag_command)
    if os.path.exists(f"{wf_user_directory}/orchestrator.py"):
        os.system(remove_orchestrator_command)


if __name__ == "__main__":
    
    args = parser.parse_args()
    csp = args.csp
    region = args.region
    part_id = "test"
    max_rps = args.max_rps
    duration = args.duration
    payload_size = args.payload_size
    dynamism = args.dynamism
    wf_name = args.wf_name
    wf_user_directory = args.wf_user_directory
    path_to_config_file = args.client_config_path
    dag_filename = args.dag_filename
    teardown_flag = args.teardown_flag
    provenance_artifact_filename = f"{csp}-{dynamism}-{payload_size}-{max_rps}rps.json"
    is_localhost = False
    if "localhost" != args.client_key:
        get_client_login_details(path_to_config_file)
    else:
        is_localhost = True
    
    run_id = 'exp1'
   
    print('==================BUILDING WF===========================')

    ##if args does not contain is_singleton_wf then set is_singleton_wf_flag to False
    
    is_singleton_wf_flag = bool(int(args.is_singleton_wf))
    
    if is_singleton_wf_flag == True:
        print('==================SINGLETON WF===========================')
        function_class = args.function_class
        function_name = args.function_name
        function_code = args.function_code
        node_name = args.node_name
        if None in [function_class, function_name, function_code, node_name]:
            raise ValueError("Function class, function name, function code and node name are required for singleton workflow")
        
        build_singleton_wf(function_class, function_name,function_code,node_name)
        wf_user_directory = os.getenv("XFBENCH_DIR") + f"/workflows/singleton_workflows/{function_class}/{function_name}"
    else:
        build_workflow(wf_user_directory)
    
    wf_user_directory += "/workflow-gen"
    
    
    print('==================DEPLOYING WF===========================')
    wf_id, refactored_wf_id, wf_deployment_id = deploy_workflow(wf_user_directory,dag_filename, region,csp)
    
    ## write deployment id to a file create if not exists else append
    deps = []
    xfaas_dir = os.getenv('XFAAS_DIR')
    deployment_id_file_path = f"{xfaas_dir}/deployments.txt"
    ## read the file if exists
    if not os.path.exists(deployment_id_file_path):
        with open(deployment_id_file_path, "w") as f:
            f.write(wf_deployment_id + "\n")
    else:
        with open(deployment_id_file_path, "r") as f:
            deps = f.readlines()
            deps = [x.strip() for x in deps]
        deps.append(wf_deployment_id)
        with open(deployment_id_file_path, "w") as f:
            for dep in deps:
                f.write(dep + "\n")

    time.sleep(10)
    
    print('==================RUNNING WF===========================')
    run_workload(csp,region,part_id,max_rps,duration,payload_size,dynamism,wf_name, wf_user_directory,wf_deployment_id,run_id,is_localhost)
    time.sleep(60)
    try:
        print('==================PLOTTING METRICS===========================')
        plot_metrics(wf_user_directory,wf_deployment_id,run_id,wf_name,region)
    except Exception as e:
        print('==================PLOTTING METRICS FAILED===========================')
        print(e)
        pass
    
    print('==================TEARING DOWN WF===========================')
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    exp_conf = f"{csp}-{region}-{max_rps}-{duration}-{payload_size}-{dynamism}-{timestamp}"
    src = f"{wf_user_directory}/{wf_deployment_id}"
    dst = f"{wf_user_directory}/{exp_conf}"
    shutil.copytree(src, dst)

    
    teardown_flag = bool(int(teardown_flag))
    
    if teardown_flag == True:
        remote_teardown(wf_user_directory,csp,region,part_id)

    local_teardown(wf_user_directory)