import numpy as np
import math
from docplex.mp.model import Model
import portion as por
import random
import pickle
import sys


def get_optimal_partitions(latencies_benchmark, data_transfers_benchmark,data_transfers,is_fan_in):

    mdl = Model('xfaas-partitioner')
    num_parts = len(latencies_benchmark[0])
    num_csps = len(data_transfers_benchmark)

    p = [(m,m+1,i,j) for m in range(0,num_parts-1) for i in range(0,num_csps) for j in range(0,num_csps) ]
    P = mdl.binary_var_dict(p,name='P')

    for m in range(0,num_parts-1):
        mdl.add_constraint(mdl.sum(P[m,m+1,i,j] for i in range(0,num_csps) for j in range(0,num_csps)) == 1)

    for m in range(0,num_parts-2):
        for i in range(0,num_csps):
            for j in range(0,num_csps):
                mdl.add_if_then(P[m,m+1,i,j]==1,mdl.sum(P[m+1,m+2,j,k] for k in range(0,num_csps)) == 1)

    mdl.minimize(mdl.sum(P[m,m+1,i,j]*data_transfers_benchmark[i][j] for m in range(0,num_parts-1) for i in range(0,num_csps) for j in range(0,num_csps))+mdl.sum(P[m,m+1,i,j]*latencies_benchmark[i][m] for m in range(0,num_parts-1) for i in range(0,num_csps) for j in range(0,num_csps))+mdl.sum(P[num_parts-2,num_parts-1,i,j]*latencies_benchmark[j][num_parts-1] for i in range(0,num_csps) for j in range(0,num_csps)))

    solution = mdl.solve()
    latency = solution.objective_value

    data = [v.name.split('_') + [solution.get_value(v)] for v in mdl.iter_variables()]

    cloud_indices = []
    for d in data:
        if d[-1] == 1:
            cloud_indices.append(int(d[-3]))
            cc = d[-2]
    cloud_indices.append(int(cc))
    return cloud_indices,latency



# latencies_benchmark = [[33, 4139, 3095, 14963.68, 3095, 33], [10, 514, 1473, 13816, 1473, 10]]
# data_transfer_benchmark = [[115.67, 1558], [692.85, 2458]]
# data_transfers = [25, 25, 25, 25, 25]
# is_fan_in = [False, False, False, True, False, False]

latencies_benchmark = [[5,8,14,2],[3,11,10,7]]
data_transfer_benchmark = [[0,12],[1,0]]
data_transfers = [64,64,64]
is_fan_in = [False,False,False,False]

print(get_optimal_partitions(latencies_benchmark,data_transfer_benchmark,data_transfers,is_fan_in))