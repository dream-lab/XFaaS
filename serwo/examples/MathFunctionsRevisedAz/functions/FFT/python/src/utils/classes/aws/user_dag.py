import json
import networkx as nx
import aws_sfn_builder as AWSSfnBuilder
from python.src.utils.classes.aws.function import Function
from collections import defaultdict


class UserDag:
    # private variables
    __dag_config_data = dict()  # dag configuration (picked up from user file)
    __nodeIDMap = (
        {}
    )  # map: nodeName -> nodeId (used internally) [NOTE [TK] - This map is changed from nodeName -> NodeId to UserGivenNodeId -> our internal nodeID ]
    __dag = nx.DiGraph()  # networkx directed graph
    __functions = {}  # map: functionName -> functionObject

    # Constructor
    def __init__(self, user_config_path):
        # throw an exception if loading file has a problem
        try:
            self.__dag_config_data = self.__load_user_spec(user_config_path)
        except Exception as e:
            raise e

        # build the networkx DAG
        # add nodes in the dag and populate the functions dict
        index = 1
        for node in self.__dag_config_data["Nodes"]:
            nodeID = "n" + str(index)
            self.__nodeIDMap[node["NodeName"]] = nodeID
            self.__nodeIDMap[node["NodeId"]] = nodeID
            self.__functions[node["NodeName"]] = Function(
                node["NodeId"],
                node["NodeName"],
                node["Path"],
                node["EntryPoint"],
                node["MemoryInMB"],
            )
            self.__dag.add_node(
                nodeID,
                NodeName=node["NodeName"],
                Path=node["Path"],
                EntryPoint=node["EntryPoint"],
                CSP=node.get("CSP"),
                MemoryInMB=node["MemoryInMB"],
                machine_list=[self._get_state(node["NodeName"])],
            )
            index += 1

        # add edges in the dag
        for edge in self.__dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    self.__dag.add_edge(self.__nodeIDMap[key], self.__nodeIDMap[val])

    def _get_state(self, nodename):
        state = AWSSfnBuilder.State.parse(
            {
                "Type": "Task",
                "Name": self.__functions[nodename].get_name(),
                "Resource": "${" + self.__functions[nodename].get_arn() + "}",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 15,  # TODO - populate these functions from networkx nodes
                        "MaxAttempts": 5,
                        "BackoffRate": 1.5,
                    }
                ],
            }
        )
        return state

    # private methods
    def __load_user_spec(self, user_config_path):
        with open(user_config_path, "r") as user_dag_spec:
            dag_data = json.load(user_dag_spec)
        return dag_data

    def _merge_linear_nodes(
        self, workflow_dag: nx.DiGraph, node_list: list
    ) -> nx.DiGraph:
        # Replaced nodeId -> userFnName
        if node_list == []:
            return workflow_dag

        outG = workflow_dag

        new_node_machine_list = []

        for node in node_list:
            new_node_machine_list.extend(outG.nodes[node]["machine_list"])

        newNodeId = "n" + str(node_list)
        outG.add_node(
            newNodeId, machine_list=new_node_machine_list
        )  # Add the 'merged' node

        for u, v in list(outG.edges()):
            if v == node_list[0]:
                # add edge from u -> new node id
                outG.add_edge(u, newNodeId)
            if u == node_list[len(node_list) - 1]:
                outG.add_edge(newNodeId, v)

        for n in node_list:  # remove the individual nodes
            outG.remove_node(n)

        return outG

    def _merge_parallel_nodes(
        self, workflow_dag: nx.DiGraph, node_list: list
    ) -> nx.DiGraph:
        # write code here to merge the parallel nodes
        # Replaced nodeId -> userFnName
        if node_list == []:
            return workflow_dag

        outG = workflow_dag

        new_node_machine_list = []

        for node in node_list:
            new_node_machine_list.append(outG.nodes[node]["machine_list"])

        # since we are only merging diamonds (same predecessor, same successor)
        predecessor = list(outG.predecessors(node_list[0]))[
            0
        ]  # coz it returns a dict_iterator
        successor = list(outG.successors(node_list[0]))[0]

        # remove all parallel nodes and add edge pred -> collapsed_parallel -> succ
        newNodeId = "n" + str(new_node_machine_list)
        outG.add_node(newNodeId, machine_list=[new_node_machine_list])

        for node in node_list:
            outG.remove_node(node)

        outG.add_edge(predecessor, newNodeId)
        outG.add_edge(newNodeId, successor)

        return outG

    def _collapse_linear_chains(self, workflow_graph: nx.DiGraph):
        # get from user workflow graph
        start_node = [
            node for node in workflow_graph.nodes if workflow_graph.in_degree(node) == 0
        ][0]
        dfs_edges = list(nx.dfs_edges(workflow_graph, source=start_node))

        # collapse linear chains
        output_graph = workflow_graph
        linear_chain = []
        set_of_linear_chains = set()
        for u, v in dfs_edges:
            if output_graph.out_degree(u) == 1 and output_graph.in_degree(v) == 1:
                if u not in linear_chain:
                    linear_chain.append(u)
                if v not in linear_chain:
                    linear_chain.append(v)
            else:
                if linear_chain:
                    set_of_linear_chains.add(tuple(linear_chain))
                linear_chain = []

        # for a -> b -> c (coz i never flush it out to set_of_linear_chains)
        if linear_chain != []:
            set_of_linear_chains.add(tuple(linear_chain))

        # merge all linear chains
        for chain in set_of_linear_chains:
            node_list = list(chain)
            output_graph = self._merge_linear_nodes(output_graph, node_list)

        return output_graph

    def _collapse_parallel_chains(self, workflow_graph: nx.DiGraph):
        start_node = [
            node for node in workflow_graph.nodes if workflow_graph.in_degree(node) == 0
        ][0]
        dfs_nodes = list(nx.dfs_preorder_nodes(workflow_graph, source=start_node))

        output_graph = workflow_graph

        set_of_parallel_chains = set()

        for curr_node in dfs_nodes:
            # for each nodes get successors create a list of nodes with same predecessor
            curr_node_succ = list(output_graph.successors(curr_node))
            diamond_forming_nodes = []

            for succ in curr_node_succ:
                if output_graph.out_degree(succ) == 1:
                    diamond_forming_nodes.append(succ)

            group_by_succ_dict = defaultdict(list)

            for node in diamond_forming_nodes:
                succ = list(output_graph.successors(node))[0]
                group_by_succ_dict[succ].append(node)

            for val in group_by_succ_dict.values():
                if len(val) > 1:
                    set_of_parallel_chains.add(tuple(val))

        for chain in set_of_parallel_chains:
            chain_list = list(chain)
            output_graph = self._merge_parallel_nodes(output_graph, chain_list)

        return output_graph

    # get workflow name:
    def get_user_dag_name(self):
        return self.__dag_config_data["WorkflowName"]

    # get a map: function_name -> function_object
    def get_node_object_map(self):
        return self.__functions

    # get a list of node dictionaries
    def get_node_param_list(self):
        functions_list = []
        for f in self.__functions.values():
            functions_list.append(f.get_as_dict())
        return functions_list

    # function to get the composite structure for statemachine generation
    def get_statemachine_structure(self):
        tasklist = []
        wf_dag = self.__dag

        # initialise graphs
        collapsed_dag = wf_dag
        output_dag = wf_dag
        while len(output_dag.nodes()) != 1:
            linear_collapsed_dag = self._collapse_linear_chains(collapsed_dag)
            collapsed_dag = self._collapse_parallel_chains(linear_collapsed_dag)
            output_dag = collapsed_dag

        for node in output_dag.nodes():
            tasklist = output_dag.nodes[node]["machine_list"]

        return tasklist
