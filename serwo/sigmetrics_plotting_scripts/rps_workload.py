import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import sys
import os
import json
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from datetime import datetime
import get_aws_containers as aws_containers

import shutil
import numpy as np
import networkx as nx
import pathlib
import pprint
import argparse
import statistics

from typing import Any
from collections import defaultdict
from matplotlib.lines import lineStyles
from azure.storage.queue import QueueClient
from python.src.utils.classes.commons.logger import LoggerFactory
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
logger = LoggerFactory.get_logger(__file__, log_level="INFO")

X = []
Y = []
Y2 = []
C = []
N = []
OVERLAYS = []
containers = []
nums = []
colors_global = ['#EBEB00','#00EBEB','#00EB00']
NEW_X = []
NEW_Y = []
class XFBenchPlotter: 
    '''
    These are base parameters for the plt globally applied in case you explictly don't set anything
    via fontdicts etc.
    These will be used by default - you can add your customizations via code to override this
    '''
    plt.rcParams['ytick.labelsize'] = 20
    plt.rcParams['xtick.labelsize'] = 20
    plt.rcParams['axes.titlesize'] = 20
    plt.rcParams['axes.labelsize'] = 20
    plt.rcParams['legend.fontsize'] = 20

    def __init__(self, workflow_directory: str, workflow_deployment_id: str, run_id: str, format: str):
        self.__workflow_directory = workflow_directory
        self.__workflow_deployment_id = workflow_deployment_id
        self.__run_id = run_id
        self.__xfaas_dag = self.__init__dag(pathlib.Path(self.__workflow_directory) / "dag.json")
        self.__format = format

        '''
        Constructed directories and paths
        '''
        self.__exp_directory = pathlib.Path(self.__workflow_directory) / self.__workflow_deployment_id / self.__run_id
        self.__artifacts_filepath = self.__exp_directory / "artifact.json"
        self.__logs_dir = self.__exp_directory / "logs"
        self.__plots_dir = self.__exp_directory / "plots"
        self.__plots_dir_upd = f"{self.__workflow_directory}/plots/overleaf"
        self.__plots_dir_upd2 = f"{self.__workflow_directory}/plots2/overleaf"

        # Create the logs and the plots directory
        if not os.path.exists(self.__logs_dir):
            os.makedirs(self.__logs_dir)

        if not os.path.exists(self.__plots_dir):
            os.makedirs(self.__plots_dir)

        if not os.path.exists(self.__plots_dir_upd):
            os.makedirs(self.__plots_dir_upd)
        
        if not os.path.exists(self.__plots_dir_upd2):
            os.makedirs(self.__plots_dir_upd2)

        '''
        Using provenance artifacts to construct the experiment configuration
        '''
        if not os.path.exists(self.__artifacts_filepath):
            raise FileNotFoundError(f"artifact.json Not Found under {self.__exp_directory}")
        
        '''
        Construct the experiment configuration from the artifacts
        '''
        with open(self.__artifacts_filepath, "r") as file:
            config = json.load(file)
        
        
        # TODO - create a function which generate the step_x and step_y from the exp_config
        self.__exp_conf = config.get("experiment_conf")
        self.__queue_name = config.get("queue_details").get("queue_name")
        self.__conn_str = config.get("queue_details").get("connection_string")
        self.__config = config
        
        '''
        Create an experiment description dictionary
        '''
        temp_conf = list(self.__exp_conf.values())[0]
        self.__exp_desc = dict(wf_name=temp_conf.get("wf_name"),
                               csp=temp_conf.get("csp"),
                               dynamism=temp_conf.get("dynamism"),
                               payload=temp_conf.get("payload_size"))
        

        self.__logfile = f"{self.__get_outfile_prefix()}_dyndb_items.jsonl"

        '''
        Get the data from the queue and push to the file
        NOTE - if you call this again and logfile exists then it won't pull from queue
        '''
        if not os.path.exists(self.__logs_dir / self.__logfile):
            self.__get_from_queue_add_to_file()


        # Constructor
    def __init__dag(self, user_config_path):
        __dag_config_data = dict() # dag configuration (picked up from user file)
        __nodeIDMap = {} # map: nodeName -> nodeId (used internally)
        __dag = nx.DiGraph() # networkx directed graph
        # throw an exception if loading file has a problem
        def __load_user_spec(user_config_path):
            with open(user_config_path, "r") as user_dag_spec:
                dag_data = json.load(user_dag_spec)
            return dag_data
        try:
            __dag_config_data = __load_user_spec(user_config_path)
            __workflow_name = __dag_config_data["WorkflowName"]
        except Exception as e:
            raise e
    
        index = 1
        for node in __dag_config_data["Nodes"]:
            nodeID = node["NodeId"]
            # TODO - add a better way to add node codenames to the DAG
            __nodeIDMap[node["NodeName"]] = nodeID
            __dag.add_node(nodeID,
                                NodeId=nodeID,
                                NodeName=node["NodeName"], 
                                Path=node["Path"],
                                EntryPoint=node["EntryPoint"],
                                MemoryInMB=node["MemoryInMB"],
                                Codename=node["Code"])
            index += 1

        # add edges in the dag
        for edge in __dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    __dag.add_edge(__nodeIDMap[key], __nodeIDMap[val])
        return __dag

    def __get_outfile_prefix(self):
        
        prefix = f"{self.__exp_desc.get('wf_name')}_{self.__exp_desc.get('csp')}_{self.__exp_desc.get('dynamism')}_{self.__exp_desc.get('payload')}"
        
        return prefix


    def __create_dynamo_db_items(self):
        print("Creating DynamoDB items")
        dynamodb_item_list = []

        queue = QueueClient.from_connection_string(conn_str=self.__conn_str, queue_name=self.__queue_name)
        response = queue.receive_messages(visibility_timeout=3000)
        print('Reading Queue')
        for message in response:
            queue_item = json.loads(message.content)
            metadata = queue_item["metadata"]
            # print(metadata)
            
            # Filtering based on workflow deployment id during creation itself
            if metadata["deployment_id"].strip() == self.__workflow_deployment_id:
                dynamo_item = {}
                invocation_id = f"{metadata['workflow_instance_id']}-{metadata['session_id']}"
                dynamo_item["workflow_deployment_id"] = metadata["deployment_id"]
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
    
    def __get_from_queue_add_to_file(self):
        logger.info(f"Getting Items from Queue - {self.__queue_name}")
        sorted_dynamo_items = sorted(self.__create_dynamo_db_items(), key=lambda x: int(x["client_request_time_ms"]))
        with open(self.__logs_dir / self.__logfile, "w") as file:
            for dynamo_item in sorted_dynamo_items:
                dynamo_item_string = json.dumps(dynamo_item) + "\n"
                file.write(dynamo_item_string)


    def __get_provenance_logs(self):
        logger.info(f"Reading logfile {self.__logfile}")
        with open(self.__logs_dir / self.__logfile, "r") as file:
            loglines = [json.loads(line) for line in file.readlines()]
        return loglines
    
    def __get_e2e_time(self, log_items):
        e2e_time = [] 
        min_time = int(log_items[0]["invocation_start_time_ms"])
        sink_node = [node for node in self.__xfaas_dag.nodes if self.__xfaas_dag.out_degree(node) == 0][0]
        for item in log_items:
            ts = (int(item["invocation_start_time_ms"])-min_time)/1000 # time in seconds
            # if ts <= 300:
            e2e_time.append(int(item["functions"][sink_node]["end_delta"])/1000) # e2e time in seconds
        print(len(e2e_time))
        return e2e_time

    def get_overlay(self):
        loglines = self.__get_provenance_logs()
        exp_conf = self.__exp_conf
        sessions_map = {}
        for xd in exp_conf:
            sessions_map[xd.strip(' ')] = exp_conf[xd]["rps"]
        overlays = []
        for log in loglines:
            session_id = log["session_id"].strip(' ')
            overlays.append(sessions_map[session_id])
        return overlays

    def slide(self,x,bucket):
        ans_y =[]
        for i in range(0,bucket):
            ans_y.append(x[i])
        
        for i in range(bucket,len(x)):
            st = i-bucket+1
            en = i+1
            c=0
            s=0
            for j in range(st,en):
                c += 1
                s += x[j]
            ans_y.append(s/c)


        return ans_y

    def plot(self,csp):
        logger.info(f"Plotting {self.__logfile}")
        loglines = self.__get_provenance_logs()
        overlay_data = self.get_overlay()
        OVERLAYS.append(overlay_data)
        print(len(overlay_data))
        timestamps = [int(item["invocation_start_time_ms"]) for item in sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"]))] # NOTE - the timeline is w.r.t client
        timeline = []
        for t in timestamps:
            ts = (t-timestamps[0])/1000
            # if ts <= 300:
            timeline.append(ts)

        e2e_time = self.__get_e2e_time(log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])))
        X.append(timeline)
        Y.append(self.slide(e2e_time,5))

        if csp == "aws":
            if "app_name" in self.__config:
                app_name = self.__config.get("app_name")
                log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"]))
                min_timestamp = int(log_items[0]["invocation_start_time_ms"])
                
                aws_containers_ts = aws_containers.get_container_count(app_name)
                aws_containers_ts = dict(sorted(aws_containers_ts.items()))
                container_spawn_times = list(aws_containers_ts.keys()) 
                # print('container spawn times: ',container_spawn_times)
                wall_clock_times = [datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M:%S') for t in container_spawn_times]
                
                container_spawn_times = [int(int(t) - min_timestamp/1000) for t in container_spawn_times]
                # temp = []
                # for i in container_spawn_times:
                #     # if i <=300:
                #     #     temp.append(i)
                container_spawn_times = [i for i in container_spawn_times]
                offset = container_spawn_times[0]
                container_spawn_times = [t-offset for t in container_spawn_times]
                num_containers = list(aws_containers_ts.values())
                print('container spawn times: ',container_spawn_times)
                print('num containers: ',num_containers)
                ## init list with 0s 
                yy = []
                cur_ptr = 1
                timeline_ptr = 0
                while timeline_ptr < len(timeline):
                    while container_spawn_times[cur_ptr] > timeline[timeline_ptr]:
                        yy.append(num_containers[cur_ptr-1])
                        timeline_ptr += 1
                        if timeline_ptr >= len(timeline):
                            break
                    cur_ptr += 1
                    if cur_ptr >= len(container_spawn_times):
                        while timeline_ptr < len(timeline):
                            yy.append(num_containers[cur_ptr-1])
                            timeline_ptr += 1
                        break

                print('Len of yy: ',len(yy))
                # print(yy)
                Y2.append(yy)
                
                
            else:
                Y2.append([]) 
        else:
            containers, mins = self.__get_azure_containers(log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])),time_line=timeline)
        

    def __get_azure_containers(self, log_items: list,time_line: list):
            # array for storing the workflow invocation ids
            wf_invocation_ids = set() # TODO - check with VK.
            dag = self.__xfaas_dag
            ## find sink node in networkx graph
            sink_node = None
            for node in dag.nodes():
                if dag.out_degree(node) == 0:
                    sink_node = node
                    break
            
            god_dict = {}
            ans = []
            mins = []
            sorted_dynamo_items = log_items
            min_start_time  = sorted_dynamo_items[0]["invocation_start_time_ms"]
            # print(sorted_dynamo_items)
            function_map = set()
            for item in sorted_dynamo_items:
                functions = item['functions']
                workflow_start_time = item['invocation_start_time_ms']

                # New addition - 
                wf_invocation_id = item['workflow_invocation_id']

                for function in functions:
                    if "cid"  in functions[function]:
                        cid = functions[function]['cid']
                        function_start_delta = functions[function]['start_delta']
                        function_start_time = int(workflow_start_time) + function_start_delta
                        if cid == '':
                            continue
                        if cid not in god_dict:
                            god_dict[cid] = []
                            
                            god_dict[cid].append((function_start_time,int(workflow_start_time), wf_invocation_id,function))
                        else:
                            god_dict[cid].append((function_start_time,int(workflow_start_time), wf_invocation_id,function))  
                        
                            

            
            functions = []
            tempp = []
            print('experiment start time:',datetime.fromtimestamp(int(min_start_time)//1000).strftime('%Y-%m-%d %H:%M:%S'))
            for cid in god_dict:
                god_dict[cid].sort()
                ## convert epoch to datetime
                epoch_st = god_dict[cid][0][1]
                epoch_en = god_dict[cid][-1][1]
                # print(epoch_st,epoch_en)
                readable_st = datetime.fromtimestamp(int(epoch_st//1000)).strftime('%Y-%m-%d %H:%M:%S')
                readable_en = datetime.fromtimestamp(int(epoch_en//1000)).strftime('%Y-%m-%d %H:%M:%S')
                tempp.append(((epoch_st- int(min_start_time))/1000,(epoch_en-int(min_start_time))/1000))
                
                print(f'cid: {cid} fist ts:',readable_st)
                print(f'cid: {cid} last ts:',readable_en)
                ans.append(god_dict[cid][0])
                # mins.append((god_dict[cid][0][0]-int(min_start_time))/1000)
                mins.append(((god_dict[cid][0][1]-int(min_start_time))/1000,god_dict[cid][0][2]))
                wf_invocation_ids.add(god_dict[cid][0][2])
                
                functions.append(god_dict[cid][0][3])
            
            concurrent_execs = []
            for i in range(0,len(time_line)):
                c = 0
                ts = time_line[i]
                for j in range(0,len(tempp)):
                    if tempp[j][0] <= ts and tempp[j][1] >= ts:
                        c+=1
                concurrent_execs.append(c)
                
            medians = []
            second_y = []
            cur_ptr = 0
            lol = []
            mins = sorted(mins)
            for i in range(0,len(mins)-1):
                temp  = []
                target_inv_id = mins[i+1][1]
                max_ts = 0
                while log_items[cur_ptr]['workflow_invocation_id'] != target_inv_id:
                    temp.append(log_items[cur_ptr]['functions'][sink_node]['end_delta'])
                    max_ts = (int(log_items[cur_ptr]['invocation_start_time_ms']) - int(min_start_time))/1000
                    lol.append(i+1)
                    cur_ptr+=1
                if len(temp) >= 1:
                    medians.append((statistics.median(temp),i+1))
                    second_y.append(max_ts)

            y = [t[0]/1000 for t in medians]
            diff = len(log_items) - len(lol)
            last = lol[-1]
            for i in range(0,diff):
                lol.append(last)
            container_count = lol

            print(len(concurrent_execs))
            Y2.append(concurrent_execs)

            print('Len God Dict:',len(god_dict))

            new_x = []
            new_y = []

            # for i in range(0,len(x)):
            #     new_x.append(x[i])
            #     c = (x[i])/(y[i])
            #     new_y.append(c)
            
            # NEW_X.append(new_x)
            # NEW_Y.append(new_y)
                
            
            return mins, wf_invocation_ids


def plot_metrics(user_wf_dir, wf_deployment_id, run_id,csp):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot(csp)


def split(x,y,overlays):
    # print(overlays)
    i = 0
    split_points = []
    for i in range(0,len(overlays)-1):
        if overlays[i] == 8 and overlays[i+1] == 1:
            split_points.append(i+1)
    
    first = split_points[0]
    second = split_points[1]

    x1 = x[:first]
    y1 = y[:first]

    x2 = x[first:second]
    y2 = y[first:second]

    x3 = x[second:]
    y3 = y[second:]

    split1 = (x1,y1)
    split2 = (x2,y2)
    split3 = (x3,y3)

    return split1,split2,split3 


def plot_8rps(wf, dynamism, colors, large_x, large_y, large_y2):
    fig, ax = plt.subplots()
    ax.set_ylabel("Sliding Window Avg. E2E Time (secs)",fontsize = 16)
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="both", which="major", linestyle="-", color="black")
    ax.grid(axis="both", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.set_xlabel('Timeline (sec)')
    ax.set_ylim(ymin=0)

    yticks = [0,40,80,120,160,200]
    yticks2 = [int(y*1.8) for y in yticks]
    yticks2 = [0,60,120,180,240,300]
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    

    zs  = [2,1,0]
    
    ax2 = ax.twinx()
    ax2.set_ylabel("# Of Concurrent Req")
    for i in range(0,len(large_x)):
        x = large_x[i]
        y = large_y[i]

        cx = []
        cy = []
        for j in range(len(x)):
            if y[j]>=200:
                cx.append(x[j])
                cy.append(y[j])
        for j in range(len(cx)):
            ax.text(cx[j]-10,200,int(cy[j]),c= 'green',fontsize=14)
        ax.plot(large_x[i],large_y[i],color =colors[i],zorder=zs[i])
    ax2.set_ylim(ymin=0)
    ax.set_xlim(xmin=0,xmax=300)
    if not yticks2 == []:
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([str(x) for x in yticks2])
    linestyles = ['--', '--', '-.']
    print(len(large_y2)-2)
    ax.grid(axis="both", which="major", linestyle="-", color="gray", linewidth = 0.2)

    ax.grid(axis="both", which="minor", linestyle="--", color="silver", linewidth = 0.2)
    zd = [5,4,3]
    for i in range(0,len(large_y2)):
        ax2.plot(large_x[i],large_y2[i],color=colors_global[i], linestyle='--',zorder=zd[i])
    plt.savefig(f"other_wfs_scaling_plot/{wf}_8rps.pdf", bbox_inches='tight')

def plot_4rps(wf, dynamism, colors, medium_x, medium_y, medium_y2):
    fig, ax = plt.subplots()
    ax.set_ylabel("Sliding Window Avg. E2E Time (secs)",fontsize=16)
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.set_xlabel('Timeline (sec)')
    ax.set_xlim(xmin=0,xmax=300)
    ax.set_ylim(ymin=0)
    yticks = [0,20,40,60,80,100]
    yticks2 = [int(1.5*y) for y in yticks]
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax2 = ax.twinx()
    ax2.set_ylabel("# Of Concurrent Req")
    zz = [2,1,0]
    for i in range(0,len(medium_x)):
        print(len(medium_x[i]),len(medium_y[i]))
        x = medium_x[i]
        y = medium_y[i]

        cx = []
        cy = []
        for j in range(len(x)):
            if y[j]>=100:
                cx.append(x[j])
                cy.append(y[j])
        for j in range(len(cx)):
            ax.text(cx[j]-10,100,int(cy[j]),c= 'green',fontsize=14)
        
        ax.plot(medium_x[i],medium_y[i],color =colors[i],zorder=zz[i])
    ax2.set_ylim(ymin=0)
    if not yticks2 == []:
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([str(x) for x in yticks2])
    linestyles = ['--', '--', '-.']
    ax.grid(axis="both", which="major", linestyle="-", color="gray", linewidth = 0.2)

    ax.grid(axis="both", which="minor", linestyle="--", color="silver", linewidth = 0.2)
    
    zz = [5,4,3]
    for i in range(0,len(medium_y2)):
        ax2.plot(medium_x[i],medium_y2[i],color=colors_global[i], linestyle='--',zorder=zz[i])
    plt.savefig(f"other_wfs_scaling_plot/{wf}_4rps.pdf", bbox_inches='tight')

def plot_1rps(wf, dynamism, colors, small_x, small_y, small_y2, aws_legend, az_legend, azv2_legend):
    fig, ax = plt.subplots()
    ax.set_ylabel("Sliding Window Avg. E2E Time (secs)",fontsize=16)
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.set_xlabel('Timeline (sec)')
    if 'image' in wf:
        ax.set_ylim(ymin=0,ymax=300)
        yticks = [0,60,120,180,240,300]
        yticks2 = [0,20,40,60,80,100]
    if 'text' in wf:
        ax.set_ylim(ymin=0,ymax=900)
        yticks = [0,150,300,450,600,750,900]
        yticks2 = [0,50,100,150,200,250,300]

    if 'math' in wf:
        ax.set_ylim(ymin=0,ymax=40)
        yticks = [0,10,20,30,40]
        yticks2 = [0,15,30,45,60]
    if 'graph' in wf:
        ax.set_ylim(ymin=0,ymax=40)
        yticks = [0,10,20,30,40,50]
        yticks2 = [0,10,20,30,40,50]

    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax2 = ax.twinx()
    ax2.set_ylabel("# Of Concurrent Req")
    label1 = 'E2E Time'
    label2 = '# Of Concurrent Req'
    z_layers = [2,1,0]
    for i in range(0,len(small_x)):
        # l1 = ax.plot(small_x[(i+1)%len(small_x)],small_y[(i+1)%len(small_x)],color =colors[(i+1)%len(small_x)],label=label1)
        l1 = ax.plot(small_x[i],small_y[i],color =colors[i],label=label1,zorder=z_layers[i])
    ax.set_xlim(xmin=0,xmax=300)
    ax2.set_ylim(ymin=0)
    if 'math' in wf:
        ax2.set_ylim(ymin=0,ymax=61)
    if not yticks2 == []:
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([str(x) for x in yticks2])
    linestyles = ['--', '--', '-.']
    zz = [5,4,3]
    for i in range(0,len(small_y2)):
        l2 = ax2.plot(small_x[i],small_y2[i],color=colors_global[i], linestyle='--',label=label2,zorder=zz[i])
    
    lstt = [aws_legend,az_legend,azv2_legend]
    lsttlabel = [i.get_label() for i in lstt] + ['E2E','# of Conc. Req.']
    lstt = lstt + [Line2D([0],[0],color="black",lw=1,linestyle='-'),Line2D([0],[0],color="black",lw=1,linestyle='--')] 
    ax.grid(axis="both", which="major", linestyle="-", color="gray", linewidth = 0.2)

    ax.grid(axis="both", which="minor", linestyle="--", color="silver", linewidth = 0.2)
    if 'graph' in wf or 'math' in wf:
        ax.legend(lstt,lsttlabel,loc='upper right',prop={'size': 12})

    plt.savefig(f"other_wfs_scaling_plot/{wf}_1rps.pdf", bbox_inches='tight')

if __name__ == "__main__":
    run_id = 'exp1'
    parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
    parser.add_argument("--dynamism",dest='dynamism',type=str,help="Dynamism")
    parser.add_argument("--wf",dest='wf',type=str,help="wf")
    # parser.add_argument("--dynamism",dest='dynamism',type=str,help="dynamism")
    
    args = parser.parse_args()
    
    wf = args.wf
    dynamism = args.dynamism

    deployments_filename = 'serwo/custom_deployments.txt'

    data = []
    with open(deployments_filename,'r') as f:
        for line in f:
            data.append(line.strip().split(','))

    i = 0
    
    for d in data:
        wf_user_directory = '/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf'
        if i==0 or i==3 or i==6:
            wf_user_directory = args.wf_user_directory
        if i<=2:
            wf_user_directory += '_aws'
        # if i>=6:
        #     wf_user_directory += '_part32'
        wf_user_directory += '/workflow-gen'
        wf_deployment_id = d[0]
        csp = d[1]
        region = d[2]
        max_rps = d[3]
        duration = d[4]
        payload_size = d[5]
        dynamism = d[6]
        plot_metrics(wf_user_directory,wf_deployment_id,run_id,csp)
        i+=1


    # print(X,Y)
    dynamism = args.dynamism
    # print(NEW_X,NEW_Y)

    colors = ['orange','blue','green','orange','blue','green','orange','blue','green']
    
    if dynamism == 'static':
       labels = ['AzS', 'AzM','AzL' ,'AzV2S', 'AzV2M','AzV2L']
    elif dynamism == 'rps':
        labels = ['Az1', 'Az4','Az8' ,'AzV21', 'AzV24','AzV28']
    elif dynamism == 'workload':
        labels = ['AzSU', 'AzST','AzAL' ,'AzV2SU', 'AzV2ST','AzV2AL']
    
    # colors = ['red','green','blue','red','green','blue']
    lineStyles = ['dashed','dashed','dashed','solid','solid','solid']

    print(len(X),len(Y),len(Y2))
    # print(X,Y,Y2)

    prod_x = X
    prod_y = Y
    prod_y2 = Y2


    # small_x =[prod_x[0],prod_x[2],prod_x[5]]
    # small_y =[prod_y[0],prod_y[2],prod_y[5]]
    # small_y2 =[prod_y2[0],prod_y2[2],prod_y2[5]]

    # medium_x =[prod_x[1],prod_x[3],prod_x[6]]
    # medium_y =[prod_y[1],prod_y[3],prod_y[6]]
    # medium_y2 =[prod_y2[1],prod_y2[3],prod_y2[6]]

    # large_x =[prod_x[4],prod_x[7]]
    # large_y =[prod_y[4],prod_y[7]]
    # large_y2 =[prod_y2[4],prod_y2[7]]

    small_x =[prod_x[0],prod_x[3],prod_x[6]]
    small_y =[prod_y[0],prod_y[3],prod_y[6]]
    small_y2 =[prod_y2[0],prod_y2[3],prod_y2[6]]

    medium_x =[prod_x[1],prod_x[4],prod_x[7]]
    medium_y =[prod_y[1],prod_y[4],prod_y[7]]
    medium_y2 =[prod_y2[1],prod_y2[4],prod_y2[7]]

    large_x =[prod_x[2],prod_x[5],prod_x[8]]
    large_y =[prod_y[2],prod_y[5],prod_y[8]]
    large_y2 =[prod_y2[2],prod_y2[5],prod_y2[8]]

    aws_legend = mpatches.Patch(color='orange', label='AWS')
    az_legend = mpatches.Patch(color='blue', label='AzS')
    azv2_legend = mpatches.Patch(color='green', label='AzN')


    plot_1rps(wf, dynamism, colors, small_x, small_y, small_y2, aws_legend, az_legend, azv2_legend)
    plot_4rps(wf, dynamism, colors, medium_x, medium_y, medium_y2)
    plot_8rps(wf, dynamism, colors, large_x, large_y, large_y2)

    

'''
for this plot

graph 

# eeda154b-7636-4795-9060-3ba91ccbd574,aws,centralindia,1,300,small,static
# b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
# 81dd3382-0546-4f5a-b5a1-282b1801dccd,azure,centralindia,1,300,small,static
# fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
# c1d356e2-4b2f-409f-b95b-3408a1699ce2,azure,centralindia,1,300,large,static
# 372dbfee-18a4-461d-b74d-cb67accf3ed4,azure_v2,centralindia,1,300,small,static
# ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
# ad1b6078-3199-4f9d-8a72-a5b4d340183a,azure_v2,centralindia,1,300,large,static

static

b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
d3a52922-f314-4558-aa7d-6828fb9b9e53,aws,centralindia,4,300,medium,static
056d4692-91b9-44c6-894d-406b77031007,aws,centralindia,8,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static
06b77318-7e18-4fa3-a32d-28b3db1796f5,azure_v2,centralindia,4,300,medium,static
84491da9-cdab-4288-81be-08fa67c6240c,azure_v2,centralindia,8,300,medium,static


workload

a153db95-3ac2-440c-9f36-f086168b4ece,aws,centralindia,8,300,medium,step_function
7c40fda9-5263-4b13-8613-d472241f1fa3,aws,centralindia,8,300,medium,sawtooth
c29b8954-1e4c-4d71-9713-cc452628df1f,aws,centralindia,8,300,medium,alibaba
46f16fb7-f991-4886-b023-2af9b3b1dd15,azure,centralindia,8,300,medium,step_function
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
e5d5ac76-f1d2-48d0-839e-a1a23099e1f7,azure_v2,centralindia,8,300,medium,step_function
3c4d6c54-e970-4fba-8aad-d132c9127509,azure_v2,centralindia,8,300,medium,sawtooth
3eeb8f2f-d31a-4fe0-a439-9bf4c9126cad,azure_v2,centralindia,8,300,medium,alibaba















other

img

d8187ac8-6eb7-41f2-99bb-5470bbf8b139,aws,centralindia,1,300,small,static
3663405c-2fa9-4e83-9488-4f7fcbca3676,aws,centralindia,1,300,medium,static
307f3d81-c23f-489b-ab56-85c9fd0036d4,azure,centralindia,1,300,small,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
67dd0dc1-650a-4ea3-a980-5a02f5881967,azure,centralindia,1,300,large,static
d8ed63e3-9875-4d92-b42d-ce915c5f4132,azure_v2,centralindia,1,300,small,static
abd0b1ad-e5aa-4eef-ba79-c855bcdfbccb,azure_v2,centralindia,1,300,medium,static
70d2eccf-022d-43a9-b5ad-59129d9173a3,azure_v2,centralindia,1,300,large,static

txts

839dd731-7444-4361-87c3-12dd447cd8ff,aws,centralindia,1,300,small,static
106ac198-66a5-4186-b260-061392b89bec,aws,centralindia,1,300,medium,static
20b15e93-6488-4aa8-8a21-6f5b3377777b,azure,centralindia,1,300,small,static
3c08d71f-9a0a-4258-a4e6-f6918781c868,azure,centralindia,1,300,medium,static
4b8c0f49-fdb2-47b2-af3f-b879dcf2b8c6,azure,centralindia,1,300,large,static
187e240d-0288-4dc1-9c71-1bad60d3a292,azure_v2,centralindia,1,300,small,static
73384198-2fc5-4e12-a2c1-15ea1673f079,azure_v2,centralindia,1,300,medium,static
56c996f4-0af6-4aa4-8f3c-65966d4f4920,azure_v2,centralindia,1,300,large,static

'''



'''
for nikhil
4 a,b,c

b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
d3a52922-f314-4558-aa7d-6828fb9b9e53,aws,centralindia,4,300,medium,static
056d4692-91b9-44c6-894d-406b77031007,aws,centralindia,8,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static
06b77318-7e18-4fa3-a32d-28b3db1796f5,azure_v2,centralindia,4,300,medium,static
84491da9-cdab-4288-81be-08fa67c6240c,azure_v2,centralindia,8,300,medium,static




latest 1rps medium for all


graph,image,math,text


b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static

3663405c-2fa9-4e83-9488-4f7fcbca3676,aws,centralindia,1,300,medium,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
9c4a4103-27f4-4865-95f5-c465663a984b,azure_v2,centralindia,1,300,medium,static

8d4a7637-c2db-410c-86cb-0f81ccc0efcf,aws,centralindia,1,300,medium,static
d09eb487-a817-48e4-88ea-9b05961308f2,azure,centralindia,1,300,medium,static
07ec8e52-94da-4dbc-9c7d-61f577e28284,azure_v2,centralindia,1,300,medium,static

106ac198-66a5-4186-b260-061392b89bec,aws,centralindia,1,300,medium,static
3c08d71f-9a0a-4258-a4e6-f6918781c868,azure,centralindia,1,300,medium,static
831da974-e232-4543-813a-8341f47ff922,azure_v2,centralindia,1,300,medium,static

5a
math
8d4a7637-c2db-410c-86cb-0f81ccc0efcf,aws,centralindia,1,300,medium,static
7c40fda9-5263-4b13-8613-d472241f1fa3,aws,centralindia,8,300,medium,sawtooth
c29b8954-1e4c-4d71-9713-cc452628df1f,aws,centralindia,8,300,medium,alibaba
d09eb487-a817-48e4-88ea-9b05961308f2,azure,centralindia,1,300,medium,static
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
07ec8e52-94da-4dbc-9c7d-61f577e28284,azure_v2,centralindia,1,300,medium,static
3c4d6c54-e970-4fba-8aad-d132c9127509,azure_v2,centralindia,8,300,medium,sawtooth
3eeb8f2f-d31a-4fe0-a439-9bf4c9126cad,azure_v2,centralindia,8,300,medium,alibaba

5b
image
3663405c-2fa9-4e83-9488-4f7fcbca3676,aws,centralindia,1,300,medium,static
7c40fda9-5263-4b13-8613-d472241f1fa3,aws,centralindia,8,300,medium,sawtooth
c29b8954-1e4c-4d71-9713-cc452628df1f,aws,centralindia,8,300,medium,alibaba
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
9c4a4103-27f4-4865-95f5-c465663a984b,azure_v2,centralindia,1,300,medium,static
3c4d6c54-e970-4fba-8aad-d132c9127509,azure_v2,centralindia,8,300,medium,sawtooth
3eeb8f2f-d31a-4fe0-a439-9bf4c9126cad,azure_v2,centralindia,8,300,medium,alibaba



5c
text

106ac198-66a5-4186-b260-061392b89bec,aws,centralindia,1,300,medium,static
7c40fda9-5263-4b13-8613-d472241f1fa3,aws,centralindia,8,300,medium,sawtooth
c29b8954-1e4c-4d71-9713-cc452628df1f,aws,centralindia,8,300,medium,alibaba
3c08d71f-9a0a-4258-a4e6-f6918781c868,azure,centralindia,1,300,medium,static
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
831da974-e232-4543-813a-8341f47ff922,azure_v2,centralindia,1,300,medium,static
3c4d6c54-e970-4fba-8aad-d132c9127509,azure_v2,centralindia,8,300,medium,sawtooth
3eeb8f2f-d31a-4fe0-a439-9bf4c9126cad,azure_v2,centralindia,8,300,medium,alibaba




'''