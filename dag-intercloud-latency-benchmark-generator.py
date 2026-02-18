import json
from statistics import median

#Az -> AWS
"""/Users/vaibhavjha/Documents/IISc/xfbench_multicloud/XFaaS/serwo/examples/static-fanout-comms/workflow-gen/70fc9eff-0c32-4456-8f0b-8d8f016daffb/exp1/logs/staticfanout_comms_azure_static_aws_dyndb_items.jsonl"""

#Aws -> Az
"""/Users/vaibhavjha/Documents/IISc/xfbench_multicloud/XFaaS/serwo/examples/static-fanout-comms/workflow-gen/baac0abc-f3d2-42db-9508-e79bd1c515b9/exp1/logs/staticfanout_comms_aws_static_aws_dyndb_items.jsonl"""

path_to_intercloud_benchmark = "/Users/vaibhavjha/Documents/IISc/xfbench_multicloud/XFaaS/serwo/examples/static-fanout-comms/workflow-gen/70fc9eff-0c32-4456-8f0b-8d8f016daffb/exp1/logs/staticfanout_comms_azure_static_aws_dyndb_items.jsonl"
# Load the data from the attached file
with open(path_to_intercloud_benchmark, 'r') as f:
    lines = f.readlines()

# Parse each JSON line and extract timing differences
differences = []

for line in lines:
    # Parse the JSON record
    record = json.loads(line)
    functions = record.get('functions', {})
    
    # Check if both node 1 and node 2 exist in the record
    if '1' in functions and '2' in functions:
        # Extract end_delta of node 1 and start_delta of node 2
        node1_end = functions['1']['end_delta']
        node2_start = functions['2']['start_delta']
        
        # Calculate the difference: start time of node 2 - end time of node 1
        diff = node2_start - node1_end
        differences.append(diff)

# Calculate the median of all differences
median_difference = median(differences)

print(f"Total data points analyzed: {len(differences)}")
print(f"Median difference (node 2 start - node 1 end): {median_difference} milliseconds")

# Optional: Show some additional statistics
print(f"Minimum difference: {min(differences)} ms")
print(f"Maximum difference: {max(differences)} ms")
print(f"Average difference: {sum(differences)/len(differences):.2f} ms")
