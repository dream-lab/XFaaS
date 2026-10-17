import xfaas_benchmark
import dp_xfaas_partitioner
import dp_fusion_partition
# import ilp_xfaas_partitioner
import sys
import random
import string
import json
import time
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP
import pathlib
project_dir = pathlib.Path(__file__).parent.resolve()

PARTITION_ID_LENGTH = 5
USER_CONFIG_PATH = f'{project_dir}/config/xfaas_user_config.json'

# Defaults when keys are missing from xfaas_user_config.json
# "partition" = MMC DP only (existing behavior)
# "partition_plus_fusion" = combined fusion+partition DP
DEFAULT_OPTIMIZATION_STRATEGY = "partition"
DEFAULT_USER_BUDGET = None  # None => DP picks min feasible terminal cost


def generate_random_string(N):
    res = ''.join(random.choices(string.ascii_lowercase +
                                 string.digits, k=N))

    return res


def load_user_config():
    """Load serwo/config/xfaas_user_config.json (strategy + budget live here)."""
    try:
        with open(USER_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f'Warning: could not load {USER_CONFIG_PATH}: {e}')
        return {}


def get_optimization_settings():
    """
    Read optimization_strategy and user_budget from xfaas_user_config.json.

    user_budget is the target_cost passed into fusion+partition DP translate().
    If null/missing, DP falls back to min feasible terminal cost.
    """
    config = load_user_config()
    strategy = config.get(
        'optimization_strategy', DEFAULT_OPTIMIZATION_STRATEGY)
    budget = config.get('user_budget', DEFAULT_USER_BUDGET)
    if budget is not None:
        budget = float(budget)
    print(f'Optimization settings from config: strategy={strategy}, '
          f'user_budget={budget}')
    return strategy, budget


def get_supported_cloud_ids():
    clouds = json.loads(
        open(f'{project_dir}/config/cloud_dictionary.json', 'r').read())
    cloud_ids = []
    for cd in clouds:
        cloud_ids.append(cd)
    return cloud_ids, clouds


def _node_ids_for_range(valid_partition_points, start_inclusive, end_inclusive):
    """Map inclusive index range over valid_partition_points to DAG node ids."""
    node_ids = []
    for idx in range(start_inclusive, end_inclusive + 1):
        node_ids.append(valid_partition_points[idx]['node_id'])
    return node_ids


def translate(clouds, cloud_dictionary, valid_partition_points, user_dag):

    final_output = []
    i = 0
    part_id = "0000"
    kk = 0
    #Adding a condition for pinned Single Node workflows:
    if (len(valid_partition_points) == 1 and len(set(clouds)) == 1 and  len(user_dag.get_dag().edges) == 0):
        function_name = (user_dag.get_dag()).nodes[valid_partition_points[0]['node_id']]['NodeName']
        out_degree = valid_partition_points[0]['out_degree']
        csp = CSP(cloud_dictionary[str(clouds[0])]['csp']) 
        region = cloud_dictionary[str(clouds[0])]['region']
        node_ids = _node_ids_for_range(valid_partition_points, 0, 0)
        partition_point = PartitionPoint(
            function_name, out_degree, csp, None, part_id, region,
            node_ids=node_ids, is_fused=False)
        return [partition_point]

    while(i < len(clouds)):
        j = i
        while j < len(clouds) and clouds[j] == clouds[i]:
            j += 1
        j -= 1
        function_name = (
            user_dag.get_dag()).nodes[valid_partition_points[j]['node_id']]['NodeName']
        out_degree = valid_partition_points[j]['out_degree']
        csp = CSP(cloud_dictionary[str(clouds[i])]['csp'])
        region = cloud_dictionary[str(clouds[i])]['region']
        node_ids = _node_ids_for_range(valid_partition_points, i, j)
        partition_point = PartitionPoint(
            function_name, out_degree, csp, None, part_id, region,
            node_ids=node_ids, is_fused=False)
        final_output.append(partition_point)
        kk += 1
        part_id = str(kk).zfill(4)
        i = j+1

    return final_output


def translate_fusion_verdict(verdict, cloud_dictionary, valid_partition_points, user_dag):
    """
    Populate PartitionPoints from fusion+partition DP verdict.

    Verdict segment (cloud_id, start_idx, end_idx) uses 1-based DP indices
    covering 0-based nodes [start_idx, end_idx).
    is_fused / node_ids are set HERE before returning to main.
    """
    final_output = []
    part_id_num = 0
    nx_dag = user_dag.get_dag()

    for cloud_id, start_idx, end_idx in verdict:
        # DP segment covers nodes with 0-based indices start_idx .. end_idx-1
        start_inclusive = start_idx
        end_inclusive = end_idx - 1
        if end_inclusive < start_inclusive:
            continue

        node_ids = _node_ids_for_range(
            valid_partition_points, start_inclusive, end_inclusive)
        boundary_pp = valid_partition_points[end_inclusive]
        function_name = nx_dag.nodes[boundary_pp['node_id']]['NodeName']
        out_degree = boundary_pp['out_degree']
        csp = CSP(cloud_dictionary[str(cloud_id)]['csp'])
        region = cloud_dictionary[str(cloud_id)]['region']
        is_fused = len(node_ids) > 1
        part_id = str(part_id_num).zfill(4)

        final_output.append(PartitionPoint(
            function_name, out_degree, csp, None, part_id, region,
            node_ids=node_ids, is_fused=is_fused))
        part_id_num += 1

    return final_output


def _memories_and_transfer_sizes(user_dag, valid_partition_points, inter_cloud_data_transfers):
    nx_dag = user_dag.get_dag()
    memories = []
    for pp in valid_partition_points:
        node_id = pp['node_id']
        memories.append(nx_dag.nodes[node_id].get('MemoryInMB', 128))

    # One transfer size per boundary before node i (i>=1); pad/truncate to n.
    n = len(valid_partition_points)
    if inter_cloud_data_transfers and len(inter_cloud_data_transfers) >= n:
        data_transfer_sizes = list(inter_cloud_data_transfers[:n])
    elif inter_cloud_data_transfers:
        data_transfer_sizes = list(inter_cloud_data_transfers) + [0] * (
            n - len(inter_cloud_data_transfers))
    else:
        data_transfer_sizes = [0] * n
    return memories, data_transfer_sizes


def partition_dag(user_dag, user_pinned_nodes, benchmark_path, is_math, disabled_pair):
    valid_partition_points = user_dag.get_partition_points()
    cloud_ids, cloud_dictionary = get_supported_cloud_ids()
    latencies_benchmark, data_transfers_benchmark, inter_cloud_data_tranfers, is_fan_in = \
        xfaas_benchmark.populate_benchmarks_for_user_dag(user_dag, user_pinned_nodes, benchmark_path,
                                                         valid_partition_points, cloud_ids)

    strategy, user_budget = get_optimization_settings()

    if strategy == "partition_plus_fusion":
        memories, data_transfer_sizes = _memories_and_transfer_sizes(
            user_dag, valid_partition_points, inter_cloud_data_tranfers)
        # user_budget from xfaas_user_config.json -> target_cost for DP translate
        verdict, cost_used = dp_fusion_partition.get_optimal_partitions(
            latencies_benchmark,
            memories,
            data_transfer_sizes,
            data_transfers_benchmark=data_transfers_benchmark,
            target_cost=user_budget,
        )
        print('Result from fusion+partition DP:\n verdict -> ',
              verdict, '\n user_budget -> ', user_budget,
              '\n cost_used -> ', cost_used)
        # Population site: node_ids + is_fused set before return to main
        final_cloud_config = translate_fusion_verdict(
            verdict, cloud_dictionary, valid_partition_points, user_dag)
        return final_cloud_config

    # Default: existing MMC partition-only path
    opt = "DP"
    if opt != 'ILP':
        print("pased this")
        clouds, min_latency = dp_xfaas_partitioner.get_optimal_partitions(latencies_benchmark,
                                                                          data_transfers_benchmark,
                                                                          inter_cloud_data_tranfers,
                                                                          is_fan_in, disabled_pair)

        if min_latency == sys.maxsize:
            print('DAG CANNOT BE PARTITIONED FOR GIVEN INPUT VALUES AND USER CONSTRAINTS')

    print('Result from DP partitioner: \n clouds -> ',
          clouds, '\n Latency -> ', min_latency)
    final_cloud_config = translate(
        clouds, cloud_dictionary, valid_partition_points, user_dag)

    return final_cloud_config


def ilp():
    pass
    # else:
    #     clouds,min_latency = ilp_xfaas_partitioner.get_optimal_partitions(latencies_benchmark,
    #                                                                      data_transfers_benchmark,
    #                                                                      inter_cloud_data_tranfers,
    #                                                                      is_fan_in)
    # if min_latency == sys.maxsize:
    #     print('DAG CANNOT BE PARTITIONED FOR GIVEN INPUT VALUES AND USER CONSTRAINTS')
    # print('Result from ILP partitioner: \n clouds -> ',clouds,'\n Latency -> ',min_latency)
    # final_cloud_config = translate(clouds,cloud_dictionary,valid_partition_points,user_dag)
    # print('Final ILP Cloud Config: ',final_cloud_config)


def optimize(user_dag, user_pinned_nodes, benchmark_path, disabled_pair=[], is_math=False):

    return partition_dag(user_dag, user_pinned_nodes, benchmark_path, is_math, disabled_pair)


def fuse(user_dag, user_dag_input, user_dir):
    # Lazy import: fusion_wrapper pulls modules that read sys.argv at import time
    import xfaas_fusion_wrapper as fusion_wrapper
    csp = "AWS"
    wf_name, wf_id, refactored_wf_id, wf_deployment_id, dag_path = fusion_wrapper.run(user_dag, user_dir,
                                                                                      user_dag_input,
                                                                                      csp)
    return csp, user_dir + '/' + dag_path
