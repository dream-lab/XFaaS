import logging
import json
import azure.functions as func
import azure.durable_functions as df
from .python.src.utils.classes.commons.serwo_objects import build_serwo_object
from .python.src.utils.classes.commons.serwo_objects import SerWOObject
import time
import os
import psutil
import uuid


def trace_containers(metadata):
    container_path = '/tmp/serwo/container.txt'
    if not os.path.exists(container_path):
        logging.info('File doesnt exist, generating....')
        os.mkdir('/tmp/serwo')
        f = open(container_path, 'w')
        uuid_gen = str(uuid.uuid4())
        f.write(uuid_gen)
        f.close()

        if uuid_gen in metadata:
            metadata[uuid_gen].append(
                {'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': 0})
        else:
            metadata[uuid_gen] = []
            metadata[uuid_gen].append(
                {'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': 0})

    else:
        f = open(container_path, 'r')
        saved_uuid = f.read()
        f.close()
        if saved_uuid in metadata:
            metadata[saved_uuid].append(
                {'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': 0})
        else:
            metadata[saved_uuid] = []
            metadata[saved_uuid].append(
                {'workflow_instance_id': metadata['workflow_instance_id'], 'func_id': 0})


def get_delta(start_time):
    curr_time = int(time.time() * 1000)
    return (curr_time-start_time)


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


def insert_end_stats_in_metadata(input):
    serwoObjectJson = json.loads(input)
    serwoObjectJson = unmarshall(serwoObjectJson)
    metadata = serwoObjectJson.get_metadata()
    end_delta = get_delta(metadata['workflow_start_time'])
    meta_list = metadata['functions']
    ne_list = []
    for meta in meta_list:
        start_delta_local = 0
        end_delta_local = 0
        func_id_local = 0
        for fid in meta:
            func_id_local = fid
            start_delta_local = meta[fid]['start_delta']
            end_delta_local = meta[fid]['end_delta']
            if fid == "0":
                end_delta_local = end_delta
        func_json = {func_id_local: {
            'start_delta': start_delta_local, 'end_delta': end_delta_local}}
        ne_list.append(func_json)
    body = serwoObjectJson.get_body()
    out_dict = dict()
    out_dict['body'] = body
    metadata['functions'] = ne_list
    out_dict['metadata'] = metadata
    input = build_serwo_object(out_dict).to_json()
    return input


def orchestrator_function(context: df.DurableOrchestrationContext):
    # convert input body to serwoObject for first function
    curr_time = int(time.time() * 1000)
    context_input = context.get_input()
    inp_dict = dict()
    inp_dict["body"] = context_input["body"]
    metadata = context_input["metadata"]
    request_timestamp = int(metadata["request_timestamp"])

    if 'workflow_start_time' not in metadata:
        metadata['workflow_start_time'] = curr_time
    if 'overheads' not in metadata:
        metadata['overheads'] = curr_time - request_timestamp
    if 'request_timestamp' not in metadata:
        metadata['request_timestamp'] = request_timestamp
    func_id = 255

    # trace_containers(metadata)

    start_delta = get_delta(metadata['workflow_start_time'])
    process = psutil.Process(os.getpid())
    memory = process.memory_info().rss
    metadata['init_orch_memory'] = memory
    end_delta = get_delta(metadata['workflow_start_time'])
    func_json = {func_id: {'start_delta': start_delta, 'end_delta': end_delta}}
    metadata['functions'].append(func_json)
    inp_dict["metadata"] = metadata

    serwoObject = build_serwo_object(inp_dict).to_json()
    # user dag execution
    pwbd = yield context.call_activity("TaskA", serwoObject)
    xvro = yield context.call_activity("TaskB", pwbd)
    bedg = yield context.call_activity("TaskC", xvro)
    itnb = yield context.call_activity("TaskD", bedg)
    cusu = yield context.call_activity("TaskM", itnb)
    dvev = yield context.call_activity("TaskN", cusu)
    rjmd = yield context.call_activity("TaskE", bedg)
    vxci = yield context.call_activity("TaskF", rjmd)
    woqq = yield context.call_activity("TaskI", vxci)
    mzmx = []
    nlxj = context.call_activity("TaskG", vxci)
    wqyw = context.call_activity("TaskH", vxci)
    skqb = context.call_activity("TaskJ", woqq)
    mzmx.append(nlxj)
    mzmx.append(wqyw)
    mzmx.append(skqb)
    ndfg = yield context.task_all(mzmx)
    aivw = []
    vorc = context.call_activity("TaskO", dvev)
    xrzy = context.call_activity("TaskK", ndfg)
    aivw.append(vorc)
    aivw.append(xrzy)
    wusb = yield context.task_all(aivw)
    rtee = yield context.call_activity("TaskL", wusb)
    cazn = yield context.call_activity("TaskP", rtee)
    xizl = yield context.call_activity("TaskQ", cazn)
    xizl = insert_end_stats_in_metadata(xizl)
    zpyq = yield context.call_activity("CollectLogs", xizl)
    return zpyq


main = df.Orchestrator.create(orchestrator_function)
