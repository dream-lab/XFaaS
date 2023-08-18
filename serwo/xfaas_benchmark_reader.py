import json

MULTIPLIER = 100


def get_multiplied(node_bm):
    for node in node_bm:
        for csp in node_bm[node]:
            new_lat = MULTIPLIER * node_bm[node][csp]["Latency"]
            node_bm[node][csp]["Latency"] = new_lat
    return node_bm


def azure_inter_function_edge_latency_model(v, rps):
    x = 2 * v * rps
    y = 0.06 * x + 0.418
    return 1000 * y


def get_user_dag_benchmark_values(dag_path):
    f = open(dag_path, "r")
    bench_mark_json = json.loads(f.read())
    bench_mark = dict()

    bench_mark["node_benchmarks"] = get_multiplied(bench_mark_json["NodeBenchmarks"])
    bench_mark["edge_benchmarks"] = dict()
    for node in bench_mark_json["EdgeBenchmarks"]:
        for neighbors in bench_mark_json["EdgeBenchmarks"][node]:
            for neighbor in neighbors:
                pair = (node, neighbor)
                bench_mark["edge_benchmarks"][pair] = dict()
                bench_mark["edge_benchmarks"][pair]["data_transfer_size"] = neighbors[
                    neighbor
                ]["DataTransferSize"]
                for key in neighbors[neighbor]["Latencies"]:
                    for latency_key in key:
                        if latency_key == "Azure":
                            ## TODO: decouple modelling part from this piece of code
                            bench_mark["edge_benchmarks"][pair][
                                latency_key
                            ] = azure_inter_function_edge_latency_model(
                                len(bench_mark["node_benchmarks"]), 1
                            )
                        else:
                            bench_mark["edge_benchmarks"][pair][latency_key] = key[
                                latency_key
                            ]
    return bench_mark
