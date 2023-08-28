import json
import networkx as nx
import random
import string
from collections import defaultdict

class UserDag:
    # private variables
    __dag_config_data = dict() # dag configuration (picked up from user file)
    __nodeIDMap = {} # map: nodeName -> nodeId (used internally) [NOTE [TK] - This map is changed from nodeName -> NodeId to UserGivenNodeId -> our internal nodeID ] (in azure we were already using this)
    __dag = nx.DiGraph() # networkx directed graph

    def __init__(self, user_config_path):
        # throw an exception if loading file has a problem
        try:
            self.__dag_config_data = self.__load_user_spec(user_config_path)
        except Exception as e:
            raise e

        # build the networkx DAG
        # add nodes in the dag and populate the functions dict
        # build the networkx DAG
        # add nodes in the dag and populate the functions dict

        index = 1
        for node in self.__dag_config_data["Nodes"]:
            # NOTE - this is different in AWS, being picked up from the user dag-description
            # nodeID = "n" + str(index)
            nodeID = node["NodeId"]
            self.__nodeIDMap[node["NodeName"]] = nodeID
            # print(node)
            # __dag.add_node(nodeID, NodeName=node["NodeName"], pre="", ret=["yield ", "context.call_activity(" + node["NodeName"]  + ",$var$)"], var=generate_random_variable_name(), machine_list=[nodeID])
            self.__dag.add_node(nodeID, NodeName=node["NodeName"], pre="", ret=["yield ", "context.call_activity(\"" + node["NodeName"]  + "\",$var$)"], var=self._generate_random_variable_name(), machine_list=[nodeID])
            index += 1


        # add edges in the dag
        for edge in self.__dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    self.__dag.add_edge(
                        self.__nodeIDMap[key], self.__nodeIDMap[val])


        start_node = [node for node in self.__dag.nodes if self.__dag.in_degree(node) == 0][0]
        self.__dag.nodes[start_node]['ret'] = ["yield ", "context.call_activity(\"" + self.__dag.nodes[start_node]["NodeName"]  + "\", serwoObject)"]



        
        start_node = [node for node in self.__dag.nodes if self.__dag.in_degree(node) == 0][0]
        self.__dag.nodes[start_node]['ret'] = ["yield ", "context.call_activity(\"" + self.__dag.nodes[start_node]["NodeName"]  + "\", serwoObject)"]
       

    def __load_user_spec(self, user_config_path):
        with open(user_config_path, "r") as user_dag_spec:
            dag_data = json.load(user_dag_spec)
        return dag_data
    
    def _generate_random_variable_name(self, n=4):
        res = ''.join(random.choices(string.ascii_letters, k=n))
        return str(res).lower()

    def _get_orchestrator_code_parallel_merge(self, dag, nodes):
        # print("Dag nodes - ",list(dag.nodes()))
        # print("Orchestrator code parallel merge - ", nodes)
        task_list_var_name = self._generate_random_variable_name()
        task_list_create = task_list_var_name + " = []\n"
        ret = ["yield ",  "context.task_all(" + task_list_var_name + ")"]
        pre = ""
        for node in nodes:
            # Remember No $var$ will be updated in parallel merge
            pre += "\n" + dag.nodes[node]['pre']
        pre += "\n" + task_list_create
        for node in nodes:
            pre += "\n" + dag.nodes[node]['var'] + " = " + dag.nodes[node]['ret'][1]
        
        # task.append()
        for node in nodes:
            pre += "\n" + task_list_var_name + ".append(" + dag.nodes[node]['var'] + ")"

        var = self._generate_random_variable_name()
        return pre, ret, var

    def _get_orchestrator_code_linear_merge(self, dag, nodes):
        # print("Dag nodes - ",list(dag.nodes()))
        # print("Orchestrator code linear merge - ", nodes)
        pre = ""
        last = nodes[-1]
        previous_var = None
        for node in nodes[:-1]:
            # $var$ will be updated in linear merge
            
            if previous_var is not None:
                pre += "\n" + dag.nodes[node]['pre'].replace("$var$", previous_var)
                var_substituted = dag.nodes[node]['ret'][1].replace("$var$", previous_var)
            else:
                pre += "\n" + dag.nodes[node]['pre']
                var_substituted = dag.nodes[node]['ret'][1]
            pre += "\n" + dag.nodes[node]['var'] + " = " + dag.nodes[node]['ret'][0] + " " + var_substituted
            previous_var = dag.nodes[node]['var']
        
        pre += "\n" + dag.nodes[last]['pre'].replace("$var$", dag.nodes[nodes[-2]]['var'])
        var = self._generate_random_variable_name()
        # $var$ will be updated in linear merge
        ret = ["yield ", dag.nodes[last]['ret'][1].replace("$var$", dag.nodes[nodes[-2]]['var'])]
        return pre, ret, var

    def _merge_linear_nodes(self, workflow_dag: nx.DiGraph, node_list: list) -> nx.DiGraph:
        # Replaced nodeId -> userFnName
        if (node_list == []):
            return workflow_dag

        outG = workflow_dag

        new_node_machine_list = []
    
        for node in node_list:
            new_node_machine_list.extend(outG.nodes[node]['machine_list'])

        newNodeId = "n"+str(node_list)
        pre, ret, var = self._get_orchestrator_code_linear_merge(outG, node_list)
        outG.add_node(newNodeId, pre=pre, ret=ret, var=var ,machine_list=new_node_machine_list) # Add the 'merged' node
        
        for u, v in list(outG.edges()):
            if v == node_list[0]:
                # add edge from u -> new node id
                outG.add_edge(u, newNodeId)
            if u == node_list[len(node_list)-1]:
                outG.add_edge(newNodeId, v)
            
        for n in node_list: # remove the individual nodes
            outG.remove_node(n)

        return outG

    def _merge_parallel_nodes(self, workflow_dag: nx.DiGraph, node_list: list) -> nx.DiGraph: 
        # write code here to merge the parallel nodes
        # Replaced nodeId -> userFnName
        if (node_list == []):
            return workflow_dag

        outG = workflow_dag

        new_node_machine_list = []

        for node in node_list:
            new_node_machine_list.append(outG.nodes[node]['machine_list'])
        
        # since we are only merging diamonds (same predecessor, same successor) 
        predecessor = list(outG.predecessors(node_list[0]))[0] # coz it returns a dict_iterator
        successor = list(outG.successors(node_list[0]))[0]

        # remove all parallel nodes and add edge pred -> collapsed_parallel -> succ
        newNodeId = "n" + str(new_node_machine_list)

        # add new node pre
        pre, ret, var = self._get_orchestrator_code_parallel_merge(outG, node_list)
        outG.add_node(newNodeId, pre=pre, ret=ret, var=var, machine_list=[new_node_machine_list])

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
                if (output_graph.out_degree(succ) == 1):
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
        for u,v in dfs_edges:
            if output_graph.out_degree(u) == 1  and output_graph.in_degree(v) == 1:
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
    
    def get_orchestrator_code(self):
        # load the dag
        wf_dag = self.__dag
        collapsed_dag = wf_dag
        output_dag = wf_dag

        # iterative linear and parallel merge
        while len(output_dag.nodes()) != 1:
            linear_collapsed_dag = self._collapse_linear_chains(collapsed_dag)
            collapsed_dag = self._collapse_parallel_chains(linear_collapsed_dag)
        output_dag = collapsed_dag

        # generated code
        final_var = self._generate_random_variable_name()
        end_node = list(output_dag.nodes())[0]
        # added a check if the graph contains only a single node
        if len(output_dag.nodes[end_node]['pre']) == 0:
            post_code = final_var + " = " + output_dag.nodes[end_node]['ret'][0] + " " + output_dag.nodes[end_node]['ret'][1]
            post_code = post_code.split("\n")
            pre_statements = [statement for statement in post_code if statement != '']

            # NOTE - !HACK!
            # adding insert_end_stats_in_metadata (Temporary and this is a very hacky way of doing it, could capture information from the
            # network structure in some way and append)
            variable_for_insert_metadata = pre_statements[-1].split("=")[0].strip()
            insert_metadata_statement = variable_for_insert_metadata + " = " + f"insert_end_stats_in_metadata({variable_for_insert_metadata})"
            pre_statements.append(insert_metadata_statement)
            pre_statements.append(f"return {final_var}")
        else:
            pre_code = output_dag.nodes[end_node]['pre'].split("\n")
            post_code = final_var + " = " + output_dag.nodes[end_node]['ret'][0] + " " + output_dag.nodes[end_node]['ret'][1]
            pre_statements = [statement for statement in pre_code if statement != '']

            # NOTE - !HACK!
            # adding insert_end_stats_in_metadata (Temporary and this is a very hacky way of doing it, could capture information from the
            # network structure in some way and append)
            variable_for_insert_metadata = pre_statements[-1].split("=")[0].strip()
            insert_metadata_statement = variable_for_insert_metadata + " = " + f"insert_end_stats_in_metadata({variable_for_insert_metadata})"
            pre_statements.append(insert_metadata_statement)
            pre_statements.append(post_code)
            pre_statements.append(f"return {final_var}")
        
        # TODO - for every taskall add the converstion from [serwo_objects] -> serwo_list_object
        orchestrator_code = "\n".join([pre_statements[0]] + ["\t" + statement for statement in pre_statements[1:]])
        return orchestrator_code