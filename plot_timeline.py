import matplotlib.pyplot as plt
import os
import os, uuid
import json
import numpy as np
import pathlib
import sys

from typing import Any
from matplotlib.lines import lineStyles
from azure.storage.queue import QueueService, QueueMessageFormat
from serwo.python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper


exp_name = sys.argv[1]
PARENT_DIR = pathlib.Path(__file__).parent
####### Read from a file ######
with open(
    f"serwo/examples/{exp_name}/build/workflow/resources/provenance-artifacts.json", "r"
) as f:
    config = json.load(f)
    workflow_refactored_id = config["refactored_workflow_id"]
    workflow_deployment_id = config["deployment_id"]

with open(f"serwo/examples/{exp_name}/queue_details.json", "r") as f:
    queue_details = json.load(f)

connect_str = queue_details["connectionString"]
queue_name = queue_details["queue"]
###################################


def add_invocations_to_dynamodb():
    queue_service = QueueService(connection_string=connect_str)
    queue_service.encode_function = QueueMessageFormat.binary_base64encode
    queue_service.decode_function = QueueMessageFormat.binary_base64decode
    metadata = queue_service.get_queue_metadata(queue_name)
    count = metadata.approximate_message_count
    print("Message count here: " + str(count))
    get_count = count // 32 + 5
    print("rounds = " + str(get_count))

    for i in range(get_count):
        messages = queue_service.get_messages(
            queue_name, num_messages=32, visibility_timeout=60
        )
        for message in messages:
            if (
                message.content.decode("utf-8")
                != "json.dumps(fin_dict).encode('utf-8')"
            ):
                queue_item = json.loads(message.content.decode("utf-8"))
                metadata = queue_item["metadata"]
                dynamo_item = {}

                dynamo_item["workflow_deployment_id"] = workflow_deployment_id
                dynamo_item["workflow_invocation_id"] = str(
                    metadata["workflow_instance_id"]
                )
                dynamo_item["client_request_time_ms"] = str(
                    metadata["request_timestamp"]
                )
                dynamo_item["invocation_start_time_ms"] = str(
                    metadata["workflow_start_time"]
                )
                dynamo_item["functions"] = {}
                for item in metadata["functions"]:
                    for key in item.keys():
                        dynamo_item["functions"][key] = item[key]

                print(
                    f"[INFO]PushToDynamo::Adding Item - deployment {workflow_deployment_id}, InvocationId - {metadata['workflow_instance_id']}"
                )
                dynPartiQLWrapper = PartiQLWrapper("workflow_invocation_table")
                try:
                    dynPartiQLWrapper.put(dynamo_item)
                except:
                    pass


# # NOTE - The timings will be sorted by the sortkey [workflow_invocation_id] by default
# def get_function_timings(table_name, function_id, workflow_deployment_id):
#     function_timings = []
#     output = partiQLWrapper.run_partiql(
#             f"SELECT request_timestamp, functions.\"{function_id}\" FROM \"{table_name}\" WHERE workflow_instance_id=?", [workflow_deployment_id])
#     for item in output['Items']:
#         function_timings.append(int(item[function_id]['end_delta'] - item[function_id]['start_delta']))
#     return function_timings

# # NOTE - The timings will be sorted by the sortkey [workflow_invocation_id] by default
# def get_interfunction_timings(table_name, src_id, sink_id, workflow_deployment_id):
#     function_timings = []

#     output = partiQLWrapper.run_partiql(
#             f"SELECT request_timestamp, functions.\"{src_id}\", functions.\"{sink_id}\" FROM \"{table_name}\" WHERE workflow_instance_id=?", [workflow_deployment_id])
#     for item in output['Items']:
#         function_timings.append(int(item[sink_id]['start_delta'] - item[src_id]['end_delta']))
#     return function_timings

# def get_invocations_sorted_by_client_time(workflow_deployment_id):
#     items = []
#     output = partiQLWrapper.run_partiql(
#             f"SELECT functions FROM workflow_invocation_table WHERE workflow_deployment_id=?", [workflow_deployment_id])
#     for item in output['Items']:
#         functions = item['functions']

#     return items


def get_e2e_timeline(workflow_deployment_id):
    last_func_id = "17"
    e2e_timings = []
    partiQLWrapper = PartiQLWrapper("workflow_invocation_table")
    output = partiQLWrapper.run_partiql(
        statement=f"SELECT * FROM workflow_invocation_table WHERE workflow_deployment_id=?",
        params=[workflow_deployment_id],
    )
    for item in output["Items"]:
        print(f"[INFO]::Processing {item['workflow_invocation_id']}")
        e2e_timings.append(item["functions"][last_func_id]["end_delta"])
    print(e2e_timings)
    return e2e_timings


def plot_from_dynamo():
    e2e_timings = get_e2e_timeline(workflow_deployment_id)
    print(e2e_timings)
    labels = [x + 1 for x in range(1, len(e2e_timings) + 1)]

    fig, ax = plt.subplots()
    ax.set_title("E2E timeline plot")
    ax.set_xlabel("Invocation Id")
    ax.set_ylabel("E2E time (ms)")
    ax.set_xticks(labels)
    # ax.set_ylim(ymin=0)
    ax.set_xticklabels([str(x) for x in labels])
    ax.grid(True)
    ax.plot(labels, e2e_timings)
    plt.savefig(f"{exp_name}_e2e_timings.pdf")
    plt.show()


if __name__ == "__main__":
    print("[INFO]::Adding invocations to DynamoDB")
    add_invocations_to_dynamodb()
    print("[INFO]::Plotting Timeline")
    plot_from_dynamo()
