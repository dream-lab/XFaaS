import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import sys
import os
import json
from datetime import datetime
import shutil
import numpy as np
import networkx as nx
import pathlib
import pprint
import matplotlib.patches as mpatches

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

ref = {
    'staticsmall1':1,
    'staticsmall2':4,
    'staticsmall3':16,
    'staticsmall4':64,
    'staticsmall5':240,
    'staticsmall6':1024,

}
god_list = []
god_dict = {}
labels_dict = {}
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
        self.__xfaas_dag = self.__init_dag(pathlib.Path(self.__workflow_directory) / "dag.json")
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

    def __get_timings_dict(self):
        logger.info("Getting timing distribution dictionary")
        logs = self.__get_provenance_logs()
        
        distribution_dict = dict(
            client_overheads=[],
            functions=defaultdict(list),
            edges=defaultdict(list),
            wf_invocation_id = []
        )

        for log in logs:
            wf_invocation_id = log["workflow_invocation_id"]
            distribution_dict["wf_invocation_id"].append(wf_invocation_id)
            distribution_dict["client_overheads"].append((int(log["invocation_start_time_ms"]) - int(log["client_request_time_ms"]))/1000)
            for u in [v for v in self.__xfaas_dag.nodes]:
                exec_time = (log["functions"][u]["end_delta"] - log["functions"][u]["start_delta"])/1000 # seconds
                distribution_dict["functions"][u].append(exec_time)
            for v1,v2 in [e for e in self.__xfaas_dag.edges]:
                edge_key = f"{v1}-{v2}"
                comm_time = (log["functions"][v2]["start_delta"] - log["functions"][v1]["end_delta"])/1000 # seconds
                distribution_dict["edges"][edge_key].append(comm_time)
        
        return distribution_dict

    

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


    def __get_cumm_time(self, function_times, edge_times, num_iters):
                           
            source = [n for n, d in self.__xfaas_dag.in_degree() if d == 0][0]
            sink = [n for n, d in self.__xfaas_dag.out_degree() if d == 0][0]
            paths = list(nx.all_simple_paths(self.__xfaas_dag, source, sink))
            
            ## cumm fn exec
            cumm_function_exec = []
            for i in range(num_iters):
                temp = []
                for path in paths:
                    tm = 0
                    for node in path:
                        tm += function_times[node][i]
                    temp.append((tm,path))
                a,b = max(temp)
                cumm_function_exec.append(a)
            

            ## cumm comm time
            cumm_comm_time = []
            for i in range(num_iters):
                temp = []
                for path in paths:
                    tm = 0
                    for j in range(0,len(path)-1):
                        tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                    temp.append((tm,path))
                a,b = max(temp)
                cumm_comm_time.append(a)
            
            ## e2e
            e2e_time = []
            for i in range(num_iters):
                temp = []
                for path in paths:
                    tm = 0
                    
                    for j in range(0,len(path)-1):
                        tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                        tm += function_times[path[j]][i]
                    tm += function_times[path[-1]][i]
                    temp.append((tm,path))
                a,b = max(temp)
                e2e_time.append(a)
                
            ss = dict()
            s2 = dict()
            s3 = dict()
            return cumm_function_exec,cumm_comm_time,e2e_time

    def __get__filtered_cumm_time(self, function_times, edge_times, num_iters,wf_invocation_ids,container_invocation_ids,include_continer):
                           
            source = [n for n, d in self.__xfaas_dag.in_degree() if d == 0][0]
            sink = [n for n, d in self.__xfaas_dag.out_degree() if d == 0][0]
            paths = list(nx.all_simple_paths(self.__xfaas_dag, source, sink))
            
            if include_continer == True:
            ## cumm fn exec
                cumm_function_exec = []
                for i in range(num_iters):
                    temp = []
                    for path in paths:
                        tm = 0
                        for node in path:
                            tm += function_times[node][i]
                        temp.append(tm)
                    if wf_invocation_ids[i] in container_invocation_ids:
                        cumm_function_exec.append(max(temp))
                

                ## cumm comm time
                cumm_comm_time = []
                for i in range(num_iters):
                    temp = []
                    for path in paths:
                        tm = 0
                        for j in range(0,len(path)-1):
                            tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                        temp.append(tm)
                    if wf_invocation_ids[i] in container_invocation_ids:
                        cumm_comm_time.append(max(temp))
                
                ## e2e
                e2e_time = []
                for i in range(num_iters):
                    temp = []
                    for path in paths:
                        tm = 0
                        
                        for j in range(0,len(path)-1):
                            tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                            tm += function_times[path[j]][i]
                        tm += function_times[path[-1]][i]
                        temp.append(tm)
                    if wf_invocation_ids[i] in container_invocation_ids:
                        e2e_time.append(max(temp))
            else:
                ## cumm fn exec
                cumm_function_exec = []
                for i in range(num_iters):
                    temp = []
                    for path in paths:
                        tm = 0
                        for node in path:
                            tm += function_times[node][i]
                        temp.append(tm)
                    if wf_invocation_ids[i] not in container_invocation_ids:
                        cumm_function_exec.append(max(temp))
                

                ## cumm comm time
                cumm_comm_time = []
                for i in range(num_iters):
                    temp = []
                    for path in paths:
                        tm = 0
                        for j in range(0,len(path)-1):
                            tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                        temp.append(tm)
                    if wf_invocation_ids[i] not in container_invocation_ids:
                        cumm_comm_time.append(max(temp))
                
                ## e2e
                e2e_time = []
                for i in range(num_iters):
                    temp = []
                    for path in paths:
                        tm = 0
                        
                        for j in range(0,len(path)-1):
                            tm += edge_times[f"{path[j]}-{path[j+1]}"][i]
                            tm += function_times[path[j]][i]
                        tm += function_times[path[-1]][i]
                        temp.append(tm)
                    if wf_invocation_ids[i] not in container_invocation_ids:
                        e2e_time.append(max(temp))



            return cumm_function_exec,cumm_comm_time,e2e_time
    def __get_provenance_logs(self):
        logger.info(f"Reading logfile {self.__logfile}")
        with open(self.__logs_dir / self.__logfile, "r") as file:
            loglines = [json.loads(line) for line in file.readlines()]
        return loglines
    

    def __get_azure_containers(self, log_items: list):
        # array for storing the workflow invocation ids
        wf_invocation_ids = set() # TODO - check with VK.
        god_dict = {}
        ans = []
        mins = []
        sorted_dynamo_items = log_items
        min_start_time  = sorted_dynamo_items[0]["invocation_start_time_ms"]
        print(len(log_items))
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
        print("God dict length: ", len(god_dict.keys()))
        for cid in god_dict:
            god_dict[cid].sort()
            ans.append(god_dict[cid][0])
            # mins.append((god_dict[cid][0][0]-int(min_start_time))/1000)
            mins.append((god_dict[cid][0][1]-int(min_start_time))/1000)
            wf_invocation_ids.add(god_dict[cid][0][2])
            functions.append(god_dict[cid][0][3])
        
        return sorted(mins), wf_invocation_ids

    def plot(self,csp):
        distribution_dict = self.__get_timings_dict()
        logs = self.__get_provenance_logs()
        container_wf_invocations_ids = []
        if csp == 'azure' or csp == 'azure_v2':
            _ , container_wf_invocations_ids = self.__get_azure_containers(log_items=sorted(logs, key=lambda k: int(k["invocation_start_time_ms"])))
        if csp == 'aws':
            pass
        cumm_compute_time, cumm_comms_time, cumm_e2e_time = self.__get__filtered_cumm_time(distribution_dict["functions"],
                                                                                distribution_dict["edges"],
                                                                                num_iters=len(self.__get_provenance_logs()),
                                                                                wf_invocation_ids= distribution_dict["wf_invocation_id"],
                                                                                container_invocation_ids= container_wf_invocations_ids,
                                                                                include_continer=False)
        
        if len(logs) == 9:
            print(cumm_comms_time)
        print(len(cumm_comms_time))
        god_list.append(cumm_comms_time)

        
    def __init_dag(self,user_config_path):
            __dag_config_data = dict() # dag configuration (picked up from user file)
            __nodeIDMap = {} # map: nodeName -> nodeId (used internally)
            __dag = nx.DiGraph() # networkx directed graph
            def __load_user_spec(user_config_path):
                with open(user_config_path, "r") as user_dag_spec:
                    dag_data = json.load(user_dag_spec)
                return dag_data
            # throw an exception if loading file has a problem
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

def plot_metrics(user_wf_dir, wf_deployment_id, run_id,csp,payload_size):
    if (payload_size == 'large' and csp == 'aws') or (payload_size == 'large' and csp == 'azure_v2' and 'image' in wf):
        god_list.append([])
        print('hello')
        return
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot(csp)
    

if __name__ == "__main__":

    run_id = 'exp1'
    parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
    parser.add_argument("--dynamism",dest='dynamism',type=str,help="Dynamism")
    parser.add_argument("--wf",dest='wf',type=str,help="WF ")
    args = parser.parse_args()
    wf_user_directory = args.wf_user_directory +'/workflow-gen'
    wf = args.wf


    deployments_filename = 'serwo/custom_deployments.txt'
    if 'graph' in wf:
        dirs = ['/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_aws','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf']
    else:
        dirs = ['/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf']
    
    if 'rps' in wf:
        labels = ['AWS 1','AzS 1','AzN 1','AWS 4','AzS 4','AzN 4','AWS 8','AzS 8','AzN 8']
    else:
        labels = ['AWS SM','AWS ME','AWS LA','AzS SM','AzS ME','AzS LA','AzN SM','AzN ME','AzN LA']


    data = []
    with open(deployments_filename,'r') as f:
        for line in f:
            data.append(line.strip().split(','))

    i = 0
    for d in data:
        wf_deployment_id = d[0]
        csp = d[1]
        region = d[2]
        max_rps = d[3]
        duration = d[4]
        payload_size = d[5]
        dynamism = d[6]
        plot_metrics(dirs[i%3]+'/workflow-gen',wf_deployment_id,run_id,csp,payload_size)
        i+=1


colors = ['orange','blue','green','orange','blue','green','orange','blue','green']

if 'rps' in wf:
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fig.set_figwidth(5)
    ax.set_ylabel("Time (sec)")
    fontdict = {'size': 20} 
    ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
    # print(god_list)
    # bplot = ax.boxplot(god_list,
    #                             vert=True,
    #                             widths=0.2,
    #                             patch_artist=True,
    #                             showfliers=False)

    med_list = []
    for l in god_list:
        med_list.append(np.median(l))

    cols = ['orange','blue','green']
    ax.bar(labels,med_list,color=cols)

    # for bplots in bplot:
    #     for patch, color in zip(bplot['boxes'], colors):
    #         patch.set_facecolor(color)
    ax.set_xticks([x+1 for x in range(0, len(labels))])
    ax.set_xticklabels(labels,rotation=90)
    if 'graph' in wf:
        yticks = [0,30,60,90]
    else:
        yticks = [0,400,800,1200]
    orange_patch = mpatches.Patch(color='orange', label='AWS')
    blue_patch = mpatches.Patch(color='blue', label='Azure')
    green_patch = mpatches.Patch(color='green', label='AzureV2')
    # # Set ylim
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax.set_ylim(ymin=0, ymax=max(ax.get_yticks()))
    

    _xloc = ax.get_xticks()
    vlines_x_between = []
    for idx in range(0, len(_xloc)-1):
        vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
    ax.vlines(x=vlines_x_between, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)

    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="-", color="black")
    ax.grid(axis="y", which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    # 
    format = 'pdf'

    fig.savefig(f'aaaa/data_transfer_{wf}_rps1.{format}',bbox_inches='tight')
else:
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fig.set_figwidth(5)
    ax.set_ylabel("Time (sec)")
    fontdict = {'size': 20} 
    ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
    med_l = []
    for v in god_list:
        med_l.append(np.median(v))
    
    n_lst = []
    n_lst.append(god_list[0])
    n_lst.append(god_list[3])
    n_lst.append(god_list[6])

    n_lst.append(god_list[1])
    n_lst.append(god_list[4])
    n_lst.append(god_list[7])

    n_lst.append(god_list[2])
    n_lst.append(god_list[5])
    n_lst.append(god_list[8])

    md_l = []
    # for n in n_lst:
    #     if n != np.nan:
    #         if len(n) == 0:
    #             md_l.append(0)
    #             continue
    #         md_l.append(np.median(n))
    #     else:
    #         md_l.append(0)

    q1 = []

    q3 = []

    for n in n_lst:

        if n != np.nan:
            if len(n) == 0:
                q3.append(0)
                q1.append(0)
                md_l.append(0)
                continue
            q3.append(np.percentile(n,75))
            q1.append(np.percentile(n,25))
            md_l.append(np.median(n))
        else:
            q1.append(0)
            q3.append(0)
            md_l.append(0)

 

 

    # br = ax.bar([x+1 for x in range(0, len(labels))], md_l, color=cls)

    

 

    cls = ['orange', 'orange', 'orange', 'blue', 'blue', 'blue', 'green', 'green', 'green']
    br = ax.bar([x+1 for x in range(0, len(labels))], md_l, color=cls)
    ax.errorbar([x+1 for x in range(0, len(labels))], md_l, yerr=[q1, q3], capsize=5, color='black', ls='none')
    formatted_labels = [
        f"{value:.2f}" if value < 9 else f"{int(value)}" for value in md_l
    ]
    ax.bar_label(ax.containers[0],labels=formatted_labels,label_type='edge',fontsize=10,color="darkviolet")
    ax.set_yscale('log')
    ax.set_ylim(0.1,10000)
    
    ax.text(2.75,0.3,'NA', rotation=90, fontdict=fontdict,color='r')

    if 'image' in wf:
        ax.text(8.75,0.3,'DNF', rotation=90, fontdict=fontdict,color='r')
        ax.text(5.75,0.3,'DNF', rotation=90, fontdict=fontdict,color='r')
   

   
    ax.set_xticks([x+1 for x in range(0, len(labels))])
    ax.set_xticklabels(labels,rotation=90)
   
    yticks = []
    orange_patch = mpatches.Patch(color='orange', label='AWS')
    blue_patch = mpatches.Patch(color='blue', label='Azure')
    green_patch = mpatches.Patch(color='green', label='AzureV2')
    # # Set ylim
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    # ax.set_ylim(ymin=0, ymax=max(ax.get_yticks()))
    
    _xloc = ax.get_xticks()
    vlines_x_between = []
    for idx in range(0, len(_xloc)-1):
        vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
    ax.vlines(x=vlines_x_between, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)

    # ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="-", color="grey")
    ax.grid(axis="y", which="minor", linestyle="-", color="lightgrey")
    ax.set_axisbelow(True)
    if 'graph' in wf:
        ax.legend(handles=[orange_patch,blue_patch,green_patch],loc='upper left',fontsize=16)
    format = 'pdf'

    fig.savefig(f'aaaa/data_transfer_{wf}_payload1.{format}',bbox_inches='tight')
        


'''
graph

payload
b2ff4532-553e-47e9-89e7-762f38bad610,aws,centralindia,1,300,small,static
81dd3382-0546-4f5a-b5a1-282b1801dccd,azure,centralindia,1,300,small,static
93d819d9-378f-4a8f-b467-370420808623,azure_v2,centralindia,1,300,small,static
6b12bfc1-8fab-45d8-8e7c-eaef64de471a,aws,centralindia,1,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static
6b12bfc1-8fab-45d8-8e7c-eaef64de471a,aws,centralindia,1,300,large,static
c1d356e2-4b2f-409f-b95b-3408a1699ce2,azure,centralindia,1,300,large,static
561b57f9-b412-40ce-a9d6-eb32c12c8b3f,azure_v2,centralindia,1,300,large,static

rps

6b12bfc1-8fab-45d8-8e7c-eaef64de471a,aws,centralindia,1,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static
b9405f14-116e-42c9-a547-ace955814366,aws,centralindia,4,300,medium,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
06b77318-7e18-4fa3-a32d-28b3db1796f5,azure_v2,centralindia,4,300,medium,static
df219ea1-e871-411d-9612-9d661fa55ff7,aws,centralindia,8,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
84491da9-cdab-4288-81be-08fa67c6240c,azure_v2,centralindia,8,300,medium,static


image

payload

d8187ac8-6eb7-41f2-99bb-5470bbf8b139,aws,centralindia,1,300,small,static
307f3d81-c23f-489b-ab56-85c9fd0036d4,azure,centralindia,1,300,small,static
996c687c-c98b-4dab-ad9b-66a4ed79c67f,azure_v2,centralindia,1,300,small,static
6154c2cc-e2cc-4f3e-9cdf-48f9aff4957b,aws,centralindia,1,300,medium,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
9c4a4103-27f4-4865-95f5-c465663a984b,azure_v2,centralindia,1,300,medium,static
6154c2cc-e2cc-4f3e-9cdf-48f9aff4957b,aws,centralindia,1,300,large,static
335c7405-1fe1-441c-bbf8-482a75f34d3a,azure,centralindia,1,300,large,static
4f6a26d8-702d-4198-ab9a-18c49a4d7b09,azure_v2,centralindia,1,300,large,static

rps

6154c2cc-e2cc-4f3e-9cdf-48f9aff4957b,aws,centralindia,1,300,medium,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
9c4a4103-27f4-4865-95f5-c465663a984b,azure_v2,centralindia,1,300,medium,static
402b6544-c464-4d9f-ba50-3afc70c0c539,aws,centralindia,4,300,medium,static
0e320456-38bf-4a9d-9439-38cdf018b1e3,azure,centralindia,4,300,medium,static
d4e311d6-4510-414d-94ea-0c452c9c8ce5,azure_v2,centralindia,4,300,medium,static
e0ae36fe-c638-424d-8cb0-9f3535620f2a,aws,centralindia,8,300,medium,static
10f411eb-de7f-459b-9fb1-bb081c384030,azure,centralindia,8,300,medium,static
ce5a758e-a36f-4884-b662-21e28e4db2dc,azure_v2,centralindia,8,300,medium,static


'''