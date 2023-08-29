from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
import json
import uuid
from botocore.exceptions import ClientError
import datetime
import os
import pathlib


def push_user_dag(dag_definition_path):
    print(":" * 80, ' dynamo user_dag push')
    # print(f"Pushing workflow configuration to Dynamo DB")
    workflow_name = ""
    try:
        wf_id = str(uuid.uuid4())
        js = open(dag_definition_path,'r').read()
        user_workflow_item = json.loads(js)
        user_workflow_item['wf_id'] = wf_id
        dynPartiQLWrapper = PartiQLWrapper('workflow_user_table')
        dynPartiQLWrapper.put(user_workflow_item)

    except Exception as e:
        print('here: ',e)

    return wf_id




def push_refactored_workflow(user_dag_file, user_dir, wf_id, csp):
    print(":" * 80, ' dynamo refactored_user_dag push')
    refactored_wf_id = str(uuid.uuid4())
    lpath = f"{user_dir}/{user_dag_file}"

    js_left = json.loads(open(lpath, "r").read())

    lp = []

    for nd in js_left["Nodes"]:
        lp.append(nd["NodeId"])

    js_left["wf_fusion_config"] = ""
    js_left["wf_id"] = wf_id
    js_left["wf_refactored_id"] = refactored_wf_id
    dc = csp

    fin_parts = [{"partition_label": dc, "function_ids": lp}]

    js_left["wf_partitions"] = fin_parts

    js_left["refactoring_strategy"] = "Single Cloud"

    try:
        dynPartiQLWrapper = PartiQLWrapper("workflow_refactored_table")
        dynPartiQLWrapper.put(js_left)
    except ClientError as e:
        print("here",e)

    return refactored_wf_id


def push_deployment_logs(user_dag_file, user_dir, wf_id, refactored_wf_id , csp):
    print(":" * 80, ' dynamo user_dag_deployment push')
    lpath = f"{user_dir}/{user_dag_file}"

    js_left = json.loads(open(lpath, "r").read())

    lp = []

    for nd in js_left["Nodes"]:
        lp.append(nd["NodeId"])
    dc = csp

    d = dict()
    d["wf_id"] = wf_id
    d["wf_refacored_id"] = refactored_wf_id
    d["wf_dc_config"] = {
        "aws": {"region": "ap-south-1", "csp": "AWS"},
        "azure": {"region": "Central India", "csp": "Azure"},
    }
    d["wf_deployment_name"] = "JPDC SMART GRID SINGLE CLOUD"

    workflow_deployment_id = str(uuid.uuid4())
    d["wf_deployment_id"] = workflow_deployment_id
    d["wf_deployment_time"] = str(datetime.datetime.now())

    a = dict()
    for nd in js_left["Nodes"]:
        a[nd["NodeId"]] = {"dc_config_id": dc, "resource_id": "", "endpoint": ""}

    d["func_deployment_config"] = a

    try:
        dynPartiQLWrapper = PartiQLWrapper("workflow_deployment_table")
        dynPartiQLWrapper.put(d)
    except ClientError as e:
        print(e)

    return workflow_deployment_id


def generate_provenance_artifacts(user_dir, wf_id, refactored_wf_id, wf_deployment_id, csp, region, part_id):
    cwd = os.getcwd()

    if "serwo" not in cwd:
        user_dir = f"serwo/{user_dir}"

    resources_dir = pathlib.Path.joinpath(
        pathlib.Path(user_dir), "build/workflow/resources"
    )

    provenance_artifacts = {
        "workflow_id": wf_id,
        "refactored_workflow_id": refactored_wf_id,
        "deployment_id": wf_deployment_id,
    }

    json_output = json.dumps(provenance_artifacts, indent=4)
    with open(
            pathlib.Path.joinpath(resources_dir, f"provenance-artifacts-{csp}-{region}-{part_id}.json"), "w+"
    ) as out:
        out.write(json_output)

    deployment_structure = {"entry_csp": csp}
    deployment_struct_json = json.dumps(deployment_structure, indent=4)
    with open(
            pathlib.Path.joinpath(resources_dir, f"deployment-structure-{csp}-{region}-{part_id}.json"), "w+"
    ) as out:
        out.write(deployment_struct_json)