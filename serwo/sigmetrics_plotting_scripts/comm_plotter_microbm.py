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
import argparse
##import mpatches
import matplotlib.patches as mpatches
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
ref = {}
god_ref = ['1KB', '4KB', '16KB', '28KB', '30KB', '32KB', '40KB', '44KB', '50KB', '60KB', '64KB', '70KB', '128KB', '240KB', '256KB', '300KB', '480KB', '500KB', '640KB', '1024KB', '4096KB', '8192KB', '10240KB', '16384KB']
# ref = {
#     'staticsmall1':1,
#     'staticsmall2':4,
#     'staticsmall3':16,
#     'staticsmall4':64,
#     'staticsmall5':240,
#     'staticsmall6':1024,

# }
god_list = []
god_dict = {}
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


    def __get_provenance_logs(self):
        logger.info(f"Reading logfile {self.__logfile}")
        with open(self.__logs_dir / self.__logfile, "r") as file:
            loglines = [json.loads(line) for line in file.readlines()]
        return loglines
    
    def gen_ref(self):
        for i in self.__exp_conf:
            ref[i] = self.__exp_conf[i]['payload_size']
    def plot(self,csp):
        local_dict = {}
        logger.info(f"Plotting {self.__logfile}")
        loglines = self.__get_provenance_logs()
        distribution_dict =self. __get_timings_dict()
        edges_time = distribution_dict['edges']['1-2']
        self.gen_ref()
        for i in range(len(edges_time)):
            
            if ref[loglines[i]['session_id']] not in local_dict:
                local_dict[ref[loglines[i]['session_id']]] = [edges_time[i]]
            else:  
                local_dict[ref[loglines[i]['session_id']]].append(edges_time[i])
        
        
        
        for k in god_ref:
            if k not in local_dict:

                local_dict[k] =[]
        for key in local_dict:
            if key not in god_dict:
                god_dict[key] = [local_dict[key]]
            else:
                god_dict[key].append(local_dict[key])
            
            

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

def plot_metrics(user_wf_dir, wf_deployment_id, run_id,csp):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot(csp)
    

if __name__ == "__main__":

    run_id = 'exp1'
    parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
    parser.add_argument("--dynamism",dest='dynamism',type=str,help="Dynamism")
    args = parser.parse_args()
    wf_user_directory = args.wf_user_directory +'/workflow-gen'


    deployments_filename = 'serwo/custom_deployments.txt'

    data = []
    with open(deployments_filename,'r') as f:
        for line in f:
            data.append(line.strip().split(','))

    for d in data:
        wf_deployment_id = d[0]
        csp = d[1]
        region = d[2]
        max_rps = d[3]
        duration = d[4]
        payload_size = d[5]
        dynamism = d[6]
        plot_metrics(wf_user_directory,wf_deployment_id,run_id,csp)

    
    labels = []
    colors = []
    for r in ref:
        ## strip kb from the string and convert to int
        sz = int(ref[r].strip('KB'))
        if sz>=1024:
            sz//=1024
            szz = str(sz)+'MB'
        else:
            szz = str(sz)+'KB'
        labels.append(f"AWS {szz}")
        labels.append(f"Az {szz}")
        labels.append(f"AzV2 {szz}")
        colors.append('orange')
        colors.append('blue')
        colors.append('green')
        
    medians = {}
    hmm = []
    for key in god_dict:
        sz = int(key.strip('KB'))
        ii = 0
        for ls in god_dict[key]:
            if key not in medians:
                medians[key] = []
            if ls == []:
                ii +=1
                continue
            else:
                md = np.median(ls)
            medians[key].append(md)
            if ii==0:
                clr = 'orange'
            elif ii==1:
                clr = 'blue'
            else:
                clr = 'green'

            ii+=1
            hmm.append((sz,md,clr))
            

            god_list.append(np.array(ls))
    
    ct = 0
    for i in range(0,len(labels)):
        if 'MB' in labels[i]:
            break
        ct+=1
    print(ct)
    kbs = 17000
    xx = [i for i in range(0,kbs)]
    # ct = 72
    labels_new = labels[0:ct]
    colors_new = colors[0:ct]
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    
    ax.set_ylabel("Time (sec)")
    ax.set_xlabel("Payload Size (KB)")
    fontdict = {'size': 15} 
    xx = set()
    for (sz,md,clr) in hmm:
        xx.add(sz)
    
        plt.loglog(sz,md,'o',color=clr)
    xx = list(sorted(xx))
    yticks = []
    vk = ax.get_yticks()
    print(vk)
    ax.set_xlim(xmin=1)
    print(xx)
    aws_legend = mpatches.Patch(color='orange', label='AWS')
    az_legend = mpatches.Patch(color='blue', label='Azure')
    azv2_legend = mpatches.Patch(color='green', label='AzureV2')
    ax.legend(handles=[aws_legend,az_legend,azv2_legend],loc='upper left',prop={'size': 15})
    ll = ax.get_xticks()
    lst = [1,10,100,1000,10000]
    ll = ax.get_yticks(minor=True)
    print(ll)
    ax.set_xticks(ll[24:-15], minor=True)
    ax.set_xticks([1,10,100,1000,10000], major=True)
    ax.grid( which="major", linestyle="-", color="black")
    ax.grid( which="minor", linestyle="-", color="grey")
    ax.set_axisbelow(True)
    format = 'pdf'
    fig.savefig(f'data_transfer_loglog.{format}',bbox_inches='tight')





    fig, ax = plt.subplots()
    fig.set_dpi(400)
    ax.set_ylabel("Time (sec)")
    ax.set_xlabel("Payload Size (KB)")
    fontdict = {'size': 15} 
    ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
    xx = set()
    for (sz,md,clr) in hmm:
        if sz > 700:
            break
        ax.scatter(sz,md,color=clr)
        
    yticks = []
    ax.set_xlim(xmin=0)
   
    aws_legend = mpatches.Patch(color='orange', label='AWS')
    az_legend = mpatches.Patch(color='blue', label='Azure')
    azv2_legend = mpatches.Patch(color='green', label='AzureV2')
    ax.legend(handles=[aws_legend,az_legend,azv2_legend],loc='upper left',prop={'size': 15})
    
   
    
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    ax.set_ylim(ymin=0)

    _xloc = ax.get_xticks()
    vlines_x_between = []
    for idx in range(0, len(_xloc)-1):
        vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
    ax.vlines(x=vlines_x_between, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)
   
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    ax.grid(axis='y', which="major", linestyle="-", color="black")
    ax.grid( axis='y',which="minor", linestyle="-", color="grey")
    ax.grid(True, which="both")
    
    ax.grid( which="major", linestyle="-", color="black")
    ax.grid( which="minor", linestyle="-", color="grey")
    
    ax.set_axisbelow(True)
    format = 'pdf'
    fig.savefig(f'data_transfer_normal.{format}',bbox_inches='tight')