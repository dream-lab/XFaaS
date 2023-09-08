import json
import sys
import subprocess
import os
import shutil
import argparse
import random

parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
# parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
# args = parser.parse_args()

def get_func_path(func_name, category_name):
    root_dir = os.getenv("XFAAS_WF_DIR")
    folder_path = f'{root_dir}/functions/{category_name}/' + func_name
    return folder_path

def get_func_file_name(func_name):
    return f'{func_name}.py'

def get_wf_dir(dag_path):
    return os.path.dirname(dag_path)

def copy_folder(src, dst):
    try:
        if not os.path.exists(dst):
            shutil.copytree(src,dst)
        else:
            ##remove the folder and copy again
            shutil.rmtree(dst)
            shutil.copytree(src,dst)
    except Exception as e:
        print(f"Error copying '{src}': {e}")

def create_dag_file(data,wf_file_path):
    # Load node data
    nodes = data["Nodes"]
    idx = 0
    res = []
    for item in nodes:
        cat_name = list(item.keys())[0]
        func_name = list(item.values())[0]
        func_nodes = list(item.values())[1]
        print(list(item.values()))

        # Get relevant paths
        func_path = get_func_path(func_name, cat_name)
        func_file = get_func_file_name(func_name)
        wf_dir = get_wf_dir(wf_file_path)
        dst_path = os.path.join(f'{wf_dir}/workflow-gen/{func_name}')

        # Create node for each func
        idx = idx + 1
        # Create src_gen folder
        copy_folder(func_path, dst_path)
        ## delete readme if exists  
        readme_path = f"{dst_path}/README.md"
        if os.path.exists(readme_path):
            os.remove(readme_path)
        
        ##delete samples if exists
        samples_path = f"{dst_path}/samples"
        if os.path.exists(samples_path):
            shutil.rmtree(samples_path)


        if len(func_nodes) == 1:
            node = {
                        "NodeId": f"{idx}",
                        "NodeName": f"{func_nodes[0]}",
                        "Path": f"{dst_path}",
                        "EntryPoint": f"{func_file}",
                        "CSP": "NA",
                        "MemoryInMB": 128
                    }
            res.append(node)
        elif len(func_nodes) > 1:
            for n in func_nodes:
                node = {
                        "NodeId": f"{idx}",
                        "NodeName": f"{n}",
                        "Path": f"{func_path}",
                        "EntryPoint": f"{func_file}",
                        "CSP": "NA",
                        "MemoryInMB": 128
                    }
                res.append(node)
                idx = idx + 1

    # dump to new dag.json file
    data["Nodes"] = res
    ## random three digit number
    
    dag_path = f"{wf_dir}/workflow-gen/dag.json"

    with open(dag_path, 'w') as file:
        ret = json.dumps(data,indent=4)
        file.write(ret)
    
    # Copy samples of first node to wf_dir
    # copy_folder(f"{res[0]['Path']}/samples/", f"{wf_dir}/samples/")

# Specify the path to your JSON file

def build(wf_base_path):
    wf_file_path = wf_base_path + "/workflow.json"
    with open(wf_file_path, 'r') as file:
        data = json.load(file)
        create_dag_file(data,wf_file_path)

# wf_base_path = args.wf_user_directory
# build(wf_base_path)
