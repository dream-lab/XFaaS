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
from .USER_FUNCTION_PLACEHOLDER import user_function as USER_FUNCTION_PLACEHOLDER_function
import cpuinfo
import sys
import objsize
import random
import string



# connect_str = 'DefaultEndpointsProtocol=https;AccountName=serwoprovenance;AccountKey=BaGZeTpyeEnO+9yd29yApEjFyzY1b4nR+3bW+mz8sJsSlBs3P29Gg8JzN4I0Lga12oefKWHI4pk3+AStD8AooA==;EndpointSuffix=core.windows.net'
# queue_name = 'serwo-provenance-queue'
# queue_service = QueueService(connection_string=connect_str)
# queue_service.encode_function = QueueMessageFormat.binary_base64encode
# queue_service.decode_function = QueueMessageFormat.binary_base64decode


function_id = {{func_id_placeholder}}


def generate_random_string(N):
    res = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase +
                                string.digits, k=N))
 
    return res

def get_delta(start_time):
    curr_time = int(time.time() * 1000)
    return curr_time - start_time



# def push_metadata_to_provenance(metadata):
#     try:
#         queue_service.put_message(queue_name, json.dumps(metadata).encode('utf-8'))
#     except Exception as e:
#         logging.info(f'Exception in pushing metadata: {e}')


def union(list1, list2):
    return list(set(list1) | set(list2))

def merge_containers_logs(metadata_list, metadata):
    workflow_instance_id = str(metadata["workflow_instance_id"])
    god_dict = dict()
    for meta in metadata_list:
        for key in meta:
            if "-" in key and workflow_instance_id in meta[key]:
                if key in god_dict:
                    god_dict[key] = union(meta[key][workflow_instance_id], god_dict[key])
                else:
                    god_dict[key] = meta[key][workflow_instance_id]
    
    for meta in metadata_list:
        for key in meta:
            if "-" in key and workflow_instance_id in meta[key]:
                metadata[key][workflow_instance_id] = god_dict[key]
    
    



def main(serwoObject, context: az_func.Context) -> str:
    try:
        basepath = f"{str(context.function_directory)}/"
        if isinstance(serwoObject, list):
            serwo_list_object = SerWOObjectsList()
            start_delta = 0
            meta_dict = dict()
            extracted = []
            input_body_size = 0
            metadata_list = []
            for res in serwoObject:
                serwo_object_res = unmarshall(json.loads(res))
                input_body_size += objsize.get_deep_size(serwo_object_res.get_body())
                serwo_list_object.add_object(serwo_object_res.get_body())
                metadata = serwo_object_res.get_metadata()
                if start_delta == 0:
                    start_delta = get_delta(metadata["workflow_start_time"])
                metadata = serwo_object_res.get_metadata()
                metadata_list.append(metadata)
                for key in metadata:
                    if "-" in key:
                        extracted.append((key, metadata[key]))
                meta_list = metadata["functions"]
                for data in meta_list:
                    for key in data:
                        meta_dict[key] = data[key]

            
            workflow_instance_id = metadata["workflow_instance_id"]
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            memory_before = memory
            logging.info(
                f"Memory Before Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}"
            )
            serwo_list_object.set_basepath(basepath=basepath)

            serwoObjectResponse = USER_FUNCTION_PLACEHOLDER_function(serwo_list_object)
            body_after = serwoObjectResponse.get_body()
            output_body_size = objsize.get_deep_size(body_after)
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            logging.info(
                f"Memory After Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}"
            )
            # cpu_brand = cpuinfo.get_cpu_info()["brand_raw"]
            memory_after = memory
            func_id = function_id
            end_delta = get_delta(metadata["workflow_start_time"])
            new_meta = []
            for key in meta_dict:
                new_meta.append({key: meta_dict[key]})
            container_directory = f'/tmp/xfaas'
            
            container_id = fetch_or_make_container_id(container_directory)
            func_json = {func_id: {"start_delta": start_delta, "end_delta": end_delta, "mem_before" : memory_before,  "mem_after" : memory_after, "in_payload_bytes" : input_body_size, "out_payload_bytes" : output_body_size,"cid":container_id}}
            new_meta.append(func_json)
            metadata["functions"] = new_meta
            

            body = serwoObjectResponse.get_body()
            return SerWOObject(body=body, metadata=metadata).to_json()
        else:
            serwoObject = unmarshall(json.loads(serwoObject))
            metadata = serwoObject.get_metadata()
            container_directory = f'/tmp/xfaas'
            
            container_id = fetch_or_make_container_id(container_directory)


            
            
            start_delta = get_delta(metadata["workflow_start_time"])
            workflow_instance_id = metadata["workflow_instance_id"]
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            memory_before = memory
            logging.info(
                f"Memory Before Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}"
            )
            serwoObject.set_basepath(basepath=basepath)
            body_before = serwoObject.get_body()
            input_body_size = objsize.get_deep_size(body_before)
            serwoObjectResponse = USER_FUNCTION_PLACEHOLDER_function(serwoObject)
            body_after = serwoObjectResponse.get_body()
            output_body_size = objsize.get_deep_size(body_after)
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss
            logging.info(
                f"Memory After Function Call: fid: {function_id}, wf_instance_id: {workflow_instance_id}, memory:{memory}"
            )
            memory_after = memory
            func_id = function_id
            end_delta = get_delta(metadata["workflow_start_time"])
            # cpu_brand = cpuinfo.get_cpu_info()["brand_raw"]
            func_json = {func_id: {"start_delta": start_delta, "end_delta": end_delta, "mem_before" : memory_before,  "mem_after" : memory_after , "in_payload_bytes" : input_body_size, "out_payload_bytes" : output_body_size,"cid": container_id}}
            metadata["functions"].append(func_json)
            metadata = metadata
            body = serwoObjectResponse.get_body()
            return SerWOObject(body=body, metadata=metadata).to_json()
    except Exception as e:
        logging.info("excep= " + str(e))
        return None

def fetch_or_make_container_id(container_directory):
    if os.path.exists(container_directory):
        files = os.listdir(container_directory)
        for file in files:
                filename = file
        container_id = filename
    else:
        container_id = generate_random_string(3)
        
        # st_time = int(time.time()*1000)
        # cpu_brand = cpuinfo.get_cpu_info()["brand_raw"]
        # en_time = int(time.time()*1000)
        # time_taken = en_time - st_time
        # container_id = f'{container_id}_{cpu_brand}_{time_taken}'
        os.mkdir(container_directory)
        os.mkdir(f'{container_directory}/{container_id}')
        
    return container_id


def trace_containers(metadata):
    container_path = "/tmp/serwo/container.txt"
    if not os.path.exists(container_path):
        os.mkdir("/tmp/serwo")
        f = open(container_path, "w")
        uuid_gen = str(uuid.uuid4())
        # metadata[uuid_gen] = {}
        f.write(uuid_gen)
        f.close()
        # if uuid_gen in metadata:
        #     uuid_map = metadata[uuid_gen]
        #     workflow_instance_id = str(metadata["workflow_instance_id"])
        #     if workflow_instance_id in uuid_map:
        #         metadata[uuid_gen][workflow_instance_id].append(function_id)
        #     else:
        #         metadata[uuid_gen][workflow_instance_id] = []
        #         metadata[uuid_gen][workflow_instance_id].append(function_id)
        # else:
        #     metadata[uuid_gen] = {}
        #     workflow_instance_id = str(metadata["workflow_instance_id"])

        #     metadata[uuid_gen][workflow_instance_id] = []
        #     metadata[uuid_gen][workflow_instance_id].append(function_id)
    else: 
        f = open(container_path, "r")
        saved_uuid = f.read()
        f.close()
        # if saved_uuid in metadata:
        #     workflow_instance_id = str(metadata["workflow_instance_id"])
        #     if workflow_instance_id in metadata[saved_uuid]:
        #         metadata[saved_uuid][workflow_instance_id].append(function_id)
        #     else:
        #         metadata[saved_uuid][workflow_instance_id] = []
        #         metadata[saved_uuid][workflow_instance_id].append(function_id)
        # else:

        #     metadata[saved_uuid] = {}
        #     workflow_instance_id = str(metadata["workflow_instance_id"])
        #     metadata[saved_uuid][workflow_instance_id] = []
        #     metadata[uuid_gen][workflow_instance_id].append(function_id)



def unmarshall(serwoObject):
    inp_dict = dict()
    if "_body" in serwoObject:
        inp_dict["body"] = serwoObject["_body"]
    if "_metadata" in serwoObject:
        inp_dict["metadata"] = serwoObject["_metadata"]
    if "_err" in serwoObject:
        inp_dict["error"] = serwoObject["_err"]
    serwoObject = build_serwo_object(inp_dict)
    return serwoObject
