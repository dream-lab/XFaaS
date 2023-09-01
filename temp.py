import json
import networkx as nx

class DagLoader:
    # private variables
    __dag_config_data = dict() # dag configuration (picked up from user file)
    __nodeIDMap = {} # map: nodeName -> nodeId (used internally)
    __dag = nx.DiGraph() # networkx directed graph
    __workflow_name = None

    # Constructor
    def __init__(self, user_config_path):
        # throw an exception if loading file has a problem
        try:
            self.__dag_config_data = self.__load_user_spec(user_config_path)
            self.__workflow_name = self.__dag_config_data["WorkflowName"]
        except Exception as e:
            raise e
       
        # build the networkx DAG
        # add nodes in the dag and populate the functions dict
        index = 1
        # add edges in the dag
        # for edge in self.__dag_config_data["Edges"]:
        #     for key in edge:
        #         for val in edge[key]:
        #             self.__dag.add_edge(self.__nodeIDMap[key], self.__nodeIDMap[val])

        for node in self.__dag_config_data["Nodes"]:
            # nodeID = self.__get_nodeId(function_name=node["NodeName"]) + f"-{str(index)}"
            nodeID = node["NodeId"]
            self.__nodeIDMap[node["NodeName"]] = nodeID
            self.__dag.add_node(nodeID,
                                NodeId=nodeID,
                                NodeName=node["NodeName"], 
                                Path=node["Path"],
                                EntryPoint=node["EntryPoint"],
                                MemoryInMB=node["MemoryInMB"])
            index += 1

        # add edges in the dag
        for edge in self.__dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    self.__dag.add_edge(self.__nodeIDMap[key], self.__nodeIDMap[val])

    # private methods
    def __load_user_spec(self, user_config_path):
        with open(user_config_path, "r") as user_dag_spec:
            dag_data = json.load(user_dag_spec)
        return dag_data

    def get_dag(self):
        return self.__dag

dagfilepath = "serwo/scratch/dag.json"
xfaas_dag = DagLoader(dagfilepath).get_dag()
nodes = [node for node in xfaas_dag.nodes]
edges = [edge for edge in xfaas_dag.edges]
print(nodes)
print(edges)

for u,v in edges:
    print(u,v)