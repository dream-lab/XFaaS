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

    def plot(self,csp):
        logger.info(f"Plotting {self.__logfile}")
        loglines = self.__get_provenance_logs()
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
                kk = 0
                num_elements = container_spawn_times[-1]+1
                yy = [0 for i in range(0,len(log_items))]
                for i in range(0,len(container_spawn_times)-1):
                    st = container_spawn_times[i]
                    et = container_spawn_times[i+1]
                    for j in range(st,et+1):
                        yy[j] = num_containers[i]
                        kk += 1
                print(num_containers)
                last = num_containers[-1]
                for i in range(0,len(log_items)):
                    if yy[i] == 0:
                        yy[i] = last
                Y2.append(yy)
            else:
                Y2.append([]) 
        else:
            containers, mins = self.__get_azure_containers(log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])))
        timestamps = [int(item["invocation_start_time_ms"]) for item in sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"]))] # NOTE - the timeline is w.r.t client
        # timeline = [(t-timestamps[0])/1000 for t in timestamps] 
        # timeline in seconds
        timeline = []
        for t in timestamps:
            ts = (t-timestamps[0])/1000
            # if ts <= 300:
            timeline.append(ts)

        e2e_time = self.__get_e2e_time(log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])))
        X.append(timeline)
        Y.append(e2e_time)

    def __get_azure_containers(self, log_items: list):
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
            for cid in god_dict:
                god_dict[cid].sort()
                ans.append(god_dict[cid][0])
                # mins.append((god_dict[cid][0][0]-int(min_start_time))/1000)
                mins.append(((god_dict[cid][0][1]-int(min_start_time))/1000,god_dict[cid][0][2]))
                wf_invocation_ids.add(god_dict[cid][0][2])
                
                functions.append(god_dict[cid][0][3])
            
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

            
            Y2.append(container_count)

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
    # dirs = [
    #     '/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf',
    #     '/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/text_analytics_wf',
    # ]
    for d in data:
        wf_user_directory = args.wf_user_directory
        if i<=2:
            wf_user_directory += '_aws'
        wf_user_directory += '/workflow-gen'
        # if i==4 or i==7:
        #     X.append([])
        #     Y.append([])
        #     Y2.append([])
        #     i+=1
        #     continue
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
    az_legend = mpatches.Patch(color='blue', label='Azure')
    azv2_legend = mpatches.Patch(color='green', label='AzureV2')

    
    fig, ax = plt.subplots()
    ax.set_ylabel("E2E Time (sec)")
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.set_xlabel('Timeline (sec)')
    ax.set_ylim(ymin=0)
    yticks = [0,20,40,60,80,100]
    yticks2 = [y//2 for y in yticks]
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax2 = ax.twinx()
    ax2.set_ylabel("Number of Containers")
    label1 = 'E2E Time'
    label2 = 'Number of Containers'
    for i in range(0,len(small_x)):
        l1 = ax.plot(small_x[i],small_y[i],color =colors[i],label=label1)
    ax.set_xlim(xmin=0,xmax=300)
    ax2.set_ylim(ymin=0)
    if not yticks2 == []:
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([str(x) for x in yticks2])
    linestyles = ['--', '--', '-.']
    for i in range(0,len(small_y2)):
        l2 = ax2.plot(small_x[i],small_y2[i],color=colors[i], linestyle='--',label=label2)
    

    lstt = [aws_legend,az_legend,azv2_legend]
    lsttlabel = [i.get_label() for i in lstt] + ['E2E','Num of Containers']
    lstt = lstt + [Line2D([0],[0],color="black",lw=1,linestyle='-'),Line2D([0],[0],color="black",lw=1,linestyle='--')] 
    ax.grid(axis="both", which="major", linestyle="-", color="gray", linewidth = 0.2)

    ax.grid(axis="both", which="minor", linestyle="--", color="silver", linewidth = 0.2)
    ax.legend(lstt,lsttlabel,loc='upper right',prop={'size': 12})

    plt.savefig(f"obs1/{wf}_medium_observation1_{dynamism}_1.pdf", bbox_inches='tight')


    fig, ax = plt.subplots()
    ax.set_ylabel("E2E Time (sec)")
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.set_xlabel('Timeline (sec)')
    ax.set_ylim(ymin=0)
    ax.set_xlim(xmin=0,xmax=300)
    yticks = [0,50,100,150]
    yticks2 = [int(y*1.2) for y in yticks]
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax2 = ax.twinx()
    ax2.set_ylabel("Number of Containers")
    
    for i in range(0,len(medium_x)):
        print(len(medium_x[i]),len(medium_y[i]))
        ax.plot(medium_x[i],medium_y[i],color =colors[i])
    ax2.set_ylim(ymin=0)
    if not yticks2 == []:
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([str(x) for x in yticks2])
    linestyles = ['--', '--', '-.']
    ax.grid(axis="both", which="major", linestyle="-", color="gray", linewidth = 0.2)

    ax.grid(axis="both", which="minor", linestyle="--", color="silver", linewidth = 0.2)
    for i in range(0,len(medium_y2)):
        ax2.plot(medium_x[i],medium_y2[i][0:len(medium_x[i])],color=colors[i], linestyle='--')
    plt.savefig(f"obs1/{wf}_medium_observation1_{dynamism}_4.pdf", bbox_inches='tight')

    fig, ax = plt.subplots()
    ax.set_ylabel("E2E Time (sec)")
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="both", which="major", linestyle="-", color="black")
    ax.grid(axis="both", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    ax.set_xlabel('Timeline (sec)')
    ax.set_ylim(ymin=0)

    yticks = [0,50,100,150,200]
    yticks2 = [int(y*1.5) for y in yticks]
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax2 = ax.twinx()
    ax2.set_ylabel("Number of Containers")
    for i in range(0,len(large_x)):
        ax.plot(large_x[i],large_y[i],color =colors[i])
    ax2.set_ylim(ymin=0)
    ax.set_xlim(xmin=0,xmax=300)
    if not yticks2 == []:
        ax2.set_yticks(yticks2)
        ax2.set_yticklabels([str(x) for x in yticks2])
    linestyles = ['--', '--', '-.']
    print(len(large_y2))
    ax.grid(axis="both", which="major", linestyle="-", color="gray", linewidth = 0.2)

    ax.grid(axis="both", which="minor", linestyle="--", color="silver", linewidth = 0.2)
    for i in range(0,len(large_y2)):
        ax2.plot(large_x[i],large_y2[i],color=colors[i], linestyle='--')
    plt.savefig(f"obs1/{wf}_medium_observation1_{dynamism}_8.pdf", bbox_inches='tight')



    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    exp_conf = f"{csp}-{region}-{max_rps}-{duration}-{payload_size}-{dynamism}-{timestamp}"
    src = f"{wf_user_directory}/{wf_deployment_id}"
    dst = f"{wf_user_directory}/paper_ready/"
    # shutil.copytree(src, dst)

    
    



'''
graph all vs azure vs azure_v2


81dd3382-0546-4f5a-b5a1-282b1801dccd,azure,centralindia,1,300,small,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
c1d356e2-4b2f-409f-b95b-3408a1699ce2,azure,centralindia,1,300,large,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
63b3912d-f7c5-4ba3-a374-53bbaeaa5e7d,azure,centralindia,8,300,medium,step_function
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
372dbfee-18a4-461d-b74d-cb67accf3ed4,azure_v2,centralindia,1,300,small,static
ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
ad1b6078-3199-4f9d-8a72-a5b4d340183a,azure_v2,centralindia,1,300,large,static
94237fe5-1fd6-4e7f-84aa-d89660d4bb5e,azure_v2,centralindia,4,300,medium,static
c2c193ae-c7cb-43f9-af52-6beee288f5b8,azure_v2,centralindia,8,300,medium,static
8b398a49-0db5-48d4-a5e2-bfdcf04fd37c,azure_v2,centralindia,8,300,medium,step_function
3c4d6c54-e970-4fba-8aad-d132c9127509,azure_v2,centralindia,8,300,medium,sawtooth
3eeb8f2f-d31a-4fe0-a439-9bf4c9126cad,azure_v2,centralindia,8,300,medium,alibaba
'''
'''
text all azure vs azure_v2

20b15e93-6488-4aa8-8a21-6f5b3377777b,azure,centralindia,1,300,small,static
3c08d71f-9a0a-4258-a4e6-f6918781c868,azure,centralindia,1,300,medium,static
4b8c0f49-fdb2-47b2-af3f-b879dcf2b8c6,azure,centralindia,1,300,large,static
5764a426-4a24-4ee5-8e95-2e6a19b8e025,azure,centralindia,4,300,medium,static
e85f0b76-9268-46ca-aca1-0d9bae2cfe22,azure,centralindia,8,300,medium,static
c5b26e08-dae3-4f1a-bcc6-aa8682513fed,azure,centralindia,8,300,medium,step_function
4d6633d2-0b9e-455a-9cb8-b207a07f27f4,azure,centralindia,8,300,medium,sawtooth
14a4b3d8-e86c-4095-9c45-5d05ef721525,azure,centralindia,8,300,medium,alibaba
187e240d-0288-4dc1-9c71-1bad60d3a292,azure_v2,centralindia,1,300,small,static
73384198-2fc5-4e12-a2c1-15ea1673f079,azure_v2,centralindia,1,300,medium,static
56c996f4-0af6-4aa4-8f3c-65966d4f4920,azure_v2,centralindia,1,300,large,static
7667af87-748d-494a-9b5c-a3cf0a130dee,azure_v2,centralindia,4,300,medium,static
543a1895-284f-418a-a51b-c507bb6ee4d8,azure_v2,centralindia,8,300,medium,static
5e049e4d-06fe-480e-a8a2-f67a2ff29f25,azure_v2,centralindia,8,300,medium,step_function
9f99aec9-082a-4c3c-9118-6ebd9146cf48,azure_v2,centralindia,8,300,medium,sawtooth
0d80eff4-c54b-4ba3-bd69-dddce630ae9f,azure_v2,centralindia,8,300,medium,alibaba

'''
'''
image all azure vs azure_v2


307f3d81-c23f-489b-ab56-85c9fd0036d4,azure,centralindia,1,300,small,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
335c7405-1fe1-441c-bbf8-482a75f34d3a,azure,centralindia,1,300,large,static
0e320456-38bf-4a9d-9439-38cdf018b1e3,azure,centralindia,4,300,medium,static
10f411eb-de7f-459b-9fb1-bb081c384030,azure,centralindia,8,300,medium,static
00a67457-dfeb-4d25-808c-93a7feeab164,azure,centralindia,8,300,medium,step_function
69830663-d639-4fc2-a4a7-9b508acbcfeb,azure,centralindia,8,300,medium,sawtooth
745ad413-36c5-482a-ac88-c719f9aa8461,azure,centralindia,8,300,medium,alibaba
d8ed63e3-9875-4d92-b42d-ce915c5f4132,azure_v2,centralindia,1,300,small,static
abd0b1ad-e5aa-4eef-ba79-c855bcdfbccb,azure_v2,centralindia,1,300,medium,static
74f39b19-8cf1-46da-8994-da8d596e3a3c,azure_v2,centralindia,1,300,large,static
5d1f830d-a252-41ee-897a-fdc3ec532dc6,azure_v2,centralindia,4,300,medium,static
7561c726-7cc2-4aed-bbe3-da1652d0e78a,azure_v2,centralindia,8,300,medium,static
e4169aa7-6434-43e8-a902-a2687783f4f4,azure_v2,centralindia,8,300,medium,step_function
8bb4207b-22c6-49eb-9bab-3b5231918d1a,azure_v2,centralindia,8,300,medium,sawtooth
ce329b02-2ba6-4557-81f8-042da1d08b04,azure_v2,centralindia,8,300,medium,alibaba
'''

'''
math all azure vs azure_v2
b3e8a1ed-16f5-4622-8adf-e79f3d489326,azure,centralindia,1,300,small,static
8e95d943-b82d-434e-9f60-de252bb872c8,azure,centralindia,1,300,medium,static
e9770cbe-b91d-4914-a3d4-ee2043402a48,azure,centralindia,1,300,large,static
e2427a51-056d-4a98-bc16-c9a93d86703d,azure,centralindia,4,300,medium,static
093bc839-2522-4dd7-be12-312d2a3141e3,azure,centralindia,8,300,medium,static
6d288d98-0221-4370-b09c-b57abdf12a2d,azure,centralindia,8,300,medium,step_function
1d3dbe1b-0f12-4f5b-8bf0-bb349f9d26ef,azure,centralindia,8,300,medium,sawtooth
a02c99cd-0b74-40df-9866-5dc35bad92bd,azure,centralindia,8,300,medium,alibaba
0801b14b-dee0-43bb-a281-9bd4c5c9cb0a,azure_v2,centralindia,1,300,small,static
80e21ed1-7091-4477-8a26-fef88dda1c10,azure_v2,centralindia,1,300,medium,static
4fe21543-3134-4835-8dba-55770daff59c,azure_v2,centralindia,1,300,large,static
8fb24acc-97bb-4109-b2d1-fe9c574356d8,azure_v2,centralindia,4,300,medium,static
d1d616f0-b6c7-477b-bf89-4b86095b8f47,azure_v2,centralindia,8,300,medium,static
fcdb531b-e20e-4b84-81e8-858ded90371b,azure_v2,centralindia,8,300,medium,step_function
7584cd23-7317-411b-83ee-20b081540501,azure_v2,centralindia,8,300,medium,sawtooth
205ce9ee-497c-4e16-811f-d5ac66f39814,azure_v2,centralindia,8,300,medium,alibaba
'''



'''
graph aws

eeda154b-7636-4795-9060-3ba91ccbd574,aws,centralindia,1,300,small,static
b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
b9405f14-116e-42c9-a547-ace955814366,aws,centralindia,4,300,medium,static
df219ea1-e871-411d-9612-9d661fa55ff7,aws,centralindia,8,300,medium,static
7ed01e5d-a4d5-40ea-8301-5e4354745b6d,aws,centralindia,8,300,medium,step_function
3081452e-df5d-40d4-9ec4-2ddd7c1a1a0e,aws,centralindia,8,300,medium,sawtooth
3e7eca6e-e1ab-4aff-bc6a-1d0495694cfb,aws,centralindia,8,300,medium,alibaba


text aws

839dd731-7444-4361-87c3-12dd447cd8ff,aws,centralindia,1,300,small,static
2dd3da29-f1b4-40e2-b224-a5781fb94e1a,aws,centralindia,1,300,medium,static
cc5fce75-4dbb-4df3-978b-54a2798d9e8e,aws,centralindia,4,300,medium,static
bf464529-10db-4722-9d04-ac902eede29b,aws,centralindia,8,300,medium,static
2f1b84ee-cff9-4ef5-ac4c-60df1093dabe,aws,centralindia,8,300,medium,step_function
5efadcfc-219f-4ff6-8497-28bfc99136fd,aws,centralindia,8,300,medium,sawtooth
f39a6fa7-3299-4fc4-bc23-2fec70536030,aws,centralindia,8,300,medium,alibaba

image aws
d8187ac8-6eb7-41f2-99bb-5470bbf8b139,aws,centralindia,1,300,small,static
6154c2cc-e2cc-4f3e-9cdf-48f9aff4957b,aws,centralindia,1,300,medium,static
402b6544-c464-4d9f-ba50-3afc70c0c539,aws,centralindia,4,300,medium,static
e0ae36fe-c638-424d-8cb0-9f3535620f2a,aws,centralindia,8,300,medium,static
b249f836-b663-49dc-a12f-c8d2ea9b9da6,aws,centralindia,8,300,medium,step_function
a2465880-46ed-4721-a5d9-96eb3f980c08,aws,centralindia,8,300,medium,sawtooth
d1fc56c5-6582-4661-a8e0-09b2fddf14aa,aws,centralindia,8,300,medium,alibaba

math aws

9057e696-0635-4c5d-8291-e05aae44cfb3,aws,centralindia,1,300,small,static
f3d0d746-aba2-4325-b486-94aa9ddf065f,aws,centralindia,1,300,medium,static
55029275-3138-48a9-9a6f-fbe438d77428,aws,centralindia,4,300,medium,static
1b1c1384-723c-45c4-9589-39a4c4f59147,aws,centralindia,8,300,medium,static
80e4b709-c646-4671-a74b-8e0cf17a487e,aws,centralindia,8,300,medium,step_function
57dae22f-a51a-4409-a4df-40d119bce62e,aws,centralindia,8,300,medium,sawtooth
bf4e11ed-e1e4-400e-83f8-7c01923c4005,aws,centralindia,8,300,medium,alibaba

'''



'''
singleton

graph_gen azure vs azurev2

b51925b4-c7a5-4f48-b82a-5b3878e4a854,azure,centralindia,1,300,medium,static
4f0363e4-611b-41c1-b723-ff10cab23660,azure_v2,centralindia,1,300,medium,static

graph_bft

481c2834-708d-423c-99c9-40c64a411b69,azure,centralindia,1,300,medium,static
b189d449-74ed-4d22-8065-97a601401c8e,azure_v2,centralindia,1,300,medium,static

graph_mst

253911e0-135d-4096-b963-aa7f6418681f,azure,centralindia,1,300,medium,static
a5e2d3bd-36c7-488b-a386-48d990e6a756,azure_v2,centralindia,1,300,medium,static

pagerank
45af9d64-47ad-4df9-803a-a4144db1c381,azure,centralindia,1,300,medium,static
3f7b6e6a-e6a0-47e8-99f5-72a2541b4ce0,azure_v2,centralindia,1,300,medium,static


text_data_gen

c03e9c3b-4d60-421b-8850-05496f30aaa8,azure,centralindia,1,300,medium,static
567f7182-6ee0-42df-b436-d7cca1e15be1,azure_v2,centralindia,1,300,medium,static

text_sort

ec6b7c11-8883-4391-a7e4-c27be21a6952,azure,centralindia,1,300,medium,static
2fbd196c-ef84-4e2a-91a2-3d7ef0a597a6,azure_v2,centralindia,1,300,medium,static


single string
a729e087-5e0a-4a17-a19e-33dab048dd99,azure,centralindia,1,300,medium,static
c01594b0-5491-4eaf-8fe9-c4056cd15a56,azure_v2,centralindia,1,300,medium,static


merge 
d7861b7b-089f-403f-ad3a-db35dde072e4,azure,centralindia,1,300,medium,static
458ebec1-e928-47ba-b6a1-0817b889aa5f,azure_v2,centralindia,1,300,medium,static

encrypt
68d50f79-499e-4744-a525-0b2e43537b5c,azure,centralindia,1,300,medium,static
1a9c7482-4a28-43b2-a321-519f58e5e5fb,azure_v2,centralindia,1,300,medium,static
'''




'''
graph payload

81dd3382-0546-4f5a-b5a1-282b1801dccd,azure,centralindia,1,300,small,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
c1d356e2-4b2f-409f-b95b-3408a1699ce2,azure,centralindia,1,300,large,static
372dbfee-18a4-461d-b74d-cb67accf3ed4,azure_v2,centralindia,1,300,small,static
ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
ad1b6078-3199-4f9d-8a72-a5b4d340183a,azure_v2,centralindia,1,300,large,static
eeda154b-7636-4795-9060-3ba91ccbd574,aws,centralindia,1,300,small,static
b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static

graph rps

fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
94237fe5-1fd6-4e7f-84aa-d89660d4bb5e,azure_v2,centralindia,4,300,medium,static
c2c193ae-c7cb-43f9-af52-6beee288f5b8,azure_v2,centralindia,8,300,medium,static

graph workload

63b3912d-f7c5-4ba3-a374-53bbaeaa5e7d,azure,centralindia,8,300,medium,step_function
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
8b398a49-0db5-48d4-a5e2-bfdcf04fd37c,azure_v2,centralindia,8,300,medium,step_function
3c4d6c54-e970-4fba-8aad-d132c9127509,azure_v2,centralindia,8,300,medium,sawtooth
3eeb8f2f-d31a-4fe0-a439-9bf4c9126cad,azure_v2,centralindia,8,300,medium,alibaba

math payload

b3e8a1ed-16f5-4622-8adf-e79f3d489326,azure,centralindia,1,300,small,static
8e95d943-b82d-434e-9f60-de252bb872c8,azure,centralindia,1,300,medium,static
e9770cbe-b91d-4914-a3d4-ee2043402a48,azure,centralindia,1,300,large,static
0801b14b-dee0-43bb-a281-9bd4c5c9cb0a,azure_v2,centralindia,1,300,small,static
80e21ed1-7091-4477-8a26-fef88dda1c10,azure_v2,centralindia,1,300,medium,static
4fe21543-3134-4835-8dba-55770daff59c,azure_v2,centralindia,1,300,large,static


image payload

307f3d81-c23f-489b-ab56-85c9fd0036d4,azure,centralindia,1,300,small,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
67dd0dc1-650a-4ea3-a980-5a02f5881967,azure,centralindia,1,300,large,static
d8ed63e3-9875-4d92-b42d-ce915c5f4132,azure_v2,centralindia,1,300,small,static
abd0b1ad-e5aa-4eef-ba79-c855bcdfbccb,azure_v2,centralindia,1,300,medium,static
70d2eccf-022d-43a9-b5ad-59129d9173a3,azure_v2,centralindia,1,300,large,static

'''




'''
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


b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
d3a52922-f314-4558-aa7d-6828fb9b9e53,aws,centralindia,4,300,medium,static
056d4692-91b9-44c6-894d-406b77031007,aws,centralindia,8,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
94237fe5-1fd6-4e7f-84aa-d89660d4bb5e,azure_v2,centralindia,4,300,medium,static
c2c193ae-c7cb-43f9-af52-6beee288f5b8,azure_v2,centralindia,8,300,medium,static


a153db95-3ac2-440c-9f36-f086168b4ece,aws,centralindia,8,300,medium,step_function
7c40fda9-5263-4b13-8613-d472241f1fa3,aws,centralindia,8,300,medium,sawtooth
c29b8954-1e4c-4d71-9713-cc452628df1f,aws,centralindia,8,300,medium,alibaba
63b3912d-f7c5-4ba3-a374-53bbaeaa5e7d,azure,centralindia,8,300,medium,step_function
74c113ab-3385-41a1-8cc5-613f393af065,azure,centralindia,8,300,medium,sawtooth
2fa4cb97-2bac-4f22-b568-15cf9d88a052,azure,centralindia,8,300,medium,alibaba
8b398a49-0db5-48d4-a5e2-bfdcf04fd37c,azure_v2,centralindia,8,300,medium,step_function
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