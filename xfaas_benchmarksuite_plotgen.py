import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import sys
import os
import json
import numpy as np
import networkx as nx
import pathlib
import pprint
import argparse

from typing import Any
from collections import defaultdict
from matplotlib.lines import lineStyles
from azure.storage.queue import QueueService, QueueMessageFormat
from serwo.python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from serwo.python.src.utils.classes.commons.logger import LoggerFactory

logger = LoggerFactory.get_logger(__file__, log_level="INFO")

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
    
        index = 1
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


def get_queue_size():
    queue_service = QueueService(connection_string=connect_str)
    queue_service.encode_function = QueueMessageFormat.binary_base64encode
    queue_service.decode_function = QueueMessageFormat.binary_base64decode
    metadata = queue_service.get_queue_metadata(queue_name)
    count = metadata.approximate_message_count
    return count

def create_dynamo_db_items():
    queue_service = QueueService(connection_string=connect_str)
    queue_service.encode_function = QueueMessageFormat.binary_base64encode
    queue_service.decode_function = QueueMessageFormat.binary_base64decode

    count = get_queue_size()
    logger.info("Message count here: " + str(count))
    get_count = count // 32 + 5
    logger.info("rounds = " + str(get_count))

    dynamodb_item_list = []

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

                dynamodb_item_list.append(dynamo_item)

    return dynamodb_item_list


def add_items_to_dynamodb(dynamo_items: list):
    # items = create_dynamo_db_items()
    for dynamo_item in dynamo_items:
        logger.info(
            f"PushToDynamoAdding Item - \
             DeploymentID - {dynamo_item['workflow_deployment_id']} - \
             InvocationId - {dynamo_item['workflow_invocation_id']}"
        )
        dynPartiQLWrapper = PartiQLWrapper("workflow_invocation_table")
        try:
            dynPartiQLWrapper.put(dynamo_item)
        except:
            pass

# NOTE - method used only for testing purposes
def get_from_queue_add_to_file():
    dynamo_items = create_dynamo_db_items()
    with open(out_path / f"{wf_name}_{csp}_{dynamism}_{payload}_dyndb_items.jsonl", "w") as file:
        for dynamo_item in dynamo_items:
            dynamo_item_string = json.dumps(dynamo_item) + "\n"
            file.write(dynamo_item_string)
    return dynamo_items


# NOTE - actual dynamo method
# def get_from_dynamo(workflow_deployment_id):
#     partiQLWrapper = PartiQLWrapper("workflow_invocation_table")
#     output = partiQLWrapper.run_partiql(
#         statement=f"SELECT * FROM workflow_invocation_table WHERE workflow_deployment_id=?",
#         params=[workflow_deployment_id],
#     )
#     return output

def get_from_dynamo(workflow_deployment_id=None):
    filename = f"{wf_name}_{csp}_{dynamism}_{payload}_dyndb_items.jsonl"
    with open(out_path / f"{filename}", "r") as file:
        res = defaultdict(list)
        lines = file.readlines()
        for line in lines:
            res["Items"].append(json.loads(line))
    return res


def get_timings(dynamo_items, session_id):
    timings = dict(e2e_timings=[], interfunction_timings=defaultdict(list), func_exec_timings=defaultdict(list))
    sink_node = [node for node in xfaas_dag.nodes if xfaas_dag.out_degree(node) == 0][0]

    count = 0
    logger.info(f"Dynamo Items - {len(dynamo_items['Items'])}")
    for item in dynamo_items["Items"]:
        # logger.info(f"Processing {item['workflow_invocation_id']}")
        
        # get e2e timings
        if item["session_id"].strip() == session_id:
            count = count + 1
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

    logger.info(f"Count {count}")   
    logger.info("Timings Dictionary", timings)
    filename = f"timings_dict_sid{session_id}_{csp}_{dynamism}_{payload}.json"
    
    logger.info(f"Saving to filename {filename}")
    with open(out_path / f"{filename}", "w") as file:
        json.dump(timings, file, indent=4)

    return timings

# TODO - pass session_id along with th e
def delete_from_dynamo(workflow_deployment_id):
    # for session_id in [100, 200, 300]:
        for idx in range(1, 388):
            workflow_invocation_id = f"{idx}"
            logger.info("Starting delete all items for", workflow_deployment_id, workflow_invocation_id)
            partiQLWrapper = PartiQLWrapper("workflow_invocation_table")
            output = partiQLWrapper.run_partiql(
                statement=f"DELETE FROM workflow_invocation_table WHERE workflow_deployment_id=? and workflow_invocation_id=?",
                params=[workflow_deployment_id, workflow_invocation_id],
            )
            logger.info(output)


def plot_e2e_timeline(e2e_all_sessions, time_marker_sessions):
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fontdict = {'size': 12}
    logger.info(f"Len Timings - {len(e2e_all_sessions)}")
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    x_val = [x for x in range(1, len(e2e_all_sessions)+1)]
    labels = [x for x in range(0, len(e2e_all_sessions) + 100, 100)]

    # ax.set_title(
    #         f"E2E timeline plot - {conf['wf_name']} - {conf['csp']} - {conf['duration']/60}mins - {conf['rps']}RPS",
    #         fontdict=fontdict
    # )
    ax.set_xlabel("Invocation Id", fontdict=fontdict)
    ax.set_ylabel("E2E time (sec)", fontdict=fontdict)

    # plotting the exec time in seconds and not milliseconds
    y_val = [y/1000 for y in e2e_all_sessions]
    ax.plot(x_val, [y/1000 for y in e2e_all_sessions])


    # Xticks are straighforward
    ax.set_xticks(labels)
    ax.set_xticklabels([str(x) for x in labels], fontdict=fontdict)

    # Auto adjustment of yticklables (Do manually if needed)
    ymax = max(y_val)
    yticks = []
    count = 0
    multiplier = 5
    while(count*multiplier <= ymax):
        yticks.append(count*multiplier)
        count = count + 1
    yticks.append(count*multiplier)

    # CUSTOM yticks
    # yticks = [0, 5, 10, 15]
    # ytickslabels = [str(x) for x in yticks]
    # ax.set_ylim(ymax=10)
    # ax.set_yticks(yticks)
    # ax.set_yticklabels(ytickslabels,
    #                   fontdict=fontdict)
    
    # Uncomment this for general purpose
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks])

    ax.set_ylim(ymin=0)
    ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])

    if len(time_marker_sessions) > 1:
        cumm_marker = time_marker_sessions[0]
        rps_change_markers = []
        for x in time_marker_sessions[1:]:
            rps_change_markers.append(cumm_marker)
            cumm_marker = cumm_marker + x

        logger.info(rps_change_markers)
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
    fig.savefig(plots_path / f"e2e_timeline_{wf_name}_{csp}_{dynamism}_{payload}.{format}", bbox_inches='tight')
    # plt.show()

def plot_box_plots(xfaas_dag, timings_all_sessions):
    
    # combine the session id timings for each edge into a single list (edge key - 'u-v')
    # create dict(
    #   "functions": defaultdict(list)),
    #   "edges": defaultdict(list)
    #   )
    distribution_dict = dict(
        functions=defaultdict(list),
        edges=defaultdict(list)
    )

    # combine the session id timings for each function into a single list
    for sid, timings in sorted(timings_all_sessions.items()):
        for nId, node_exec_dist in sorted(timings["func_exec_timings"].items()):
            distribution_dict["functions"][nId] += [x/1000 for x in node_exec_dist]
        for eId, edge_exec_dist in sorted(timings["interfunction_timings"].items()):
            distribution_dict["edges"][eId] += [x/1000 for x in edge_exec_dist]

    # iterate over sorted keys on 'functions', 'edges' and plot boxes
    def plot_func_exec_box():
        fig, ax = plt.subplots()
        fig.set_dpi(400)
        fontdict = {'size': 12}

        ax.set_xlabel("Function ID", fontdict=fontdict)
        ax.set_ylabel("Exec Time (sec)", fontdict=fontdict)
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())


        function_labels = [str(l) for l in sorted([int(x) for x in distribution_dict["functions"]])]
        logger.info(function_labels)
        function_data = [np.array(distribution_dict["functions"][f"{x}"]) for x in function_labels]
        
        # rectangular box plot
        bplot1 = ax.boxplot(function_data,
                            vert=True,  # vertical box alignment
                            patch_artist=True,  # fill with color
                            labels=function_labels,
                            showfliers=False)
        
        ax.set_xticklabels(function_labels, 
                           fontdict=fontdict)    
        ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])

        color_node = 'lightblue'
        for patch in bplot1['boxes']:
            patch.set_facecolor(color_node)

        # NOTE - uncomment this for default
        # ymax = 0.25
        ax.set_ylim(ymin=0)
        ax.grid(axis="y", which="major", linestyle="-", color="black")
        ax.grid(axis="y", which="minor", linestyle="--", color="grey")
        ax.set_axisbelow(True)

        fig.savefig(plots_path / f"fn_exec_box_{wf_name}_{csp}_{dynamism}_{payload}.{format}", bbox_inches='tight')

        # plt.show()
    
    def plot_edge_exec_box():
        fig, ax = plt.subplots()
        fig.set_dpi(400)
        fontdict = {'size': 12}

        ax.set_xlabel("Edge ID", fontdict=fontdict)
        ax.set_ylabel("Exec Time (sec)", fontdict=fontdict)
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
        
        # TODO - plot edge later
        interfunction_labels = list([f"{u}-{v}" for u,v in xfaas_dag.edges])
        logger.info(f"Interfunction Labels - {interfunction_labels}")
        interfunction_data = [np.array(distribution_dict["edges"][f"{x}"]) for x in interfunction_labels]
        
        # rectangular box plot
        bplot1 = ax.boxplot(interfunction_data,
                            vert=True,  # vertical box alignment
                            patch_artist=True,
                            showfliers=False)  # fill with color
                            # labels=interfunction_labels)
        
        ax.set_xticklabels(interfunction_labels, 
                           rotation=90,
                           fontdict=fontdict)
        
        ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])

        color_node = 'lightgreen'
        for patch in bplot1['boxes']:
            patch.set_facecolor(color_node)

        ax.set_ylim(ymin=0)
        ax.grid(axis="y", which="major", linestyle="-", color="black")
        ax.grid(axis="y", which="minor", linestyle="--", color="grey")
        ax.set_axisbelow(True)

        fig.savefig(plots_path / f"edge_exec_box_{wf_name}_{csp}_{dynamism}_{payload}.{format}", bbox_inches='tight')
        # plt.show()


    def plot_interleaved():
        fig, ax = plt.subplots()
        fig.set_dpi(400)
        fontdict = {'size': 12}

        ax.set_xlabel(f"{wf_name}", fontdict=fontdict)
        ax.set_ylabel("Time (sec)", fontdict=fontdict)
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())

        interleaved_label_ids = []
        interleaved_data = []
        visited = set()
        def get_edges(n):
            return [(u,v) for u,v in xfaas_dag.edges if u == n]
        
        def get_color(id):
            if "-" in id:
                return "lightgreen"
            else:
                return "lightblue"
            
        def get_data(id):
            if "-" in id:
                return np.array(distribution_dict["edges"][id])
            else:
                return np.array(distribution_dict["functions"][id])

        # create some sort of an ordered labels for the interleaved plot
        for u in xfaas_dag.nodes:
            if u not in visited:
                interleaved_label_ids.append(u)
                edges = get_edges(u)
                interleaved_label_ids += [f"{n1}-{n2}" for n1, n2 in edges]
                visited.add(u)

        logger.info(f"Interleaved Labels - {interleaved_label_ids}")
        interleaved_data = [get_data(id) for id in interleaved_label_ids]

        # rectangular box plot
        bplot1 = ax.boxplot(interleaved_data,
                            vert=True,  # vertical box alignment
                            patch_artist=True,
                            showfliers=False)  # fill with color
                            # labels=interfunction_labels)
        
        # NOTE - modify this label to include the function and edge abbreviations
        interleaved_labels_modified = ['GGen', 'GGen-BFT', 'GGen-PR', 'GGen-MST', 'BFT', 'BFT-Agg', 'PR', 'PR-Agg', 'MST', 'MST-Agg', 'Agg']
        
        logger.info(f"Interleaved Labels - {interleaved_labels_modified}")
        ax.set_xticklabels(interleaved_labels_modified, 
                           rotation=90,
                           fontdict=fontdict)
        

        # CUSTOM yticks
        # yticks = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        # ytickslabels = [str(x) for x in yticks]
        # ax.set_ylim(ymax=0.8)
        # ax.set_yticks(yticks)
        # ax.set_yticklabels(ytickslabels,
        #                    fontdict=fontdict)

        ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])

        for idx, patch in enumerate(bplot1['boxes']):
            patch.set_facecolor(get_color(interleaved_label_ids[idx]))

        ax.set_ylim(ymin=0)
        ax.grid(axis="y", which="major", linestyle="-", color="black")
        ax.grid(axis="y", which="minor", linestyle="--", color="grey")
        ax.set_axisbelow(True)
        
        fig.savefig(plots_path / f"interleaved_exec_box_{wf_name}_{csp}_{dynamism}_{payload}.{format}", bbox_inches='tight')
        

    # conditional plotting 
    if is_interleaved:
        plot_interleaved()
    
    # NOTE - uncomment this if you want edge and func exec separate
    # plot_func_exec_box()
    # plot_edge_exec_box()


def plotter(workflow_deployment_id, experiment_conf):
    # logger.info("Querying DynamoDB Once")
    # dynamo_items = get_from_dynamo(workflow_deployment_id=workflow_deployment_id)
    logger.info("Querying File Mock Dynamo")
    dynamo_items = get_from_dynamo(
                        workflow_deployment_id=workflow_deployment_id
                    )
    # add a filter based on deployment Id (since a single queue will contain multiple session ids)
    filtered_dynamo_items = defaultdict(list)
    filtered_dynamo_items["Items"] = [item for item in dynamo_items["Items"] if item["workflow_deployment_id"] == workflow_deployment_id]

    timings_all_sessions = dict()
    e2e_all_sessions = []
    time_marker_sessions = []
    

    # create the session_id -> timings dict.
    for session_id, conf in experiment_conf.items():
        logger.info(f"Getting Timings For Session Id - {session_id}")
        timings = get_timings(dynamo_items=filtered_dynamo_items, session_id=session_id)
        e2e_timings = timings["e2e_timings"]
        logger.info(len(e2e_timings))
        e2e_all_sessions += e2e_timings 
        time_marker_sessions.append(len(e2e_timings))   
        timings_all_sessions[session_id] = timings

    # plot e2e timeline
    plot_e2e_timeline(
        e2e_all_sessions=e2e_all_sessions,
        time_marker_sessions=time_marker_sessions
    )

    # plot box plots
    plot_box_plots(
        xfaas_dag=xfaas_dag,
        timings_all_sessions=timings_all_sessions
    )

    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="What the program does",
        epilog="Text at the bottom of help",
    )

    parser.add_argument("--user-dir",dest='user_dir',type=str,help="Workflow User Directory")
    parser.add_argument("--artifacts-filename",dest='artifacts_filename',type=str,help="Provenance Artifacts Filename")
    parser.add_argument("--interleaved",dest='is_interleaved',type=bool,help="Plot Interleaved")
    parser.add_argument("--format",dest="format",type=str,help="Plot format (svg | pdf)")
    parser.add_argument("--out-dir",dest="out_dir",type=str,help="Output directory")
    args = parser.parse_args()

    user_dir = pathlib.Path(args.user_dir)
    provenance_filename = args.artifacts_filename
    is_interleaved = args.is_interleaved
    format = args.format
    out_dir = args.out_dir

    out_path = user_dir / f"build/workflow/resources/{out_dir}"
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    
    plots_path = out_path / f"plots"
    if not os.path.exists(plots_path):
        os.mkdir(plots_path)

    provenance_path = user_dir / f"provenance-artifacts/{provenance_filename}"
    # with open(user_dir / f"build/workflow/resources/{provenance_filename}", "r") as f:
    with open(user_dir / f"{provenance_path}", "r") as f:
        config = json.load(f)
        workflow_refactored_id = config["refactored_workflow_id"]
        workflow_deployment_id = config["deployment_id"]
        experiment_conf = config["experiment_conf"]
        global_exp_conf = list(experiment_conf.values())[0]

    wf_name = global_exp_conf['wf_name']
    csp = global_exp_conf['csp']
    dynamism = global_exp_conf['dynamism']
    payload = global_exp_conf['payload_size']

    with open(user_dir / "queue_details.json", "r") as f:
        queue_details = json.load(f)
    connect_str = queue_details["connectionString"]
    queue_name = queue_details["queue"]

    dagfilepath = user_dir / "dag-original.json"
    xfaas_dag = DagLoader(dagfilepath).get_dag()

    logger.info("Getting from Queue and Adding to file")
    items = get_from_queue_add_to_file()
    # logger.info("Pushing to DynamoDB")
    # add_items_to_dynamodb(items)
    
    logger.info("Plotting Timeline")
    plotter(
        workflow_deployment_id=workflow_deployment_id,
        experiment_conf=experiment_conf
    )

    # delete_temp(workflow_deployment_id=workflow_deployment_id)