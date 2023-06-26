import numpy as np
import sys


def get_optimal_partitions(latencies_benchmark, data_transfers_benchmark,data_transfers,is_fan_in):

    print(latencies_benchmark)
    print(data_transfers_benchmark)
    n = len(latencies_benchmark[0])
    k = len(data_transfers_benchmark)

    dp = np.zeros((n,k,k), dtype=float)
    for i in range(0,k):
        for j in range(0,k):
            dp[0][j][i] = latencies_benchmark[i][0]

    for i in range(1,n):
        for j in range(0,k):
            min_col = float(sys.maxsize)
            for x in range(0,k):
                if(dp[i-1][x][j] != float(sys.maxsize)):
                    min_col = min(min_col,dp[i-1][x][j])
            for v in range(0,k):
                data_tranfer_latency =float( get_data_transfer_value(data_transfers_benchmark, i, j, v, data_transfers,is_fan_in))
                if data_tranfer_latency != sys.maxsize and latencies_benchmark[v][i] != sys.maxsize and min_col!=sys.maxsize:
                    dp[i][j][v] = min_col + data_tranfer_latency + latencies_benchmark[v][i]
                else:
                    dp[i][j][v] = float(sys.maxsize)

    min_latency = float(sys.maxsize)
    min_i = 0
    min_j = 0
    cloud_indices = []
    for i in range(0,k):
        for j in range(0,k):
            if dp[n-1][i][j] < min_latency:
                min_i = i
                min_j = j
                min_latency = dp[n-1][i][j]


    cloud_indices.append(min_j)
    cloud_indices.append(min_i)
    for i in range(n-2,0,-1):
        min_lat = float(sys.maxsize)
        min_i_local = 0
        for j in range (0,k):
            if min_lat > dp[i][j][min_i]:
                min_lat = dp[i][j][min_i]
                min_i_local = j
        cloud_indices.append(min_i_local)
        min_i = min_i_local

    return list(reversed(cloud_indices)),min_latency


def get_data_transfer_value(data_transfers_benchmark, i, j, v, data_tranfers,is_fan_in):

    constraints_violated = evaluate_inter_cloud_data_transfer_constraints(data_tranfers, i, j, v)
    if constraints_violated:
        return float(sys.maxsize)

    else:
        if is_fan_in[i]:
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


# print(get_optimal_partitions([[5,8,14,2],[3,11,10,7]],[[0,12],[1,0]],[64,64,64],[False,False,False,False]))
