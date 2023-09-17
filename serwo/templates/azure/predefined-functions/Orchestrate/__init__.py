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
    function_id = 0
    container_path = "/tmp/serwo/container.txt"
    if not os.path.exists(container_path):
        os.mkdir("/tmp/serwo")
        f = open(container_path, "w")
        uuid_gen = str(uuid.uuid4())
        metadata[uuid_gen] = {}
        f.write(uuid_gen)
        f.close()
        if uuid_gen in metadata:
            uuid_map = metadata[uuid_gen]
            workflow_instance_id = str(metadata["workflow_instance_id"])
            if workflow_instance_id in uuid_map:
                metadata[uuid_gen][workflow_instance_id].append(function_id)
            else:
                metadata[uuid_gen][workflow_instance_id] = []
                metadata[uuid_gen][workflow_instance_id].append(function_id)
        else:
            metadata[uuid_gen] = {}
            workflow_instance_id = str(metadata["workflow_instance_id"])

            metadata[uuid_gen][workflow_instance_id] = []
            metadata[uuid_gen][workflow_instance_id].append(function_id)
    else:
        f = open(container_path, "r")
        saved_uuid = f.read()
        f.close()
        if saved_uuid in metadata:
            workflow_instance_id = metadata["workflow_instance_id"]
            if workflow_instance_id in metadata[saved_uuid]:
                metadata[saved_uuid][workflow_instance_id].append(function_id)
            else:
                metadata[saved_uuid][workflow_instance_id] = []
                metadata[saved_uuid][workflow_instance_id].append(function_id)
        else:

            metadata[saved_uuid] = {}
            workflow_instance_id = metadata["workflow_instance_id"]
            metadata[saved_uuid][workflow_instance_id] = []
            metadata[saved_uuid][workflow_instance_id].append(function_id)


def get_delta(start_time):
    curr_time = int(time.time() * 1000)
    return curr_time - start_time


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


def insert_end_stats_in_metadata(input):
    serwoObjectJson = json.loads(input)
    serwoObjectJson = unmarshall(serwoObjectJson)
    metadata = serwoObjectJson.get_metadata()
    end_delta = get_delta(metadata["workflow_start_time"])
    meta_list = metadata["functions"]
    ne_list = []
    for meta in meta_list:
        start_delta_local = 0
        end_delta_local = 0
        func_id_local = 0
        mem_before = 0
        mem_after = 0
        body_size_before = 0
        body_size_after = 0
        cid = ''
        for fid in meta:
            func_id_local = fid
            start_delta_local = meta[fid]["start_delta"]
            end_delta_local = meta[fid]["end_delta"]
            if "mem_before" in meta[fid]:
                mem_before = meta[fid]["mem_before"]
                mem_after = meta[fid]["mem_after"]
                body_size_before = meta[fid]["in_payload_bytes"]
                body_size_after = meta[fid]["out_payload_bytes"]
                cid = meta[fid]["cid"]
            if fid == "0":
                end_delta_local = end_delta
        func_json = {
            func_id_local: {
                "start_delta": start_delta_local,
                "end_delta": end_delta_local,
                "mem_before": mem_before,
                "mem_after": mem_after,
                "in_payload_bytes": body_size_before,
                "out_payload_bytes": body_size_after,
                "cid": cid
            }
        }
        ne_list.append(func_json)
    body = serwoObjectJson.get_body()
    out_dict = dict()
    out_dict["body"] = body
    metadata["functions"] = ne_list
    out_dict["metadata"] = metadata
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

    if "workflow_start_time" not in metadata:
        metadata["workflow_start_time"] = curr_time
    if "overheads" not in metadata:
        metadata["overheads"] = curr_time - request_timestamp
    if "request_timestamp" not in metadata:
        metadata["request_timestamp"] = request_timestamp
    func_id = 255

    start_delta = get_delta(metadata["workflow_start_time"])
    process = psutil.Process(os.getpid())
    memory = process.memory_info().rss
    metadata["init_orch_memory"] = memory
    end_delta = get_delta(metadata["workflow_start_time"])
    func_json = {func_id: {"start_delta": start_delta, "end_delta": end_delta}}
    metadata["functions"].append(func_json)
    inp_dict["metadata"] = metadata

    serwoObject = build_serwo_object(inp_dict).to_json()
    # user dag execution
    ubcs = yield context.call_activity("Source", serwoObject)
    tpss = []
    pdwm = context.call_activity("Branch0", ubcs)
    zund = context.call_activity("Branch1", ubcs)
    vxoh = context.call_activity("Branch2", ubcs)
    umqf = context.call_activity("Branch3", ubcs)
    ajkf = context.call_activity("Branch4", ubcs)
    bzac = context.call_activity("Branch5", ubcs)
    yhzj = context.call_activity("Branch6", ubcs)
    nwag = context.call_activity("Branch7", ubcs)
    qith = context.call_activity("Branch8", ubcs)
    ausw = context.call_activity("Branch9", ubcs)
    qchy = context.call_activity("Branch10", ubcs)
    innf = context.call_activity("Branch11", ubcs)
    sstf = context.call_activity("Branch12", ubcs)
    ynpo = context.call_activity("Branch13", ubcs)
    gpsc = context.call_activity("Branch14", ubcs)
    ruqm = context.call_activity("Branch15", ubcs)
    guit = context.call_activity("Branch16", ubcs)
    ovjg = context.call_activity("Branch17", ubcs)
    nwzh = context.call_activity("Branch18", ubcs)
    bxpr = context.call_activity("Branch19", ubcs)
    mjpi = context.call_activity("Branch20", ubcs)
    nuht = context.call_activity("Branch21", ubcs)
    xgey = context.call_activity("Branch22", ubcs)
    tbjj = context.call_activity("Branch23", ubcs)
    wssj = context.call_activity("Branch24", ubcs)
    hccq = context.call_activity("Branch25", ubcs)
    abme = context.call_activity("Branch26", ubcs)
    osul = context.call_activity("Branch27", ubcs)
    kaxc = context.call_activity("Branch28", ubcs)
    uhjb = context.call_activity("Branch29", ubcs)
    tygp = context.call_activity("Branch30", ubcs)
    gzvv = context.call_activity("Branch31", ubcs)
    yipc = context.call_activity("Branch32", ubcs)
    nxse = context.call_activity("Branch33", ubcs)
    vgdl = context.call_activity("Branch34", ubcs)
    fwye = context.call_activity("Branch35", ubcs)
    ndoy = context.call_activity("Branch36", ubcs)
    xfzw = context.call_activity("Branch37", ubcs)
    lhbn = context.call_activity("Branch38", ubcs)
    uemt = context.call_activity("Branch39", ubcs)
    mdss = context.call_activity("Branch40", ubcs)
    lfup = context.call_activity("Branch41", ubcs)
    rmmy = context.call_activity("Branch42", ubcs)
    wfsi = context.call_activity("Branch43", ubcs)
    mbbz = context.call_activity("Branch44", ubcs)
    gbdx = context.call_activity("Branch45", ubcs)
    baxv = context.call_activity("Branch46", ubcs)
    ctpw = context.call_activity("Branch47", ubcs)
    tgyz = context.call_activity("Branch48", ubcs)
    ydai = context.call_activity("Branch49", ubcs)
    ihiv = context.call_activity("Branch50", ubcs)
    pynm = context.call_activity("Branch51", ubcs)
    ucgx = context.call_activity("Branch52", ubcs)
    ooaa = context.call_activity("Branch53", ubcs)
    qxhj = context.call_activity("Branch54", ubcs)
    lgid = context.call_activity("Branch55", ubcs)
    cmkr = context.call_activity("Branch56", ubcs)
    xzfj = context.call_activity("Branch57", ubcs)
    kexb = context.call_activity("Branch58", ubcs)
    ycui = context.call_activity("Branch59", ubcs)
    rlbl = context.call_activity("Branch60", ubcs)
    xlnx = context.call_activity("Branch61", ubcs)
    iszd = context.call_activity("Branch62", ubcs)
    gsdr = context.call_activity("Branch63", ubcs)
    kcyb = context.call_activity("Branch64", ubcs)
    hnzz = context.call_activity("Branch65", ubcs)
    emce = context.call_activity("Branch66", ubcs)
    yers = context.call_activity("Branch67", ubcs)
    leuq = context.call_activity("Branch68", ubcs)
    eyen = context.call_activity("Branch69", ubcs)
    dksk = context.call_activity("Branch70", ubcs)
    rmfl = context.call_activity("Branch71", ubcs)
    fzxz = context.call_activity("Branch72", ubcs)
    zrrr = context.call_activity("Branch73", ubcs)
    hiii = context.call_activity("Branch74", ubcs)
    soer = context.call_activity("Branch75", ubcs)
    jkfv = context.call_activity("Branch76", ubcs)
    muwb = context.call_activity("Branch77", ubcs)
    rfkt = context.call_activity("Branch78", ubcs)
    nqff = context.call_activity("Branch79", ubcs)
    wjcf = context.call_activity("Branch80", ubcs)
    vxrx = context.call_activity("Branch81", ubcs)
    fztu = context.call_activity("Branch82", ubcs)
    vmzh = context.call_activity("Branch83", ubcs)
    gdpj = context.call_activity("Branch84", ubcs)
    papf = context.call_activity("Branch85", ubcs)
    deac = context.call_activity("Branch86", ubcs)
    xjed = context.call_activity("Branch87", ubcs)
    mcdv = context.call_activity("Branch88", ubcs)
    njgc = context.call_activity("Branch89", ubcs)
    gnyx = context.call_activity("Branch90", ubcs)
    plyu = context.call_activity("Branch91", ubcs)
    qrhl = context.call_activity("Branch92", ubcs)
    txmy = context.call_activity("Branch93", ubcs)
    tprc = context.call_activity("Branch94", ubcs)
    jxld = context.call_activity("Branch95", ubcs)
    noaw = context.call_activity("Branch96", ubcs)
    inbs = context.call_activity("Branch97", ubcs)
    sukx = context.call_activity("Branch98", ubcs)
    uwkz = context.call_activity("Branch99", ubcs)
    tpss.append(pdwm)
    tpss.append(zund)
    tpss.append(vxoh)
    tpss.append(umqf)
    tpss.append(ajkf)
    tpss.append(bzac)
    tpss.append(yhzj)
    tpss.append(nwag)
    tpss.append(qith)
    tpss.append(ausw)
    tpss.append(qchy)
    tpss.append(innf)
    tpss.append(sstf)
    tpss.append(ynpo)
    tpss.append(gpsc)
    tpss.append(ruqm)
    tpss.append(guit)
    tpss.append(ovjg)
    tpss.append(nwzh)
    tpss.append(bxpr)
    tpss.append(mjpi)
    tpss.append(nuht)
    tpss.append(xgey)
    tpss.append(tbjj)
    tpss.append(wssj)
    tpss.append(hccq)
    tpss.append(abme)
    tpss.append(osul)
    tpss.append(kaxc)
    tpss.append(uhjb)
    tpss.append(tygp)
    tpss.append(gzvv)
    tpss.append(yipc)
    tpss.append(nxse)
    tpss.append(vgdl)
    tpss.append(fwye)
    tpss.append(ndoy)
    tpss.append(xfzw)
    tpss.append(lhbn)
    tpss.append(uemt)
    tpss.append(mdss)
    tpss.append(lfup)
    tpss.append(rmmy)
    tpss.append(wfsi)
    tpss.append(mbbz)
    tpss.append(gbdx)
    tpss.append(baxv)
    tpss.append(ctpw)
    tpss.append(tgyz)
    tpss.append(ydai)
    tpss.append(ihiv)
    tpss.append(pynm)
    tpss.append(ucgx)
    tpss.append(ooaa)
    tpss.append(qxhj)
    tpss.append(lgid)
    tpss.append(cmkr)
    tpss.append(xzfj)
    tpss.append(kexb)
    tpss.append(ycui)
    tpss.append(rlbl)
    tpss.append(xlnx)
    tpss.append(iszd)
    tpss.append(gsdr)
    tpss.append(kcyb)
    tpss.append(hnzz)
    tpss.append(emce)
    tpss.append(yers)
    tpss.append(leuq)
    tpss.append(eyen)
    tpss.append(dksk)
    tpss.append(rmfl)
    tpss.append(fzxz)
    tpss.append(zrrr)
    tpss.append(hiii)
    tpss.append(soer)
    tpss.append(jkfv)
    tpss.append(muwb)
    tpss.append(rfkt)
    tpss.append(nqff)
    tpss.append(wjcf)
    tpss.append(vxrx)
    tpss.append(fztu)
    tpss.append(vmzh)
    tpss.append(gdpj)
    tpss.append(papf)
    tpss.append(deac)
    tpss.append(xjed)
    tpss.append(mcdv)
    tpss.append(njgc)
    tpss.append(gnyx)
    tpss.append(plyu)
    tpss.append(qrhl)
    tpss.append(txmy)
    tpss.append(tprc)
    tpss.append(jxld)
    tpss.append(noaw)
    tpss.append(inbs)
    tpss.append(sukx)
    tpss.append(uwkz)
    sdec = yield context.task_all(tpss)
    pzob = yield context.call_activity("Sink", sdec)
    pzob = insert_end_stats_in_metadata(pzob)
    cbqh = yield context.call_activity("CollectLogs", pzob)
    return cbqh


main = df.Orchestrator.create(orchestrator_function)
