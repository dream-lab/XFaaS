import json
import statistics
import argparse

def process(aws, azure, dag):
    nodes = {}
    edges = {}

    for node in dag['Nodes']:
        id = node['NodeId']
        nodes[id] = {
            "0": calc_nodes(aws, id),  
            "1": calc_nodes(azure, id)  
        }
    
    for edge in dag['Edges']:
        for k, v in edge.items():
            source_id = get_id(dag, k)
            for target_node in v:
                target_id = get_id(dag, target_node)
                
                if source_id != target_id:
                    if source_id not in edges:
                        edges[source_id] = {}

                    edges[source_id][target_id] = {
                        "DataTransferSize": 1,  
                        "Latencies": [
                            [calc_edges(aws, source_id, target_id), 0],  #[[aws->aws, aws->az]]
                            [0, calc_edges(azure, source_id, target_id)]  # [[az->aws], [az->az]]
                        ]
                    }

    return {"NodeBenchmarks": nodes, "EdgeBenchmarks": edges}

def calc_nodes(data, id):
    latencies = []
    for entry in data:
        if id in entry['functions']:
            metadata = entry['functions'][id]
            latencies.append(metadata['end_delta'] - metadata['start_delta'])
    
    median = statistics.median(latencies) if latencies else 0
    return {
        "Latency": median,
        "Cost": 0  
    }

def calc_edges(data, source_id, target_id):
    latencies = []
    
    for entry in data:
        if source_id in entry['functions'] and target_id in entry['functions']:
            source = entry['functions'][source_id]
            target = entry['functions'][target_id]
            
            
            latency = target['start_delta'] - source['end_delta']
            latencies.append(latency)

    median = statistics.median(latencies) if latencies else 0
    return median

def get_id(dag, node_name):
    for node in dag['Nodes']:
        if node['NodeName'] == node_name:
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

    aws = process_jsonl(args.aws)
    
    azure = process_jsonl(args.azure)
    
    with open(args.dag, 'r') as file:
        dag = json.load(file)
    
    benchmarks = process(aws, azure, dag)

    with open(args.output, 'w') as file:
        json.dump(benchmarks, file, indent=2)

    print(f"data saved - {args.output}")

if __name__ == "__main__":
    main()