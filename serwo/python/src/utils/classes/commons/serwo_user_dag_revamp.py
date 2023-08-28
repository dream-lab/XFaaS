import os
import json
import uuid
import networkx as nx
import pathlib
from collections import defaultdict
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP
import python.src.utils.classes.commons.serwo_benchmark_evaluator as serwo_benchmark_evaluator

class DAGLoader:
    # private variables
    __dag_config_data = dict() # dag configuration (picked up from user file)
    __nodeIDMap = {} # map: nodeName -> nodeId (used internally)
    __dag = nx.DiGraph() # networkx directed graph
    __workflow_name = None

    # Constructor
    def __init__(self, user_config_path):
        # throw an exception if loading file has a problem
        try:
            with open(user_config_path, "r") as file:
                self.__dag_config_data = json.load(file)
            self.__workflow_name = self.__dag_config_data["WorkflowName"]
        except Exception as e:
            raise e
       
        # add the nodes in the networkx dag
        index = 1
        for node in self.__dag_config_data["Nodes"]:
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

    def get_dag(self) -> nx.DiGraph:
        return self.__dag
    
    def get_workflow_name(self):
        return self.__workflow_name

    def get_node_id_map(self):
        return self.__nodeIDMap
    
    def create_dag_description(self, dest: pathlib.Path, partition_point: PartitionPoint):
        if os.path.exists(dest):
            # iterate over all the nodes
            json_contents = dict()
            json_contents["WorkflowID"] = str(uuid.uuid4())
            json_contents["WorkflowName"] = self.__workflow_name +  partition_point.get_part_id()
            json_contents["CSP"] = partition_point.get_left_csp()
            json_contents["Region"] = partition_point.get_region()
            json_contents["Nodes"] = []
            json_contents["Edges"] = []
            for node, attributes in self.__dag.nodes(data=True):
                json_contents["Nodes"].append(
                    {
                        "NodeId": attributes["NodeId"],
                        "NodeName": attributes["NodeName"],
                        "Path": attributes["Path"],
                        "EntryPoint": attributes["EntryPoint"],
                        "CSP": attributes["CSP"],
                        "MemoryInMB": attributes["MemoryInMB"]
                    }
                )

                successors = self.__dag.successors(node)
                nodename = attributes["NodeName"]
                edge_dict = { nodename: [] }
                for succ in successors:
                    edge_dict[nodename].append(self.__dag.nodes[succ]["NodeName"])

                json_contents["Edges"].append(edge_dict)

            # Write the dag description to the destination
            filename = f"dag-description\
                -{partition_point.get_left_csp()}\
                -{partition_point.get_part_id()}"
            
            with open(dest / filename, "w") as outfile:
                json.dump(json_contents, indent=4)


    # def get_partitioned_graph(self, partition_point: PartitionPoint, new_node_params:dict, forward_function_params:dict):
    #     # this works on the assumption that the function names are unique
    #     partition_point_nodeName = partition_point.get_partition_point_name()
    #     partition_point_nodeId = self.__nodeIDMap[partition_point_nodeName]
    #     # get source and sink nodes for the entire user dag
    #     source_nodeId = [node for node in self.__dag.nodes if self.__dag.in_degree(node) == 0][0]
    #     sink_nodeId = [node for node in self.__dag.nodes if self.__dag.out_degree(node) == 0][0]

    #     print("Inside serwo_user_dag::get_partitioned_graph")
    #     print("Source id - ", self.__dag.nodes[source_nodeId]["NodeName"])
    #     print("Sink id - ", self.__dag.nodes[sink_nodeId]["NodeName"])

    #     # modify the user dag by adding the egress node (this changes the user dag)
    #     egressNodeId, _ = self.__create_egress_node(
    #                             partition_point_id=partition_point_nodeId,
    #                             new_node_params=new_node_params,
    #                             forward_function_params=forward_function_params
    #                         )
        
    #     # partition the graph from source node -> partition point, partition point -> sink node
    #     paths_between_source_egress = nx.all_simple_paths(self.__dag,
    #                                                   source=source_nodeId,
    #                                                   target=egressNodeId)
        
    #     paths_between_egress_sink = nx.all_simple_paths(self.__dag,
    #                                                     source=egressNodeId,
    #                                                     target=sink_nodeId)

    #     # partition the graph based on nodes
    #     outG = self.get_dag()
    #     nodes_between_source_and_egress = {node for path in paths_between_source_egress for node in path}
    #     nodes_between_egress_and_sink = {node for path in paths_between_egress_sink for node in path}

    #     # remove the egress node from subgraph between egress and sink
    #     nodes_between_egress_and_sink.remove(egressNodeId)

    #     left_subgraph = outG.subgraph(nodes_between_source_and_egress)
    #     right_subgraph = outG.subgraph(nodes_between_egress_and_sink)
        
    #     print("Left subgraph edges")
    #     for u,v in list(left_subgraph.edges()):
    #        print(left_subgraph.nodes[u]['NodeName'], left_subgraph.nodes[v]['NodeName'])

    #     print("Right subgraph edges")
    #     for u,v in list(right_subgraph.edges()):
    #        print(right_subgraph.nodes[u]['NodeName'], right_subgraph.nodes[v]['NodeName'])

    #     return left_subgraph, right_subgraph

    # def get_partitioned_graph_v2(self, partition_point: PartitionPoint, new_node_params:dict, forward_function_params:dict):
        # this works on the assumption that the function names are unique
        partition_point_nodeName = partition_point.get_partition_point_name()
        partition_point_nodeId = self.__nodeIDMap[partition_point_nodeName]
        # get source and sink nodes for the entire user dag
        source_nodeId = [node for node in self.__dag.nodes if self.__dag.in_degree(node) == 0][0]
        sink_nodeId = [node for node in self.__dag.nodes if self.__dag.out_degree(node) == 0][0]

        print("Inside serwo_user_dag::get_partitioned_graph")
        print("Source id - ", self.__dag.nodes[source_nodeId]["NodeName"])
        print("Sink id - ", self.__dag.nodes[sink_nodeId]["NodeName"])

        # modify the user dag by adding the egress node (this changes the user dag)
        egressNodeId, _ = self.__create_egress_node(
                                partition_point_id=partition_point_nodeId,
                                new_node_params=new_node_params,
                                forward_function_params=forward_function_params
                            )
        
        # # partition the graph from source node -> partition point, partition point -> sink node
        # paths_between_source_egress = nx.all_simple_paths(self.__dag,
        #                                               source=source_nodeId,
        #                                               target=egressNodeId)
        
        # paths_between_egress_sink = nx.all_simple_paths(self.__dag,
        #                                                 source=egressNodeId,
        #                                                 target=sink_nodeId)

        # partition the graph based on nodes
        # outG = self.get_dag()
        # nodes_between_source_and_egress = {node for path in paths_between_source_egress for node in path}
        # nodes_between_egress_and_sink = {node for path in paths_between_egress_sink for node in path}

        # remove the egress node from subgraph between egress and sink
        # nodes_between_egress_and_sink.remove(egressNodeId)

        # left_subgraph = outG.subgraph(nodes_between_source_and_egress)
        # right_subgraph = outG.subgraph(nodes_between_egress_and_sink)
        
        print("Subgraph edges")
        for u,v in list(self.__dag.edges()):
           print(self.__dag.nodes[u]['NodeName'], self.__dag.nodes[v]['NodeName'])

        return self.__dag