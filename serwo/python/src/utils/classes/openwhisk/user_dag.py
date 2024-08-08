import json
import copy
import random
import string
import itertools
import networkx as nx
from collections import defaultdict

from .function import Function

class UserDag:
    # dag configuration (picked up from user file)
    __dag_config_data = dict()

    # map: nodeName -> nodeId (used internally) [NOTE [TK] - This map is changed from nodeName -> NodeId to UserGivenNodeId -> our internal nodeID]
    __nodeIDMap = ({})

    __dag = nx.DiGraph() # networkx directed graph
    __functions = {} # map: functionName -> functionObject

    def __init__(self, user_config_path) -> None:
        try:
            self.__dag_config_data = self.__load_user_spec(user_config_path)
        except Exception as e:
            raise e
        
        for index, node in enumerate(self.__dag_config_data["Nodes"]):
            nodeID = "n" + str(index+1)
            # nodeID = "n" + node["NodeName"] # Uncomment to make debugging easier
            nodeVar = self._generate_random_variable_name()

            self.__nodeIDMap[node["NodeName"]] = nodeID
            self.__nodeIDMap[node["NodeId"]] = nodeID
            self.__functions[node["NodeName"]] = Function(
                id=node["NodeId"],
                name=node["NodeName"],
                path=node["Path"],
                entry_point=node["EntryPoint"],
                memory=node["MemoryInMB"],
            )

            workflowName = self.__dag_config_data["WorkflowName"]
            nodeName = node["NodeName"]

            self.__dag.add_node(
                nodeID,
                NodeName=node["NodeName"],
                Path=node["Path"],
                EntryPoint=node["EntryPoint"],
                CSP=node.get("CSP"),
                MemoryInMB=node["MemoryInMB"],
                machine_list=[nodeID],
                var_machine_list=[nodeVar],
                ret=[f'composer.action("/guest/{workflowName}/{nodeName}")'], # only applicable for leaf nodes (not for sequence/parallel)
                var=nodeVar,
                code_generation_done=False,
                node_type="action", # Can be one of [action/parallel/sequence]
            )

        for edge in self.__dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    self.__dag.add_edge(self.__nodeIDMap[key], self.__nodeIDMap[val])

    def _generate_random_variable_name(self, n=4):
        res = ''.join(random.choices(string.ascii_letters, k=n))
        return str(res).lower()
    
    def __load_user_spec(self, user_config_path):
        with open(user_config_path, "r") as user_dag_spec:
            dag_data = json.load(user_dag_spec)

        return dag_data
    
    def get_user_dag_name(self):
        return self.__dag_config_data["WorkflowName"]
    
    def get_node_object_map(self):
        return self.__functions
    
    def get_node_param_list(self):
        functions_list = []
        for f in self.__functions.values():
            functions_list.append(f.get_as_dict())

        return functions_list
    
    def _merge_linear_nodes(self, graph: nx.DiGraph, node_list: list):
        """
        Doesn't return anything since operating on deep copy of graphs might get heavy.
        Works on side effect on nx.Digraph.
        """
        if len(node_list) == 0:
            return
        
        new_node_machine_list = []
        new_node_var_machine_list = []
        for node in node_list:
            new_node_machine_list.extend(graph.nodes[node]["machine_list"])

            if graph.nodes[node]["node_type"] == "action":
                new_node_var_machine_list.extend(graph.nodes[node]["var_machine_list"])
            else:
                # new_node_var_machine_list.extend(graph.nodes[node]["var"])
                if type(graph.nodes[node]["var"]) == str:
                    new_node_var_machine_list.extend([graph.nodes[node]["var"]])
                else:
                    new_node_var_machine_list.extend(graph.nodes[node]["var"])

        new_node_id = "n" + str(node_list)
        graph.add_node(
            new_node_id, var=self._generate_random_variable_name(), 
            machine_list=new_node_machine_list,
            var_machine_list=new_node_var_machine_list,
            node_type="sequence", code_generation_done=False,
        )

        for u, v in list(graph.edges()):
            if v == node_list[0]:
                # replace the first node of the sequence with sequence node's id
                graph.add_edge(u, new_node_id)
            
            if u == node_list[-1]:
                # make the last node of the sequence point to sequence's next node (where sequence ends)
                graph.add_edge(new_node_id, v)
        
        # remove the individual nodes
        for n in node_list:
            graph.remove_node(n)

        return

    
    def _collapse_linear_chains(self, graph: nx.DiGraph):
        """
        Doesn't return anything since operating on deep copy of graphs might get heavy.
        Works on side effect on nx.Digraph.
        """
        start_node = [node for node in graph.nodes if graph.in_degree(node) == 0][0]
        dfs_edges = list(nx.dfs_edges(graph, source=start_node))
        
        linear_chain = []
        set_of_linear_chains = set()
        for u, v in dfs_edges:
            if graph.out_degree(u) == 1 and graph.in_degree(v) == 1:
                if u not in linear_chain:
                    linear_chain.append(u)

                if v not in linear_chain:
                    linear_chain.append(v)
            else:
                if linear_chain:
                    set_of_linear_chains.add(tuple(linear_chain))
                
                linear_chain = []

        if linear_chain != []:
            set_of_linear_chains.add(tuple(linear_chain))
            linear_chain = []
        
        for chain in set_of_linear_chains:
            node_list = list(chain)
            self._merge_linear_nodes(graph, node_list)

        return
    
    def _merge_parallel_nodes(self, graph: nx.DiGraph, node_list):
        """
        Doesn't return anything since operating on deep copy of graphs might get heavy.
        Works on side effect on nx.Digraph.
        """
        if len(node_list) == 0:
            return
        
        new_node_machine_list = []
        new_node_var_machine_list = []
        for node in node_list:
            new_node_machine_list.append(graph.nodes[node]["machine_list"])
            # new_node_var_machine_list.append(graph.nodes[node]["var_machine_list"])

            if graph.nodes[node]["node_type"] == "action":
                new_node_var_machine_list.extend(graph.nodes[node]["var_machine_list"])
            else:
                # new_node_var_machine_list.append(graph.nodes[node]["var"])
                if type(graph.nodes[node]["var"]) == str:
                    new_node_var_machine_list.extend([graph.nodes[node]["var"]])
                else:
                    new_node_var_machine_list.extend(graph.nodes[node]["var"])

        # since we are only merging diamonds (same predecessor, same successor) 
        predecessor = list(graph.predecessors(node_list[0]))[0]
        successor = list(graph.successors(node_list[0]))[0]

        new_node_id = "n" + str(new_node_machine_list)
        graph.add_node(
            new_node_id, var=self._generate_random_variable_name(), 
            machine_list=[new_node_machine_list],
            var_machine_list=new_node_var_machine_list,
            node_type="parallel", code_generation_done=False,
        )

        for node in node_list:
            graph.remove_node(node)

        graph.add_edge(predecessor, new_node_id)
        graph.add_edge(new_node_id, successor)

        return

    def _collapse_parallel_chains(self, graph: nx.DiGraph):
        """
        Doesn't return anything since operating on deep copy of graphs might get heavy.
        Works on side effect on nx.Digraph.
        """
        start_node = [node for node in graph.nodes if graph.in_degree(node) == 0][0]
        dfs_nodes = list(nx.dfs_preorder_nodes(graph, source=start_node))

        set_of_parallel_chains = set()
        for curr_node in dfs_nodes:
            curr_node_succ = list(graph.successors(curr_node))
            diamond_forming_node = []

            for succ in curr_node_succ:
                if graph.out_degree(succ) == 1:
                    diamond_forming_node.append(succ)

            group_by_succ_dict = defaultdict(list)
            for node in diamond_forming_node:
                succ = list(graph.successors(node))[0]
                group_by_succ_dict[succ].append(node)

            for val in group_by_succ_dict.values():
                if len(val) > 1:
                    set_of_parallel_chains.add(tuple(val))

        for chain in set_of_parallel_chains:
            chain_list = list(chain)
            self._merge_parallel_nodes(graph, chain_list)
        
        return
    
    def get_updated_nodes(self, dag):
        """
        TODO: Change me to a better approach, I won't scale well for bigger graphs.
        """
        updated_node_ids = []

        start_node = [node for node in dag.nodes if dag.in_degree(node) == 0][0]
        bfs_nodes = list(nx.bfs_layers(dag, sources=start_node))
        bfs_nodes = list(itertools.chain.from_iterable(bfs_nodes))
        for node_id in bfs_nodes:
            if not dag.nodes[node_id]["code_generation_done"]:
                updated_node_ids.append(node_id)

        return updated_node_ids

    def get_orchestrator_code(self):
        """
        Breaker of linear and parallel chains.
        TODO: Test me thoroughly
        """
        original_dag = self.__dag
        output_dag = copy.deepcopy(original_dag) # preserving the original dag
        generated_code = 'const composer = require("openwhisk-composer");\n\n'        
        
        # Creating an action definition for each node of the graph
        start_node = [node for node in output_dag.nodes if output_dag.in_degree(node) == 0][0]
        bfs_nodes = list(nx.bfs_layers(output_dag, sources=start_node))
        bfs_nodes = list(itertools.chain.from_iterable(bfs_nodes))
        for curr_node in bfs_nodes:
            generated_code += f"{output_dag.nodes[curr_node]['var']} = {output_dag.nodes[curr_node]['ret'][0]};\n";
            output_dag.nodes[curr_node]["code_generation_done"] = True

        iteration = 1
        while len(output_dag.nodes()) != 1:
            self._collapse_linear_chains(output_dag)
            new_linear_nodes = self.get_updated_nodes(output_dag)
            if len(new_linear_nodes) > 0:
                generated_code += f"\n// Iteration{iteration}: Sequence\n"

            for new_node in new_linear_nodes:
                node = output_dag.nodes[new_node]
                node["code_generation_done"] = True

                sub_node_machines = []
                for machine in node["var_machine_list"]:
                    sub_node_machines.append(machine)
                
                generated_code += f"{node['var']} = composer.sequence({', '.join(sub_node_machines)});\n";

            self._collapse_parallel_chains(output_dag)
            new_parallel_nodes = self.get_updated_nodes(output_dag)
            if len(new_parallel_nodes) > 0:
                generated_code += f"\n// Iteration{iteration}: Parallel\n"

            for new_node in new_parallel_nodes:
                node = output_dag.nodes[new_node]
                node["code_generation_done"] = True

                sub_node_machines = []
                for machine in node["var_machine_list"]:
                    sub_node_machines.append(machine)

                generated_code += f"{node['var']} = composer.parallel({', '.join(sub_node_machines)});\n";
            
            iteration += 1

        generated_code += f"\nmodule.exports = {output_dag.nodes[list(output_dag.nodes)[0]]['var']};\n"
        return generated_code
    