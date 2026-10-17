from collections import defaultdict
from collections import OrderedDict
import sys


def fuse(start, end, latencies, memories, prev_cloud, cur_cloud):
    tot_lat = 0
    max_mem = -1
    for i in range(start, end + 1):
        tot_lat += latencies[cur_cloud][i - 1]
        max_mem = max(max_mem, memories[i - 1])
    tot_cost = tot_lat * max_mem

    return tot_cost, tot_lat


def solve(latencies, memories, data_transfer_sizes, data):
    dp = defaultdict(dict)
    n = len(latencies[0])
    k = len(latencies)
    fill_base_case(dp, n, k, latencies, memories)

    for i in range(2, n + 1):
        for prev_cloud in range(0, k):
            for cur_cloud in range(0, k):
                for j in range(i, 0, -1):
                    cost, latency, search_list = init_operators(
                        data, data_transfer_sizes, dp, i, j, latencies,
                        memories, prev_cloud, cur_cloud)

                    populate_dp(cost, dp, i, latency, search_list,
                                prev_cloud, cur_cloud, j)

                clean_dp(dp, i, prev_cloud, cur_cloud)

    return dp


def fill_base_case(dp, n, k, latencies, memories):
    for i in range(n + 1):
        dp[i] = {}
        for j in range(k):
            dp[i][j] = {}
            for L in range(k):
                dp[i][j][L] = None
                if i == 0:
                    dp[i][j][L] = {0: (0, 0, 0)}

    for i in range(0, k):
        for j in range(0, k):
            base_cost = memories[0] * latencies[j][0]
            dp[1][i][j] = {base_cost: (latencies[j][0], 0, base_cost)}


def populate_dp(cost, dp, i, latency, search_list, prev_cloud, cur_cloud, j):
    for key in search_list:
        new_cost = key + cost
        new_latency = search_list[key][0] + latency

        if dp[i][prev_cloud][cur_cloud] is not None:
            if new_cost in dp[i][prev_cloud][cur_cloud]:
                if new_latency < dp[i][prev_cloud][cur_cloud][new_cost][0]:
                    dp[i][prev_cloud][cur_cloud][new_cost] = (
                        new_latency, j - 1, cost)
            else:
                dp[i][prev_cloud][cur_cloud][new_cost] = (
                    new_latency, j - 1, cost)
        else:
            dp[i][prev_cloud][cur_cloud] = dict()
            dp[i][prev_cloud][cur_cloud][new_cost] = (
                new_latency, j - 1, cost)
    dp[i][prev_cloud][cur_cloud] = dict(
        OrderedDict(sorted(dp[i][prev_cloud][cur_cloud].items())))


def init_operators(data, data_transfer_sizes, dp, i, j, latencies, memories,
                   prev_cloud, cur_cloud):
    cost, latency = fuse(j, i, latencies, memories, prev_cloud, cur_cloud)
    data_transfer_size = data_transfer_sizes[j - 1]
    data_transfer_latency = data[data_transfer_size][prev_cloud][cur_cloud][0]
    data_transfer_cost = data[data_transfer_size][prev_cloud][cur_cloud][1]
    cost += data_transfer_cost
    latency += data_transfer_latency
    search_list = dp[j - 1][prev_cloud][cur_cloud]
    return cost, latency, search_list


def clean_dp(dp, i, prev_cloud, cur_cloud):
    prv = sys.maxsize
    rm_keys = []
    for xd in dp[i][prev_cloud][cur_cloud]:
        if prv < dp[i][prev_cloud][cur_cloud][xd][0]:
            rm_keys.append(xd)
        else:
            prv = dp[i][prev_cloud][cur_cloud][xd][0]
    for k in rm_keys:
        del dp[i][prev_cloud][cur_cloud][k]


def translate(dp, target_cost):
    n = len(dp) - 1
    k = len(dp[0])
    start = n
    verdict = []
    temp_target_cost = target_cost
    while start != 0:
        candidates = []
        for i in range(0, k):
            for j in range(0, k):
                if dp[start][i][j] is None:
                    continue
                for cst in dp[start][i][j]:
                    latency, index, delta_cost = dp[start][i][j][cst]
                    if cst <= temp_target_cost:
                        candidates.append(
                            (latency, cst, index, delta_cost, i, j))

        candidates = sorted(candidates)
        if len(candidates) == 0:
            raise ValueError(
                'ERROR: THE GIVEN COST IS NOT SUFFICIENT FOR FUSION+PARTITION DP')
        to_pick = candidates[0]
        temp_target_cost -= to_pick[3]
        old_start = start
        start = to_pick[2]
        cloud_id = to_pick[-2]
        if old_start == n:
            verdict.append((to_pick[-1], start, old_start))
        else:
            verdict.append((cloud_id, start, old_start))

    return list(reversed(verdict))


def _default_transfer_table(k, data_transfer_sizes, data_transfers_benchmark):
    """Build size -> prev_cloud -> cur_cloud -> (latency, cost) table for DP."""
    data = defaultdict(lambda: defaultdict(dict))
    unique_sizes = set(data_transfer_sizes)
    unique_sizes.add(0)
    for size in unique_sizes:
        for prev_cloud in range(k):
            for cur_cloud in range(k):
                # Prefer inter-cloud matrix when available; else zero same-cloud.
                if (data_transfers_benchmark is not None
                        and prev_cloud < len(data_transfers_benchmark)
                        and cur_cloud < len(data_transfers_benchmark[prev_cloud])):
                    latency = data_transfers_benchmark[prev_cloud][cur_cloud]
                else:
                    latency = 0 if prev_cloud == cur_cloud else 1
                cost = 0 if prev_cloud == cur_cloud else 1
                data[size][prev_cloud][cur_cloud] = (latency, cost)
    return data


def get_optimal_partitions(latencies_benchmark, memories, data_transfer_sizes,
                           data_transfers_benchmark=None, target_cost=None,
                           transfer_data=None):
    """
    Combined fusion + partition DP.

    Returns:
        verdict: List[(cloud_id, start_idx, end_idx)]
                 each segment covers 1-based DP indices (start, end]
                 i.e. 0-based node indices start .. end-1
        min_cost_used: cost budget that was feasible
    """
    k = len(latencies_benchmark)
    if transfer_data is None:
        transfer_data = _default_transfer_table(
            k, data_transfer_sizes, data_transfers_benchmark)

    dp = solve(latencies_benchmark, memories,
               data_transfer_sizes, transfer_data)

    if target_cost is None:
        # No user_budget from config: pick min feasible terminal cost.
        n = len(latencies_benchmark[0])
        candidates = []
        for i in range(k):
            for j in range(k):
                if dp[n][i][j] is None:
                    continue
                for cst in dp[n][i][j]:
                    candidates.append(cst)
        if not candidates:
            raise ValueError('FUSION+PARTITION DP produced no feasible solution')
        target_cost = min(candidates)
        print(f'No user_budget provided; using min feasible DP cost={target_cost}')
    else:
        print(f'Using user_budget as target_cost={target_cost}')

    verdict = translate(dp, target_cost)
    return verdict, target_cost


if __name__ == '__main__':
    c = int(sys.argv[1])
    l = [[32, 14, 1, 1, 1], [30, 1, 1, 1, 1]]
    m = [3, 1, 2, 1, 1]
    d = [0, 28, 25, 26, 27]

    data = defaultdict(lambda: defaultdict(dict))
    for size in [0, 25, 26, 27, 28]:
        for pc in (0, 1):
            for cc in (0, 1):
                data[size][pc][cc] = (1, 1)
    data[0][0][0] = (0, 0)
    data[25][0][0] = (5, 2)
    data[26][0][0] = (1, 4)
    data[27][0][0] = (7, 2)
    data[28][0][0] = (1, 1)
    data[0][0][1] = (0, 0)
    data[25][0][1] = (5, 2)
    data[26][0][1] = (1, 4)
    data[27][0][1] = (7, 2)
    data[28][0][1] = (1, 1)
    data[0][1][0] = (0, 0)
    data[25][1][0] = (5, 2)
    data[26][1][0] = (1, 4)
    data[27][1][0] = (7, 2)
    data[28][1][0] = (1, 1)
    data[0][1][1] = (0, 0)
    data[25][1][1] = (5, 2)
    data[26][1][1] = (1, 4)
    data[27][1][1] = (7, 2)
    data[28][1][1] = (1, 1)

    verdict, cost = get_optimal_partitions(
        l, m, d, transfer_data=data, target_cost=c)
    print('::' * 80)
    print(verdict, cost)
