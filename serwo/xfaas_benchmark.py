import json
from copy import deepcopy
import networkx as nx
import sys


def evaluate_sub_dag(csp_id, sub_dag, user_pinned_nodes):
    nodes = list(sub_dag.nodes)

    constraints_violated = evaluate_node_and_edge_constraints(csp_id, sub_dag, user_pinned_nodes)

    if constraints_violated:
        return sys.maxsize

    else:
        if len(nodes) == 1:
            return sub_dag.nodes[nodes[0]]['NodeBenchmark'][csp_id]['Latency']
        else:
            sub_dag_latency = calculate_sub_dag_latency(csp_id, nodes, sub_dag)

            return sub_dag_latency


def calculate_sub_dag_latency(csp_id, nodes, sub_dag):
    for node in nodes:
        successors = sub_dag.successors(node)
        for succ in successors:
            edge_latency = sub_dag.edges[(node, succ)]['EdgeBenchmark']['Latencies'][csp_id][csp_id]
            node_latency = sub_dag.nodes[node]['NodeBenchmark'][csp_id]['Latency']
            val = edge_latency + node_latency
            sub_dag.edges[(node, succ)]['edge_latency'] = -1 * val
    sources = []
    sink = ''
    for nd in nodes:
        if sub_dag.in_degree(nd) == 0:
            sources.append(nd)
        if sub_dag.out_degree(nd) == 0:
            sink = nd
    max_latency = -1
    for src in sources:
        critical_path = nx.shortest_path(sub_dag, src, sink, weight="edge_latency")
        path_latency = 0
        for index in range(0, len(critical_path) - 1):
            path_latency += sub_dag[critical_path[index]][critical_path[index + 1]]["edge_latency"]

        path_latency = path_latency * -1
        max_latency = max(path_latency, max_latency)

    max_latency += sub_dag.nodes[sink]['NodeBenchmark'][csp_id]['Latency']
    return max_latency


def evaluate_node_and_edge_constraints(csp_id, sub_dag, user_pinned_nodes):
    flag = False
    for nd in sub_dag.nodes:
        if nd in user_pinned_nodes:
            pinned_csp = user_pinned_nodes[nd]
            if pinned_csp != csp_id:
                flag = True
                break
    for ed in sub_dag.edges:
        if sub_dag.edges[ed]['EdgeBenchmark']['DataTransferSize'] > 256 and csp_id == '0':
            flag = True
            break
    return flag


def populate_benchmarks_for_user_dag(user_dag,user_pinned_nodes,benchmark_path,valid_partition_points,cloud_ids):
    bm_data, edges, latency_map, user_dag_copy = init_benchmark_populator(benchmark_path, user_dag,cloud_ids)

    latency_benchmark = populate_latanecy_benchmarks(bm_data, cloud_ids, edges, latency_map, user_dag_copy,
                                                     user_pinned_nodes, valid_partition_points)
    data_transfer_benchmark = populate_data_transfer_benchmarks(cloud_ids, edges, user_dag_copy)
    inter_cloud_data_transfer = populate_inter_cloud_data_transfers(user_dag_copy, valid_partition_points)
    is_fan_in = populate_is_fan_in(user_dag_copy, valid_partition_points)

    return latency_benchmark, data_transfer_benchmark, inter_cloud_data_transfer, is_fan_in


def init_benchmark_populator(benchmark_path, user_dag,cloud_ids):
    user_dag_copy = deepcopy(user_dag.get_dag())
    latency_map = dict()
    for cd in cloud_ids:
        latency_map[cd] = []
    bm_data = json.loads(open(benchmark_path, 'r').read())
    nodes = user_dag_copy.nodes
    edges = user_dag_copy.edges
    for nd in nodes:
        user_dag_copy.nodes[nd]['NodeBenchmark'] = bm_data['NodeBenchmarks'][nd]
    return bm_data, edges, latency_map, user_dag_copy


def populate_is_fan_in(user_dag_copy, valid_partition_points):
    is_fan_in = []
    for nd in valid_partition_points:
        predecessors = list(user_dag_copy.predecessors(nd['node_id']))
        if len(predecessors) > 1:
            is_fan_in.append(True)
        else:
            is_fan_in.append(False)
    return is_fan_in


def populate_inter_cloud_data_transfers(user_dag_copy, valid_partition_points):
    inter_cloud_data_transfer = []
    for nd in valid_partition_points:
        successors = list(user_dag_copy.successors(nd['node_id']))
        for sc in successors:
            inter_cloud_data_transfer.append(
                user_dag_copy.edges[(nd['node_id'], sc)]['EdgeBenchmark']['DataTransferSize'])
            break
    return inter_cloud_data_transfer


def populate_latanecy_benchmarks(bm_data, cloud_ids, edges, latency_map, user_dag_copy, user_pinned_nodes,
                                 valid_partition_points):
    edges_data = dict()
    for edge_data in bm_data['EdgeBenchmarks']:
        src = edge_data
        for neighbors in bm_data['EdgeBenchmarks'][src]:
            for dest in neighbors:
                edges_data[(src, dest)] = neighbors[dest]
    for ed in edges:
        user_dag_copy.edges[ed]['EdgeBenchmark'] = edges_data[ed]
    top_sort = list(nx.topological_sort(user_dag_copy))
    for i in range(0, len(valid_partition_points)):
        sub_nodes = []
        if i == 0:
            sub_nodes.append(valid_partition_points[i]['node_id'])
            subgr = user_dag_copy.subgraph(sub_nodes)
        else:
            prv_node = valid_partition_points[i - 1]['node_id']
            cur_node = valid_partition_points[i]['node_id']
            flag = 0
            for nd in top_sort:
                if flag == 1:
                    sub_nodes.append(nd)
                    if nd == cur_node:
                        break
                if nd == prv_node:
                    flag = 1
            subgr = user_dag_copy.subgraph(sub_nodes)
        for csp_id in range(0, len(cloud_ids)):
            latency = evaluate_sub_dag(cloud_ids[csp_id], subgr, user_pinned_nodes)
            latency_map[cloud_ids[csp_id]].append(latency)
    latency_benchmark = []
    for cd in latency_map:
        latency_benchmark.append(latency_map[cd])
    return latency_benchmark


def populate_data_transfer_benchmarks(cloud_ids, edges, user_dag_copy):
    data_transfer_benchmark = []
    for ed in edges:
        edge_bm = user_dag_copy.edges[ed]['EdgeBenchmark']['Latencies']
        for csp_id_outer in cloud_ids:
            temp = []
            for csp_id_inner in cloud_ids:
                temp.append(edge_bm[csp_id_outer][csp_id_inner])
            data_transfer_benchmark.append(temp)
        break

    return data_transfer_benchmark
