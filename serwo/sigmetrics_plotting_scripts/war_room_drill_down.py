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

    def plot(self,csp,wf):
        logger.info(f"Plotting {self.__logfile}")
        loglines = self.__get_provenance_logs()
        distribution_dict = self.__get_timings_dict()
       
        self.__do_coldstarts_for_nodes(csp,wf,log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])))

        self.__do_coldstarts_for_edges(csp,wf,log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])))
        

    def __do_coldstarts_for_nodes(self,csp,wf, log_items: list):
            # array for storing the workflow invocation ids
            wf_invocation_ids = set() # TODO - check with VK.
            dag = self.__xfaas_dag
            dist_dict = self.__get_timings_dict()
            
            sink_node = None
            for node in dag.nodes():
                if dag.out_degree(node) == 0:
                    sink_node = node
                    break
            
            god_dict = {}
            ans = []
            mins = []
            righty = []
            if wf == 'image':
                righty = [0.5,0.84,0.77,0.70,1.91,9.55,4.38,2.37,0.5]
                righty = [(i * 20 * 0.9536) for i in righty]
            else:
                righty = [1.04,1.04,1.95,1.06,0.5]
                righty = [(i * 20 * 0.9536) for i in righty]
                
            sorted_dynamo_items = log_items
            min_start_time  = sorted_dynamo_items[0]["invocation_start_time_ms"]
            
            function_map = set()
            cs_flag = dict()
            for item in sorted_dynamo_items:
                functions = item['functions']
                workflow_start_time = item['invocation_start_time_ms']
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
                   
            new_map = dict()

            cold_start = dict()
            fn_cold_start = dict()

            for cid in god_dict:
                god_dict[cid].sort(key=lambda x: x[0])
                node_id = god_dict[cid][0][3]
                wf_id = god_dict[cid][0][2]
                fn_cold_start[(wf_id, node_id)] = 1
                
            fns = dist_dict['functions']

            fn_colds = dict()
            fn_warm = dict()
            dagg = self.__xfaas_dag
            for n in dagg.nodes():
                fn_colds[n] = []
                fn_warm[n] = []
            for f in fns:
                for i in range(len(fns[f])):
                    pp = (dist_dict['wf_invocation_id'][i], f)
                    if pp in fn_cold_start:
                        fn_colds[f].append(fns[f][i])
                    else:
                        fn_warm[f].append(fns[f][i])

            colors = []
            for n in dagg.nodes():
                colors.append('orange')
                colors.append('darkblue')
            god_fns = []
            for n in dagg.nodes():
                god_fns.append(fn_warm[n])
                god_fns.append(fn_colds[n])
                
            
            x = [i+1 for i in range(len(god_fns))]
            fig, ax = plt.subplots()
            fig.set_dpi(400)
            if wf == 'image':
                fig.set_figheight(7)
                fig.set_figwidth(9)
            else:
                fig.set_figheight(7)

            ax.set_ylabel('Time (s)')
            
            

            
            # if wf =='image':
            #     yticks = [0,0.5,1,1.5,2]
            # else:
            #     yticks = [0,0.4,0.8,1.2]
            fn_codes = []
            for n in dagg.nodes():
                fn_codes.append(dagg.nodes[n]['Codename'])
            xlabels = []
            for i in range(len(fn_codes)):
                xlabels.append(fn_codes[i])
                xlabels.append('')
            
            q1,q3 = [],[]
            god_median = []
            for i in range(len(god_fns)):
                if len(god_fns[i]) == 0:
                    god_median.append(0)
                    q3.append(0)
                    q1.append(0)
                else:
                    god_median.append(np.median(god_fns[i]))
                    q3.append(np.percentile(god_fns[i],75))
                    q1.append(np.percentile(god_fns[i],25))
            zeros = []
            i = 1
            for g in god_median:
                if g == 0:
                    zeros.append(i-0.3)
                i+=1
            ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
            for j in zeros:
                ax.text(j, 0.01, 'No ColdStarts', color='black', fontsize=20,rotation=90)
            yticks = []
            if not yticks == []:
                ax.set_yticks(yticks)
                ax.set_yticklabels([str(x) for x in yticks])
            
            ax.bar(x, god_median, color=colors)
            ax.errorbar(x,god_median,yerr=[q1,q3],capsize=5,color='black',ls="none")
            ax.set_ylabel('Time (s)')
            ax.set_yscale('log')
            ax2 = ax.twinx()
            if wf == 'graph':
                xx  = [1.5,3.5,5.5,7.5,9.5]
            else:
                xx  = [1.5,3.5,5.5,7.5,9.5,11.5,13.5,15.5,17.5]
            ax2.set_ylabel('Memory Usage(MiB)')
            yticks2 = [0,40,80,120,160,200]
            ax2.set_ylim(ymin=0)
            
            if not yticks2 == []:
                ax2.set_yticks(yticks2)
                ax2.set_yticklabels([str(x) for x in yticks2])

            sizes = [150 for i in range(len(righty))]
            ax2.scatter(xx,righty,marker='x',color='red',label='Memory Usage',sizes=sizes)
            
            
            
            # ax.set_xlim(0)
            xvlines = [i+0.5 for i in range(2,len(god_median),2)]
            # ax.set_ylim(ymin=0, ymax=max(ax.get_yticks()))
            _xloc = ax.get_xticks()
            vlines_x_between = []
            for idx in range(0, len(_xloc)-1):
                vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
            
            ax.set_xticks(x,xlabels,rotation=20)
            if csp == 'azure' and wf == 'graph':
                aws_legend = mpatches.Patch(color='darkblue', label='Warm Starts')
                az_legend = mpatches.Patch(color='orange', label='Cold Starts')
                ax.legend(handles=[aws_legend,az_legend],loc='upper left',prop={'size': 18})
            
            ax.set_ylim(ymin=0.0001, ymax=10)

            ax.grid(axis="y", which="major", linestyle="-", color="gray")
            ax.grid(axis="y", which="minor", linestyle="-", color="lightgray")
            ax.set_axisbelow(True)
            ax.vlines(xvlines,0,ax.get_ylim()[1],linestyles='solid',color='gray',linewidth=0.2)
            format = 'pdf'
            plt.savefig(f'log_scales/cold_warm_{csp}_{wf}_functions.pdf', bbox_inches='tight')


    def __do_coldstarts_for_edges(self,csp,wf, log_items: list):
            # array for storing the workflow invocation ids
            wf_invocation_ids = set() # TODO - check with VK.
            dag = self.__xfaas_dag
            dist_dict = self.__get_timings_dict()
            
            sink_node = None
            for node in dag.nodes():
                if dag.out_degree(node) == 0:
                    sink_node = node
                    break
            
            god_dict = {}
            sorted_dynamo_items = log_items
            
            for item in sorted_dynamo_items:
                functions = item['functions']
                workflow_start_time = item['invocation_start_time_ms']
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
            
            edge_cold_start = dict()
            for cid in god_dict:
                god_dict[cid] = sorted(god_dict[cid], key=lambda x: x[0])
                node_id = god_dict[cid][0][3]
                wf_id = god_dict[cid][0][2]
                
                predecessor_edges = dag.in_edges(node_id)
                ##make similar edge wfid pair map like previous one
                for ed in predecessor_edges:
                    s,t = ed
                    
                    edge_id = f'{s}-{t}'
                    edge_cold_start[(wf_id,edge_id)] = 1

        
                
            edges = dist_dict['edges']

            edge_colds = dict()
            edge_warm = dict()
            dagg = self.__xfaas_dag
            for n in dagg.edges():
                src, dst = n
                keey = f'{src}-{dst}'
                edge_colds[keey] = []
                edge_warm[keey] = []
            
            for f in edges:
                for i in range(len(edges[f])):
                    pp = (dist_dict['wf_invocation_id'][i], f)
                    if pp in edge_cold_start:
                        edge_colds[f].append(edges[f][i])
                    else:
                        edge_warm[f].append(edges[f][i])

            god_edges = []
            for n in dagg.edges():
                s,t = n
                keey = f'{s}-{t}'
                print('count of cold: ',len(edge_colds[keey]),edge_colds[keey])
                print('Non Cold Starts: ',edge_warm[keey][0:10])
                god_edges.append(edge_warm[keey])
                god_edges.append(edge_colds[keey])
                


            colors = []
            for n in dagg.edges():
                colors.append('orange')
                colors.append('darkblue')
            
            
            xlabels = []
            for n in dagg.edges():
                s,t = n
                keey = f'{s}-{t}'
                s_code = dag.nodes[s]['Codename']
                t_code = dag.nodes[t]['Codename']
                xlabels.append(f'{s_code}-{t_code}')
                xlabels.append('')

            yticks = []
           
            x = [i+1 for i in range(len(god_edges))]
            fig, ax = plt.subplots()
            fig.set_dpi(400)
            if wf == 'image':
                fig.set_figwidth(9)
            god_median = []
            q1,q3 = [],[]
            for i in range(len(god_edges)):
                if len(god_edges[i]) == 0:
                    god_median.append(0)
                    q3.append(0)
                    q1.append(0)
                else:
                    god_median.append(np.median(god_edges[i]))
                    q3.append(np.percentile(god_edges[i],75))
                    q1.append(np.percentile(god_edges[i],25))

            zeros = []
            i = 1
            for g in god_median:
                if g == 0:
                    zeros.append(i-0.3)
                i+=1

            
            ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
            for j in zeros:
                ax.text(j, 0.5, 'No ColdStarts', color='black', fontsize=20,rotation=90)
            if not yticks == []:
                ax.set_yticks(yticks)
                ax.set_yticklabels([str(x) for x in yticks])
            
            ax.bar(x, god_median, color=colors)
            ax.errorbar(x,god_median,yerr=[q1,q3],capsize=5,color='black',ls="none")
            ax.set_ylabel('Time (s)')
            ax.set_yscale('log')
            
            ax.set_xlim(0)
            xvlines = [i+0.5 for i in range(2,len(god_median),2)]
            ax.set_ylim(ymin=0, ymax=100)
            _xloc = ax.get_xticks()
            vlines_x_between = []
            for idx in range(0, len(_xloc)-1):
                vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
            
            ax.set_xticks(x,xlabels,rotation=20)
            if csp == 'azure' and wf == 'graph':
                aws_legend = mpatches.Patch(color='orange', label='Warm Starts')
                az_legend = mpatches.Patch(color='darkblue', label='Cold Starts')
                ax.legend(handles=[aws_legend,az_legend],loc='upper left',prop={'size': 18})
            
            # ax.set_yscale('log')
            # ax.set_ylim(ymin=1,ymax=10)

            ax.set_ylim(ymin=0.1,ymax=1000)
            ax.grid(axis="y", which="major", linestyle="-", color="gray")
            ax.grid(axis="y", which="minor", linestyle="-", color="lightgray")
            ax.set_axisbelow(True)
            ax.vlines(xvlines,0,ax.get_ylim()[1],linestyles='solid',color='gray',linewidth=0.2)
            format = 'pdf'
            
            plt.savefig(f'log_scales/cold_warm_{csp}_{wf}_edges.pdf', bbox_inches='tight')


def plot_metrics(user_wf_dir, wf_deployment_id, run_id,csp,wf):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot(csp,wf)


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
    
    dirs = ['/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf']
    for d in data:
        wf_user_directory = args.wf_user_directory
        ## first two read 0, next two read 1
        if i < 2:
            wf_user_directory = dirs[0]
            wf = 'graph'
        else:
            wf_user_directory = dirs[1]
            wf = 'image'
        
        wf_user_directory += '/workflow-gen'
        wf_deployment_id = d[0]
        csp = d[1]
        region = d[2]
        max_rps = d[3]
        duration = d[4]
        payload_size = d[5]
        dynamism = d[6]
        plot_metrics(wf_user_directory,wf_deployment_id,run_id,csp,wf)
        i+=1


   
'''
graph 1 rps medium 
image 1 rps medium

fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
9c4a4103-27f4-4865-95f5-c465663a984b,azure_v2,centralindia,1,300,medium,static

'''