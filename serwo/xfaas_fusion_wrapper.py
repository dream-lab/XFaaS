import serwo_function_fuse as default_fusion
from python.src.utils.classes.commons.serwo_user_dag import SerWOUserDag
import pathlib
from copy import deepcopy
import xfaas_benchmark_reader as default_benchmark_reader
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
import sys
import json
DAG_DEFINITION_FILE = sys.argv[2]
DAG_BENCHMARK_FILENAME = 'dag-benchmark.json'
MULTIPLIER = 100
PARENT_DIRECTORY = pathlib.Path(__file__).parent
USER_DIR = sys.argv[1]
CSP = sys.argv[3]
DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
DAG_BENCHMARK_PATH = f'{USER_DIR}/{DAG_BENCHMARK_FILENAME}'


def push_user_dag_to_provenance(wf_id):
    global dynPartiQLWrapper, e
    # convert this to an api call
    print(":" * 80)
    print(f"Pushing workflow configuration to Dynamo DB")

    workflow_name = ""
    try:
        # print(f"{USER_DIR}/{DAG_DEFINITION_FILE}")
        f = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
        js = open(f,'r').read()
        user_workflow_item = json.loads(js)

        user_workflow_item['wf_id'] = wf_id
        workflow_name = user_workflow_item["WorkflowName"]

        dynPartiQLWrapper = PartiQLWrapper('workflow_user_table')
        dynPartiQLWrapper.put(user_workflow_item)
    except ClientError as e:
        print(e)
    print(":" * 80)
    return workflow_name





def update_graph_with_benchmark_data(G, CSP):
    bm_dict = default_benchmark_reader.get_user_dag_benchmark_values(DAG_BENCHMARK_PATH)
    for node in G.nodes:
        G.nodes[node]['ExecDur'] = bm_dict['node_benchmarks'][node][CSP]['Latency']
    for edge in G.edges:
        G.edges[edge]['TransferTime'] = bm_dict['edge_benchmarks'][edge][CSP]
    return G

def run():
    global wf_id, wf_name
    wf_id = str(uuid.uuid4())
    wf_name = push_user_dag_to_provenance(wf_id)
    global G, node, god_list
    gg = SerWOUserDag(DAG_DEFINITION_PATH).get_dag()
    fin_g = deepcopy(gg)
    G = deepcopy(fin_g)
    user_og_graph = deepcopy(G)
    print(user_og_graph)
    G1 = deepcopy(G)
    fc, latency, user_graph_latency, cost, user_dag_cost = default_fusion.fuse_graph(G, CSP,
                                                                                     cost_factor=1.2)


if __name__ == "__main__":

    wf_name, wf_id, refactored_wf_id, wf_deployment_id = run()

    # Genreate Jmx post deployment
    # generate JMX post deployment
    # try:
    #     JMXGenerator.generate_jmx_files(
    #         workflow_name=wf_name,
    #         workflow_deployment_id=wf_deployment_id,
    #         user_dir=USER_DIR,
    #         template_root_dir="python/src/jmx-templates",
    #         csp=ccsp.lower()
    #     )
    # except Exception as e:
    #     print(e)


    # resources dir
    # resources dir
    cwd = os.getcwd()
    user_dir = USER_DIR
    if 'serwo' not in cwd:
        user_dir = f"serwo/{USER_DIR}"

    resources_dir=pathlib.Path.joinpath(pathlib.Path(user_dir), "build/workflow/resources")
    # resources_dir=pathlib.Path.joinpath(pathlib.Path(USER_DIR), "build/workflow/resources")
    provenance_artifacts = {
        "workflow_id": wf_id,
        "refactored_workflow_id": refactored_wf_id,
        "deployment_id": wf_deployment_id
    }

    print("::Provenance Artifacts::")
    print(provenance_artifacts)

    print("::Writing provenance artifacts output to JSON file::")
    json_output = json.dumps(provenance_artifacts, indent=4)
    with open(pathlib.Path.joinpath(resources_dir, "provenance-artifacts.json"), "w+") as out:
        out.write(json_output)


    print("::Adding deployment structure JSON::")
    deployment_structure = {
        "entry_csp": CSP.lower()
    }
    deployment_struct_json = json.dumps(deployment_structure, indent=4)
    with open(pathlib.Path.joinpath(resources_dir, "deployment-structure.json"), "w+") as out:
        out.write(deployment_struct_json)