import json

with open("/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAz/build/workflow/resources/graph-azure-dynamic-medium-alibaba/graph_azure_alibaba_medium_dyndb_items.jsonl", "r") as f:
    lines = f.readlines()
    items = [json.loads(line) for line in lines]
    sorted_items = sorted(items,key=lambda x: x["client_request_time_ms"])

    for idx, item in enumerate(sorted_items):
        print(idx, (int(item["invocation_start_time_ms"]) - int(item["client_request_time_ms"]))/(1000*60))
