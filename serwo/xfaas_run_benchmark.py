import json
import argparse
import subprocess
import pathlib
import os
import shutil

parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
parser.add_argument("--csp",dest='csp',type=str,help="CSP name")
parser.add_argument("--region",dest='region',type=str,help="Region name")
parser.add_argument("--part-id",dest='part_id',type=str,help="Partition ID")
parser.add_argument("--max-rps",dest='max_rps',type=int,help="Max RPS")
parser.add_argument("--duration",dest='duration',type=int,help="Duration(sec)")
parser.add_argument("--payload-size",dest='payload_size',type=str,help="Payload size: Values: Small/Medium/Large")
parser.add_argument("--dynamism",dest='dynamism',type=str,help="Dynamism: Values: staic/alibaba/step_function")
parser.add_argument("--wf-name",dest='wf_name',type=str,help="Workflow name")
parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
parser.add_argument("--path-to-pem",dest='path_to_pem',type=str,help="Path to pem file")
parser.add_argument("--provenance-artifact-filename",dest='provenance_artifact_filename',type=str,help="Provenance artifact filename")

args = parser.parse_args()
provenance_artifact_filename = args.provenance_artifact_filename
deployment_id = ''
azure_server_ip = '4.240.90.234'
azure_user_id = 'azureuser'

aws_server_ip = '65.0.17.98'
aws_user_id = 'ubuntu'

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

def make_aws_jmx_file(csp, rps, duration, payload_size, wf_name, execute_url, state_machine_arn, dynamism, session_id, wf_user_directory, part_id, region, path_to_pem_file):
    jmx_template_path, jmx_output_path,jmx_output_filename = get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism,session_id)
    template_aws_jmx_file(rps, duration, execute_url, state_machine_arn, payload_size, jmx_template_path, jmx_output_path, session_id)
    send_jmx_file_to_aws_server(jmx_output_path,jmx_output_filename, path_to_pem_file)
    dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region)


def make_azure_jmx_file(csp, rps, duration, payload_size, wf_name, execute_url, dynamism, session_id, wf_user_directory, part_id, region):
    jmx_template_path, jmx_output_path,jmx_output_filename = get_jmx_paths(csp, rps, duration, payload_size, wf_name, dynamism,session_id)
    template_azure_jmx_file(rps, duration, execute_url, payload_size, jmx_template_path, jmx_output_path, session_id)
    send_jmx_file_to_azure_server(jmx_output_path,jmx_output_filename)
    dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region)



def dump_experiment_conf(jmx_output_filename, csp, rps, duration, payload_size, wf_name, dynamism, session_id, wf_user_directory, part_id, region):
   
    provenance_artefacts_updated_path = f"{wf_user_directory}/provenance-artifacts/{provenance_artifact_filename}.json"
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
    # os.system(f"ssh {azure_user_id}@{azure_server_ip} {shell_file_name}")
    

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
    # os.system(f"ssh -i {path_to_pem_file} {aws_user_id}@{aws_server_ip} {shell_file_name}")


def run(csp,region,part_id,max_rps,duration,payload_size,dynamism,wf_name, wf_user_directory,path_to_pem_file):
    copy_provenance_artifacts(csp, region, part_id, wf_user_directory)
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
            make_azure_jmx_file(csp, rps_fraction * max_rps * 60.0, duration*duration_fraction, payload_size, wf_name, execute_url, dynamism, ne_session_id, wf_user_directory, part_id, region )
            ## temp hack for sawtooth
            # make_azure_jmx_file(csp, rps_fraction * 60.0, duration_fraction, payload_size, wf_name, execute_url, dynamism, ne_session_id, wf_user_directory, part_id, region )
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
            # make_aws_jmx_file(csp, rps_fraction * max_rps * 60.0, duration*duration_fraction, payload_size, wf_name, execute_url, state_machine_arn, dynamism, ne_session_id, wf_user_directory, part_id, region, path_to_pem_file)

            ## temp hack for sawtooth
            make_aws_jmx_file(csp, rps_fraction * 60.0, duration_fraction, payload_size, wf_name, execute_url, state_machine_arn, dynamism, ne_session_id, wf_user_directory, part_id, region, path_to_pem_file)
            i += 1
        generate_aws_shell_script_and_scp(payload_size, wf_name, rps_fraction * max_rps, duration*duration_fraction,dynamism)

def copy_provenance_artifacts(csp, region, part_id, wf_user_directory):
    ## make a directory provenance-artifacts in the user workflow directory
    ## copy the provenance artifacts from the build directory to the user workflow directory
    global deployment_id
    os.makedirs(f"{wf_user_directory}/provenance-artifacts", exist_ok=True)
    provenance_artefacts_path = f"{wf_user_directory}/build/workflow/resources/provenance-artifacts-{csp}-{region}-{part_id}.json"
    with open(provenance_artefacts_path) as f:
        provenance_artifact = json.load(f)
    deployment_id = provenance_artifact['deployment_id']

    provenance_artefacts_updated_path = f"{wf_user_directory}/provenance-artifacts/{provenance_artifact_filename}.json"
   
    shutil.copyfile(provenance_artefacts_path, provenance_artefacts_updated_path)
        
    


if __name__ == "__main__":
    args = parser.parse_args()
    csp = args.csp
    region = args.region
    part_id = args.part_id
    max_rps = args.max_rps
    duration = args.duration
    payload_size = args.payload_size
    dynamism = args.dynamism
    wf_name = args.wf_name
    wf_user_directory = args.wf_user_directory
    path_to_pem_file = args.path_to_pem
    

    run(csp,region,part_id,max_rps,duration,payload_size,dynamism,wf_name, wf_user_directory,path_to_pem_file)

