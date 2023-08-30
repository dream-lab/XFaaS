import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import os
import json
import numpy as np
import networkx as nx

from typing import Any
from collections import defaultdict
from matplotlib.lines import lineStyles
from azure.storage.queue import QueueService, QueueMessageFormat
from serwo.python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from serwo.python.src.utils.classes.commons.logger import LoggerFactory

class DagLoader:
    # private variables
    __dag_config_data = dict() # dag configuration (picked up from user file)
    __nodeIDMap = {} # map: nodeName -> nodeId (used internally)
    __dag = nx.DiGraph() # networkx directed graph

    # Constructor
    def __init__(self, user_config_path):
        # throw an exception if loading file has a problem
        try:
            self.__dag_config_data = self.__load_user_spec(user_config_path)
            self.__workflow_name = self.__dag_config_data["WorkflowName"]
        except Exception as e:
            raise e
       
        # build the networkx DAG
        # add nodes in the dag and populate the functions dict
        index = 1
        # add edges in the dag
        # for edge in self.__dag_config_data["Edges"]:
        #     for key in edge:
        #         for val in edge[key]:
        #             self.__dag.add_edge(self.__nodeIDMap[key], self.__nodeIDMap[val])

        for node in self.__dag_config_data["Nodes"]:
            # nodeID = self.__get_nodeId(function_name=node["NodeName"]) + f"-{str(index)}"
            nodeID = node["NodeId"]
            self.__nodeIDMap[node["NodeName"]] = nodeID
            self.__dag.add_node(nodeID,
                                NodeId=nodeID,
                                NodeName=node["NodeName"], 
                                Path=node["Path"],
                                EntryPoint=node["EntryPoint"],
                                MemoryInMB=node["MemoryInMB"])
            index += 1

        # add edges in the dag
        for edge in self.__dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    self.__dag.add_edge(self.__nodeIDMap[key], self.__nodeIDMap[val])

    # private methods
    def __load_user_spec(self, user_config_path):
        with open(user_config_path, "r") as user_dag_spec:
            dag_data = json.load(user_dag_spec)
        return dag_data

    def get_dag(self):
        return self.__dag


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
                
                # invocation id is a combination of the instanceId-sessionId
                invocation_id = f"{metadata['workflow_instance_id']}-{metadata['session_id']}"

                dynamo_item["workflow_deployment_id"] = workflow_deployment_id
                # dynamo_item["workflow_invocation_id"] = str(
                #     metadata["workflow_instance_id"]
                # )
                dynamo_item["workflow_invocation_id"] = invocation_id
                dynamo_item["client_request_time_ms"] = str(
                    metadata["request_timestamp"]
                )
                dynamo_item["invocation_start_time_ms"] = str(
                    metadata["workflow_start_time"]
                )

                # add session id to dynamo db
                dynamo_item["session_id"] = str(metadata["session_id"])

                dynamo_item["functions"] = {}
                for item in metadata["functions"]:
                    for key in item.keys():
                        dynamo_item["functions"][key] = item[key]

                print(
                    f"[INFO]PushToDynamo::Adding Item - deployment {workflow_deployment_id}, InvocationId - {invocation_id}"
                )
                dynPartiQLWrapper = PartiQLWrapper("workflow_invocation_table")
                try:
                    dynPartiQLWrapper.put(dynamo_item)
                except:
                    pass


def get_from_dynamo(workflow_deployment_id):
    partiQLWrapper = PartiQLWrapper("workflow_invocation_table")
    output = partiQLWrapper.run_partiql(
        statement=f"SELECT * FROM workflow_invocation_table WHERE workflow_deployment_id=?",
        params=[workflow_deployment_id],
    )
    return output


def get_timings(dynamo_items, session_id):
    timings = dict(e2e_timings=[], interfunction_timings=defaultdict(list), func_exec_timings=defaultdict(list))
    sink_node = [node for node in xfaas_dag.nodes if xfaas_dag.out_degree(node) == 0][0]

    for item in dynamo_items["Items"]:
        # print(f"[INFO]::Processing {item['workflow_invocation_id']}")
        
        # get e2e timings
        if item["session_id"] == session_id:
            timings["e2e_timings"].append(int(item["functions"][sink_node]["end_delta"]))

            # get function exec timings
            for node in [u for u in xfaas_dag.nodes]:
                func_exec_time = item["functions"][node]["end_delta"] - item["functions"][node]["start_delta"]
                timings["func_exec_timings"][node].append(int(func_exec_time))

            # get interfunction timings
            for u,v in [e for e in xfaas_dag.edges]:
                edge_key = f"{u}-{v}"
                edge_time = item["functions"][v]["start_delta"] - item["functions"][u]["end_delta"]
                timings["interfunction_timings"][edge_key].append(int(edge_time))

    # print("[INFO]::Timings Dictionary", timings)
    return timings


def delete_temp(workflow_deployment_id):
    # for session_id in [100, 200, 300]:
        for idx in range(1, 388):
            workflow_invocation_id = f"{idx}"
            print("Starting delete all items for", workflow_deployment_id, workflow_invocation_id)
            partiQLWrapper = PartiQLWrapper("workflow_invocation_table")
            output = partiQLWrapper.run_partiql(
                statement=f"DELETE FROM workflow_invocation_table WHERE workflow_deployment_id=? and workflow_invocation_id=?",
                params=[workflow_deployment_id, workflow_invocation_id],
            )
            print(output)


def plot_e2e_timeline_from_dynamo(workflow_deployment_id):
    print("[INFO]::Querying DynamoDB Once")
    dynamo_items = get_from_dynamo(workflow_deployment_id=workflow_deployment_id)
    
    e2e_all_sessions = []
    time_marker_sessions = []
    for session_id, conf in experiment_conf.items():
        e2e_timings = get_timings(dynamo_items=dynamo_items, session_id=session_id)["e2e_timings"]
        e2e_all_sessions += e2e_timings 
        time_marker_sessions.append(len(e2e_timings))   

    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fontdict = {'size': 15}
    print(f"Len Timings - {len(e2e_all_sessions)}")
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    x_val = [x for x in range(1, len(e2e_all_sessions)+1)]
    labels = [x for x in range(0, len(e2e_all_sessions) + 100, 200)]

    # ax.set_title(
    #         f"E2E timeline plot - {conf['wf_name']} - {conf['csp']} - {conf['duration']/60}mins - {conf['rps']}RPS",
    #         fontdict=fontdict
    # )
    ax.set_xlabel("Invocation Id", fontdict=fontdict)
    ax.set_ylabel("E2E time (ms)", fontdict=fontdict)

    ax.plot(x_val, e2e_all_sessions)


    yticks = ax.get_yticks()
    ax.set_xticks(labels)
    ax.set_xticklabels([str(x) for x in labels], fontdict=fontdict)

    yticks = [y for y in range(0, max(e2e_all_sessions) + 1500, 500)]
    ax.set_yticklabels([str(y) for y in yticks], fontdict=fontdict)

    ax.set_ylim(ymin=0, ymax=max(yticks))

    if len(time_marker_sessions) > 1:
        cumm_marker = time_marker_sessions[0]
        rps_change_markers = []
        for x in time_marker_sessions[1:]:
            rps_change_markers.append(cumm_marker)
            cumm_marker = cumm_marker + x

        print(rps_change_markers)
        ax.vlines(  rps_change_markers,
                    ymin=0,
                    ymax=max(yticks), 
                    linestyles='dashed',
                    color='grey' )

    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="--", color="grey")
    ax.set_axisbelow(True)
    # ax.margins(x=0)
    # ax.minorticks_on()
    ax.set_axisbelow(True)
    fig.savefig(f"{folder}/draft_e2e_timings_2.pdf", bbox_inches='tight')
    # plt.show()
        


if __name__ == "__main__":
    folder = "serwo/scratch"
    with open(f"{folder}/provenance-artifacts.json", "r") as f:
        config = json.load(f)
        workflow_refactored_id = config["refactored_workflow_id"]
        workflow_deployment_id = config["deployment_id"]
        experiment_conf = config["experiment_conf"]

    with open(f"{folder}/queue-details.json", "r") as f:
        queue_details = json.load(f)
    connect_str = queue_details["connectionString"]
    queue_name = queue_details["queue"]

    dagfilepath = f"{folder}/dag.json"
    xfaas_dag = DagLoader(dagfilepath).get_dag()

    print("[INFO]::Adding invocations to DynamoDB")
    # add_invocations_to_dynamodb()
    print("[INFO]::Plotting Timeline")

    plot_e2e_timeline_from_dynamo(
        workflow_deployment_id=workflow_deployment_id
    )

    # delete_temp(workflow_deployment_id=workflow_deployment_id)
