import xfaas_fusion_wrapper as fusion_wrapper
import xfaas_benchmark
import dp_xfaas_partitioner
import sys


def partition_dag(user_dag,user_dir,user_dag_input,user_pinned_nodes,benchmark_path):

    valid_partition_points = user_dag.get_partition_points()
    latencies_benchmark, data_transfers_benchmark, inter_cloud_data_tranfers, is_fan_in = xfaas_benchmark.populate_benchmarks_for_user_dag(user_dag,
                                                                                                     user_dir,
                                                                                                     user_pinned_nodes,
                                                                                                     benchmark_path,
                                                                                                     valid_partition_points)

    print('Benchmark Populator values \n',latencies_benchmark,data_transfers_benchmark,inter_cloud_data_tranfers,is_fan_in)
    clouds,min_latency = dp_xfaas_partitioner.get_optimal_partitions(latencies_benchmark,
                                                         data_transfers_benchmark,
                                                         inter_cloud_data_tranfers,
                                                                     is_fan_in)

    if min_latency == sys.maxsize:
        print('DAG CANNOT BE PARTITIONED FOR GIVEN INPUT VALUES AND USER CONSTRAINTS')
    print('Result from partitioner -> ',clouds,min_latency)
    return user_dir


def optimize(user_dag,user_dir,user_dag_input,user_pinned_nodes,benchmark_path):

    return partition_dag(user_dag,user_dir,user_dag_input,user_pinned_nodes,benchmark_path)

def fuse(user_dag, user_dag_input, user_dir):
    csp = "AWS"
    wf_name, wf_id, refactored_wf_id, wf_deployment_id, dag_path = fusion_wrapper.run(user_dag, user_dir,
                                                                                      user_dag_input,
                                                                                      csp)
    return csp, user_dir + '/' + dag_path
