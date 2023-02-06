import sys
import os
import subprocess
import json

location = "centralindia"
resource = "xfaasQueues"
storage_account_name = 'xfaasstorage'


def generate():
    try:
        stream = os.popen(f"az group create --name {resource} --location {location}")
        stream.close()

        stream = os.popen(f"az storage account create --resource-group {resource} --name {storage_account_name} --location {location}")
        stream.close()

        stream = os.popen(f'az storage queue create -n azure-single-cloud --account-name {storage_account_name}')
        stream.close()

        stream = os.popen(f'az storage queue create -n aws-single-cloud --account-name {storage_account_name}')
        stream.close()

        stream = os.popen(f'az storage queue create -n xfaas-partition --account-name {storage_account_name}')
        stream.close()

        stream = os.popen(f'az storage queue create -n azure-fusion --account-name {storage_account_name}')
        stream.close()

        stream = os.popen(f'az storage queue create -n aws-fusion --account-name {storage_account_name}')
        stream.close()



    except Exception as e:
        pass



def create_logging_queues():
    stream = os.popen("az group exists --name xfaasQueues")
    xd = bool(stream.read())
    stream.close()
    if xd == True:
        pass
    else:
        print('Creating logging queues')


    stream = os.popen(f'az storage account show-connection-string --name {storage_account_name} --resource-group {resource}')
    json_str = json.loads(stream.read())
    stream.close()

    out_path = 'serwo/python/src/utils/CollectLogDirectories'
    template_path = 'serwo/python/src/utils/CollectLogDirectories/CollectLogsTemplate/func.py'
    print(json_str)
    aws_sc = out_path+'/CollectAwsSc'
    azure_sc = out_path+'/CollectAzureSc'
    xfaas_mc = out_path+'/CollectMc'
    aws_fc = out_path+'/CollectAwsFs'
    azure_fc = out_path+'/CollectAzureFs'

    if not os.path.exists(aws_sc):
        os.mkdir(aws_sc)

    if not os.path.exists(azure_sc):
        os.mkdir(azure_sc)

    if not os.path.exists(xfaas_mc):
        os.mkdir(xfaas_mc)

    if not os.path.exists(azure_fc):
        os.mkdir(azure_fc)

    if not os.path.exists(aws_fc):
        os.mkdir(aws_fc)

    connection_str = json_str['connectionString']

    write_output_files(azure_sc, connection_str, template_path,'azure-single-cloud')
    write_output_files(aws_sc, connection_str, template_path,'aws-single-cloud')
    write_output_files(xfaas_mc, connection_str, template_path,'xfaas-partition')
    write_output_files(azure_fc, connection_str, template_path,'azure-fusion')
    write_output_files(aws_fc, connection_str, template_path,'aws-fusion')


def write_output_files(out_path, connection_str, template_path,queue):
    temp_code = open(template_path, 'r').read()
    find_string = 'CONNECTION_STRING_PLACEHOLDER'
    out = temp_code.replace(find_string, connection_str)
    find_string = 'QUEUE_NAME_PLACEHOLDER'
    outt = out.replace(find_string, queue)
    ou = open(out_path + '/func.py', 'w')
    ou.write(outt)
    ou.close()

    ss = 'azure-storage-queue==2.1.0\npsutil'
    oo = open(out_path + '/requirements.txt', 'w')
    oo.write(ss)
    oo.close()


create_logging_queues()