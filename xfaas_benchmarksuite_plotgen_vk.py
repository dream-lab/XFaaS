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
                
                # Filtering based on workflow deployment id during creation itself
                if metadata["deployment_id"].strip() == workflow_deployment_id:

                    dynamo_item = {}
                    
                    # invocation id is a combination of the instanceId-sessionId
                    invocation_id = f"{metadata['workflow_instance_id']}-{metadata['session_id']}"

                    # NOTE - the deployment id is now being propagated in the provenance via modified runner templates
                    # needed it for filtering on the experiment data
                    dynamo_item["workflow_deployment_id"] = metadata["deployment_id"]
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

# NOTE - in this function the time comes in milliseconds we convert to seconds later while plotting itself
def get_timings(dynamo_items, session_id):
    timings = dict(e2e_timings=[], interfunction_timings=defaultdict(list), func_exec_timings=defaultdict(list))
    sink_node = [node for node in xfaas_dag.nodes if xfaas_dag.out_degree(node) == 0][0]

    count = 0
    logger.info(f"Dynamo Items Length - {len(dynamo_items['Items'])}")

    # Sort the items w.r.t the invocation start time
    sorted_dynamo_items = sorted(dynamo_items["Items"],key=lambda x: x["invocation_start_time_ms"])
    for item in sorted_dynamo_items:
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


def plot_e2e_timeline(e2e_all_sessions, time_marker_sessions, timeline):
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fontdict = {'size': 12}
    logger.info(f"Len Timings - {len(e2e_all_sessions)}")
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    x_val = [x for x in range(1, len(e2e_all_sessions)+1)]
    labels = [x for x in range(0, len(e2e_all_sessions) + 100, 100)]
    
    ax.set_ylabel("E2E time (sec)", fontdict=fontdict)
    # plotting the exec time in seconds and not milliseconds
    # NOTE - PLOT WITH TIMELINE
    ax.set_xlabel("Timeline (sec)", fontdict=fontdict)
    ax.plot(timeline, [y/1000 for y in e2e_all_sessions])
    ax.xaxis.set_tick_params(which='major', labelsize=fontdict['size'])

    yticks_ax1 = [y for y in range(0, 100, 20)]


    # Auto adjustment of yticklables (Do manually if needed)
    # ymax = max(y_val)
    # yticks = []
    # count = 0
    # multiplier = 5
    # while(count*multiplier <= ymax):
    #     yticks.append(count*multiplier)
    #     count = count + 1
    # yticks.append(count*multiplier)

    # CUSTOM yticks
    # yticks = list(range(0, 45, 5))
    # ytickslabels = [str(x) for x in yticks]
    # ax.set_ylim(ymin=0, ymax=max(yticks))
    # ax.set_yticks(yticks)
    # ax.set_yticklabels(ytickslabels,
    #                   fontdict=fontdict)
    
    # Uncomment this for general purpose
    ax.set_yticks(yticks_ax1)
    ax.set_yticklabels([str(y) for y in yticks_ax1])

    ax.set_ylim(ymin=0, ymax=max(yticks_ax1))
    ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
    

    # Dynamism OVERLAY - (START) - move this to a separate function
    # NOTE - step function overlay
    # # Sawtooth step y 
    # step_y = [1,2,3,4,5,6,7,8,0]*3
    # step_x = []
    # invoc_id = 0
    # for rps in step_y:
    #     if rps == 0:
    #         invoc_id = invoc_id + 60
    #     else:
    #         invoc_id = invoc_id + 8
    #     step_x.append(invoc_id)

    # Step up down config
    # step_y = [1,4,8,4,1]
    # invoc_id = 0
    # step_x = []
    # for rps in step_y:
    #     invoc_id = invoc_id + 60
    #     step_x.append(invoc_id)

    # Alibaba
    # step_x = [1, 5, 12, 18, 38, 46, 52, 72, 75, 76, 79, 80, 87, 137, 142, 170, 196, 199, 200, 201, 202, 203, 208, 209, 218, 220, 229, 240]
    # step_y = [1, 7, 10, 5, 1, 1, 1, 1, 1, 6, 1, 1, 1, 1, 2, 3, 14, 17, 4, 2, 8, 1, 1, 1, 6, 1, 1, 1] 

    # logger.info(f"Step X - {step_x}")
    # ax2 = ax.twinx()
    # ax2.set_ylim(ymin=0)
    # ax2.set_ylabel("RPS", fontdict=fontdict)
    # yticks_ax2 = [int(y/10) for y in yticks_ax1]
    # ax2.set_yticks(yticks_ax2)
    # ax2.set_yticklabels([str(y) for y in yticks_ax2], fontdict=fontdict)
    # ax2.step([0] + step_x, [1] + step_y, linestyle='dashed', color='red')
    # Dynamism OVERLAY - (END)
    

    # NOTE - code to add vlines (start)
    # if len(time_marker_sessions) > 1:
    #     cumm_marker = time_marker_sessions[0]
    #     rps_change_markers = []
    #     for x in time_marker_sessions[1:]:
    #         rps_change_markers.append(cumm_marker)
    #         cumm_marker = cumm_marker + x

    #     logger.info(rps_change_markers)
    #     ax.vlines(  rps_change_markers,
    #                 ymin=0,
    #                 ymax=max(yticks), 
    #                 linestyles='dashed',
    #                 color='grey' )
    # NOTE - code to add vlines (end)

    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    # ax.margins(x=0)
    # ax.minorticks_on()
    fig.savefig(plots_path / f"e2e_timeline_{wf_name}_{csp}_{dynamism}_{payload}.{format}", bbox_inches='tight')
    # plt.show()

def plot_box_plots(xfaas_dag, timings_all_sessions, e2e_all_sessions):
    
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
    # here the time is converted to seconds
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
        ax.grid(axis="y", which="minor", linestyle="-", color="grey")
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
        ax.grid(axis="y", which="minor", linestyle="-", color="grey")
        ax.set_axisbelow(True)

        fig.savefig(plots_path / f"edge_exec_box_{wf_name}_{csp}_{dynamism}_{payload}.{format}", bbox_inches='tight')
        # plt.show()


    def plot_interleaved():
        fig, ax = plt.subplots()
        fig.set_dpi(400)
        fontdict = {'size': 14}

        ax.set_ylabel("Time (sec)", fontdict=fontdict)
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())

        # CUSTOM yticks
        yticks_ax1 = [0, 0.2, 0.4, 0.6, 0.8, 1]
        yticks_ax2 = [round(3*y, 1) for y in yticks_ax1]

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
        
        def get_label_color(id):
            if "-" in id:
                return "green"
            else:
                return "blue"     
            
        def get_data(id):
            if "-" in id:
                return np.array(distribution_dict["edges"][id])
            else:
                return np.array(distribution_dict["functions"][id])

        #
        def get_cumm_time_func(time_map, num_iters):
            
            cumm_time = []
            for idx in range(0, num_iters):
                temp = []
                for key in time_map.keys():
                    temp.append(time_map[key][idx])
                cumm_time.append(temp)
            return np.array([sum(x) for x in cumm_time])
        
        def get_cumm_time_edge(time_map, edge_set, num_iters):
            s_time = [['1', '2', '12', '22'], ['1', '3', '13', '22'], ['1', '4', '14', '22'], ['1', '5', '15', '22'], ['1', '6', '16', '22'], ['1', '7', '17', '22'], ['1', '8', '18', '22'], ['1', '9', '19', '22'], ['1', '10', '20', '22']]
            cumm_time = []
            for idx in range(0, num_iters):
                maxval = -1
                mx = []
                for it in s_time:
                    tme = 0
                    for i in range(0,2):
                        edge = f'{it[i]}-{it[i+1]}'
                        tme += time_map[edge][idx]
                    mx.append(tme)
                maxval = max(mx)
                # for key in edge_set:
                #     if time_map[key][idx] > maxval:
                #         maxval = time_map[key][idx]
                cumm_time.append(maxval)
            return cumm_time

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
                            widths=0.32,
                            showfliers=False)  # fill with color
                            # labels=interfunction_labels)
        
        cumm_labels = []
        ######## CUMMULATIVE TIME ADDITION (START) #########
        # NOTE - push this to an outer function for each graph
        # UNCOMMENT / COMMENT FROM HERE (START) 
        # Get the cummulative function timings
        ax2 = ax.twinx()
        ax2.set_ylabel("Cummulative Time (sec)", fontdict=fontdict)
        cumm_labels = ['Cumm. Func', 'Cumm. Edge', 'Cumm. E2E']
        cumm_func_time = get_cumm_time_func(time_map=distribution_dict["functions"], num_iters=len(e2e_all_sessions))
        
        # NOTE - customise these with respect to the workflow
        ##### CUSTOM edge timing calculation (Start) #####
        # Graph - 
        cumm_edge_time1 = get_cumm_time_edge(time_map=distribution_dict["edges"], 
                                            num_iters=len(e2e_all_sessions), 
                                            edge_set=['1-2', '1-3', '1-4'])
        
        # print(cumm_edge_time1)
        # cumm_edge_time2 = get_cumm_time_edge(time_map=distribution_dict["edges"], 
        #                                     num_iters=len(e2e_all_sessions), 
        #                                     edge_set=['2-5', '3-5', '4-5'])
        
        # cumm_edge_time = np.array([sum(x) for x in list(zip(cumm_edge_time1, cumm_edge_time2))])
        cumm_edge_time = np.array(cumm_edge_time1)
        ####### CUSTOM edge timing calculation (End) ####


        cumm_e2e_time = np.array([t/1000 for t in e2e_all_sessions])

        # Write to file for later use
        cumm_time_dir_path = out_path / f"cumm_time_dir"
        if not os.path.exists(cumm_time_dir_path):
            os.mkdir(cumm_time_dir_path)

        logger.info(f"Writing the cummulative timings dictionary to {cumm_time_dir_path}")
        with open(cumm_time_dir_path / f"cumm_time_dict.json", "w") as outfile:
            cumm_time_dict = dict(cumm_e2e_time=list(cumm_e2e_time),
                                  cumm_edge_time=list(cumm_edge_time),
                                  cumm_func_time=list(cumm_func_time))
            json.dump(cumm_time_dict, outfile, indent=2)

        bplot2 = ax2.boxplot([cumm_func_time, cumm_edge_time, cumm_e2e_time],
                             positions=[len(interleaved_data) + offset for offset in range(1,4)],
                             vert=True,
                             patch_artist=True,
                             showfliers=False)
        
        
        # color='pink'
        colors = ['blue', 'green', 'brown']
        for patch, color in zip(bplot2['boxes'], colors):
            patch.set_facecolor(color)

        # ax2.set_ylim(ymin=0, ymax=max(yticks_ax2))
        ax2.set_yticks(yticks_ax2)
        ax2.set_yticklabels([str(x) for x in yticks_ax2])
        ax2.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
        # UNCOMMENT / COMMENT FROM HERE (END)
        ######## CUMMULATIVE TIME ADDITION (END#########
        
        # NOTE - modify this label to include the function and edge abbreviations
        # interleaved_labels_modified = ['GGen', 'GGen-BFT', 'GGen-PR', 'GGen-MST', 'BFT', 'BFT-Agg', 'PR', 'PR-Agg', 'MST', 'MST-Agg', 'Agg'] + cumm_labels
        interleaved_labels_modified = []
        logger.info(f"Interleaved Labels - {interleaved_labels_modified+cumm_labels}")
        ax.set_xticklabels(interleaved_label_ids+cumm_labels, 
                           rotation=90,
                           fontdict=fontdict)
        


        ytickslabels = [str(x) for x in yticks_ax1]
        # ax.set_ylim(ymin=0, ymax=max(yticks_ax1))
        ax.set_yticks(yticks_ax1)
        ax.set_yticklabels(ytickslabels,
                           fontdict=fontdict)

        ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
        ax.set_ylim(ymin=0)
        for idx, patch in enumerate(bplot1['boxes']):
            patch.set_facecolor(get_color(interleaved_label_ids[idx]))

        # set the label colors
        for idx, xtick in enumerate(ax.get_xticklabels()[0:len(interleaved_label_ids)]):
            xtick.set_color(get_label_color(interleaved_label_ids[idx]))

        ##### VLINES #####
        # add a separator between the cumulative and the function timings
        vlines_x_cumm_sep = [(ax.get_xticks()[len(interleaved_label_ids)-1] + ax.get_xticks()[len(interleaved_label_ids)])/2]
        ax.vlines(x=vlines_x_cumm_sep, ymin=0, ymax=max(yticks_ax1), linestyles='solid', color='black')
        
        # add lighter vlines between the boxes themselves
        _xloc = ax.get_xticks()[0: len(interleaved_label_ids)]
        vlines_x_between = []
        for idx in range(0, len(_xloc)-1):
            vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
        ax.vlines(x=vlines_x_between, ymin=0, ymax=max(yticks_ax1), linestyles='solid', color='darkgrey')

        # add lighter vlines between the cumm functions
        _xloc = ax.get_xticks()[len(interleaved_label_ids):]
        vlines_x_between_cumm = []
        for idx in range(0, len(_xloc)-1):
            vlines_x_between_cumm.append(_xloc[idx]/2 + _xloc[idx+1]/2)
        ax.vlines(x=vlines_x_between_cumm, ymin=0, ymax=max(yticks_ax1), linestyles='solid', color='darkgrey')
        ###### VLINES ####

        ax.grid(axis="y", which="major", linestyle="-", color="black")
        ax.grid(axis="y", which="minor", linestyle="-", color="grey")
        ax.set_axisbelow(True)
        
        fig.savefig(plots_path / f"interleaved_exec_box_{wf_name}_{csp}_{dynamism}_{payload}_same_scaled.{format}", bbox_inches='tight')
        

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
    # filtered_dynamo_items = defaultdict(list)
    # filtered_dynamo_items["Items"] = [item for item in dynamo_items["Items"] if item["workflow_deployment_id"] == workflow_deployment_id]

    timings_all_sessions = dict()
    e2e_all_sessions = []
    time_marker_sessions = []
    timestamps = sorted([int(item["invocation_start_time_ms"]) for item in dynamo_items["Items"]])
    start_time = timestamps[0]
    # NOTE - this timeline is in seconds
    timeline = [(x-start_time)/1000 for x in timestamps]

    # create the session_id -> timings dict.
    for session_id, conf in experiment_conf.items():
        logger.info(f"Getting Timings For Session Id - {session_id}")
        timings = get_timings(dynamo_items=dynamo_items, session_id=session_id)
        e2e_timings = timings["e2e_timings"]
        logger.info(len(e2e_timings))
        e2e_all_sessions += e2e_timings 
        time_marker_sessions.append(len(e2e_timings))   
        timings_all_sessions[session_id] = timings

    # NOTE - that the e2e_timings all sessions are in milliseconds here 
    # The plotting part is where we do a /1000 for convert to seconds
    # plot e2e timeline
    # plot_e2e_timeline(
    #     e2e_all_sessions=e2e_all_sessions,
    #     time_marker_sessions=time_marker_sessions,
    #     timeline=timeline
    # )

    # plot box plots
    plot_box_plots(
        xfaas_dag=xfaas_dag,
        timings_all_sessions=timings_all_sessions,
        e2e_all_sessions=e2e_all_sessions
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
        os.makedirs(out_path)
    
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
    
    # logger.info("Plotting Timeline")
    # plotter(
    #     workflow_deployment_id=workflow_deployment_id,
    #     experiment_conf=experiment_conf
    # )

    # delete_temp(workflow_deployment_id=workflow_deployment_id)