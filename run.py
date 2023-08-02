import sys
import os
import subprocess
import json
import string
import random
import boto3
import botocore.session
from azure.storage.queue import QueueServiceClient

#TODO use argparse

def generate_random_string(N):
    res = ''.join(random.choices(string.ascii_lowercase +
                                string.digits, k=N))
 
    return res


##TODO - move creation of queues to one single place
##TODO - add aws/open faas queue generation for provenance
def generate():
    try:
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};"
        queue_service_client = QueueServiceClient.from_connection_string(connection_string)
        queue_service_client.create_queue(queue_name)

    #TODO -  push queue names to provenance
    except Exception as e:
        print(e)
        pass

from azure.storage.queue import QueueServiceClient

def create_aws_credentials_file():
    print(f":: Creating credentials file for AWS ::")
    session = botocore.session.get_session()
    access_key_id = session.get_credentials().access_key
    secret_access_key = session.get_credentials().secret_key
    credentials = {"access_key_id": access_key_id, "secret_access_key": secret_access_key}

    with open(f"serwo/{user_dir}/aws_credentials.json", "w+") as out:
        out.write(json.dumps(credentials, indent=4))


def set_up():
    stream = os.popen("az group exists --name xfaasQueues")
    xd = bool(stream.read())
    stream.close()
    if xd == True:
        generate()
    else:
       print("Storage Queue Not Found, Run python3 xfaas_env_setup.py")
       exit()

    stream = os.popen(f'az storage account show-connection-string --name {storage_account_name} --resource-group {resource}')
    json_str = json.loads(stream.read())
    stream.close()


    
    out_path = 'serwo/python/src/utils/CollectLogDirectories'
    template_path = 'serwo/python/src/utils/CollectLogDirectories/CollectLogsTemplate/func.py'
    print("Queue connection string here",json_str)
    output_logs_dir = out_path+'/CollectLogs'
    if not os.path.exists(output_logs_dir):
        os.mkdir(output_logs_dir)
    connection_str = json_str['connectionString']
    
    print(queue_name)
    write_output_files(output_logs_dir, connection_str, template_path,queue_name)
    return {
        "queue": queue_name,
        "connectionString": connection_str
    }

def write_output_files(out_path, connection_str, template_path,queue):
    temp_code = open(template_path, 'r').read()
    find_string = 'CONNECTION_STRING_PLACEHOLDER'
    out = temp_code.replace(find_string, connection_str)
    find_string = 'QUEUE_NAME_PLACEHOLDER'
    outt = out.replace(find_string, queue)
    ou = open(out_path + '/func.py', 'w')
    ou.write(outt)
    ou.close()


#--partition, --fusion, --single-cloud
option = sys.argv[3]
user_dir = sys.argv[1]
user_json = sys.argv[2]

random_string = generate_random_string(N=7)
queue_name = f"xfaas-logging-queue-{random_string}"

location = "centralindia"
resource = "xfaasQueues"
storage_account_name = 'xfaasstorage'

queue_details = set_up()

# create credentials file for aws
create_aws_credentials_file()


if option == '--partition':
    if len(sys.argv)>4 and sys.argv[4]=='--fusion':
        print('OPERATION NOT YET SUPPORTED, STAY TUNED!')
        exit()
    os.chdir('serwo')
    with open(f"{user_dir}/queue_details.json", "w+") as f:
        f.write(json.dumps(queue_details, indent=4))
    subprocess.call(['python3','serwo_create_multicloud_statemachine.py',user_dir,user_json])
    # stream = os.popen(f"python3 serwo_create_multicloud_statemachine.py {user_dir} {user_json}")
    # stream.close()

elif option == '--single-cloud':
    csp = sys.argv[4]
    os.chdir('serwo')
    with open(f"{user_dir}/queue_details.json", "w+") as f:
        f.write(json.dumps(queue_details, indent=4))
    ##TODO Function call
    ##TODO (handling of imports)
    ##TODO serwo -> xfaas

    subprocess.call(['python3','serwo_single_cloud.py',user_dir,user_json,csp])
    # save to file

    # stream = os.popen(f"python3 serwo_single_cloud.py {user_dir} {user_json} {csp}")
    # stream.close()

elif option == '--fusion':
    csp = sys.argv[4]
    os.chdir('serwo')
    if csp == 'aws':
        fuse_csp_call = 'AWS'
    elif csp =='azure':
        fuse_csp_call = 'Azure'
    with open(f"{user_dir}/queue_details.json", "w+") as f:
        f.write(json.dumps(queue_details, indent=4))
    subprocess.call(['python3','serwo_function_fuse.py',user_dir,user_json,fuse_csp_call])

else:
    print('INVALID INPUT')

credentials_filepath = f"{user_dir}/aws_credentials.json"
if os.path.exists(credentials_filepath):
    print("::Deleting AWS Credentials file::")
    os.system(f"rm -r {credentials_filepath}")
