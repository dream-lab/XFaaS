import json
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP
import python.src.utils.classes.commons.serwo_user_dag as serwo_user_dag
import sys
from copy import deepcopy
import networkx as nx

AWS_DATA_TRANSFER_THRESHOLD_IN_KB = 256
AZURE_QUEUE_DATA_TRANSFER_THRESHOLD_IN_KB = 64
glo = []
RPS = 1


def get_user_dag_benchmark_values(dag_path):
    f = open(dag_path, "r")
    bench_mark_json = json.loads(f.read())
    bench_mark = dict()
    bench_mark["node_benchmarks"] = bench_mark_json["NodeBenchmarks"]
    bench_mark["edge_benchmarks"] = dict()
    for node in bench_mark_json["EdgeBenchmarks"]:
        for neighbors in bench_mark_json["EdgeBenchmarks"][node]:
            for neighbor in neighbors:
                pair = (node, neighbor)
                bench_mark["edge_benchmarks"][pair] = dict()
                bench_mark["edge_benchmarks"][pair]["data_transfer_size"] = neighbors[
                    neighbor
                ]["DataTransferSize"]
                for key in neighbors[neighbor]["Latencies"]:
                    for latency_key in key:
                        bench_mark["edge_benchmarks"][pair][latency_key] = key[
                            latency_key
                        ]

    return bench_mark


def validate_edges(edge_benchmarks, csp, edges):
    for u, v in edges:
        edge_data_transfer = edge_benchmarks[(u, v)]["data_transfer_size"]
        if csp == "AWS":
            if edge_data_transfer > AWS_DATA_TRANSFER_THRESHOLD_IN_KB:
                return -1

    return 0


def validate_inter_cloud_edge(last_node_out_edges, edge_benchmarks, downstream_csp):
    for u, v in last_node_out_edges:
        edge_data_transfer = edge_benchmarks[(u, v)]["data_transfer_size"]
        if (
            downstream_csp == "AWS"
            and edge_data_transfer > AWS_DATA_TRANSFER_THRESHOLD_IN_KB
        ):
            return -1
        if (
            downstream_csp == "Azure"
            and edge_data_transfer > AZURE_QUEUE_DATA_TRANSFER_THRESHOLD_IN_KB
        ):
            return -1
    return 0


def azure_inter_function_edge_latency_model(v, rps):
    x = 2 * v * rps
    y = 0.06 * x + 0.418
    return 1000 * y


def get_edge_cost(edge_benchmarks, csp, u, v, nodes):
    if csp == "AWS":
        return edge_benchmarks[(u, v)][csp]
    else:
        return azure_inter_function_edge_latency_model(nodes, RPS)


def get_user_dag_cost(G, CSP, node_benchmark):
    cost = 0

    for node in G.nodes:
        memory_in_mb = node_benchmark[node][CSP]["Cost"]
        latency = node_benchmark[node][CSP]["Latency"]
        # gb_s = ((G.nodes[node]['MemoryInMB']/1024) * (G.nodes[node]['ExecDur']/1000))
        gb_s = (memory_in_mb / 1024) * (latency / 1000)
        if CSP == "AWS":
            cost += gb_s * 0.0000166667 + 0.0000285
        else:
            cost += gb_s * 0.000016 + 0.00000786
    return cost


def set_edge_latency(
    G1: nx.classes.digraph.DiGraph, edge_benchmark, node_benchmark, csp
):
    for node in G1.nodes:
        successors = G1.successors(node)
        for succ in successors:
            edge_cost = get_edge_cost(edge_benchmark, csp, node, succ, len(G1.nodes()))

            val = node_benchmark[node][csp]["Latency"] + edge_cost

            G1.edges[(node, succ)]["edge_latency"] = -1 * val
    return G1


def get_longest_path(G1, source, sink, csp, edge_benchmark, node_benchmark):
    G1 = set_edge_latency(G1, edge_benchmark, node_benchmark, csp)
    sp = nx.shortest_path(G1, source, sink, weight="edge_latency")
    path_latency = 0
    for index in range(0, len(sp) - 1):
        path_latency += G1[sp[index]][sp[index + 1]]["edge_latency"]

    path_latency = path_latency * -1

    path_latency += node_benchmark[sink][csp]["Latency"]
    if len(G1.nodes) == 1:
        for node in G1.nodes:
            path_latency = node_benchmark[sink][csp]["Latency"]
            return None, path_latency
    return sp, path_latency


def get_cost_for_critical_path(sub_dag, edge_benchmarks, node_benchmarks, csp):
    graph = nx.DiGraph()

    for node in sub_dag.nodes():
        graph.add_node(node, weight=node_benchmarks[node][csp]["Latency"])

    for u, v in sub_dag.edges():
        graph.add_edge(u, v, weight=edge_benchmarks[(u, v)][csp])

    src = 0
    sink = 0
    for nd in graph.nodes():
        if graph.in_degree(nd) == 0:
            src = nd
        if graph.out_degree(nd) == 0:
            sink = nd
    sp, latency = get_longest_path(
        graph, src, sink, csp, edge_benchmarks, node_benchmarks
    )
    # print(sp,latency)
    # longest_path = nx.dag_longest_path(graph)
    #
    # latency = 0
    # for i in range(len(longest_path)-1):
    #     (u,v) = (longest_path[i],longest_path[i+1])
    #     if csp == 'AWS':
    #         latency += edge_benchmarks[(u,v)][csp]
    #     else:
    #         latency += azure_inter_function_edge_latency_model(len(sub_dag.nodes()),RPS)
    #
    #
    # for node in longest_path:
    #     latency += node_benchmarks[node][csp]['Latency']

    return latency


def get_cost_for_sub_dag(node_benchmarks, edge_benchmarks, sub_dag, csp):
    total_latency = 0
    cost = get_user_dag_cost(sub_dag, csp, node_benchmarks)
    total_latency += get_cost_for_critical_path(
        sub_dag, edge_benchmarks, node_benchmarks, csp
    )

    ## TODO - what to do with cost?
    return total_latency, cost


def evaluate_sub_dag(sub_dag, bench_mark_values, csp):
    edge_benchmarks = bench_mark_values["edge_benchmarks"]
    node_benchmarks = bench_mark_values["node_benchmarks"]
    validation_value = validate_edges(edge_benchmarks, csp, sub_dag.edges())
    if validation_value == -1:
        return validation_value

    cost_for_sub_dag, rs = get_cost_for_sub_dag(
        node_benchmarks, edge_benchmarks, sub_dag, csp
    )
    return cost_for_sub_dag, rs


def get_inter_cloud_overhead(
    last_node, last_node_out_edges, bench_mark_values, edge_key
):
    edge_benchmarks = bench_mark_values["edge_benchmarks"]

    if len(last_node_out_edges) == 1:
        for u, v in last_node_out_edges:
            out_edge = (u, v)
            return edge_benchmarks[out_edge][edge_key]

    for u, v in last_node_out_edges:
        out_edge = (u, v)
        return 2 * edge_benchmarks[out_edge][edge_key]


def evaluate_inter_cloud_node(
    last_node, last_node_out_edges, bench_mark_values, downstream_csp
):
    if downstream_csp == "AWS":
        edge_key = "AzureToAWS"
    else:
        edge_key = "AWSToAzure"

    edge_benchmarks = bench_mark_values["edge_benchmarks"]
    validation_value = validate_inter_cloud_edge(
        last_node_out_edges, edge_benchmarks, downstream_csp
    )
    if validation_value == -1:
        return -1
    total_overhead_for_inter_cloud = get_inter_cloud_overhead(
        last_node=last_node,
        last_node_out_edges=last_node_out_edges,
        bench_mark_values=bench_mark_values,
        edge_key=edge_key,
    )
    return total_overhead_for_inter_cloud


def evaluate_aws_to_azure(
    left_sub_dag, right_sub_dag, bench_mark_values, last_node, last_node_out_edges
):
    cost_left_sub_dag, rs_left = evaluate_sub_dag(
        left_sub_dag, bench_mark_values, "AWS"
    )
    cost_inter_cloud = evaluate_inter_cloud_node(
        last_node, last_node_out_edges, bench_mark_values, "Azure"
    )
    cost_right_sub_dag, rs_right = evaluate_sub_dag(
        right_sub_dag, bench_mark_values, "Azure"
    )

    if cost_left_sub_dag == -1 or cost_right_sub_dag == -1 or cost_inter_cloud == -1:
        ##INVALID_PARTITION, RETURNING INT_MAX
        print("INVALID PARTITION POINNT")
        return sys.maxsize

    c = rs_left + rs_right
    # print('total laws,raz= ',cost_left_sub_dag + cost_right_sub_dag + cost_inter_cloud, 'cost= ',c)
    return cost_left_sub_dag + cost_right_sub_dag + cost_inter_cloud


def evaluate_azure_to_aws(
    left_sub_dag, right_sub_dag, bench_mark_values, last_node, last_node_out_edges
):
    cost_left_sub_dag, rs_left = evaluate_sub_dag(
        left_sub_dag, bench_mark_values, "Azure"
    )

    cost_inter_cloud = evaluate_inter_cloud_node(
        last_node, last_node_out_edges, bench_mark_values, "AWS"
    )

    cost_right_sub_dag, rs_right = evaluate_sub_dag(
        right_sub_dag, bench_mark_values, "AWS"
    )

    if cost_left_sub_dag == -1 or cost_right_sub_dag == -1 or cost_inter_cloud == -1:
        ##INVALID_PARTITION, RETURNING INT_MAX
        print("INVALID PARTITION POINT")
        return sys.maxsize

    c = rs_left + rs_right
    # print('total laz,raws= ',cost_left_sub_dag + cost_right_sub_dag + cost_inter_cloud, 'cost= ',c)
    return cost_left_sub_dag + cost_right_sub_dag + cost_inter_cloud


def enumerate(
    left_partition,
    right_partition,
    bench_mark_values,
    u_graph,
    user_pinned_csp,
    user_pinned_partition_id,
):
    if len(left_partition) == 0 or len(right_partition) == 0:
        return "invalid"

    if user_pinned_partition_id == 1:
        pin = "right"
    if user_pinned_partition_id == 0:
        pin = "left"

    last_node = left_partition[len(left_partition) - 1]
    last_node_out_edges = u_graph.out_edges(last_node)
    left_sub_dag = u_graph.subgraph(left_partition)
    right_sub_dag = u_graph.subgraph(right_partition)

    cost_for_azure_to_aws = evaluate_azure_to_aws(
        left_sub_dag=left_sub_dag,
        right_sub_dag=right_sub_dag,
        bench_mark_values=bench_mark_values,
        last_node=last_node,
        last_node_out_edges=last_node_out_edges,
    )

    cost_for_aws_to_azure = evaluate_aws_to_azure(
        left_sub_dag=left_sub_dag,
        right_sub_dag=right_sub_dag,
        bench_mark_values=bench_mark_values,
        last_node=last_node,
        last_node_out_edges=last_node_out_edges,
    )

    if cost_for_aws_to_azure == sys.maxsize and cost_for_azure_to_aws == sys.maxsize:
        return "invalid"

    glo.append((cost_for_aws_to_azure, cost_for_azure_to_aws))
    if user_pinned_partition_id != -1:
        if pin == "left":
            if user_pinned_csp == "AWS":
                return "AWSToAzure", cost_for_aws_to_azure
            elif user_pinned_csp == "Azure":
                return "AzureToAWS", cost_for_azure_to_aws
        elif pin == "right":
            if user_pinned_csp == "AWS":
                return "AzureToAWS", cost_for_azure_to_aws
            elif user_pinned_csp == "Azure":
                return "AWSToAzure", cost_for_aws_to_azure
    if cost_for_aws_to_azure < cost_for_azure_to_aws:
        return "AWSToAzure", cost_for_aws_to_azure
    else:
        return "AzureToAWS", cost_for_azure_to_aws


def handle_two_parts(u_graph, partition_points, bench_mark_values, user_pinned_csp):
    global_min_cost = 999999
    global_route = ""
    fin_part = dict()
    crono = []
    for partition_point in partition_points:
        user_pinned_partition_id = -1
        if "user_pinned_part_id" in partition_point:
            user_pinned_partition_id = partition_point["user_pinned_part_id"]

        left_partition, right_partition = serwo_user_dag.get_partition_lists(
            partition_point, u_graph
        )
        best_combination = enumerate(
            left_partition,
            right_partition,
            bench_mark_values,
            u_graph,
            user_pinned_csp,
            user_pinned_partition_id,
        )
        if best_combination == "invalid":
            continue
        route, cost = best_combination
        if cost < global_min_cost:
            global_min_cost = cost
            global_route = route
            fin_part = partition_point
        crono.append((cost, route, partition_point))
    if global_route == "AzureToAWS":
        left = "Azure"
        right = "AWS"
    else:
        left = "AWS"
        right = "Azure"

    if len(fin_part) == 0:
        return "null"

    fin_part["left_csp"] = CSP.toCSP(left)
    fin_part["right_csp"] = CSP.toCSP(right)
    fin_part["partition_cost"] = global_min_cost

    crono = sorted(crono)
    # print(f'sorted list : {crono}')

    # print('god logs: ',glo)
    return fin_part
    # return PartitionPoint("func2", CSP.toCSP("AWS"), CSP.toCSP("Azure"))


def enumerate_single(u_graph, bench_mark_values, user_pinned_csp):
    aws_cost, rs_full = evaluate_sub_dag(
        u_graph, bench_mark_values=bench_mark_values, csp="AWS"
    )
    azure_cost, rs_full = evaluate_sub_dag(
        u_graph, bench_mark_values=bench_mark_values, csp="Azure"
    )

    if aws_cost == -1 or azure_cost == -1:
        return "invalid"
    if user_pinned_csp == "AWS":
        return "AWS", aws_cost
    if user_pinned_csp == "Azure":
        return "Azure", azure_cost

    if aws_cost <= azure_cost:
        return "AWS", aws_cost
    return "Azure", azure_cost


def handle_one_part(u_graph, bench_mark_values, user_pinned_csp):
    best_csp = enumerate_single(
        u_graph, bench_mark_values=bench_mark_values, user_pinned_csp=user_pinned_csp
    )
    if best_csp != "invalid":
        return best_csp


ans = []
tmp = []


def recurse(n, left, k):
    if k == 0:
        ans.append(deepcopy(tmp))
        return

    for i in range(left, n + 1):
        tmp.append(i)
        recurse(n, i + 1, k - 1)
        tmp.pop()


def enumurate_all_combinations(length, start_index, num_parts):
    global ans
    ans = []
    recurse(length, start_index, num_parts - 1)
    lol = []
    for x in ans:
        xd = [0]
        for aa in x:
            xd.append(aa)
        xd.append(length + 1)
        lol.append(xd)
    return lol


def bfs(src, dest, ind, G):
    n_vis = []
    if ind == 0:
        n_vis.append(src)

    edgess = nx.bfs_edges(G, src)
    vis = dict()
    for e in edgess:
        if e[0] != dest:
            if e[0] != src and not (e[0] in vis.keys()):
                n_vis.append(e[0])
                vis[e[0]] = True
            if e[1] != src and not (e[1] in vis.keys()):
                n_vis.append(e[1])
                vis[e[1]] = True
        else:
            break

    return n_vis


def handle_generic_num_parts(
    u_graph,
    partition_points,
    bench_mark_values,
    user_pinned_csp,
    num_parts,
    user_pinned_nodes,
):
    partition_store = enumurate_all_combinations(
        len(partition_points) - 2, 0, num_parts
    )
    minn_cost = sys.maxsize
    fin_partition_config = []
    min_first = ""
    for partition_config in partition_store:
        l = len(partition_config)
        first = "AWS"
        second = "Azure"
        cst1 = handle_multi_multi_cloud_csp(
            bench_mark_values,
            l,
            partition_config,
            partition_points,
            u_graph,
            first,
            second,
            user_pinned_nodes,
            user_pinned_csp,
        )

        first = "Azure"
        second = "AWS"
        cst2 = handle_multi_multi_cloud_csp(
            bench_mark_values,
            l,
            partition_config,
            partition_points,
            u_graph,
            first,
            second,
            user_pinned_nodes,
            user_pinned_csp,
        )

        local_config, local_first, local_min = evaluate_local_min(
            cst1, cst2, partition_config
        )

        fin_partition_config, min_first, minn_cost = evaluate_global_min(
            fin_partition_config,
            local_config,
            local_first,
            local_min,
            min_first,
            minn_cost,
        )

    print(
        "Final Best Partition: Cost: ",
        minn_cost,
        "First CSP: ",
        min_first,
        "Partition Confg",
        fin_partition_config,
    )
    xdd = len(fin_partition_config)
    parts = []
    for i in range(1, xdd - 1):
        parts.append(deepcopy(partition_points[fin_partition_config[i]]))

    for i in range(0, len(parts)):
        left_csp, right_csp = evaluate_left_right_csp(i, min_first)
        parts[i]["left_csp"] = CSP.toCSP(left_csp)
        parts[i]["right_csp"] = CSP.toCSP(right_csp)

    return parts


def evaluate_left_right_csp(i, min_first):
    if min_first == "AWS":
        if i % 2 == 0:
            left_csp = "AWS"
            right_csp = "Azure"
        else:
            left_csp = "Azure"
            right_csp = "AWS"
    else:
        if i % 2 == 0:
            left_csp = "Azure"
            right_csp = "AWS"
        else:
            left_csp = "AWS"
            right_csp = "Azure"
    return left_csp, right_csp


def evaluate_local_min(cst1, cst2, partition_config):
    if cst1 == sys.maxsize and cst2 == sys.maxsize:
        local_min = cst2
        local_config = partition_config
        local_first = "Azure"

    elif cst1 == sys.maxsize:
        local_min = cst2
        local_config = partition_config
        local_first = "Azure"
    elif cst2 == sys.maxsize:
        local_min = cst1
        local_config = partition_config
        local_first = "AWS"
    else:
        if cst1 < cst2:
            local_min = cst1
            local_config = partition_config
            local_first = "AWS"
        else:
            local_min = cst2
            local_config = partition_config
            local_first = "Azure"
    return local_config, local_first, local_min


def evaluate_global_min(
    fin_partition_config, local_config, local_first, local_min, min_first, minn_cost
):
    if local_min < minn_cost:
        minn_cost = local_min
        fin_partition_config = local_config
        min_first = local_first
    return fin_partition_config, min_first, minn_cost


def handle_multi_multi_cloud_csp(
    bench_mark_values,
    l,
    partition_config,
    partition_points,
    u_graph,
    first,
    second,
    user_pinned_nodes,
    pinned_csp,
):
    is_pinned = dict()
    fin_cost = 0
    for n in user_pinned_nodes:
        is_pinned[n] = True
    for i in range(0, l - 1):
        lef = partition_points[partition_config[i]]["node_id"]
        rig = partition_points[partition_config[i + 1]]["node_id"]
        nds = bfs(lef, rig, i, u_graph)
        sbg = u_graph.subgraph(nds)

        if i % 2 == 0:
            temp_csp = first
            downstream_csp = second
        else:
            temp_csp = second
            downstream_csp = first

        if i < l - 2:
            top_sort = list(nx.topological_sort(sbg))
            last_node_out_edge = u_graph.out_edges(top_sort[-1])
            inter_cloud_cost = evaluate_inter_cloud_node(
                top_sort[-1], last_node_out_edge, bench_mark_values, downstream_csp
            )
            if inter_cloud_cost == -1:
                return sys.maxsize
            fin_cost += inter_cloud_cost
        for nd in nds:
            if nd in is_pinned:
                if temp_csp != pinned_csp:
                    return sys.maxsize
        cst = evaluate_sub_dag(sbg, bench_mark_values, temp_csp)
        if cst == -1:
            return sys.maxsize
        fin_cost += cst[0]

    return fin_cost


def get_best_partition_point(
    u_graph, partition_points, dag_path, num_parts, user_pinned_csp, user_pinned_nodes
):
    bench_mark_values = get_user_dag_benchmark_values(dag_path=dag_path)
    if num_parts == 1:
        return handle_one_part(
            u_graph,
            bench_mark_values=bench_mark_values,
            user_pinned_csp=user_pinned_csp,
        )
    if num_parts == 2:
        return handle_two_parts(
            u_graph,
            partition_points=partition_points,
            bench_mark_values=bench_mark_values,
            user_pinned_csp=user_pinned_csp,
        )

    else:
        return handle_generic_num_parts(
            u_graph,
            partition_points=partition_points,
            bench_mark_values=bench_mark_values,
            user_pinned_csp=user_pinned_csp,
            num_parts=num_parts,
            user_pinned_nodes=user_pinned_nodes,
        )
