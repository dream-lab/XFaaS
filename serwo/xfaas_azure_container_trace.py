import sys
import json
file_path = sys.argv[1]

#open a jsonl file

##convert below to a function
# for each line in the file

def get_azure_containers(file_path):
    god_dict = {}
    ans = []
    with open(file_path) as f:
        lines = f.readlines()
    for line in lines:
        js = json.loads(line)
        functions = js['functions']
        workflow_start_time = js['invocation_start_time_ms']
        for function in functions:
            if "cid"  in functions[function]:
                cid = functions[function]['cid']
                function_start_delta = functions[function]['start_delta']
                function_start_time = int(workflow_start_time) + function_start_delta
                if cid == '':
                    continue
                if cid not in god_dict:
                    god_dict[cid] = []
                    god_dict[cid].append(function_start_time)
                else:
                    god_dict[cid].append(function_start_time)
    for cid in god_dict:
        god_dict[cid].sort()
        ans.append(god_dict[cid][0])
    return ans

    


if __name__ == '__main__':
    ans = get_azure_containers(file_path)
    print(ans)