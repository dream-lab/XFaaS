import json
import statistics
import argparse


def process(aws, azure, dag):
    nodes = {}
    edges = {}

    for node in dag['Nodes']:
        nid = node['NodeId']
        nodes[nid] = {
            "0": calc_nodes(aws, nid),   # AWS
            "1": calc_nodes(azure, nid)  # Azure
        }
    
    for edge in dag['Edges']:
        for k, v in edge.items():
            source_id = get_id(dag, k)
            for target_node in v:
                target_id = get_id(dag, target_node)
                if source_id is None or target_id is None:
                    continue
                if source_id == target_id:
                    continue

                if source_id not in edges:
                    edges[source_id] = {}

                # Latencies: keep existing per-cloud diagonals (placeholders for cross-cloud as in original)
                aws_lat = calc_edges(aws, source_id, target_id)
                az_lat = calc_edges(azure, source_id, target_id)

                # Data transfer sizes (bytes): combine AWS+Azure runs and take median of per-invocation max(out,in)
                aws_pairs = transfer_pairs(aws, source_id, target_id)   # list of per-invocation sizes
                az_pairs  = transfer_pairs(azure, source_id, target_id)
                combined_pairs = aws_pairs + az_pairs
                data_transfer_size = statistics.median(combined_pairs) if combined_pairs else 0

                edges[source_id][target_id] = {
                    "DataTransferSize": data_transfer_size,  # bytes (median across AWS+Azure runs)
                    "Latencies": [
                        [aws_lat, 0],  # [AWS->AWS, AWS->Azure] (cross left as in original)
                        [0, az_lat]    # [Azure->AWS, Azure->Azure]
                    ]
                }

    return {"NodeBenchmarks": nodes, "EdgeBenchmarks": edges}


def calc_nodes(data, nid):
    latencies = []
    for entry in data:
        funcs = entry.get('functions', {})
        if nid in funcs:
            meta = funcs[nid]
            lat = meta.get('end_delta', 0) - meta.get('start_delta', 0)
            latencies.append(lat)
    median = statistics.median(latencies) if latencies else 0
    return {"Latency": median, "Cost": 0}


def calc_edges(data, source_id, target_id):
    latencies = []
    for entry in data:
        funcs = entry.get('functions', {})
        if source_id in funcs and target_id in funcs:
            s = funcs[source_id]
            t = funcs[target_id]
            latency = t.get('start_delta', 0) - s.get('end_delta', 0)
            latencies.append(latency)
    return statistics.median(latencies) if latencies else 0


def transfer_pairs(data, source_id, target_id):
    """
    Returns a list of per-invocation transfer sizes (bytes) for source->target,
    using max(out_payload_bytes, in_payload_bytes) to avoid undercounting.
    """
    sizes = []
    for entry in data:
        funcs = entry.get('functions', {})
        if source_id in funcs and target_id in funcs:
            s = funcs[source_id]
            t = funcs[target_id]
            out_b = s.get('out_payload_bytes', 0) or 0
            in_b  = t.get('in_payload_bytes', 0) or 0
            sizes.append(max(out_b, in_b))
    return sizes


def get_id(dag, node_name):
    for node in dag['Nodes']:
        if node['NodeName'] == node_name or node['NodeId'] == node_name:
            return node['NodeId']
    return None


def process_jsonl(file_path):
    with open(file_path, 'r') as file:
        return [json.loads(line) for line in file]


def main():
    parser = argparse.ArgumentParser(description='dag benchmark')
    parser.add_argument('--aws', type=str, help='aws absolute path')
    parser.add_argument('--azure', type=str, help='azure absolute path')
    parser.add_argument('--dag', type=str, help='dag absolute path')
    parser.add_argument('--output', type=str, help='output file name', default="dag-benchmark.json")

    args = parser.parse_args()

    aws = process_jsonl(args.aws) if args.aws else []
    azure = process_jsonl(args.azure) if args.azure else []
    with open(args.dag, 'r') as file:
        dag = json.load(file)
    
    benchmarks = process(aws, azure, dag)

    with open(args.output, 'w') as file:
        json.dump(benchmarks, file, indent=2)

    print(f"data saved - {args.output}")


if __name__ == "__main__":
    main()

