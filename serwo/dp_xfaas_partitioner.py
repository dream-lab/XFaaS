import numpy as np
import sys


def get_optimal_partitions(latencies_benchmark, data_transfers_benchmark,data_transfers,is_fan_in,disabled_pair):

   
    
    time_values_aws_azn = [
        [0.12, 0.45, 0.78, 0.95, 0.52],  # In aws
        [0.15, 0.51, 0.83, 1.02, 0.58],  # In azn
        [0.45, 0.09, 0.62, 0.88, 0.73],  # Sg aws
        [0.51, 0.12, 0.67, 0.94, 0.78],  # Sg azn
        [0.78, 0.62, 0.13, 0.92, 0.89],  # Sy aws
        [0.83, 0.67, 0.16, 0.98, 0.95],  # Sy azn
        [0.95, 0.88, 0.92, 0.08, 0.68],  # US aws
        [1.02, 0.94, 0.98, 0.11, 0.72],  # US azn
        [0.52, 0.73, 0.89, 0.68, 0.12],   # EU aws
        [0.58, 0.78, 0.95, 0.72, 0.18]   # EU azn
    ]

    time_values_aws_azn = np.array(time_values_aws_azn)*1000

    # print("time_values_aws_azn",time_values_aws_azn)



    n = len(latencies_benchmark[0])
    k = len(data_transfers_benchmark)

    if len (disabled_pair) > 0:
        first = disabled_pair[0]
        second = disabled_pair[1]


        for i in range(len(latencies_benchmark[first])):
            latencies_benchmark[first][i] = 9999999
        for i in range(len(latencies_benchmark[second])):
            latencies_benchmark[second][i] = 9999999

        for i in range(0,len(latencies_benchmark)):
            if i%2 ==0:
                num_to_add = time_values_aws_azn[first][i//2]
            else:
                num_to_add = time_values_aws_azn[second][i//2]
            
            latencies_benchmark[i][0] += num_to_add


        data_transfers_benchmark[first][first] = 9999999
        data_transfers_benchmark[first][second] = 9999999
        data_transfers_benchmark[second][first] = 9999999
        data_transfers_benchmark[second][second] = 9999999

        
        
            
                

    

    print("latencies_benchmark",latencies_benchmark)
    
    dp = np.zeros((n,k,k), dtype=float)
    for i in range(0,k):
        for j in range(0,k):
            dp[0][j][i] = latencies_benchmark[i][0]

    for i in range(1,n):
        for j in range(0,k):
            min_col = float(sys.maxsize)
            for x in range(0,k):
                if dp[i-1][x][j] != float(sys.maxsize):
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
        if is_fan_in[i] and j != v:
            return data_transfers_benchmark[j][v] + data_transfers_benchmark[v][v]

        return data_transfers_benchmark[j][v]


def evaluate_inter_cloud_data_transfer_constraints(data_tranfers, i, j, v):
    flag = False
    #Added Large payload support hence commenting this out
    # if v == 1 and j == 0 and data_tranfers[i - 1] > 64:
    #     flag = True
    # if v == 0 and j == 1 and data_tranfers[i - 1] > 256:
    #     flag = True
    # if v==0 and j==0 and data_tranfers[i-1] > 256:
    #     flag = True

    return flag


# print(get_optimal_partitions([[5,8,14,2],[3,11,10,7]],[[0,12],[1,0]],[64,64,64],[False,False,False,False]))
