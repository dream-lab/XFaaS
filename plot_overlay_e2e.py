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
# from azure.storage.queue import QueueService, QueueMessageFormat
from serwo.python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from serwo.python.src.utils.classes.commons.logger import LoggerFactory

# logger = LoggerFactory.get_logger(__file__, log_level="INFO")

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


def get_from_dynamo(filepath):
    with open(filepath, "r") as file:
        res = defaultdict(list)
        lines = file.readlines()
        for line in lines:
            res["Items"].append(json.loads(line))
    return res


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
    # ax.set_yticks(yticks)
    # ax.set_yticklabels([str(y) for y in yticks])

    ax.set_ylim(ymin=0)
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
    step_y = [1,4,8,4,1]
    invoc_id = 0
    step_x = []
    for rps in step_y:
        invoc_id = invoc_id + 60
        step_x.append(invoc_id)

    # logger.info(f"Step X - {step_x}")
    ax2 = ax.twinx()
    ax2.set_ylim(ymin=0)
    ax2.set_ylabel("RPS", fontdict=fontdict)
    ax2.set_yticks([y for y in range(0, 9)])
    ax2.set_yticklabels([str(y) for y in range(0, 9)], fontdict=fontdict)
    ax2.step([0] + step_x, [1] + step_y, linestyle='dashed', color='red')
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


def per_file_e2e_timings(filepath):
    # logger.info("Querying DynamoDB Once")
    # dynamo_items = get_from_dynamo(workflow_deployment_id=workflow_deployment_id)
    # logger.info("Querying File Mock Dynamo")
    dynamo_items = get_from_dynamo(
                        filepath=filepath
                    )
    # Sorted timestamps
    timestamps = sorted([int(item["invocation_start_time_ms"]) for item in dynamo_items["Items"]])
    start_time = timestamps[0]
    # NOTE - this timeline is in seconds
    timeline = [(x-start_time)/1000 for x in timestamps]
    
    # Request execution logs sorted by invocation start time
    sorted_dynamo_items = sorted(dynamo_items["Items"],key=lambda x: x["invocation_start_time_ms"])
    sink_node = [node for node in xfaas_dag.nodes if xfaas_dag.out_degree(node) == 0][0]

    # item in seconds
    e2e_time_per_req = [item["functions"][sink_node]["end_delta"]/1000 for item in sorted_dynamo_items]

    return e2e_time_per_req, timeline

    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="What the program does",
        epilog="Text at the bottom of help",
    )

    parser.add_argument("--user-dir",dest='user_dir',type=str,help="Workflow User Directory")
    parser.add_argument("--format",dest="format",type=str,help="Plot format (svg | pdf)")
    parser.add_argument("--out-file",dest="out_file",type=str,help="Output Filepath")
    args = parser.parse_args()

    user_dir = pathlib.Path(args.user_dir)
    format = args.format
    out_file = args.out_file + f".{format}"
    out_path = pathlib.Path(__file__).parent / f"serwo/bigdata-plots"
    
    dagfilepath = user_dir / "dag-original.json"
    xfaas_dag = DagLoader(dagfilepath).get_dag()

    # AWS filepaths
    small_1rps_fp = "/Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/FileSystemRevisedAws/build/workflow/resources/filesystem-aws-static-small-1rps/fileProcessing_aws_static_small_dyndb_items.jsonl"
    medium_1rps_fp = "/Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/FileSystemRevisedAws/build/workflow/resources/filesystem-aws-static-medium-1rps/fileProcessing_aws_static_medium_dyndb_items.jsonl"

    # Azure filepaths
    # small_1rps_fp = "/Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/FileSystemRevisedAz/build/workflow/resources/filesystem-azure-static-small-1rps/fileProcessing_azure_static_small_dyndb_items.jsonl"
    # medium_1rps_fp = "/Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/FileSystemRevisedAz/build/workflow/resources/filesystem-azure-static-medium-1rps/fileProcessing_azure_static_medium_dyndb_items.jsonl"
    # large_1rps_fp = "/Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/FileSystemRevisedAz/build/workflow/resources/filesystem-azure-static-large-1rps/fileProcessing_azure_static_large_dyndb_items.jsonl"

    # logger.info("Plotting Timeline")

    exec_time1, timeline1 = per_file_e2e_timings(small_1rps_fp)
    exec_time2, timeline2 = per_file_e2e_timings(medium_1rps_fp)
    # exec_time3, timeline3 = per_file_e2e_timings(large_1rps_fp)
    
    # logger.info("Time 1")
    # print(exec_time1, timeline1)
    # logger.info("Time 2")
    # print(exec_time2, timeline2)

    # Plotting code 
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fontdict = {'size': 12}
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.set_ylabel("E2E time (sec)", fontdict=fontdict)
    # NOTE - PLOT WITH TIMELINE
    ax.set_xlabel("Timeline (sec)", fontdict=fontdict)



    
    # plot small
    ax.plot(timeline1, exec_time1, linewidth=1, linestyle='-', color='green', label='Small')
    # plot medium
    ax.plot(timeline2, exec_time2, linewidth=1, linestyle='-', color='blue', label='Medium')
    # plot large
    # ax.plot(timeline3, exec_time3, linewidth=1, linestyle='-', color='red', label='Large')

    ax.xaxis.set_tick_params(which='major', labelsize=fontdict['size'])
    ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
    
    ax.set_ylim(ymin=0, ymax=1000)
    yticks = [x for x in range(0,1200,200)]
    yticklabels = [str(x) for x in yticks]
    ax.set_yticks(yticks)
    # ax.set_yticklabels(yticklabels)
    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.legend(loc='upper left')

    plt.savefig(out_path / f"{out_file}", bbox_inches='tight')