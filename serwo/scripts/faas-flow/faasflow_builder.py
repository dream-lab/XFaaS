import sys, os
import pathlib
import json

user_input_1 = sys.argv[1]
json_file_name = sys.argv[2]

parent_directory = pathlib.Path(__file__).parent.absolute().parent.absolute().parent
user_json_dir=f"{parent_directory}/{user_input_1}"
build_dir=f"{user_json_dir}/build/workflow/faasflow"
resources_json = f"{user_json_dir}/build/workflow/resources/faasflow_resources.json"
resource_dir=f"{user_json_dir}/build/workflow/resources"

def build_working_dir():
    global fsfl_functions_path
    a, user_wf_name = get_user_workflow_details()
    fsfl_functions_path = f"{build_dir}/{user_wf_name}"
    if not os.path.exists(fsfl_functions_path):
        os.makedirs(fsfl_functions_path)

def get_user_workflow_details():
    json_path = user_json_dir+'/'+json_file_name
    data = json.load(open(json_path))
    fns_data = data['Nodes']
    return fns_data, data['WorkflowName']

def build_user_fn_dirs(user_fns_data):
    for fn in user_fns_data:
        name = fn['NodeName']
        dir_path = fsfl_functions_path+'/'+name
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

def build_meta_files(user_fns_data):
    #TODO - Create workflow.yml, flow.yml
    

def runner():
    print(parent_directory)
    build_working_dir()
    user_fns_data, user_app_name = get_user_workflow_details()
    build_user_fn_dirs(user_fns_data)
    print(user_fns_data)
runner()