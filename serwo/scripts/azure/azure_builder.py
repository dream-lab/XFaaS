import os
import json
import shutil
import uuid
import pathlib
from botocore.exceptions import ClientError
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from jinja2 import Environment, FileSystemLoader
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
from random import randint
import sys
import find_and_replace as fr

USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]

## User and Azure Build Paths

user_dag_file_name=DAG_DEFINITION_FILE
xfaas_working_directory = pathlib.Path(__file__).parent.absolute().parent.absolute().parent
user_workflow_directory= f"{xfaas_working_directory}/{USER_DIR}"
resource_dir=f"{user_workflow_directory}/build/workflow/resources"
build_dir=f"{user_workflow_directory}/build/workflow/azure"
resources_json = f"{user_workflow_directory}/build/workflow/resources/azure_resources.json"
az_functions_path = ''

TEMP_TRIGGER = 'TEMP_TRIGGER'
orchestrator_generator_path = f'{xfaas_working_directory}/azure_create_statemachine.py'

## Meta files Paths
obj_dir_str = 'python/src/utils/classes/commons'
json_templates_base = f'{xfaas_working_directory}/python/src/faas-templates/azure/json-templates'
host_json_path = json_templates_base + '/'+'host.json'
local_settings_path = json_templates_base + '/'+'local.settings.json'
function_json = json_templates_base + '/'+'function.json'
serwo_object = f'{xfaas_working_directory}/python/src/utils/classes/commons/serwo_objects.py'
starter_path = f'{xfaas_working_directory}/python/src/faas-templates/azure/predefined-functions/Starter'
orchestrator_path = f'{xfaas_working_directory}/python/src/faas-templates/azure/predefined-functions/Orchestrate'
queue_trigger_path = f'{xfaas_working_directory}/python/src/faas-templates/azure/predefined-functions/QueueTrigger'

## Runner template
runner_template_file = f'{xfaas_working_directory}/python/src/runner-templates/azure/runner_template.py'
runner_template_file_secondary = f'{xfaas_working_directory}/python/src/runner-templates/azure/runner_template_secondary.py'
runner_template_temp_dir = f'{xfaas_working_directory}/python/src/runner-templates/azure'


def build_working_dir(location, part_id):
    global az_functions_path
    a, user_workflow_name = get_user_workflow_details()
    az_functions_path=f"{build_dir}/{user_workflow_name}"
    if not os.path.exists(az_functions_path):
        os.makedirs(az_functions_path)

def get_user_workflow_details():
    json_path = user_workflow_directory + '/' + user_dag_file_name
    data = json.load(open(json_path))
    fns_data = data['Nodes']
    return fns_data,data['WorkflowName']


def build_user_fn_dirs(user_fns_data):
    for fn in user_fns_data:
        name = fn['NodeName']
        dir_path = az_functions_path+'/'+name
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def remove(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"File '{path}' has been removed.")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Folder '{path}' and its contents have been removed.")
        else:
            print(f"'{path}' is not a valid file or folder.")
    except Exception as e:
        print(f"An error occurred: {e}")


def populate_orchestrator():

    stream = os.popen(f"python3 {orchestrator_generator_path} {user_workflow_directory} {user_dag_file_name} {TEMP_TRIGGER}")

    stream.close()
    orchestrator_generated_path = f"{user_workflow_directory}/orchestrator.py"
    orch_dest_path = f"{orchestrator_path}/__init__.py"
    shutil.copyfile(orchestrator_generated_path , orch_dest_path)


def generate_function_json_for_queue_trigger(ingress_queue_name):
    dict = {'scriptFile': '__init__.py', 'bindings': [{'name': 'msg', 'type': 'queueTrigger', 'direction': 'in', 'connection': 'AzureWebJobsStorage'},{"name": "starter","type": "durableClient","direction": "in"}]}
    dict['bindings'][0]['queueName'] = ingress_queue_name
    path = f'{queue_trigger_path}/function.json'
    with open(path, 'w') as f:
        json.dump(dict, f)

def template_queue_trigger(user_app_name):
    queue_function_path = f'{queue_trigger_path}'
    queue_function_name = 'queue_runner_template.py'

    # load jinja2 environment
    try:
        file_loader = FileSystemLoader(queue_function_path)
        env = Environment(loader=file_loader)
        template = env.get_template(queue_function_name)
    except Exception as e:
        print(e)
        print("Error in creating Jinja2 Environment for queue trigger")
    # render
    try:
        output = template.render(app_placeholder=user_app_name)
    except Exception as e:
        print(e)
        print("Error in rendering queue trigger function")
    # flush
    try:
        with open(f"{queue_function_path}/__init__.py", "w") as out:
            out.write(output)
    except Exception as e:
        print(e)
        print("Error in flushing queue trigger function")



def copy_meta_files(user_fns_data,ingress_queue_name,user_app_name):
    shutil.copyfile(host_json_path,az_functions_path+'/host.json')
    shutil.copyfile(local_settings_path,az_functions_path+'/local.settings.json')
    for fn in user_fns_data:
        name = fn['NodeName']
        dir_path = az_functions_path+'/'+name
        shutil.copyfile(function_json,dir_path+'/function.json')

        obj_dir = dir_path+'/' + obj_dir_str
        if not os.path.exists(obj_dir):
            os.makedirs(obj_dir)
        shutil.copyfile(serwo_object,obj_dir+'/serwo_objects.py')

    path = az_functions_path+'/Starter'
    if not os.path.exists(path):
        os.mkdir(path)
    copytree(starter_path , path)


    populate_orchestrator()

    path = az_functions_path+'/Orchestrate'
    if not os.path.exists(path):
        os.mkdir(path)
    copytree(orchestrator_path , path)

    path = az_functions_path+'/QueueTrigger'
    generate_function_json_for_queue_trigger(ingress_queue_name)
    if not os.path.exists(path):
        os.mkdir(path)
    template_queue_trigger(user_app_name)
    copytree(queue_trigger_path , path)

    shutil.copyfile(resources_json,f'{az_functions_path}/QueueTrigger/azure_resources.json')


def gen_requirements(user_fns_data):
    req_file = open(az_functions_path+'/requirements.txt', "w")
    libs = set()
    for fn in user_fns_data:
        req_path = f'{xfaas_working_directory}/' + fn['Path'] + '/requirements.txt'
        if os.path.exists(req_path):
            content = open(req_path).readlines()
            for line in content:
                libs.add(line)

    libs.add('azure-functions')
    libs.add('azure-functions-durable')
    libs.add('azure-storage-queue==2.1.0')
    libs.add('psutil')
    for lib in libs:
        req_file.write(str(lib)+'\n')

    req_file.close()


def generate_function_id(f_id):
    output_dir = runner_template_file_secondary
    try:
        file_loader = FileSystemLoader(runner_template_temp_dir)
        env = Environment(loader=file_loader)
        template = env.get_template("runner_template.py")
    except Exception as exception:
        raise Exception("Error in loading jinja template environment")

    # render function
    try:
        output = template.render(func_id_placeholder=f_id)
    except Exception as exception:
        raise Exception("Error in jinja template render function")

    try:
        # flush out the generator yaml
        with open(f"{output_dir}", "w+") as runner:
            runner.write(output)

    except Exception as exception:
        raise Exception("Error in writing to template file")


def copy_all_dirs(fn_dir_path,fin_func_dir):

    dirs = os.listdir(fn_dir_path)

    for dir in dirs:
        if '__pycache__' in dir or 'dependencies' in dir or 'requirements.txt' in dir:
            continue
        if 'fused' in fn_dir_path:
            if '.py' in dir and 'Collect' not in fn_dir_path:
                str_find = 'from '
                str_replace = 'from .'
                path = f'{fn_dir_path}/{dir}'
                fr.f_and_r(path,f'{fin_func_dir}/func.py',str_find,str_replace)

        if '.py' not in dir:
            if not os.path.exists(fin_func_dir+'/'+dir):
                shutil.copytree(fn_dir_path+'/'+dir,fin_func_dir+'/'+dir,False,None)
            in_dir = os.listdir(fin_func_dir+'/'+dir)

            obj_dir = fin_func_dir+'/'+dir+'/' + obj_dir_str
            if not os.path.exists(obj_dir):
                os.makedirs(obj_dir)
            shutil.copyfile(serwo_object,obj_dir+'/serwo_objects.py')
            for f in in_dir:
                if '.py' in f:
                    print('-----',f)
                    str_find = 'from python.src.utils.classes.commons.serwo_objects import'
                    str_replace = 'from .python.src.utils.classes.commons.serwo_objects import'
                    path = fin_func_dir+'/'+dir+'/'+f
                    fr.f_and_r(path,fin_func_dir+'/'+dir+'/'+f,str_find,str_replace)


        else:
            if 'fused' not in fn_dir_path:
                shutil.copyfile(fn_dir_path+'/'+dir,fin_func_dir+'/'+dir)
                str_find = 'from python.src.utils.classes.commons.serwo_objects import'
                str_replace = 'from .python.src.utils.classes.commons.serwo_objects import'
                path = fin_func_dir+'/'+dir
                fr.f_and_r(path,fin_func_dir+'/'+dir,str_find,str_replace)


def push_user_dag_to_provenance(wf_id):
    global dynPartiQLWrapper, e
    # convert this to an api call
    print(":" * 80)
    print(f"Pushing workflow configuration to Dynamo DB")
    try:
        # print(f"{USER_DIR}/{DAG_DEFINITION_FILE}")
        f = user_workflow_directory + '/' + DAG_DEFINITION_FILE
        js = open(f,'r').read()
        user_workflow_item = json.loads(js)

        user_workflow_item['wf_id'] = wf_id


        dynPartiQLWrapper = PartiQLWrapper('workflow_user_table')
        dynPartiQLWrapper.put(user_workflow_item)
    except ClientError as e:
        print(e)
    print(":" * 80)

def re_written_generator(user_fns_data):
    for fn in user_fns_data:
        fin_func_dir = az_functions_path+'/'+fn['NodeName']

        fn_dir_pat = f'{xfaas_working_directory}/' + fn['Path']
        copy_all_dirs(fn_dir_pat,fin_func_dir)

        if os.path.exists(fn_dir_pat+'/dependencies'):
            copytree(fn_dir_pat+'/dependencies' , fin_func_dir+'/dependencies')

        path = runner_template_temp_dir + '/' + fn['NodeName']
        if not os.path.exists(path):
            os.mkdir(path)
        copytree(fn_dir_pat , path)
        stream = os.popen(f"rm {path}/requirements.txt")
        stream.close()

        az_func_dir = az_functions_path+'/'+fn['NodeName']
        fn_path = f"{path}/{fn['EntryPoint']}"

        '''
        NOTE - explicit typecast to integer
        '''
        generate_function_id(int(fn['NodeId']))
        str_find = 'USER_FUNCTION_PLACEHOLDER'
        str_replace = fn['EntryPoint'][0:-3]
        pathh = runner_template_file_secondary

        tmp_runner_path = runner_template_temp_dir + '/'+fn['NodeName']+ '/runner.py'
        fr.f_and_r(pathh,tmp_runner_path,str_find,str_replace)
        shutil.copyfile(tmp_runner_path,f'{path}/__init__.py')

        str_find = 'from python.src.utils.classes.commons.serwo_objects import'
        str_replace = 'from .python.src.utils.classes.commons.serwo_objects import'

        pathh = f"{path}/__init__.py"
        fr.f_and_r(pathh,path+'/__init__.py',str_find,str_replace)

        fin_func_path = az_functions_path+'/'+fn['NodeName']+'/__init__.py'
        shutil.copyfile(path+'/__init__.py' , fin_func_path)

        stream = os.popen(f"rm -r {path}")
        stream.close()

        stream = os.popen(f"rm {runner_template_file_secondary}")
        stream.close()


def generate_app_name_and_populate_and_get_ingress_queue_name(user_app_name):
    xd = randint(100000, 999999)
    app_name = f'serwo{user_app_name}{xd}'
    f = open(resources_json,'r')
    data = json.loads(f.read())
    if 'app_name' not in data:
        data['app_name'] = app_name
    data['user_dir'] = az_functions_path
    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
    with open(resources_json, 'w') as f:
        json.dump(data, f)
    return data['queue_name'],data['app_name']

def add_collect_logs():
    return

def push_refactored_user_dag_to_provenance(wf_id,refactored_wf_id):
    path = user_workflow_directory + '/' + DAG_DEFINITION_FILE
    js = json.loads(open(path,'r').read())
    dc = 'azure'
    lp = []
    for nd in js['Nodes']:
        lp.append(nd['NodeId'])

    fin_parts = [{'partition_label':dc,'function_ids':lp}]
    js['wf_partitions'] = fin_parts
    js['wf_fusion_config'] = ''
    js['refactoring_strategy'] = 'Azure only'
    js['wf_id'] = wf_id
    js['refactored_wf_id'] =refactored_wf_id


def run(location,part_id):
    build_working_dir(location,part_id)


if __name__ == '__main__':
    print(xfaas_working_directory)
    # build_working_dir()
    # user_fns_data,user_app_name = get_user_workflow_details()
    # ingress_queue_name,app_name = generate_app_name_and_populate_and_get_ingress_queue_name(user_app_name)
    # build_user_fn_dirs(user_fns_data)
    # copy_meta_files(user_fns_data,ingress_queue_name,app_name)
    # gen_requirements(user_fns_data)
    # re_written_generator(user_fns_data)