import json
import argparse
import subprocess
import pathlib
import os
import shutil
from xfaas_main import run as xfaas_deployer
import time

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
parser.add_argument("--dag-file-name",dest='dag_filename',type=str,help="DAG FILE NAME")

args = parser.parse_args()
provenance_artifact_filename = None
deployment_id = ''
azure_server_ip = ''
azure_user_id  = ''
aws_server_ip = ''
aws_user_id = ''
aws_key_pem_path = ''

def get_client_login_details(config_path):
    global azure_server_ip, azure_user_id, aws_server_ip, aws_user_id, aws_key_pem_path
    with open(config_path) as f:
        data = json.load(f)
    azure_server_ip = data['azure_server_ip']
    azure_user_id = data['azure_user_id']
    aws_server_ip = data['aws_server_ip']
    aws_user_id = data['aws_user_id']

    aws_key_pem_path = data['aws_key_path']
    # azure_server_ip = '4.240.90.234'
    # azure_user_id = 'azureuser'

    # aws_server_ip = '65.0.17.98'
    # aws_user_id = 'ubuntu'
    # return azure_server_ip,azure_user_id,aws_server_ip,aws_user_id

# azure_server_ip, azure_user_id, aws_server_ip, aws_user_id = get_client_login_details()

azure_shell_script_commands = []
aws_shell_script_commands = []

def read_dynamism_file(dynamism):
    file_path = pathlib.Path(__file__).parent / f"benchmark_resources/dynamism/{dynamism}/config.csv"
    with open(file_path) as f:  
        data = f.readlines()
    data = [x.strip() for x in data]
    final_data = []
    for d in data:
        vals = [float(x) for x in d.split(",") if x != ""]
        final_data.append((vals[0],vals[1]))
    return final_data


def get_azure_app_url(csp,region,part_id,wf_user_directory):
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


def template_azure_jmx_file(rps, duration, execute_url, payload_size, input_jmx, output_path, session_id):
    rps_keyword = "RPS"
    execute_url_keyword = "URL"
    duration_keyword = "DURATION"
    payload_size_keyword = "PAYLOAD"
    session_id_keyword = "SESSION"
    deployment_id_keyword = "DEPLOYMENT_ID"

    with open(input_jmx) as f:
        data = f.read()
    data = data.replace(rps_keyword, str(rps))
    data = data.replace(execute_url_keyword, execute_url)
    data = data.replace(duration_keyword, str(int(duration)))
    data = data.replace(payload_size_keyword, payload_size)
    data = data.replace(session_id_keyword, str(session_id))
    data = data.replace(deployment_id_keyword, deployment_id)
    to_replace = '"ThreadGroup.num_threads">2'
    if rps == 1020.0 or rps == 840.0:
        data = data.replace(to_replace, f'"ThreadGroup.num_threads">17')
    
    with open(output_path, "w") as f:
        f.write(data)


def template_aws_jmx_file(rps, duration, execute_url, state_machine_arn, payload_size, input_jmx, output_path, session_id):
    global deployment_id
    rps_keyword = "RPS"
    execute_url_keyword = "URL"
    duration_keyword = "DURATION"
    payload_size_keyword = "PAYLOAD"
    state_machine_arn_keyword = "STATE_MACHINE_ARN"
    session_id_keyword = "SESSION"
    deployment_id_keyword = "DEPLOYMENT_ID"


    with open(input_jmx) as f:
        data = f.read() 
    data = data.replace(rps_keyword, str(rps))
    data = data.replace(execute_url_keyword, f'{execute_url}/execute')
    data = data.replace(duration_keyword, str(int(duration)))
    data = data.replace(payload_size_keyword, payload_size)
    data = data.replace(state_machine_arn_keyword, state_machine_arn)
    data = data.replace(session_id_keyword, str(session_id))
    data = data.replace(deployment_id_keyword, deployment_id)

    with open(output_path, "w") as f:
        f.write(data)

def make_aws_jmx_file(csp, rps, duration, payload_size, wf_name, execute_url, state_machine_arn, dynamism, session_id, wf_user_directory, part_id, region, path_to_pem_file, wf_deployment_id):
    jmx_template_path, jmx_output_path,jmx_output_filename = get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism,session_id)
    template_aws_jmx_file(rps, duration, execute_url, state_machine_arn, payload_size, jmx_template_path, jmx_output_path, session_id)
    send_jmx_file_to_aws_server(jmx_output_path,jmx_output_filename, path_to_pem_file)
    dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region, wf_deployment_id)


def make_azure_jmx_file(csp, rps, duration, payload_size, wf_name, execute_url, dynamism, session_id, wf_user_directory, part_id, region, wf_deployment_id):
    jmx_template_path, jmx_output_path,jmx_output_filename = get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism,session_id)
    template_azure_jmx_file(rps, duration, execute_url, payload_size, jmx_template_path, jmx_output_path, session_id)
    send_jmx_file_to_azure_server(jmx_output_path,jmx_output_filename)
    dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region, wf_deployment_id)



def dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region,wf_deployment_id):
   
    provenance_artefacts_updated_path = f"{wf_user_directory}/{wf_deployment_id}/provenance-artifacts/{provenance_artifact_filename}"
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
    

def send_jmx_file_to_aws_server(jmx_output_path,jmx_output_filename, path_to_pem_file):
    aws_server_jmx_files_dir = f"/home/{aws_user_id}/bigdata-jmx-files"
    remote_copy_command = f"scp -i {path_to_pem_file} {jmx_output_path} {aws_user_id}@{aws_server_ip}:{aws_server_jmx_files_dir}"
    os.system(remote_copy_command)
    experiment_begin_command = f"/home/{aws_user_id}/apache-jmeter-5.5/bin/jmeter -n -t {aws_server_jmx_files_dir}/{jmx_output_filename}  -l {aws_server_jmx_files_dir}/{jmx_output_filename}.jtl"
    aws_shell_script_commands.append(experiment_begin_command)
    

def send_jmx_file_to_azure_server(jmx_output_path,jmx_output_filename):
    azure_server_jmx_files_dir = f"/home/{azure_user_id}/bigdata-jmx-files"
    remote_copy_command = f"scp {jmx_output_path} {azure_user_id}@{azure_server_ip}:{azure_server_jmx_files_dir}"
    os.system(remote_copy_command)
    experiment_begin_command = f"/home/{azure_user_id}/apache-jmeter-5.4.3/bin/jmeter -n -t {azure_server_jmx_files_dir}/{jmx_output_filename}  -l {azure_server_jmx_files_dir}/{jmx_output_filename}.jtl"
    azure_shell_script_commands.append(experiment_begin_command)
    
    

def get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism, session_id):
    jmx_template_path = pathlib.Path(__file__).parent / f"benchmark_resources/workflows/{wf_name}/payload/{payload_size}/{csp}/jmx_template.jmx"
    jmx_output_filename = f"{csp}-{wf_name}-{payload_size}-{dynamism}-{int(rps/60)}-{int(duration)}-session-{session_id}.jmx"
    jmx_output_path  = pathlib.Path(__file__).parent / f"benchmark_resources/generated_jmx_resources/{jmx_output_filename}"
    return jmx_template_path,jmx_output_path,jmx_output_filename


def generate_azure_shell_script_and_scp(payload_size, wf_name, rps, duration,dynamism):
    shell_file_name  = f"azure-{payload_size}-{wf_name}-{rps}-{duration}-{dynamism}.sh"
    output_path = pathlib.Path(__file__).parent / f"benchmark_resources/generated_shell_scripts/{shell_file_name}"
    code = "#!/bin/sh\n"
    for command in azure_shell_script_commands:
        code += command + "\n"
        # code += "sleep 20\n"
    with open(output_path, "w") as f:
        f.write(code)
    os.system(f"scp {output_path} {azure_user_id}@{azure_server_ip}:shell_scripts/")
    os.system(f"ssh {azure_user_id}@{azure_server_ip} 'chmod +x shell_scripts/{shell_file_name}'")
    os.system(f"ssh {azure_user_id}@{azure_server_ip} ./shell_scripts/{shell_file_name}")
    

def generate_aws_shell_script_and_scp(payload_size, wf_name, rps, duration,dynamism):
    shell_file_name  = f"aws-{payload_size}-{wf_name}-{rps}-{duration}-{dynamism}.sh"
    output_path = pathlib.Path(__file__).parent / f"benchmark_resources/generated_shell_scripts/{shell_file_name}"
    code = "#!/bin/sh\n"
    for command in aws_shell_script_commands:
        code += command + "\n"
        # code += "sleep 20\n"
    with open(output_path, "w") as f:
        f.write(code)
    os.system(f"scp -i {path_to_pem_file} {output_path} {aws_user_id}@{aws_server_ip}:shell_scripts/")
    os.system(f"ssh -i {path_to_pem_file} {aws_user_id}@{aws_server_ip} 'chmod +x shell_scripts/{shell_file_name}'")
    
    os.system(f"ssh -i {path_to_pem_file} {aws_user_id}@{aws_server_ip} ./shell_scripts/{shell_file_name}")


def run_workload(csp,region,part_id,max_rps,duration,payload_size,dynamism,wf_name, wf_user_directory,path_to_pem_file, wf_deployment_id):
    copy_provenance_artifacts(csp, region, part_id, wf_user_directory, wf_deployment_id,max_rps)
    saw_tooth = [(8,1),(8,2),(8,3),(8,4),(8,5),(8,6),(8,7),(8,8)]
    dynamism_data = read_dynamism_file(dynamism)
    if csp == 'azure':
        execute_url = get_azure_app_url(csp,region,part_id,wf_user_directory)
        
        dynamism_updated = dynamism

        if dynamism == 'sawtooth':
            dynamism_updated = "st"
        elif dynamism == 'alibaba':
            dynamism_updated = "a"
        elif dynamism == 'step-up':
            dynamism_updated = "su"
        elif dynamism == 'google':
            dynamism_updated = "g"

        session_id = dynamism_updated + payload_size
        i = 1
        for d in dynamism_data:
            duration_fraction = d[0]
            rps_fraction = d[1]
            ne_session_id = session_id + str(i)
            if "sawtooth" == dynamism or "alibaba"  == dynamism :
                make_azure_jmx_file(csp, rps_fraction * 60.0, duration_fraction, payload_size, wf_name, execute_url, dynamism, ne_session_id, wf_user_directory, part_id, region, wf_deployment_id )
            else:
                make_azure_jmx_file(csp, rps_fraction * max_rps * 60.0, duration*duration_fraction, payload_size, wf_name, execute_url, dynamism, ne_session_id, wf_user_directory, part_id, region , wf_deployment_id)
            
            i += 1
        generate_azure_shell_script_and_scp(payload_size, wf_name, rps_fraction * max_rps, duration*duration_fraction,dynamism)


    elif csp == 'aws':
        dynamism_updated = dynamism

        if dynamism == 'sawtooth':
            dynamism_updated = "st"
        elif dynamism == 'alibaba':
            dynamism_updated = "a"
        elif dynamism == 'step-up':
            dynamism_updated = "su"
        elif dynamism == 'google':
            dynamism_updated = "g"

        session_id = dynamism_updated + payload_size 

        execute_url, state_machine_arn = get_aws_resources(csp,region,part_id,wf_user_directory)
        i =  1
        for d in dynamism_data:
            duration_fraction = d[0]
            rps_fraction = d[1]
            ne_session_id = session_id + str(i)
            if "sawtooth" == dynamism or "alibaba" == dynamism:
                make_aws_jmx_file(csp, rps_fraction * 60.0, duration_fraction, payload_size, wf_name, execute_url, state_machine_arn, dynamism, ne_session_id, wf_user_directory, part_id, region, path_to_pem_file, wf_deployment_id)
            else:
                make_aws_jmx_file(csp, rps_fraction * max_rps * 60.0, duration*duration_fraction, payload_size, wf_name, execute_url, state_machine_arn, dynamism, ne_session_id, wf_user_directory, part_id, region, path_to_pem_file, wf_deployment_id)

            
            i += 1
        generate_aws_shell_script_and_scp(payload_size, wf_name, rps_fraction * max_rps, duration*duration_fraction,dynamism)

def copy_provenance_artifacts(csp, region, part_id, wf_user_directory,wf_deployment_id,rps):
    ## make a directory provenance-artifacts in the user workflow directory
    ## copy the provenance artifacts from the build directory to the user workflow directory
    global deployment_id
    os.makedirs(f"{wf_user_directory}/{wf_deployment_id}/provenance-artifacts", exist_ok=True)
    provenance_artefacts_path = f"{wf_user_directory}/build/workflow/resources/provenance-artifacts-{csp}-{region}-{part_id}.json"
    with open(provenance_artefacts_path) as f:
        provenance_artifact = json.load(f)
    deployment_id = provenance_artifact['deployment_id']

    provenance_artefacts_updated_path = f"{wf_user_directory}/{wf_deployment_id}/provenance-artifacts/{provenance_artifact_filename}"
   
    shutil.copyfile(provenance_artefacts_path, provenance_artefacts_updated_path)
        
    
def deploy_workflow(user_wf_dir,dag_filename, region,csp):
    
    wf_id, refactored_wf_id, wf_deployment_id = xfaas_deployer(user_wf_dir, dag_filename ,'dag-benchmark-revised.json',csp,region)
    return wf_id, refactored_wf_id, wf_deployment_id

def plot_metrics(user_wf_dir, artificats_filename):
    # os.chdir('..')
    command = f'python3 xfaas_benchmarksuite_plotgen_vk.py --user-dir {user_wf_dir} --artifacts-file {artificats_filename}.json  --interleaved True --format pdf --out-dir {artificats_filename}-long'
    os.system(command)

    

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
    wf_user_directory = args.wf_user_directory+"/workflow-gen"
    path_to_config_file = args.client_config_path
    dag_filename = args.dag_filename
    provenance_artifact_filename = f"{csp}-{dynamism}-{payload_size}-{max_rps}rps.json"
    get_client_login_details(path_to_config_file)
    path_to_pem_file = aws_key_pem_path

    ## do an ls in aws client

    
    # print('==================DEPLOYING WF===========================')
    # wf_id, refactored_wf_id, wf_deployment_id = deploy_workflow(wf_user_directory,dag_filename, region,csp)
    # time.sleep(20)
    # print('==================RUNNING WF===========================')
    wf_deployment_id = "fb895579-69d6-4573-aff6-5f0f596914b9"
    run_workload(csp,region,part_id,max_rps,duration,payload_size,dynamism,wf_name, wf_user_directory,path_to_pem_file,wf_deployment_id)
    time.sleep(20)
    # print('==================PLOTTING METRICS===========================')
    # plot_metrics(wf_user_directory,provenance_artifact_filename)


