import json
import pandas as pd
import requests
import networkx as nx
import os



cost_factor  = 0.000016

def read_dictionary_from_file(file_path):
    with open(file_path, 'r') as file:
        # Read the content of the file
        content = file.read()
        # Evaluate the content as a dictionary
        dictionary_data = json.loads(content)
        return dictionary_data
    
# path="output_obj.txt"
def creating_outobject(url):
    # data = read_dictionary_from_file(path)
    response_API = requests.get(url)
    data = response_API.text
    # Parse the data into JSON format
    data = json.loads(data)
    out_obj=json.loads(data['output'])
    
    out_obj=out_obj['_metadata']['functions']
    instanceId=data['instanceId']
    out_obj=json.loads(data['output'])
    out_obj=out_obj['_metadata']['functions']
    out=[]
    for fn in out_obj:
        # temp={}
        for fn_name in fn:
            obj=fn[fn_name]
            # print(obj)
            # print(type(obj['start_delta']))
            start_delta=int(obj['start_delta'])
            end_delta = obj['end_delta']
            mem_before=obj['mem_before']
            mem_after = obj['mem_after']
            net_time=abs(end_delta-start_delta)
            net_mem=abs(mem_after-mem_before)
            temp={
                'NodeId':fn_name,
                'start_delta':start_delta,
                'end_delta':end_delta,
                'mem_before':mem_before,
                'mem_after':mem_after,
                'net_time':net_time,
                'net_mem':net_mem,
                'cost':cost_factor*(net_time/1000)*(net_mem/1073741824)
            }
            out.append(temp)
    return out,instanceId,


def custom_dfs(graph, node, dataframe,result_list, node_to_nodeid,path="",ntime=0,cost=0):

    
    neighbors = list(graph.neighbors(node))
    path+=node+'->'
    nodeId=node_to_nodeid[node]
    # print(nodeId)
    # print(dataframe)
    node_data=dataframe.loc[nodeId].to_dict()
    # print(node_data)
    ntime+= node_data['net_time']
    cost+= node_data['cost']
    paths_with_weights = []
    for neighbor in neighbors:
        custom_dfs(graph, neighbor, dataframe, result_list,node_to_nodeid,path, ntime,cost)

    if len(neighbors)==0:
        result_list.append((path, (ntime,cost)))
        # print("We are in last node")
        return [(path, ntime,cost)]
    
    return paths_with_weights

class result_analysis:
    def data_analysis(url_list):
        for url,wf_path in url_list:
            out,instance_id=creating_outobject(url)
            df = pd.DataFrame.from_dict(out).set_index('NodeId')
            df_grouped = df.groupby('NodeId').agg({
    'start_delta': 'min',
    'end_delta': 'max',
    'mem_before': 'min',
    'mem_after': 'max',
    'net_time': 'sum',
    'net_mem': 'sum',
    'cost': 'sum'
})
            print(df)
            df=df_grouped
            print(df_grouped)
            # dag_path=wf_path+'/'
            dag_path=os.path.join(wf_path,'dag.json')
            with open(dag_path, 'r') as file:
                data = json.load(file)

            # Create a directed graph
            node_to_nodeid={}
            nodeid_to_node={}
            graph = nx.DiGraph()

            # Add nodes to the graph
            for node in data['Nodes']:
                graph.add_node(node['NodeName'])
                node_to_nodeid[node['NodeName']]=node['NodeId']
                nodeid_to_node[node["NodeId"]]=node['NodeName']

            # Add edges to the graph
            for edge in data['Edges']:
                for source, targets in edge.items():
                    for target in targets:
                        graph.add_edge(source, target)  # Assuming each edge has only one target

            # Print the graph nodes and edges
            # print("Nodes:", graph.nodes(data=False))
            # print("Edges:", graph.edges())
            # print("NodeMap:",node_to_nodeid)
            workflow_name=data['WorkflowName']
            result_list=[]
            custom_dfs(graph, nodeid_to_node['1'], df,result_list,node_to_nodeid)

            max_time=max_cost=0
            critical_path=""
            for (path,(time,cost)) in result_list:
                if time>max_time:
                    (critical_path,(max_time,max_cost))=(path,(time,cost))
            max_time=max_time/1000
            start_node_data=df.loc['1'].to_dict()
            end_node_data=df.loc['253'].to_dict()
            start_timestamp=start_node_data['start_delta']
            end_timestamp=end_node_data['end_delta']
            total_workflow_exec_time=(end_timestamp-start_timestamp)/1000
            waiting_time=(total_workflow_exec_time-max_time)
            total_cost=df['cost'].sum()
            print('For workflow:\t', workflow_name,'\n\t InstanceId:\t',instance_id ,'\n\t\tTotal workflow execution time:\t',total_workflow_exec_time , 'seconds\n\t\tTotal funtion exec time(as per critical path):\t',max_time,'seconds\n\t\tTotal waiting time(as per critical path):\t',waiting_time,'seconds\n\t\tCritical Path:\t',critical_path,'\b\b\n\t\tTotal Cost: \t$ ',total_cost)
            results={
                "WorkFlowName":workflow_name,
                "InstanceId":instance_id,
                "Total_workflow_exec_time":total_workflow_exec_time,
                "TotalFuntionExecutionTime":max_time,
                "Total_waiting_time":waiting_time,
                "CriticalPath":critical_path,
                "TotalCost":total_cost,
                "PathResults": []
            }
            

            # print(result_list)
            print("\n\nFor each path total execution time and total waiting time")
            for (path,(time,cost)) in result_list:
                time=time/1000
                out={"Path":path,
                     "Total_exec_time":time,
                     "Total waiting time":total_workflow_exec_time-time}
                print("Path:",path,'\tTotal exec time:',time,'sec\tTotal waiting time:',total_workflow_exec_time-time,"sec")
                results["PathResults"].append(out)

            result_dir = wf_path + '/Results'
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)
            json_file_path = os.path.join(result_dir, f'{instance_id}.json')
            text_file_path = os.path.join(result_dir, f'{instance_id}.txt')
            with open(json_file_path, 'w') as json_file:
                json.dump(results, json_file, indent=4)

            print(f"Results saved to {json_file_path}")

            with open(text_file_path, 'w') as f:
                f.write('For workflow:\t' + workflow_name + '\n\t InstanceId:\t' + instance_id + '\n\t\tTotal workflow execution time:\t' + str(total_workflow_exec_time) + ' seconds\n\t\tTotal funtion exec time(as per critical path):\t' + str(max_time) + ' seconds\n\t\tTotal waiting time(as per critical path):\t' + str(waiting_time) + ' seconds\n\t\tCritical Path:\t' + critical_path + '\b\b\n\t\tTotal Cost: \t$ ' + str(total_cost) + '\n\n\nFor each path total execution time and total waiting time\n')
                for (path, (time, cost)) in result_list:
                    time = time / 1000
                    f.write("Path:" + str(path) + '\tTotal exec time:' + str(time) + ' sec\tTotal waiting time:' + str(total_workflow_exec_time - time) + " sec\n")

            # print('\n\n')
            # output_file = 'output.xlsx'
            # sheet_name = instance_id[0:30]
            # if not os.path.isfile(output_file):
            # # Create a new workbook and save it if the file does not exist
            #     wb = Workbook()
            #     wb.save(output_file)

            
            # with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:
            #     # Check if the sheet name already exists in the workbook
            #     if sheet_name in writer.book.sheetnames:
            #         # Get the sheet by name and remove it
            #         std = writer.book[sheet_name]
            #         writer.book.remove(std)
            #     # Write the DataFrame to the sheet
            #     df.to_excel(writer, sheet_name=sheet_name, index=True)

        print("Results stored sucessfully.")


