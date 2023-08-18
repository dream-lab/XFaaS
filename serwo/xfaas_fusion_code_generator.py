from copy import deepcopy
from serwo_generate_fused_functions import FusionCodeGenerator
from python.src.utils.classes.commons.csp import CSP
import networkx as nx
import shutil
import os
from jinja2 import Environment, FileSystemLoader
import json

serwo_object_import = "\nfrom python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList"
serwo_func_line_import = "\ndef function(serwoObject) -> SerWOObject:"
final_code = ""
fusion_template_path = "python/src/fusion-template/"
fusion_template_path_temp = "python/src/fusion-template/fused_runner_temp.py"


def template(import_line, code):
    output_dir = fusion_template_path_temp
    try:
        file_loader = FileSystemLoader(fusion_template_path)
        env = Environment(loader=file_loader)
        template = env.get_template("fused_runner.py")
        print(f"Created Azure jinja2 environment for Runner")
    except Exception as exception:
        raise Exception("Error in loading jinja template environment")

    # render function
    try:
        output = template.render(import_code=import_line, code=code)
    except:
        raise Exception("Error in jinja template render function")

    try:
        # flush out the generator yaml
        with open(f"{output_dir}", "w+") as runner:
            runner.write(output)
            print(f"Writing python file to directory")
    except:
        raise Exception("Error in writing to template file")

    os.system(f"autopep8 --in-place {fusion_template_path_temp}")


def is_complex(id):
    if "F" in id:
        return True
    return False


def calc_start(node, id_to_fc_map):
    if not is_complex(node):
        return node
    while True:
        sd = id_to_fc_map[node].get_entry_node()
        if not is_complex(sd):
            return sd
        else:
            node = sd


def calc_end(node, id_to_fc_map):
    if not is_complex(node):
        return node
    while True:
        sd = id_to_fc_map[node].get_exit_node()
        if not is_complex(sd):
            return sd
        else:
            node = sd


def mutate(old_graph, new_node_id, new_node_val, start, end, id_to_fc_map):
    predecessors = deepcopy(old_graph.predecessors(start))
    successors = deepcopy(old_graph.successors(end))
    se = new_node_val

    global_set = set()
    for xd in se:
        if "Nodes" in old_graph.nodes[xd]:
            sse = old_graph.nodes[xd]["Nodes"]
            for s in sse:
                global_set.add(s)
        else:
            global_set.add(xd)
    start = calc_start(start, id_to_fc_map)
    end = calc_end(end, id_to_fc_map)
    old_graph.add_node(new_node_id, Nodes=global_set, Start=start, End=end)
    print("=======")
    print(se)
    print(global_set)
    for xd in new_node_val:
        old_graph.remove_node(xd)

    for nd in predecessors:
        old_graph.add_edge(nd, new_node_id)
    for nd in successors:
        old_graph.add_edge(new_node_id, nd)


def generate_sub_graph(nodes, user_og_graph):
    return user_og_graph.subgraph(nodes)


def generate(G, fc, user_og_graph, suffix_str, user_dir, dag_definition_path):
    id_to_fc_map = dict()
    for fusion_candidate in fc:
        id_to_fc_map[fusion_candidate.get_id()] = fusion_candidate

    round = 0
    while True:
        copy_g = deepcopy(G)
        global_flag = 0
        for fusion_candidate in fc:
            all_nodes_present_in_graph = True
            for node in fusion_candidate.get_nodes():
                if G.has_node(node) != True:
                    all_nodes_present_in_graph = False
                    break
            if all_nodes_present_in_graph:
                global_flag = 1
                nodes_to_fuse = fusion_candidate.get_nodes()
                entry = fusion_candidate.get_entry_node()
                exit = fusion_candidate.get_exit_node()

                _id = fusion_candidate.get_id()

                global_set = nodes_to_fuse
                mutate(copy_g, _id, global_set, entry, exit, id_to_fc_map)

        G = deepcopy(copy_g)
        round += 1

        if global_flag == 0:
            break

    final_edges = []
    for u, v in G.edges():
        uu = calc_start(u, id_to_fc_map)
        vv = calc_start(v, id_to_fc_map)
        final_edges.append((uu, vv))
    k = "Nodes"
    start_key = "Start"
    end_key = "End"
    pth, pp, fin_graph = generate_fused_code(
        G,
        end_key,
        k,
        start_key,
        user_og_graph,
        suffix_str,
        final_edges,
        user_dir,
        dag_definition_path,
    )
    return pth, pp, fin_graph


def extract_native(path):
    xd = ""
    for c in reversed(path):
        if c == "/":
            break
        xd += c
    ans = ""
    for c in reversed(xd):
        ans += c
    return ans


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def get_app_name(dag_definition_path):
    ff = open(dag_definition_path, "r")
    jsson = json.loads(ff.read())
    return jsson["WorkflowName"]


def create_dag_description(
    workflow_name: str, graph: nx.DiGraph, csp: CSP, output_dir: str, suffix_str: str
):
    # base skeleton of the output json
    output_dict = dict(WorkflowName=workflow_name)
    output_dict["Nodes"] = []
    output_dict["Edges"] = []

    # populate the node list
    for node in graph.nodes:
        # node items
        print("Inside create DAG description")
        print(graph.nodes[node]["NodeId"])
        print("NodeName", graph.nodes[node]["NodeName"])
        csp_string = CSP.toString(csp)
        node_item = dict(
            NodeId=graph.nodes[node]["NodeId"],
            NodeName=graph.nodes[node]["NodeName"],
            Path=graph.nodes[node]["Path"],
            EntryPoint=graph.nodes[node]["EntryPoint"],
            MemoryInMB=graph.nodes[node]["MemoryInMB"],
            CSP=csp_string,
        )

        # edge items
        node_successors = list(graph.successors(node))
        edge_item_value = []
        if node_successors:
            edge_item_key = graph.nodes[node]["NodeName"]
            # iterate over all successors of the node and add the nodename
            for succnode in node_successors:
                edge_item_value.append(graph.nodes[succnode]["NodeName"])
            edge_item = {edge_item_key: edge_item_value}
            # append the edge dict
            output_dict["Edges"].append(edge_item)

        # append the node dict
        output_dict["Nodes"].append(node_item)

    # write to output file
    if "aws" in suffix_str:
        csp_string = "aws"
    elif "Azure" in suffix_str:
        csp_string = "azure"

    output_dag_description_filename = f"serwo-{csp_string}-dag-description.json"
    output_dag_description_filepath = f"{output_dir}/{output_dag_description_filename}"
    with open(output_dag_description_filepath, "w") as outfile:
        print(f"Writing json to directory {output_dag_description_filepath}")
        json.dump(output_dict, outfile, indent=4)

    return output_dag_description_filename


def handle_dependencies_and_requirements(paths, op_path):
    req_path = f"{op_path}/requirements.txt"
    if os.path.exists(req_path):
        ff = open(req_path, "w")
    else:
        ff = open(req_path, "a")
    reqs = set()
    for path in paths:
        ft = open(f"{path}/requirements.txt")
        lines = ft.readlines()
        for line in lines:
            reqs.add(line)

    for xd in reqs:
        ff.write(xd + "\n")

    for path in paths:
        pt = f"{path}/requirements.txt"
        if os.path.exists(pt):
            stream = os.popen(f"rm {pt}")
            stream.close()

    f = 0
    for path in paths:
        pt = f"{path}/dependencies"
        if os.path.exists(pt):
            f = 1

    if f:
        dep_path = f"{op_path}/dependencies"
        if not os.path.exists(dep_path):
            os.mkdir(dep_path)
        for path in paths:
            pt = f"{path}/dependencies"
            if os.path.exists(pt):
                copytree(f"{pt}", f"{dep_path}")

    for path in paths:
        pt = f"{path}/dependencies"
        if os.path.exists(pt):
            stream = os.popen(f"rm -r {pt}")
            stream.close()


def generate_fused_code(
    G,
    end_key,
    k,
    start_key,
    user_og_graph,
    suffix_str,
    final_edges,
    user_dir,
    dag_definition_path,
):
    fused_src_path = f"{user_dir}/src-fused-{suffix_str}"
    if not os.path.exists(fused_src_path):
        os.mkdir(fused_src_path)
    index = 0
    fin_graph = nx.DiGraph()
    edges_to_add = []
    for node in G.nodes():
        if k in G.nodes[node]:
            nodes_ls = list(G.nodes[node][k])
            start = G.nodes[node][start_key]
            end = G.nodes[node][end_key]
            sub_graph_to_fuse = generate_sub_graph(nodes_ls, user_og_graph)
            sub_graph_to_fuse = nx.DiGraph(sub_graph_to_fuse)
            import_line = ""
            kp = "Path"
            kn = "NodeName"
            ep = "EntryPoint"
            for node in sub_graph_to_fuse.nodes():
                import_line += f"\nfrom {extract_native(sub_graph_to_fuse.nodes[node][kp])} import {sub_graph_to_fuse.nodes[node][ep][:-3]} as {sub_graph_to_fuse.nodes[node][kn]}"

            global final_code
            max_mem = 0
            for node in sub_graph_to_fuse.nodes():
                max_mem = max(max_mem, user_og_graph.nodes[node]["MemoryInMB"])
            new_node_id = user_og_graph.nodes[start]["NodeId"]
            new_node_name = user_og_graph.nodes[start]["NodeName"]
            new_entry_point = "func.py"
            for u, v in user_og_graph.in_edges(start):
                if fin_graph.has_node(u):
                    edges_to_add.append((u, start))

            for u, v in user_og_graph.out_edges(end):
                if fin_graph.has_node(v):
                    edges_to_add.append((start, v))

            code = FusionCodeGenerator(sub_graph_to_fuse).get_fused_code()

            final_code += import_line
            final_code += serwo_object_import
            final_code += serwo_func_line_import
            final_code += code
            template(import_line, code)
            fused_dir_id = "fused-" + suffix_str + "-" + str(index)
            path = fused_src_path + "/" + fused_dir_id
            if not os.path.exists(path):
                os.mkdir(path)
            ls_of_paths = []
            for id in nodes_ls:
                user_src_path = user_og_graph.nodes[id]["Path"]
                user_og_path = extract_native(user_src_path)
                pth = path + "/" + user_og_path
                if not os.path.exists(pth):
                    os.mkdir(path + "/" + user_og_path)
                copytree(user_src_path, path + "/" + user_og_path)
                ls_of_paths.append(path + "/" + user_og_path)
            handle_dependencies_and_requirements(ls_of_paths, path)
            new_path = path
            shutil.copyfile(fusion_template_path_temp, path + "/func.py")
            stream = os.popen(f"rm {fusion_template_path_temp}")
            stream.close()
            index += 1
        else:
            node_prop = user_og_graph.nodes[node]
            user_src_path = node_prop["Path"]
            new_path = user_src_path
            new_node_name = node_prop["NodeName"]
            max_mem = node_prop["MemoryInMB"]
            new_entry_point = node_prop["EntryPoint"]
            new_node_id = node_prop["NodeId"]

            for u, v in user_og_graph.out_edges(node):
                if fin_graph.has_node(v):
                    edges_to_add.append((u, v))
            user_og_path = extract_native(user_src_path)
            pth = fused_src_path + "/" + user_og_path
            if not os.path.exists(pth):
                os.mkdir(fused_src_path + "/" + user_og_path)
            copytree(user_src_path, fused_src_path + "/" + user_og_path)

        print("================================================")

        fin_graph.add_node(
            new_node_id,
            NodeId=new_node_id,
            NodeName=new_node_name,
            Path=new_path,
            EntryPoint=new_entry_point,
            CSP="Azure",
            MemoryInMB=max_mem,
        )

    for u, v in final_edges:
        fin_graph.add_edge(u, v)
    print(fin_graph)
    for node in fin_graph.nodes():
        print("id: ", node, fin_graph.nodes[node])

    deep_fin = deepcopy(fin_graph)
    top_sort = list(nx.topological_sort(deep_fin))
    id = top_sort[-1]
    print("last node: ", id)
    print("ending ", deep_fin)
    pp = create_dag_description(
        get_app_name(dag_definition_path),
        deep_fin,
        CSP.toCSP("AWS"),
        user_dir,
        suffix_str,
    )
    return fused_src_path, pp, fin_graph
