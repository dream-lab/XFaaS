import networkx as nx
from enum import Enum
from collections import defaultdict
from copy import deepcopy
import json
import datetime
from distutils.dir_util import copy_tree

from botocore.exceptions import ClientError
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
import uuid
import random
from jinja2 import Environment, FileSystemLoader
import pathlib
import shutil
from python.src.utils.classes.commons.csp import CSP
import sys
from python.src.utils.classes.commons.partition_point import PartitionPoint
import os
from python.src.utils.classes.commons.serwo_user_dag import SerWOUserDag
from serwo_generate_fused_functions import FusionCodeGenerator
import python.src.utils.generators.commons.jmx_generator as JMXGenerator

LEFT_JSON_NAME =''
RIGHT_JSON_NAME = ''
god_list = []
god_cost = []
class NodeTypes(Enum):
    LINEAR = 0
    FORK = 1
    JOIN = 2

fusion_template_path = 'python/src/fusion-template/'
fusion_template_path_temp = 'python/src/fusion-template/fused_runner_temp.py'
DAG_BENCHMARK_FILENAME = 'dag-benchmark.json'
PARENT_DIRECTORY = pathlib.Path(__file__).parent
USER_DIR = sys.argv[1]
MULTIPLIER = 100
ccsp = sys.argv[3]
DAG_DEFINITION_FILE = sys.argv[2]
DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
DAG_BENCHMARK_PATH = f'{USER_DIR}/{DAG_BENCHMARK_FILENAME}'
serwo_object_import = '\nfrom python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList'
APP_NAME = 'SmartGridAwsFusion02'
serwo_func_line_import = '\ndef function(serwoObject) -> SerWOObject:'
final_code = ''
class FusionCandidate:
    def __init__(self, _id, G, entry_node, exit_node, CSP):
        self._id = _id
        self._mem = -1
        self._compute_time = 0
        self._entry_node = entry_node
        self._exit_node = exit_node
        self._current_cost = None
        self._nodes = self._get_all_nodes_between(G, entry_node, exit_node, CSP)
    def _get_all_nodes_between(self, G, entry_node, exit_node, CSP):
        # Get compute time and max mem from this function
        nodes = set()
        current_cost = 0
        for path in list(nx.all_simple_paths(G, entry_node, exit_node)):
            for node in path:
                nodes.add(node)
        for node in nodes:
            gb_s = (G.nodes[node]['MemoryInMB']/1024) * (G.nodes[node]['ExecDur'] / 1000)
            if CSP == "AWS":
                current_cost += gb_s * 0.0000166667
                current_cost += 0.0000285
            elif CSP == "Azure":
                current_cost += gb_s * 0.000016
                current_cost += 0.00000786
            self._compute_time += G.nodes[node]['ExecDur']
            if G.nodes[node]['MemoryInMB'] > self._mem:
                self._mem = G.nodes[node]['MemoryInMB']
        self._current_cost = current_cost
        return nodes

    def get_id(self):
        return self._id

    def get_delta_cost(self, CSP):
        gb_s = ((self._mem/1024) * (self._compute_time/1000))
        if CSP == "AWS":
            return (gb_s * 0.0000166667) + 0.0000285 - self._current_cost
        else:
            return (gb_s * 0.000016) + 0.00000786 - self._current_cost

    def get_max_memory(self):
        return self._mem

    def get_total_compute_time(self):
        return self._compute_time

    def get_entry_node(self):
        return self._entry_node

    def get_exit_node(self):
        return self._exit_node

    def get_nodes(self):
        return self._nodes


"""
G = nx.DiGraph()
for index in range(1, 6):
    G.add_node(index)
G.add_edge(1, 2, edge_latency=-10)
G.add_edge(1, 3, edge_latency=-20)
G.add_edge(1, 4, edge_latency=-1)
G.add_edge(2, 5, edge_latency=-2)
G.add_edge(3, 5, edge_latency=-2)
G.add_edge(4, 5, edge_latency=-2)
"""


def get_node_type(G, node):
    if G.in_degree(node) > 1 and G.out_degree(node) <= 1:
        return NodeTypes.JOIN
    if G.in_degree(node) <= 1 and G.out_degree(node) > 1:
        return NodeTypes.FORK
    if G.in_degree(node) == 1 and G.out_degree(node) == 1:
        return NodeTypes.LINEAR


# Find corresponding joins
def find_join_pairs(G, source, sink):
    pairs = set()
    stack = []
    for path in list(nx.all_simple_paths(G, source, sink)):
        for node in path:
            node_type = get_node_type(G, node)
            if node_type == NodeTypes.FORK:
                stack.append(node)
            elif node_type == NodeTypes.JOIN:
                fork_node = stack.pop()
                pairs.add((fork_node, node))
    return pairs


# print(list(nx.all_simple_paths(G, 1, 5)))
# found_pairs = list(find_join_pairs(1, 17))
def get_all_fusion_candidates(G, source, sink, round, CSP):
    index = 1
    fusion_candidate_map = {}
    found_pairs = list(find_join_pairs(G, source, sink))
    for edge in list(nx.dfs_edges(G, source)):
        if G.out_degree(edge[0]) == 1 and G.in_degree(edge[1]) == 1:
            _id = "F"+str(round)+str(index)
            f = FusionCandidate(_id, G, edge[0], edge[1], CSP)
            fusion_candidate_map[_id] = f
            index += 1
    for pair in found_pairs:
        _id = "F"+str(round)+str(index)
        f = FusionCandidate(_id, G, pair[0], pair[1], CSP)
        fusion_candidate_map[_id] = f
        index += 1
    return fusion_candidate_map


def sort_list(tup,reverse):
    return sorted(tup, key=lambda x: x[1], reverse=reverse)


def set_edge_latency(G1: nx.classes.digraph.DiGraph):
    for node in G1.nodes:
        successors = G1.successors(node)
        for succ in successors:
            val = G1.nodes[node]['ExecDur'] + G1.edges[(node, succ)]['TransferTime']
            G1.edges[(node, succ)]['edge_latency'] = -1*val
    return G1


def get_longest_path(G1, source, sink):
    G1 = set_edge_latency(G1)
    sp = nx.shortest_path(G1, source, sink, weight="edge_latency")
    path_latency = 0
    for index in range(0, len(sp)-1):
        path_latency += G1[sp[index]][sp[index+1]]["edge_latency"]

    path_latency = path_latency * -1

    path_latency += G1.nodes[sink]['ExecDur']
    if len(G1.nodes) == 1:
        for node in G1.nodes:
            path_latency = G1.nodes[node]['ExecDur']
            return None, path_latency
    return sp, path_latency


def get_latency_for_fusion_candidate(G: nx.classes.digraph.DiGraph, fusion_candidate: FusionCandidate, source, sink,csp):
    G1 = deepcopy(G)
    G1 = update_graph(G1, fusion_candidate,csp)


    if source in fusion_candidate.get_nodes():
        source = fusion_candidate.get_id()
    if sink in fusion_candidate.get_nodes():
        sink = fusion_candidate.get_id()
    _, path_latency = get_longest_path(G1, source, sink)
    return path_latency


def update_graph(G: nx.classes.digraph.DiGraph, fusion_candidate: FusionCandidate,csp):
    entry_node = fusion_candidate.get_entry_node()
    exit_node = fusion_candidate.get_exit_node()
    G.add_node(fusion_candidate.get_id(),
               NodeId=fusion_candidate.get_id(),
               MemoryInMB=fusion_candidate.get_max_memory(),
               ExecDur=fusion_candidate.get_total_compute_time()
               )

    for pred in G.predecessors(entry_node):
        G.add_edge(pred, fusion_candidate.get_id(), TransferTime=G.edges[(pred, entry_node)]['TransferTime'])
    for succ in G.successors(exit_node):
        G.add_edge(fusion_candidate.get_id(), succ, TransferTime=G.edges[(exit_node, succ)]['TransferTime'])
    nodes = fusion_candidate.get_nodes()
    for node in nodes:
        G.remove_node(node)

    node_length = len(G.nodes())
    if csp == 'Azure':
        for u,v in G.edges():
            G.edges[(u,v)]['TransferTime'] = azure_inter_function_edge_latency_model(node_length,1)

    return G


def update_fusion_candidate_data_structs(fusion_candidate, fusion_candidates, node_to_candidates_map):
    del fusion_candidates[fusion_candidate.get_id()]
    for node in fusion_candidate.get_nodes():
        del node_to_candidates_map[node]


def get_fusion_candidates_on_path(path, node_to_candidates_map):
    fusion_candidates_on_path = []
    for node in path:
        fusion_candidates_on_path.extend(node_to_candidates_map[node])
    return list(set(fusion_candidates_on_path))



def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def fuse_graph(G, source, sink, CSP, cost_factor):
    G = update_graph_with_benchmark_data(G, CSP)

    # print(f'Full cost {CSP} = ',get_user_dag_cost(G,CSP))

    _, user_graph_latency = get_longest_path(G, source, sink)
    do_fusion = []
    user_dag_cost = get_user_dag_cost(G, CSP)
    current_dag_cost = user_dag_cost
    round = 0
    while True:
        if len(G.nodes) == 1:
            _, latency = get_longest_path(G, source, sink)
            cost = get_user_dag_cost(G, CSP)

            return do_fusion, latency, user_graph_latency, cost, user_dag_cost
        fusion_candidates = get_all_fusion_candidates(G, source, sink, round, CSP)
        round += 1
        node_to_candidates_map = defaultdict(list)

        # Get the reverse map: graph node name -> fusion_id
        for fusion_candidate in fusion_candidates.values():
            for node in fusion_candidate.get_nodes():
                node_to_candidates_map[node].append(fusion_candidate.get_id())

        critical_path, critical_path_latency = get_longest_path(G, source, sink)

        fusion_candidates_on_path = get_fusion_candidates_on_path(critical_path, node_to_candidates_map)

        if not fusion_candidates_on_path:

            _, latency = get_longest_path(G, source, sink)
            cost = get_user_dag_cost(G, CSP)

            return do_fusion, latency, user_graph_latency, cost, user_dag_cost
        sorted_fusion_candidates = []
        positive = []
        negative = []
        for fusion_candidate_id in fusion_candidates_on_path:
            fusion_candidate = fusion_candidates[fusion_candidate_id]
            delta_latency = critical_path_latency - get_latency_for_fusion_candidate(G, fusion_candidate, source, sink,CSP)
            delta_cost = fusion_candidate.get_delta_cost(CSP)
            if delta_cost == 0:
                positive.append((fusion_candidate.get_id(), 99999))
                # sorted_fusion_candidates.append((fusion_candidate.get_id(), 99999))
            elif delta_latency > 0:
                # sorted_fusion_candidates.append((fusion_candidate.get_id(), delta_latency/delta_cost))
                if delta_cost < 0:
                    negative.append((fusion_candidate.get_id(), delta_latency/delta_cost))
                else:
                    positive.append((fusion_candidate.get_id(), delta_latency/delta_cost))

        positive_sorted = sort_list(positive,True)
        negative_sorted = sort_list(negative,True)

        sorted_fusion_candidates = negative_sorted + positive_sorted
        if not sorted_fusion_candidates:

            _, latency = get_longest_path(G, source, sink)
            cost = get_user_dag_cost(G, CSP)

            return do_fusion, latency, user_graph_latency, cost, user_dag_cost
        # sorted_fusion_candidates = sort_list(sorted_fusion_candidates)
        no_fusion_candidate_feasible = True
        for fusion_candidate_tuple in sorted_fusion_candidates:
            fusion_candidate = fusion_candidates[fusion_candidate_tuple[0]]
            delta_latency = critical_path_latency - get_latency_for_fusion_candidate(G, fusion_candidate, source, sink,CSP)

        for fusion_candidate_tuple in sorted_fusion_candidates:
            fusion_candidate = fusion_candidates[fusion_candidate_tuple[0]]
            if current_dag_cost + fusion_candidate.get_delta_cost(CSP) <= cost_factor * user_dag_cost:

                current_dag_cost += fusion_candidate.get_delta_cost(CSP)
                do_fusion.append(fusion_candidate)
                update_god_list(fusion_candidate)
                god_cost.append(current_dag_cost)

                G = update_graph(G, fusion_candidate , CSP)


                # Need to update source and sink
                if source in fusion_candidate.get_nodes():
                    source = fusion_candidate.get_id()
                if sink in fusion_candidate.get_nodes():
                    sink = fusion_candidate.get_id()

                no_fusion_candidate_feasible = False
                break
            else:
                pass
        if no_fusion_candidate_feasible:

            _, latency = get_longest_path(G, source, sink)
            cost = get_user_dag_cost(G, CSP)

            return do_fusion, latency, user_graph_latency, cost, user_dag_cost

def update_god_list(fusion_candidate):
    if len(god_list) == 0:
        god_list.append([fusion_candidate])
    else:
        prv = deepcopy(god_list[-1])
        ne = fusion_candidate
        prv.append(fusion_candidate)
        god_list.append(prv)

def get_user_dag_cost(G, CSP):
    cost = 0

    for node in G.nodes:
        gb_s = ((G.nodes[node]['MemoryInMB']/1024) * (G.nodes[node]['ExecDur']/1000))
        if CSP == "AWS":
            cost += gb_s * 0.0000166667 + 0.0000285
        else:
            cost += gb_s * 0.000016 + 0.00000786
    return cost

def get_multiplied(node_bm):
    for node in node_bm:
        for csp in node_bm[node]:
            new_lat = MULTIPLIER*node_bm[node][csp]['Latency']
            node_bm[node][csp]['Latency'] = new_lat
    return node_bm

def get_user_dag_benchmark_values(dag_path):
    f = open(dag_path, 'r')
    bench_mark_json = json.loads(f.read())
    bench_mark = dict()

    bench_mark['node_benchmarks'] = get_multiplied(bench_mark_json['NodeBenchmarks'])

    bench_mark['edge_benchmarks'] = dict()
    for node in bench_mark_json['EdgeBenchmarks']:
        for neighbors in bench_mark_json['EdgeBenchmarks'][node]:
            for neighbor in neighbors:
                pair = (node,neighbor)
                bench_mark['edge_benchmarks'][pair] = dict()
                bench_mark['edge_benchmarks'][pair]['data_transfer_size'] = neighbors[neighbor]['DataTransferSize']
                for key in neighbors[neighbor]['Latencies']:
                    for latency_key in key:
                        if latency_key == 'Azure':

                            bench_mark['edge_benchmarks'][pair][latency_key] = azure_inter_function_edge_latency_model(len(bench_mark['node_benchmarks']),1)
                        else:
                            bench_mark['edge_benchmarks'][pair][latency_key] = key[latency_key]
    return bench_mark

def get_app_name():
    ff = open(DAG_DEFINITION_PATH,'r')
    jsson = json.loads(ff.read())
    return jsson['WorkflowName']

def update_graph_with_benchmark_data(G, CSP):
    bm_dict = get_user_dag_benchmark_values(DAG_BENCHMARK_PATH)

    for node in G.nodes:
        G.nodes[node]['ExecDur'] = bm_dict['node_benchmarks'][node][CSP]['Latency']
    for edge in G.edges:
        G.edges[edge]['TransferTime'] = bm_dict['edge_benchmarks'][edge][CSP]
    return G

def extract_native(path):
    xd = ''
    for c in reversed(path):
        if c =='/':
            break
        xd+=c
    ans = ''
    for c in reversed(xd):
        ans+=c
    return ans

def mutate(old_graph,new_node_id,new_node_val,start,end,id_to_fc_map):
    predecessors = deepcopy(old_graph.predecessors(start))
    successors = deepcopy(old_graph.successors(end))
    se = new_node_val

    global_set = set()
    for xd in se:
        if 'Nodes' in old_graph.nodes[xd]:
            sse = old_graph.nodes[xd]['Nodes']
            for s in sse:
                global_set.add(s)
        else:
            global_set.add(xd)
    start = calc_start(start,id_to_fc_map)
    end = calc_end(end,id_to_fc_map)
    old_graph.add_node(new_node_id,Nodes=global_set,Start=start,End=end)
    print('=======')
    print(se)
    print(global_set)
    for xd in new_node_val:
        old_graph.remove_node(xd)

    for nd in predecessors:
        old_graph.add_edge(nd,new_node_id)
    for nd in successors:
        old_graph.add_edge(new_node_id,nd)



def get_final_graph(G, fc,user_og_graph,suffix_str):
    id_to_fc_map = dict()
    for fusion_candidate in fc:
        id_to_fc_map[fusion_candidate.get_id()] = fusion_candidate

    round = 0


    while True:
        copy_g = deepcopy(G)
        # print(f'before : {round}')
        # print(G)
        # print(G.nodes())
        add_node_list = []
        add_edge_list = []
        remove_node_list = []
        global_flag = 0
        for fusion_candidate in fc:
            all_nodes_present_in_graph = True
            for node in fusion_candidate.get_nodes():
                if G.has_node(node) != True:
                    all_nodes_present_in_graph = False
                    break
            if all_nodes_present_in_graph:
                global_flag = 1
                nodes_to_fuse = fusion_candidate.get_nodes()
                entry = fusion_candidate.get_entry_node()
                exit = fusion_candidate.get_exit_node()

                _id = fusion_candidate.get_id()

                global_set = nodes_to_fuse
                print('glo')
                print(global_set)
                # for xd in nodes_to_fuse:
                #     key = 'Nodes'
                #     if key in G.nodes[xd]:
                #         sse = G.nodes[xd][key]
                #         for x in sse:
                #             global_set.add(x)
                #     else:
                #         global_set.add(xd)


                mutate(copy_g,_id,global_set,entry,exit,id_to_fc_map)


        G = deepcopy(copy_g)

        # print(f'after : {round}')
        round+=1
        # print(copy_g)
        # print(copy_g.nodes())
        # print('edges: ',copy_g.edges())

        if global_flag ==0:
            break


    final_edges =[]
    for u,v in G.edges():

        uu = calc_start(u,id_to_fc_map)
        vv = calc_start(v,id_to_fc_map)

        # print('final edges: ',uu,vv)
        final_edges.append((uu,vv))
    k = 'Nodes'
    start_key = 'Start'
    end_key = 'End'
    pth,pp,fin_graph = generate_fused_code(G, end_key, k, start_key, user_og_graph,suffix_str,final_edges)
    return pth,pp,fin_graph



def generate_fused_code(G, end_key, k, start_key, user_og_graph,suffix_str,final_edges):
    fused_src_path = f'{USER_DIR}/src-fused-{suffix_str}'
    if not os.path.exists(fused_src_path):
        os.mkdir(fused_src_path)
    index = 0
    fin_graph = nx.DiGraph()
    edges_to_add = []
    for node in G.nodes():

        if k in G.nodes[node]:
            nodes_ls = list(G.nodes[node][k])
            start = G.nodes[node][start_key]
            end = G.nodes[node][end_key]
            sub_graph_to_fuse = generate_sub_graph(nodes_ls, user_og_graph)
            sub_graph_to_fuse = nx.DiGraph(sub_graph_to_fuse)
            import_line = ''
            kp = 'Path'
            kn = 'NodeName'
            ep = 'EntryPoint'
            for node in sub_graph_to_fuse.nodes():
                import_line += f'\nfrom {extract_native(sub_graph_to_fuse.nodes[node][kp])} import {sub_graph_to_fuse.nodes[node][ep][:-3]} as {sub_graph_to_fuse.nodes[node][kn]}'

            global final_code
            max_mem = 0
            for node in sub_graph_to_fuse.nodes():
                max_mem = max(max_mem,user_og_graph.nodes[node]['MemoryInMB'])
            new_node_id = user_og_graph.nodes[start]['NodeId']
            new_node_name = user_og_graph.nodes[start]['NodeName']
            new_entry_point = 'func.py'
            for u,v in user_og_graph.in_edges(start):
                if fin_graph.has_node(u):
                    edges_to_add.append((u,start))

            for u,v in user_og_graph.out_edges(end):
                if fin_graph.has_node(v):
                    edges_to_add.append((start,v))

            code = FusionCodeGenerator(sub_graph_to_fuse).get_fused_code()

            final_code += import_line
            final_code += serwo_object_import
            final_code += serwo_func_line_import
            final_code += code
            template(import_line, code)
            fused_dir_id = 'fused-'+suffix_str+'-'+str(index)
            path = fused_src_path+'/'+fused_dir_id
            if not os.path.exists(path):
                os.mkdir(path)
            ls_of_paths = []
            for id in nodes_ls:
                user_src_path = user_og_graph.nodes[id]['Path']
                user_og_path = extract_native(user_src_path)
                pth = path+'/'+user_og_path
                if not os.path.exists(pth):
                    os.mkdir(path+'/'+user_og_path)
                copytree(user_src_path,path+'/'+user_og_path)
                ls_of_paths.append(path+'/'+user_og_path)
            handle_dependencies_and_requirements(ls_of_paths,path)
            new_path = path
            shutil.copyfile(fusion_template_path_temp,path+'/func.py')
            stream = os.popen(f"rm {fusion_template_path_temp}")
            stream.close()
            index += 1
        else:
            node_prop = user_og_graph.nodes[node]
            user_src_path = node_prop['Path']
            new_path = user_src_path
            new_node_name = node_prop['NodeName']
            max_mem = node_prop['MemoryInMB']
            new_entry_point = node_prop['EntryPoint']
            new_node_id = node_prop['NodeId']

            for u,v in user_og_graph.out_edges(node):
                if fin_graph.has_node(v):
                    edges_to_add.append((u,v))
            user_og_path = extract_native(user_src_path)
            pth = fused_src_path+'/'+user_og_path
            if not os.path.exists(pth):
                os.mkdir(fused_src_path+'/'+user_og_path)
            copytree(user_src_path,fused_src_path+'/'+user_og_path)


        print('================================================')


        fin_graph.add_node(new_node_id,NodeId = new_node_id,NodeName= new_node_name, Path= new_path, EntryPoint= new_entry_point, CSP="Azure", MemoryInMB=max_mem)


    for u,v in final_edges:
        fin_graph.add_edge(u,v)
    print(fin_graph)
    for node in fin_graph.nodes():
        print('id: ',node,fin_graph.nodes[node])

    deep_fin = deepcopy(fin_graph)
    top_sort = list(nx.topological_sort(deep_fin))
    id = top_sort[-1]
    print('last node: ',id)
    print('ending ',deep_fin)
    pp = create_dag_description(get_app_name(), deep_fin,CSP.toCSP("AWS"),USER_DIR,suffix_str)
    return fused_src_path,pp,fin_graph

def create_dag_description(workflow_name: str, graph: nx.DiGraph, csp:CSP, output_dir: str,suffix_str:str):
    # base skeleton of the output json
    output_dict = dict(WorkflowName=workflow_name)
    output_dict["Nodes"] = []
    output_dict["Edges"] = []

    # populate the node list
    for node in graph.nodes:
        # node items
        print("Inside create DAG description")
        print(graph.nodes[node]["NodeId"])
        print("NodeName", graph.nodes[node]["NodeName"])
        csp_string = CSP.toString(csp)
        node_item = dict(
            NodeId=graph.nodes[node]['NodeId'],
            NodeName=graph.nodes[node]['NodeName'],
            Path=graph.nodes[node]['Path'],
            EntryPoint=graph.nodes[node]['EntryPoint'],
            MemoryInMB=graph.nodes[node]['MemoryInMB'],
            CSP=csp_string
        )

        # edge items
        node_successors = list(graph.successors(node))
        edge_item_value = []
        if node_successors:
            edge_item_key = graph.nodes[node]['NodeName']
            # iterate over all successors of the node and add the nodename
            for succnode in node_successors:
                edge_item_value.append(graph.nodes[succnode]['NodeName'])
            edge_item = {
                edge_item_key: edge_item_value
            }
            # append the edge dict
            output_dict["Edges"].append(edge_item)

        # append the node dict
        output_dict["Nodes"].append(node_item)


    # write to output file
    if "aws" in suffix_str:
        csp_string = 'aws'
    elif "Azure" in suffix_str:
        csp_string = 'azure'

    output_dag_description_filename = f"serwo-{csp_string}-dag-description.json"
    output_dag_description_filepath = f"{output_dir}/{output_dag_description_filename}"
    with open(output_dag_description_filepath, "w") as outfile:
        print(f"Writing json to directory {output_dag_description_filepath}")
        json.dump(output_dict, outfile, indent=4)

    return output_dag_description_filename

def handle_dependencies_and_requirements(paths,op_path):

    req_path = f'{op_path}/requirements.txt'
    if os.path.exists(req_path):
        ff = open(req_path,'w')
    else:
        ff = open(req_path,'a')
    reqs = set()
    for path in paths:
        ft = open(f'{path}/requirements.txt')
        lines = ft.readlines()
        for line in lines:
            reqs.add(line)

    for xd in reqs:
        ff.write(xd+'\n')

    for path in paths:
        pt = f'{path}/requirements.txt'
        if os.path.exists(pt):
            stream = os.popen(f'rm {pt}')
            stream.close()

    f = 0
    for path in paths:
        pt = f'{path}/dependencies'
        if os.path.exists(pt):
            f = 1

    if f:
        dep_path = f'{op_path}/dependencies'
        if not os.path.exists(dep_path):
            os.mkdir(dep_path)
        for path in paths:
            pt = f'{path}/dependencies'
            if os.path.exists(pt):
                copytree(f'{pt}' , f'{dep_path}')

    for path in paths:
        pt = f'{path}/dependencies'
        if os.path.exists(pt):
            stream = os.popen(f'rm -r {pt}')
            stream.close()



def template(import_line,code):
    output_dir = fusion_template_path_temp
    try:
        file_loader = FileSystemLoader(fusion_template_path)
        env = Environment(loader=file_loader)
        template = env.get_template("fused_runner.py")
        print(f"Created Azure jinja2 environment for Runner")
    except Exception as exception:
        raise Exception("Error in loading jinja template environment")

    # render function
    try:
        output = template.render(import_code=import_line,code=code)
    except:
        raise Exception("Error in jinja template render function")

    try:
        # flush out the generator yaml
        with open(f"{output_dir}", "w+") as runner:
            runner.write(output)
            print(f"Writing python file to directory")
    except:
        raise Exception("Error in writing to template file")


    os.system(f"autopep8 --in-place {fusion_template_path_temp}")


def generate_sub_graph(nodes,user_og_graph):
    return  user_og_graph.subgraph(nodes)


def is_complex(id):
    if 'F' in id:
        return True
    return False

def calc_start(node,id_to_fc_map):
    if not is_complex(node):
        return node
    while True:
        sd = id_to_fc_map[node].get_entry_node()
        if not is_complex(sd):
            return sd
        else:
            node = sd

def calc_end(node,id_to_fc_map):
    if not is_complex(node):
        return node
    while True:
        sd = id_to_fc_map[node].get_exit_node()
        if not is_complex(sd):
            return sd
        else:
            node = sd

def azure_inter_function_edge_latency_model(v,rps):
    x = 2 * v * rps
    y = 0.06 * x + 0.418
    return 1000*y

def func_fuse_module(partition_point, left_sub_dag,right_sub_dag):

    G = deepcopy(left_sub_dag)
    user_og_graph = deepcopy(G)
    source_node_id = [node for node in G.nodes if G.in_degree(node) == 0][0]
    sink_node_id = [node for node in G.nodes if G.out_degree(node) == 0][0]
    G1 = deepcopy(G)
    csp = CSP.toString(partition_point.get_left_csp())
    if csp == 'aws':
        csp_to_send = "AWS"
    else:
        csp_to_send = "Azure"
    fc = fuse_graph(G, source_node_id, sink_node_id, csp_to_send, cost_factor=1.2)
    l = partition_point.get_left_csp()
    csp_l = CSP.toString(l)
    suffix_str = f'left-{csp_l}'
    get_final_graph(G1,fc,user_og_graph,suffix_str)


    G = deepcopy(right_sub_dag)
    user_og_graph = deepcopy(G)
    source_node_id = [node for node in G.nodes if G.in_degree(node) == 0][0]
    sink_node_id = [node for node in G.nodes if G.out_degree(node) == 0][0]
    G1 = deepcopy(G)
    csp = CSP.toString(partition_point.get_right_csp())
    if csp == 'aws':
        csp_to_send = "AWS"
    else:
        csp_to_send = "Azure"
    fc = fuse_graph(G, source_node_id, sink_node_id, csp_to_send, cost_factor=1.2)
    r = partition_point.get_right_csp()
    csp_r = CSP.toString(r)
    suffix_str = f'right-{csp_r}'
    get_final_graph(G1,fc,user_og_graph,suffix_str)


def run_with_partition():
    global G
    G = SerWOUserDag(DAG_DEFINITION_PATH).get_dag()
    pp = PartitionPoint("func2", 3, CSP.toCSP("AWS"), CSP.toCSP("Azure"))
    func_fuse_module(pp, G, G)


import pickle
def generate_refactored_workflow(refactored_wf_id,fused_dir,fused_dag):
    print(refactored_wf_id,fused_dir,fused_dag)
    user_dag_path = f'{USER_DIR}/{DAG_DEFINITION_FILE}'
    dag_json = json.loads(open(user_dag_path,'r').read())
    fused_config = []
    dirs = os.listdir(fused_dir)
    node_id_map = dict()
    for nd in dag_json['Nodes']:
        node_id_map[nd['NodeName']] = nd['NodeId']
    for dir in dirs:
        if 'fused' in dir:
            pyth_path = fused_dir+'/'+dir+'/func.py'
            code = open(pyth_path,'r').readlines()
            fusedd = []
            for line in code:
                if '.function' in line:
                    fusedd.append(line.split()[2].split('.')[0])


            fused_func_id = node_id_map[fusedd[0]]
            original_func_ids = []
            for f in fusedd:
                original_func_ids.append(node_id_map[f])
            dct = dict()
            dct['fused_function_id'] = fused_func_id
            dct['original_function_ids'] = original_func_ids

            fused_config.append(dct)


    print(fused_config)
    print('======')
    dag_json['refactoring_strategy'] = 'Function fusion'
    dag_json['wf_refactored_id'] = refactored_wf_id
    dag_json['wf_partitions'] = []
    partition_label = ccsp
    function_ids = []
    fused_nodes = json.loads(open(f'{USER_DIR}/{fused_dag}','r').read())['Nodes']
    for fd in fused_nodes:
        function_ids.append(fd['NodeId'])

    obj = dict()
    obj["partition_label"] = partition_label
    obj['function_ids'] = function_ids
    dag_json['wf_partitions'].append(obj)
    # print(dag_json)

    try:
        #TODO - create table for refactored wf
        dynPartiQLWrapper = PartiQLWrapper('workflow_refactored_table')
        dynPartiQLWrapper.put(dag_json)
    except ClientError as e:
        print(e)
        exit()



def generate_deployment_logs(left,user_dir,wf_id,refactored_wf_id):
    workflow_deployment_id = str(uuid.uuid4())

    dc = ccsp.lower()
    lpath = f"{user_dir}/{left}"
    print(lpath)
    js_left = json.loads(open(lpath,'r').read())

    lp = []


    for nd in js_left['Nodes']:
        lp.append(nd['NodeId'])




    d = dict()
    d['wf_id'] = wf_id
    d['refactored_wf_id'] = refactored_wf_id
    d["wf_dc_config"] = {
        'aws' : {"region": "ap-south-1", "csp": "AWS"},
        'azure' : {"region": "Central India", "csp": "Azure"}
    }
    d['wf_deployment_name'] = 'JPDC SMART GRID Fusion'

    d['wf_deployment_id'] = workflow_deployment_id
    d['wf_deployment_time'] = str(datetime.datetime.now())

    a=dict()
    for nd in js_left['Nodes']:
        a[nd['NodeId']] = {'dc_config_id' : dc ,"resource_id":'','endpoint':''}


    d['func_deployment_config'] = a
    try:
        dynPartiQLWrapper = PartiQLWrapper('workflow_deployment_table')
        dynPartiQLWrapper.put(d)
        print('====')
    except ClientError as e:
        print(e)
        exit()
    
    return workflow_deployment_id

def add_collect_logs_function(dag_path,G):
    out_path = 'python/src/utils/CollectLogDirectories'

    node_name = 'CollectLogs'
    collect_dir =  out_path + '/'+node_name




    xd = list(nx.topological_sort(G))
    ind = len(xd)-1
    max_id = int(xd[ind])
    print(max_id)
    fnc_src = f'{USER_DIR}/src'

    dest = fnc_src+'/'+node_name

    copy_tree(collect_dir, dest)
    dagg = json.loads(open(f'{USER_DIR}/{dag_path}','r').read())
    collect = dict()

    node_name_max= ''
    for nd in dagg['Nodes']:
        if int(nd['NodeId']) == max_id:
            node_name_max = nd['NodeName']

    edge = {node_name_max :[node_name]}

    collect['NodeId'] = '256'
    collect['NodeName'] = node_name
    collect['Path'] = fnc_src + '/'+node_name
    collect['EntryPoint'] = 'func.py'
    collect['CSP'] = ccsp
    collect['MemoryInMB'] = 256
    dagg['Nodes'].append(collect)
    dagg['Edges'].append(edge)
    outt = open(f'{USER_DIR}/{dag_path}','w')
    outt.write(json.dumps(dagg))
    outt.close()


import subprocess
def deploy(dag):

    if ccsp == 'AWS':
        subprocess.call(['python3', 'aws_create_statemachine.py',USER_DIR ,dag, 'REST'])
    elif ccsp == 'Azure':
        os.chdir('..')
        subprocess.call(['sh', f'./azure_build.sh',USER_DIR ,dag])


def run_without_partition():
    wf_id = str(uuid.uuid4())
    wf_name = push_user_dag_to_provenance(wf_id)
    global G, node, god_list
    gg = SerWOUserDag(DAG_DEFINITION_PATH).get_dag()
    fin_g = deepcopy(gg)


    G = deepcopy(fin_g)

    user_og_graph = deepcopy(G)
    print(user_og_graph)
    CSP = sys.argv[3]
    source_nodeId = [node for node in G.nodes if G.in_degree(node) == 0][0]
    sink_nodeId = [node for node in G.nodes if G.out_degree(node) == 0][0]
    G1 = deepcopy(G)

    fc, latency, user_graph_latency, cost, user_dag_cost = fuse_graph(G, source_nodeId, sink_nodeId, CSP,
                                                                      cost_factor=1.2)
    # print(
    #     f'latency before {user_graph_latency}, latency after: {latency}, cost before: {user_dag_cost}, cost after: {cost}')



    # with open(f'{CSP}_2.pkl', 'wb') as f:
    #     pickle.dump(god_list, f)

    # with open(f'{CSP}_2.pkl', 'rb') as f:
    #     god_list = pickle.load(f)

    # print(len(god_list))
    # print(f'Evolution of costs in fusion per stage: {CSP}')
    # print(god_cost)
    #
    # idx = int(sys.argv[3])
    # fc = god_list[idx]
    # print('final')
    # for fusion_candidate in fc:
    #     print(fusion_candidate.get_id(), fusion_candidate.get_nodes())


    # fcc = god_list_2[-1]
    # print('final 2')
    # print(len(god_list_2))
    # for fusion_candidate in fcc:
    #     print(fusion_candidate.get_id(), fusion_candidate.get_nodes())


    suffix_str = f'{CSP}'
    fused_pth,dag_p,G = get_final_graph(G1,fc,user_og_graph,suffix_str)
    add_collect_logs_function(dag_p,G)
    refactored_wf_id  = str(uuid.uuid4())
    generate_refactored_workflow(refactored_wf_id,fused_pth,dag_p)
    workflow_deployment_id = generate_deployment_logs(dag_p,USER_DIR,wf_id,refactored_wf_id)
    deploy(dag_p)

    return wf_name, wf_id, refactored_wf_id, workflow_deployment_id 

def push_user_dag_to_provenance(wf_id):
    global dynPartiQLWrapper, e
    # convert this to an api call
    print(":" * 80)
    print(f"Pushing workflow configuration to Dynamo DB")
    
    workflow_name = ""
    try:
        # print(f"{USER_DIR}/{DAG_DEFINITION_FILE}")
        f = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
        js = open(f,'r').read()
        user_workflow_item = json.loads(js)

        user_workflow_item['wf_id'] = wf_id
        workflow_name = user_workflow_item["WorkflowName"]

        dynPartiQLWrapper = PartiQLWrapper('workflow_user_table')
        dynPartiQLWrapper.put(user_workflow_item)
    except ClientError as e:
        print(e)
    print(":" * 80)
    return workflow_name

if __name__ == "__main__":
    #run_with_partition()
    wf_name, wf_id, refactored_wf_id, wf_deployment_id = run_without_partition()
    
    # Genreate Jmx post deployment
    # generate JMX post deployment
    # try:
    #     JMXGenerator.generate_jmx_files(
    #         workflow_name=wf_name,
    #         workflow_deployment_id=wf_deployment_id,
    #         user_dir=USER_DIR,
    #         template_root_dir="python/src/jmx-templates",
    #         csp=ccsp.lower()
    #     )
    # except Exception as e:
    #     print(e)
    
    
    # resources dir
    resources_dir=pathlib.Path.joinpath(pathlib.Path(USER_DIR), "build/workflow/resources")
    provenance_artifacts = {
        "workflow_id": wf_id,
        "refactored_workflow_id": refactored_wf_id,
        "deployment_id": wf_deployment_id
    }

    print("::Provenance Artifacts::")
    print(provenance_artifacts)

    print("::Writing provenance artifacts output to JSON file::")
    json_output = json.dumps(provenance_artifacts, indent=4)
    with open(pathlib.Path.joinpath(resources_dir, "provenance-artifacts.json"), "w+") as out:
        out.write(json_output)


    print("::Adding deployment structure JSON::")
    deployment_structure = {
        "entry_csp": ccsp.lower()
    }    
    deployment_struct_json = json.dumps(deployment_structure, indent=4)
    with open(pathlib.Path.joinpath(resources_dir), "deployment-structure.json", "w+") as out:
        out.write(deployment_struct_json)    