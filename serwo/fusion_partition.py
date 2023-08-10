from collections import defaultdict
from collections import OrderedDict
import sys

n,k,c = 5,2,30
l = [[2,4,1,1,1],[2,4,1,1,1]]
m = [3,1,2,1,1]
d = [0,25,26,27,28]

data = defaultdict(lambda: defaultdict(dict))

data[0][0][0] = 0,0
data[25][0][0] = 5,2
data[26][0][0] = 1,4
data[27][0][0] = 7,2
data[28][0][0] = 1,1

data[0][0][1] = 0,0
data[25][0][1] = 5,2
data[26][0][1] = 1,4
data[27][0][1] = 7,2
data[28][0][1] = 1,1

data[0][1][0] = 0,0
data[25][1][0] = 5,2
data[26][1][0] = 1,4
data[27][1][0] = 7,2
data[28][1][0] = 1,1

data[0][1][1] = 0,0
data[25][1][1] = 5,2
data[26][1][1] = 1,4
data[27][1][1] = 7,2
data[28][1][1] = 1,1


def fuse(start,end,latencies,memories,prev_cloud,cur_cloud):
    tot_lat = 0
    max_mem = -1
    for i in range(start,end+1):
        tot_lat += latencies[cur_cloud][i-1]
        max_mem = max(max_mem,memories[i-1])
    tot_cost = tot_lat*max_mem

    return tot_cost,tot_lat


def solve(latencies,memories,data_transfer_sizes,data):
    dp = dict()
    fill_base_case(dp,n,k)

    for i in range(2,n+1):
        news = []
        for j in range(i,0,-1):
            for prev_cloud in range(0,k):
                for cur_cloud in range(0,k):

                    cost, latency, search_list = init_operators(data,data_transfer_sizes,
                                                                dp, i, j, latencies,
                                                                memories,prev_cloud,cur_cloud)
                    populate_dp(cost, dp, i, latency, search_list)
                    news.append((cost,latency,dp[j-1]))
        print(news)
        clean_dp(dp, i)

    for dd in dp:
        print(dd,'->',dp[dd])


def fill_base_case(dp, n, k):
    dp[0] = {0: 0}
    for i in range(0,k):
        for j in range(0,k):
            dp[0][i][j] = {0: 0}
    dp[1] = {l[0][0] * m[0]: l[0][0]}


def populate_dp(cost, dp, i, latency, search_list):
    for key in search_list:
        new_cost = key + cost
        new_latency = search_list[key] + latency

        if i in dp:
            if new_cost in dp[i]:
                dp[i][new_cost] = min(new_latency, dp[i][new_cost])
            else:
                dp[i][new_cost] = new_latency
        else:
            dp[i] = dict()
            dp[i][new_cost] = new_latency
    dp[i] = dict(OrderedDict(sorted(dp[i].items())))


def init_operators(data, data_transfer_sizes,dp, i, j, latencies, memories,prev_cloud,cur_cloud):
    cost, latency = fuse(j, i, latencies, memories,prev_cloud,cur_cloud)
    data_transfer_size = data_transfer_sizes[j - 1]
    data_transfer_latency = data[data_transfer_size][prev_cloud][cur_cloud][0]
    data_transfer_cost = data[data_transfer_size][prev_cloud][cur_cloud][1]
    cost += data_transfer_cost
    latency += data_transfer_latency
    search_list = dp[j - 1][prev_cloud][cur_cloud]
    return cost, latency, search_list


def clean_dp(dp, i):
    prv = sys.maxsize
    rm_keys = []
    for xd in dp[i]:
        if prv < dp[i][xd]:
            rm_keys.append(xd)
        else:
            prv = dp[i][xd]
    for k in rm_keys:
        del dp[i][k]


if __name__ == '__main__':
    solve(l,m,d,data)
