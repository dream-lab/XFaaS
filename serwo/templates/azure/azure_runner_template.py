
import logging
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList
from python.src.utils.classes.commons.serwo_objects import build_serwo_object
from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object
import json
import time
import os
import uuid
import psutil
import azure.functions as az_func
from .USER_FUNCTION_PLACEHOLDER import function as USER_FUNCTION_PLACEHOLDER_function
from azure.storage.queue import (
    QueueService,
    QueueMessageFormat
)


connect_str_provenance = 'DefaultEndpointsProtocol=https;AccountName=serwoprovenance;AccountKey=BaGZeTpyeEnO+9yd29yApEjFyzY1b4nR+3bW+mz8sJsSlBs3P29Gg8JzN4I0Lga12oefKWHI4pk3+AStD8AooA==;EndpointSuffix=core.windows.net'
queue_name_provenance = 'serwo-provenance-queue'
queue_service_provenance = QueueService(connection_string=connect_str_provenance)
queue_service_provenance.encode_function = QueueMessageFormat.binary_base64encode
queue_service_provenance.decode_function = QueueMessageFormat.binary_base64decode

# connect_str = 'DefaultEndpointsProtocol=https;AccountName=serwoprovenance;AccountKey=BaGZeTpyeEnO+9yd29yApEjFyzY1b4nR+3bW+mz8sJsSlBs3P29Gg8JzN4I0Lga12oefKWHI4pk3+AStD8AooA==;EndpointSuffix=core.windows.net'
# queue_name = 'serwo-provenance-queue'
# queue_service = QueueService(connection_string=connect_str)
# queue_service.encode_function = QueueMessageFormat.binary_base64encode
# queue_service.decode_function = QueueMessageFormat.binary_base64decode


function_id = {{func_id_placeholder}}


def get_delta(start_time):
    curr_time = int(time.time() * 1000)
    return (curr_time-start_time)



def push_metadata_to_provenance(metadata):
    try:
        queue_service_provenance.put_message(queue_name_provenance, json.dumps(metadata).encode('utf-8'))
    except Exception as e:
        logging.info(f'Exception in pushing metadata: {e}')

# def push_metadata_to_provenance(metadata):
#     try:
#         queue_service.put_message(queue_name, json.dumps(metadata).encode('utf-8'))
#     except Exception as e:
#         logging.info(f'Exception in pushing metadata: {e}')


def main(serwoObject, context: az_func.Context) -> str:
    try:
        basepath = f"{str(context.function_directory)}/"
        if isinstance(serwoObject, list):
            serwo_list_object = SerWOObjectsList()
            start_delta = 0
            meta_dict = dict()
            extracted = []
            for res in serwoObject:
                serwo_object_res = unmarshall(json.loads(res))
                serwo_list_object.add_object(serwo_object_res.get_body())
                metadata = serwo_object_res.get_metadata()
                if start_delta == 0:
                    start_delta = get_delta(metadata['workflow_start_time'])
                metadata = serwo_object_res.get_metadata()
                for key in metadata:
                    if '-' in key:
                        extracted.append( (key,metadata[key]))
                meta_list = metadata['functions']
                for data in meta_list:
                    for key in data:
                        meta_dict[key] = data[key]
            workflow_instance_id = metadata['workflow_instance_id']
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            logging.info(f'Memory Before Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}')
            serwo_list_object.set_basepath(basepath=basepath)
            serwoObjectResponse = USER_FUNCTION_PLACEHOLDER_function(serwo_list_object)
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            logging.info(f'Memory After Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}')
            func_id = function_id
            end_delta = get_delta(metadata['workflow_start_time'])
            new_meta = []
            for key in meta_dict:
                new_meta.append({key : meta_dict[key]})
            func_json = {func_id : {'start_delta' : start_delta,'end_delta' : end_delta}}
            new_meta.append(func_json)
            metadata['functions'] = new_meta
            # metadata[str(func_id)+'_fan_in'] = extracted
            # trace_containers(metadata)
            body = serwoObjectResponse.get_body()
            return SerWOObject(body=body , metadata=metadata).to_json()
        else:
            serwoObject = unmarshall(json.loads(serwoObject))
            metadata = serwoObject.get_metadata()
            # trace_containers(metadata)
            start_delta = get_delta(metadata['workflow_start_time'])
            workflow_instance_id = metadata['workflow_instance_id']
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            logging.info(f'Memory Before Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}')
            serwoObject.set_basepath(basepath=basepath)
            serwoObjectResponse = USER_FUNCTION_PLACEHOLDER_function(serwoObject)
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            logging.info(f'Memory After Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}')
            func_id = function_id
            end_delta = get_delta(metadata['workflow_start_time'])
            func_json = {func_id : {'start_delta' : start_delta,'end_delta' : end_delta}}
            metadata['functions'].append(func_json)
            metadata = metadata
            body = serwoObjectResponse.get_body()
            return SerWOObject(body=body,metadata=metadata).to_json()
    except Exception as e:
        logging.info("excep= "+str(e))
        return None
def trace_containers(metadata):
    container_path = '/tmp/serwo/container.txt'
    if not os.path.exists(container_path):
        logging.info('File doesnt exist, generating....')
        os.mkdir('/tmp/serwo')
        f = open(container_path, 'w')
        uuid_gen = str(uuid.uuid4())
        metadata[uuid_gen] = []
        f.write(uuid_gen)
        f.close()
        if uuid_gen in metadata:
            metadata[uuid_gen].append({'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': function_id})
        else:
            metadata[uuid_gen] = []
            metadata[uuid_gen].append({'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': function_id})
    else:
        f = open(container_path, 'r')
        saved_uuid = f.read()
        f.close()
        logging.info('file exists dumping metadata = ' + str(metadata) + ' saved = ' + saved_uuid)
        if saved_uuid in metadata:
            metadata[saved_uuid].append({'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': function_id})
        else:
            metadata[saved_uuid] = []
            metadata[saved_uuid].append({'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': function_id})

def unmarshall(serwoObject):
    inp_dict = dict()
    if '_body' in serwoObject:
        inp_dict['body'] = serwoObject['_body']
    if '_metadata' in serwoObject:
        inp_dict['metadata'] = serwoObject['_metadata']
    if '_err' in serwoObject:
        inp_dict['error'] = serwoObject['_err']
    serwoObject = build_serwo_object(inp_dict)
    return serwoObject