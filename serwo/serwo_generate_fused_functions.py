import json
import networkx as nx
import random
import string
from collections import defaultdict
from random import randint
from copy import deepcopy
from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


class FusionCodeGenerator:
    # private variables
    __dag_config_data = dict()  # dag configuration (picked up from user file)
    __nodeIDMap = {}  # map: nodeName -> nodeId (used internally)
    __dag = nx.DiGraph()  # networkx directed graph

    def __init__(self, dag_to_fuse):

        # build the networkx DAG
        # add nodes in the dag and populate the functions dict
        # build the networkx DAG
        # add nodes in the dag and populate the functions dict

        for node in dag_to_fuse.nodes():
            output_var = self._generate_random_variable_name()
            dag_to_fuse.nodes[node]['input_var'] = None
            dag_to_fuse.nodes[node]['output_var'] = output_var
            dag_to_fuse.nodes[node]['code'] = output_var + " = " + dag_to_fuse.nodes[node]["NodeName"] + \
                                              ".function($input_var$)" + "\n\t" + dag_to_fuse.nodes[node]['output_var'] \
                                              + ".set_basepath($input_var$.get_basepath())"


        start_node = [node for node in dag_to_fuse if dag_to_fuse.in_degree(node) == 0][0]

        dag_to_fuse.nodes[start_node]['code'] = dag_to_fuse.nodes[start_node]['output_var'] + " = " + \
                                                dag_to_fuse.nodes[start_node]["NodeName"] + ".function(serwoObject)" + \
                                                "\n\t" + dag_to_fuse.nodes[start_node]['output_var'] + \
                                                ".set_basepath(serwoObject.get_basepath())"
        dag_to_fuse.nodes[start_node]['input_var'] = "serwoObject"

        self.__dag = dag_to_fuse

    def __load_user_spec(self, user_config_path):
        with open(user_config_path, "r") as user_dag_spec:
            dag_data = json.load(user_dag_spec)
        return dag_data

    def _generate_random_variable_name(self, n=4):
        res = ''.join(random.choices(string.ascii_letters, k=n))
        return str(res).lower()

    def _get_fusion_code_parallel_merge(self, dag, nodes):
        code = ""
        get_base_path_from = None
        for node in nodes:
            # Remember No $var$ will be updated in parallel merge
            code += "\n\t" + dag.nodes[node]['code']
            get_base_path_from = dag.nodes[node]['output_var']
        output_var = self._generate_random_variable_name()
        code += "\n\t" + output_var + ' = SerWOObjectsList()'
        for node in nodes:
            code += "\n\t" + output_var + '.add_object(body=' + dag.nodes[node]['output_var'] + '.get_body())'

        code += "\n\t" + output_var + ".set_basepath(" + get_base_path_from + ".get_basepath())"
        # TODO: Verify assertion that the input_var will always be None
        return None, code, output_var

    def _get_fusion_code_linear_merge(self, dag, nodes):
        code = ""
        last = nodes[-1]
        first = nodes[0]
        previous_var = None
        for node in nodes[:-1]:
            # $var$ will be updated in linear merge
            if previous_var is not None:
                code += "\n\t" + dag.nodes[node]['code'].replace("$input_var$", previous_var)
            else:
                code += "\n\t" + dag.nodes[node]['code']
            previous_var = dag.nodes[node]["output_var"]
        code += "\n\t" + dag.nodes[last]['code'].replace("$input_var$", dag.nodes[nodes[-2]]['output_var'])
        input_var = dag.nodes[first]['input_var']
        output_var = dag.nodes[last]['output_var']
        return input_var, code, output_var

    def _merge_linear_nodes(self, workflow_dag: nx.DiGraph, node_list: list) -> nx.DiGraph:
        # Replaced nodeId -> userFnName
        if (node_list == []):
            return workflow_dag
        outG = workflow_dag

        newNodeId = "n" + str(node_list)
        input_var, code, output_var = self._get_fusion_code_linear_merge(outG, node_list)

        outG.add_node(newNodeId, input_var=input_var, code=code, output_var=output_var)  # Add the 'merged' node
        for u, v in list(outG.edges()):
            if v == node_list[0]:
                # add edge from u -> new node id
                outG.add_edge(u, newNodeId)
            if u == node_list[len(node_list) - 1]:
                outG.add_edge(newNodeId, v)
        for n in node_list:  # remove the individual nodes
            outG.remove_node(n)
        return outG

    def _merge_parallel_nodes(self, workflow_dag: nx.DiGraph, node_list: list) -> nx.DiGraph:
        # write code here to merge the parallel nodes
        # Replaced nodeId -> userFnName
        if (node_list == []):
            return workflow_dag
        outG = workflow_dag

        # since we are only merging diamonds (same predecessor, same successor)
        predecessor = list(outG.predecessors(node_list[0]))[0]  # coz it returns a dict_iterator
        successor = list(outG.successors(node_list[0]))[0]
        # remove all parallel nodes and add edge pred -> collapsed_parallel -> succ
        xd = randint(1000, 9999)
        newNodeId = "n" + str(xd)
        # add new node pre
        input_var, code, output_var = self._get_fusion_code_parallel_merge(outG, node_list)
        outG.add_node(newNodeId, input_var=input_var, code=code, output_var=output_var)
        for node in node_list:
            outG.remove_node(node)
        outG.add_edge(predecessor, newNodeId)
        outG.add_edge(newNodeId, successor)
        return outG

    def _collapse_parallel_chains(self, workflow_graph: nx.DiGraph):
        start_node = [node for node in workflow_graph.nodes if workflow_graph.in_degree(node) == 0][0]
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

    def _collapse_linear_chains(self, workflow_graph: nx.DiGraph):
        # get from user workflow graph
        start_node = [node for node in workflow_graph.nodes if workflow_graph.in_degree(node) == 0][0]
        dfs_edges = list(nx.dfs_edges(workflow_graph, source=start_node))
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
        # print("Set of linear chains", len(set_of_linear_chains))
        for chain in set_of_linear_chains:
            node_list = list(chain)
            # print(node_list)
            output_graph = self._merge_linear_nodes(output_graph, node_list)
        return output_graph

    def get_fused_code(self):
        # load the dag
        wf_dag = self.__dag
        collapsed_dag = wf_dag
        output_dag = wf_dag
        # iterative linear and parallel merge
        while len(output_dag.nodes()) != 1:
            linear_collapsed_dag = self._collapse_linear_chains(collapsed_dag)
            collapsed_dag = self._collapse_parallel_chains(linear_collapsed_dag)
        output_dag = collapsed_dag
        for node in output_dag:
            return output_dag.nodes[node]['code'] + '\n\treturn ' + output_dag.nodes[node]['output_var']
