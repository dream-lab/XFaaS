import xfaas_fusion_wrapper as fusion_wrapper
import xfaas_benchmark
import dp_xfaas_partitioner
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
def generate_random_string(N):
    res = ''.join(random.choices(string.ascii_lowercase +
                                 string.digits, k=N))

    return res

def get_supported_cloud_ids():
    clouds = json.loads(open(f'{project_dir}/config/cloud_dictionary.json', 'r').read())
    cloud_ids = []
    for cd in clouds:
        cloud_ids.append(cd)
    return cloud_ids,clouds


def translate(clouds,cloud_dictionary,valid_partition_points,user_dag):
    final_output = []
    i = 0
    while(i < len(clouds)):
        j = i
        while j < len(clouds) and clouds[j] == clouds[i]:
            j += 1
        j -= 1
        function_name = (user_dag.get_dag()).nodes[valid_partition_points[j]['node_id']]['NodeName']
        out_degree = valid_partition_points[j]['out_degree']
        csp = CSP(cloud_dictionary[str(clouds[i])]['csp'])
        region = cloud_dictionary[str(clouds[i])]['region']
        part_id = generate_random_string(PARTITION_ID_LENGTH)
        partition_point = PartitionPoint(function_name, out_degree, csp, None, part_id, region)
        final_output.append(partition_point)
        i = j+1

    return final_output


def partition_dag(user_dag,user_pinned_nodes,benchmark_path):
    valid_partition_points = user_dag.get_partition_points()
    cloud_ids,cloud_dictionary = get_supported_cloud_ids()
    latencies_benchmark, data_transfers_benchmark, inter_cloud_data_tranfers, is_fan_in = \
        xfaas_benchmark.populate_benchmarks_for_user_dag(user_dag,user_pinned_nodes,benchmark_path,
                                                         valid_partition_points, cloud_ids)
    opt = "DP"

    if opt != 'ILP':
        clouds,min_latency = dp_xfaas_partitioner.get_optimal_partitions(latencies_benchmark,
                                                             data_transfers_benchmark,
                                                             inter_cloud_data_tranfers,
                                                                         is_fan_in)

        if min_latency == sys.maxsize:
            print('DAG CANNOT BE PARTITIONED FOR GIVEN INPUT VALUES AND USER CONSTRAINTS')
        print('Result from DP partitioner: \n clouds -> ',clouds,'\n Latency -> ',min_latency)

        final_cloud_config = translate(clouds,cloud_dictionary,valid_partition_points,user_dag)

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


def optimize(user_dag,user_pinned_nodes,benchmark_path):

    return partition_dag(user_dag,user_pinned_nodes,benchmark_path)

def fuse(user_dag, user_dag_input, user_dir):
    csp = "AWS"
    wf_name, wf_id, refactored_wf_id, wf_deployment_id, dag_path = fusion_wrapper.run(user_dag, user_dir,
                                                                                      user_dag_input,
                                                                                      csp)
    return csp, user_dir + '/' + dag_path
