import numpy as np
import sys

init_comm_overhheads = [151,2114.5,67.2]
def get_optimal_partitions(latencies_benchmark, data_transfers_benchmark,data_transfers,is_fan_in,cloud_memory_constraints
                           ,partition_memory_requirements):

    n = len(latencies_benchmark[0])
    k = len(data_transfers_benchmark)

    

    max_mem = max(cloud_memory_constraints) + 1


    dp = np.zeros((n,k,k),dtype=set)
    ## clear the dp array
    for i in range(n):
        for j in range(k):
            for v in range(k):
                dp[i][j][v] = set()
    ## dict in above is a list to value dict

   

    for i in range(k):
        for j in range(k):
            ##dict with key as a list and value as a float
            dp[0][i][j] = set()

            nl = cloud_memory_constraints.copy()
            pth = [j]

            left_mem = cloud_memory_constraints[j] - partition_memory_requirements[0]
            latencyy = latencies_benchmark[j][0] + init_comm_overhheads[j]
            if left_mem < 0:
                latencyy = float(sys.maxsize)
            nl[j] = left_mem
            dp[0][i][j].add((tuple(nl),latencyy,tuple(pth) ))

   
    
    

    for i in range(1,n):
        for j in range(k):
            for v in range(k):
                dp[i][j][v] = set()
                for u in range(k):
                    for (nl, latency,path) in dp[i-1][u][j]:
                        nll = list(nl)
                        ptth = list(path)
                        left_mem = nll[v] - partition_memory_requirements[i]
                        latency += latencies_benchmark[v][i] + get_data_transfer_value(data_transfers_benchmark, i, j, v, data_transfers,is_fan_in)
                        if left_mem >= 0:
                            nll[v] = left_mem
                            ptth.append(v)
                            dp[i][j][v].add((tuple(nll),latency,tuple(ptth) ))
                        

    cloud_indices = [0]*n
    min_latency = float(sys.maxsize)
    
    # print(dp[n-1])
    for i in range(k):
        for j in range(k):
            for (nl,latency,path) in dp[n-1][i][j]:
                if min_latency > latency:
                    min_latency = latency
                    cloud_indices = path
    return cloud_indices,min_latency


def get_data_transfer_value(data_transfers_benchmark, i, j, v, data_tranfers,is_fan_in):

    constraints_violated = evaluate_inter_cloud_data_transfer_constraints(data_tranfers, i, j, v)
    if constraints_violated:
        return float(sys.maxsize)

    else:
        if is_fan_in[i] and j != v:
            return data_transfers_benchmark[j][v] + data_transfers_benchmark[v][v]

        return data_transfers_benchmark[j][v]


def evaluate_inter_cloud_data_transfer_constraints(data_tranfers, i, j, v):
    flag = False
    if v == 1 and j == 0 and data_tranfers[i - 1] > 64:
        flag = True
    if v == 0 and j == 1 and data_tranfers[i - 1] > 256:
        flag = True
    if v==0 and j==0 and data_tranfers[i-1] > 256:
        flag = True

    return flag


#io, cpu_int, cpu_float, mem
#aws,azure,openfaas
rps = 1
compute_stress = [[1634, 16, 1, 4275], [171, 16, 5, 537], [380.0, 3.0, 1.8, 1627.5]]
base_mem_req = [256, 128, 128, 512] 
mem_req = [f*rps for f in base_mem_req]
is_fan_in = [False, False, False, False]
cloud_mem_constraints = [16354,16354,4096]


# comm_bm_1 = [[88, 442, 4180], [385.0, 2320.0, 4752], [973, 1831, 674.5]]
# comm_bm_4 = [[92, 421, 4070], [326, 2397.5, 3873], [950.5, 1588, 681.0]]
# comm_bm_16 = [[97, 443, 3834], [354, 2472.0, 4190], [965.5, 1135, 686.0]]
# comm_bm_32 = [[103, 486, 4884], [380, 2626.5, 3880], [963, 1120.0, 694.5]]

# comm_bm_60 = [[113, 556, 4155.0], [524, 2875.0, 3882.5], [982, 1361, 691.5]]
# comm_bm_64 = [[120, 540, 4120], [464, 3140.5, 99999], [980, 1160.5, 678.5]]
# comm_bm_128 = [[145, 635, 4150], [614, 3469.5, 99999], [1018.0, 1336.0, 688.5]]
comm_bm_250 = [[183, 786, 4150], [736, 4100.5, 99999], [1114, 99999.0, 695.5]]

# print(get_optimal_partitions(compute_stress,comm_bm_1,[1,1,1],is_fan_in,cloud_mem_constraints,mem_req))
# print(get_optimal_partitions(compute_stress,comm_bm_4,[4,4,4],is_fan_in,cloud_mem_constraints,mem_req))
# print(get_optimal_partitions(compute_stress,comm_bm_16,[16,16,16],is_fan_in,cloud_mem_constraints,mem_req))
# print(get_optimal_partitions(compute_stress,comm_bm_32,[32,32,32],is_fan_in,cloud_mem_constraints,mem_req))
# print(get_optimal_partitions(compute_stress,comm_bm_60,[60,60,60],is_fan_in,cloud_mem_constraints,mem_req))

# print(get_optimal_partitions(compute_stress,comm_bm_64,[64,64,64],is_fan_in,cloud_mem_constraints,mem_req))
# print(get_optimal_partitions(compute_stress,comm_bm_128,[128,128,128],is_fan_in,cloud_mem_constraints,mem_req))
print(get_optimal_partitions(compute_stress,comm_bm_250,[250,250,250],is_fan_in,cloud_mem_constraints,mem_req))

