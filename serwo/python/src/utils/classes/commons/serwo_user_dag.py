import json
import networkx as nx
from collections import defaultdict
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP
import python.src.utils.classes.commons.serwo_benchmark_evaluator as serwo_benchmark_evaluator
class SerWOUserDag:
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
    
    def __get_nodeId(self, function_name):
        return f"SerWOFunc-{function_name}"

    # placeholder method for returning the networkx dag
    def get_dag(self) -> nx.DiGraph:
        return self.__dag

    def __create_egress_node(self, partition_point_id, new_node_params, forward_function_params):
        outG = self.__dag
        egressNodeId = new_node_params.get("NodeId")
        forwardFunctionId = None

        # add the new node
        # NOTE - the default memory requirement for the egress function is 128MB
        outG.add_node(  egressNodeId, 
                        NodeId=egressNodeId,
                        NodeName=new_node_params["NodeName"],
                        EntryPoint=new_node_params["EntryPoint"],
                        Path=new_node_params["Path"],
                        MemoryInMB=128
                    )
    
        # for u,v in list(outG.edges()):
        #     if u == partition_point_id:
        #         outG.add_edge(u, egressNodeId)
        #         outG.add_edge(egressNodeId, v)
        #         outG.remove_edge(u, v)

        out_degree_partition_point = outG.out_degree(partition_point_id)

        # remove all edges from the partition point to the successors
        successor_partition_point = list(outG.successors(partition_point_id))
        for successor in successor_partition_point:
            outG.remove_edge(partition_point_id, successor)
        outG.add_edge(partition_point_id, egressNodeId)

        if out_degree_partition_point > 1:
            forwardFunctionId = forward_function_params.get("NodeId")
            outG.add_node(
                forwardFunctionId,
                NodeId=forwardFunctionId,
                NodeName=forward_function_params["NodeName"],
                EntryPoint=forward_function_params["EntryPoint"],
                Path=forward_function_params["Path"],
                MemoryInMB=128
            )
            outG.add_edge(egressNodeId, forwardFunctionId)
            for successor in successor_partition_point:
                outG.add_edge(forwardFunctionId, successor)
        else:
            outG.add_edge(egressNodeId, successor_partition_point[0])

        self.__dag = outG
        return egressNodeId, forwardFunctionId
    
    def get_workflow_name(self):
        return self.__workflow_name



    def get_partition_points_after_user_pinning(self, partition_points, user_pinned_nodes, num_parts,user_pinned_csp):
        if len(user_pinned_nodes) == 0:
            return partition_points

        if num_parts==2:
            return self.handle_two_partitions(partition_points, user_pinned_nodes)
        else:
            return self.handle_three_partitions(partition_points, user_pinned_nodes)

    def handle_three_partitions(self, partition_points, user_pinned_nodes):
        return

    def handle_two_partitions(self, partition_points, user_pinned_nodes):
        u_graph = self.__dag
        fin_parts = []
        for partition_point in partition_points:
            left_partition, right_partition = get_partition_lists(partition_point, u_graph)
            part_id = is_partition_valid(left_partition, right_partition, user_pinned_nodes)
            if part_id !=-1:
                np = partition_point
                np['user_pinned_part_id'] = part_id
                fin_parts.append(np)
        return fin_parts



    def get_partition_points(self):
        # TODO[VK] - add the partition point logic
        uGraph = self.__dag

        top_sort = list(nx.topological_sort(uGraph))
        top_indices = dict()
        ind = 0
        for node in top_sort:
            top_indices[node] = ind
            ind += 1
        dp = dict()
        dp[top_sort[0]] = 0

        for i in range(1,len(top_sort)):
            in_edges = uGraph.in_edges(top_sort[i])
            in_degree = uGraph.in_degree(top_sort[i])
            if in_degree > 1:
                self.handle_joins(dp, i, in_edges, top_sort, uGraph)
            else:
                self.handle_intermediate_nodes(dp, i, in_edges, top_sort, uGraph)

        nodes = uGraph.nodes()

        partition_node_list = []
        for u in nodes:
            if dp[u] == 0:
                partition_node_list.append((top_indices[u],u))

        partition_node_list = sorted(partition_node_list)
        fin_partition_list_with_out_degree = []
        src_check = uGraph.out_degree(top_sort[0])
        fin_partition_list_with_out_degree.append((top_sort[0],src_check))
        for u,v in partition_node_list:
            out_degree = uGraph.out_degree(v)
            fin_partition_list_with_out_degree.append((v,out_degree))

        fin_list = []
        is_exists = dict()
        for u,out_degree in fin_partition_list_with_out_degree:
            in_deg = uGraph.in_degree(u)
            if u not in is_exists:
                is_exists[u] = 1
                fin_list.append(dict(node_id=u,out_degree=out_degree,in_degree=in_deg))

        sink = top_sort[len(top_sort)-1]
        if  sink not in is_exists:
            in_deg = uGraph.in_degree(sink)
            fin_list.append(dict(node_id=sink,out_degree=0,in_degree=in_deg))

        return fin_list
        return [PartitionPoint("func2", CSP.toCSP("AWS"), CSP.toCSP("Azure"))]

    def handle_intermediate_nodes(self, dp, i, in_edges, top_sort, uGraph):
        for u, v in in_edges:
            in_edge = u
        if uGraph.out_degree(in_edge) == 1:
            dp[top_sort[i]] = dp[in_edge]
        else:
            dp[top_sort[i]] = 1 + dp[in_edge]

    def handle_joins(self, dp, i, in_edges, top_sort, uGraph):
        out_val = 999
        for src, dest in in_edges:
            out_val = min(out_val, dp[src])

        # for j in range(0,i):
        #     src = top_sort[j]
        #     out_edges = uGraph.out_edges(src)
        #     for so, vo in out_edges:
        #         if vo not in dp and vo != top_sort[i]:
        #             if top_sort[i]=='11':
        #                 print(f'not vis?? {vo}')
        #             c += 1
        #             break

        dp[top_sort[i]] = out_val - 1



    def get_best_partition(self,partition_points,num_parts,dag_path,user_pinned_csp,user_pinned_nodes):

        return serwo_benchmark_evaluator.get_best_partition_point(u_graph = self.__dag,
                                                            partition_points=partition_points,
                                                            num_parts=num_parts,
                                                            dag_path= dag_path,
                                                            user_pinned_csp=user_pinned_csp,
                                                            user_pinned_nodes=user_pinned_nodes)



    def get_partitioned_graph(self, partition_point: PartitionPoint, new_node_params:dict, forward_function_params:dict):
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
        
        # partition the graph from source node -> partition point, partition point -> sink node
        paths_between_source_egress = nx.all_simple_paths(self.__dag,
                                                      source=source_nodeId,
                                                      target=egressNodeId)
        
        paths_between_egress_sink = nx.all_simple_paths(self.__dag,
                                                        source=egressNodeId,
                                                        target=sink_nodeId)

        # partition the graph based on nodes
        outG = self.get_dag()
        nodes_between_source_and_egress = {node for path in paths_between_source_egress for node in path}
        nodes_between_egress_and_sink = {node for path in paths_between_egress_sink for node in path}

        # remove the egress node from subgraph between egress and sink
        nodes_between_egress_and_sink.remove(egressNodeId)

        left_subgraph = outG.subgraph(nodes_between_source_and_egress)
        right_subgraph = outG.subgraph(nodes_between_egress_and_sink)
        
        print("Left subgraph edges")
        for u,v in list(left_subgraph.edges()):
           print(left_subgraph.nodes[u]['NodeName'], left_subgraph.nodes[v]['NodeName'])

        print("Right subgraph edges")
        for u,v in list(right_subgraph.edges()):
           print(right_subgraph.nodes[u]['NodeName'], right_subgraph.nodes[v]['NodeName'])

        return left_subgraph, right_subgraph

    
def set_diff(a,b):
    a =set(a)
    b=set(b)
    return list(a.difference(b))


def is_partition_valid(left_partition,right_partition,user_pinned_nodes):
    node_to_partition = dict()
    ## 0 means left partition, 1 means right partition
    for node in left_partition:
        node_to_partition[node] = 0
    for node in right_partition:
        node_to_partition[node] = 1

    distinct_user_pinned_nodes_part = set()

    for node in user_pinned_nodes:
        distinct_user_pinned_nodes_part.add(node_to_partition[node])

    part_id = -1

    if len(distinct_user_pinned_nodes_part)==1:
        for part in distinct_user_pinned_nodes_part:
            part_id = part
        return part_id
    return part_id

def get_partition_lists(partition_point, u_graph):
    top_sort = list(nx.topological_sort(u_graph))
    top_indices = dict()
    ind = 0
    for node in top_sort:
        top_indices[node] = ind
        ind += 1

    all_nodes = u_graph.nodes()
    temp_src = partition_point['node_id']
    dfs = nx.dfs_edges(u_graph, temp_src)

    df = dict()
    for u, v in dfs:
        if u == temp_src:
            df[v] = 1
        else:
            df[u] = 1
            df[v] = 1
    right_partition = sorted(df.keys())
    left_partition = set_diff(all_nodes, right_partition)
    right_partition_top_sort = []
    left_partition_top_sort = []
    for node in right_partition:
        right_partition_top_sort.append((top_indices[node],node))
    right_partition_top_sort = sorted(right_partition_top_sort)
    for node in left_partition:
        left_partition_top_sort.append((top_indices[node],node))
    left_partition_top_sort = sorted(left_partition_top_sort)

    left_partition = []
    right_partition = []
    for u,v in left_partition_top_sort:
        left_partition.append(v)
    for u,v in right_partition_top_sort:
        right_partition.append(v)

    return left_partition, right_partition