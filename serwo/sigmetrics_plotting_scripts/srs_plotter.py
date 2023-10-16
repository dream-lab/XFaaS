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

    def __get_cumm_time(self, function_times, edge_times, num_iters):
                           
            source = [n for n, d in self.__xfaas_dag.in_degree() if d == 0][0]
            sink = [n for n, d in self.__xfaas_dag.out_degree() if d == 0][0]
            
            if source == sink:
                cumm_function_exec = []
                for i in range(num_iters):
                    tm = function_times[source][i]
                    cumm_function_exec.append(tm)
                return cumm_function_exec,[],[]

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


            return cumm_function_exec,cumm_comm_time,e2e_time
    
    def plot(self,csp):
        logger.info(f"Plotting {self.__logfile}")
        loglines = self.__get_provenance_logs()
        distribution_dict = self.__get_timings_dict()
        cumm_compute_time, cumm_comms_time, cumm_e2e_time = self.__get_cumm_time(distribution_dict["functions"],
                                                                                distribution_dict["edges"],
                                                                                num_iters=len(loglines))
        
        
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

            print('experiment start time:',datetime.fromtimestamp(int(min_start_time)//1000).strftime('%Y-%m-%d %H:%M:%S'))
            for cid in god_dict:
                god_dict[cid].sort()
                ## convert epoch to datetime
                epoch_st = god_dict[cid][0][1]
                epoch_en = god_dict[cid][-1][1]
                print(epoch_st,epoch_en)
                readable_st = datetime.fromtimestamp(int(epoch_st//1000)).strftime('%Y-%m-%d %H:%M:%S')
                readable_en = datetime.fromtimestamp(int(epoch_en//1000)).strftime('%Y-%m-%d %H:%M:%S')

                print(f'cid: {cid} fist ts:',readable_st)
                print(f'cid: {cid} last ts:',readable_en)
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
    if dynamism == 'payload':
        cc=1
    elif dynamism == 'rps':
        cc=2
    for d in data:
        wf_user_directory = args.wf_user_directory
        if i<=cc:
            wf_user_directory += '_aws'
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



    aws_legend = mpatches.Patch(color='orange', label='AWS')
    az_legend = mpatches.Patch(color='blue', label='Azure')
    azv2_legend = mpatches.Patch(color='green', label='AzureV2')


    
    

'''
for this plot

graph  payload

eeda154b-7636-4795-9060-3ba91ccbd574,aws,centralindia,1,300,small,static
b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
81dd3382-0546-4f5a-b5a1-282b1801dccd,azure,centralindia,1,300,small,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
c1d356e2-4b2f-409f-b95b-3408a1699ce2,azure,centralindia,1,300,large,static
372dbfee-18a4-461d-b74d-cb67accf3ed4,azure_v2,centralindia,1,300,small,static
ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
ad1b6078-3199-4f9d-8a72-a5b4d340183a,azure_v2,centralindia,1,300,large,static

static 1.4.8

b570e2ba-d423-40e8-92dc-2456c6730b55,aws,centralindia,1,300,medium,static
d3a52922-f314-4558-aa7d-6828fb9b9e53,aws,centralindia,4,300,medium,static
056d4692-91b9-44c6-894d-406b77031007,aws,centralindia,8,300,medium,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
41837ca7-1f18-474f-b12f-bdcc9b4265aa,azure,centralindia,4,300,medium,static
ec96bde2-fc13-4474-a2b1-345b11b74430,azure,centralindia,8,300,medium,static
ef6b9c9a-d4d1-4ba4-a1e5-83382c9ee4bf,azure_v2,centralindia,1,300,medium,static
94237fe5-1fd6-4e7f-84aa-d89660d4bb5e,azure_v2,centralindia,4,300,medium,static
c2c193ae-c7cb-43f9-af52-6beee288f5b8,azure_v2,centralindia,8,300,medium,static

'''