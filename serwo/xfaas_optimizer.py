import xfaas_fusion_wrapper as fusion_wrapper
import xfaas_benchmark
import dp_xfaas_partitioner
# import ilp_xfaas_partitioner
import sys
import json
import time

def get_supported_cloud_ids():
    clouds = json.loads(open('config/cloud_dictionary.json', 'r').read())
    cloud_ids = []
    for cd in clouds:
        cloud_ids.append(cd)
    return cloud_ids,clouds


def translate(clouds,cloud_dictionary):
    final_output = []
    for cd in clouds:
        final_output.append(cloud_dictionary[str(cd)])
    return final_output


def partition_dag(user_dag,user_dir,user_dag_input,user_pinned_nodes,benchmark_path):
    valid_partition_points = user_dag.get_partition_points()
    cloud_ids,cloud_dictionary = get_supported_cloud_ids()
    latencies_benchmark, data_transfers_benchmark, inter_cloud_data_tranfers, is_fan_in = xfaas_benchmark.populate_benchmarks_for_user_dag(user_dag,
                                                                                                     user_dir,
                                                                                                     user_pinned_nodes,
                                                                                                     benchmark_path,
                                                                                                     valid_partition_points,
                                                                                                     cloud_ids)

    print('Benchmark Populator values \n',latencies_benchmark,data_transfers_benchmark,inter_cloud_data_tranfers,is_fan_in)

    opt = sys.argv[4]
    st = time.time()
    if opt == 'DP':
        clouds,min_latency = dp_xfaas_partitioner.get_optimal_partitions(latencies_benchmark,
                                                             data_transfers_benchmark,
                                                             inter_cloud_data_tranfers,
                                                                         is_fan_in)

        if min_latency == sys.maxsize:
            print('DAG CANNOT BE PARTITIONED FOR GIVEN INPUT VALUES AND USER CONSTRAINTS')
        print('Result from DP partitioner: \n clouds -> ',clouds,'\n Latency -> ',min_latency)

        final_cloud_config = translate(clouds,cloud_dictionary)
        print('Final DP Cloud Config: ',final_cloud_config)

    else:
        clouds,min_latency = ilp_xfaas_partitioner.get_optimal_partitions(latencies_benchmark,
                                                                         data_transfers_benchmark,
                                                                         inter_cloud_data_tranfers,
                                                                         is_fan_in)

        if min_latency == sys.maxsize:
            print('DAG CANNOT BE PARTITIONED FOR GIVEN INPUT VALUES AND USER CONSTRAINTS')
        print('Result from ILP partitioner: \n clouds -> ',clouds,'\n Latency -> ',min_latency)

        final_cloud_config = translate(clouds,cloud_dictionary)
        print('Final ILP Cloud Config: ',final_cloud_config)

    en = time.time()

    print('TIME TAKEN = ',(en-st), ' seconds')
    return user_dir


def optimize(user_dag,user_dir,user_dag_input,user_pinned_nodes,benchmark_path):

    return partition_dag(user_dag,user_dir,user_dag_input,user_pinned_nodes,benchmark_path)

def fuse(user_dag, user_dag_input, user_dir):
    csp = "AWS"
    wf_name, wf_id, refactored_wf_id, wf_deployment_id, dag_path = fusion_wrapper.run(user_dag, user_dir,
                                                                                      user_dag_input,
                                                                                      csp)
    return csp, user_dir + '/' + dag_path
