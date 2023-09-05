import xfaas_init as xfaas_init
import xfaas_optimizer as xfaas_optimizer
import xfaas_provenance as xfaas_provenance
import xfaas_resource_generator as xfaas_resource_generator
import xfaas_build as xfaas_build
import xfaas_deploy as xfaas_deploy
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP

import sys
import json
import pathlib
project_dir = pathlib.Path(__file__).parent.resolve()

USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]

DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
BENCHMARK_FILE = sys.argv[3]
benchmark_path = f'{USER_DIR}/{BENCHMARK_FILE}'
csp = sys.argv[4]
region = sys.argv[5]
part_id = "test"
def get_user_pinned_nodes():

    config = json.loads(open(f'{project_dir}/config/xfaas_user_config.json', 'r').read())
    if "user_pinned_nodes" in config:
        return config['user_pinned_nodes']
    else:
        return None


def run(user_wf_dir, dag_definition_file, benchmark_file, csp,region):
    dag_definition_path = f"{user_wf_dir}/{dag_definition_file}"
    user_pinned_nodes = get_user_pinned_nodes()
    xfaas_user_dag = xfaas_init.init(dag_definition_path)
    # partition_config = xfaas_optimizer.optimize(xfaas_user_dag,
    #                                             user_pinned_nodes, benchmark_path)

    partition_config = [PartitionPoint("function_name", 2, CSP(csp), None, part_id, region)]

    wf_id = xfaas_provenance.push_user_dag(dag_definition_path)
    refactored_wf_id = xfaas_provenance.push_refactored_workflow(dag_definition_file, user_wf_dir, wf_id,csp)
    wf_deployment_id = xfaas_provenance.push_deployment_logs(dag_definition_file,user_wf_dir,wf_id,refactored_wf_id,csp)
    xfaas_resource_generator.generate(user_wf_dir, dag_definition_path, partition_config,dag_definition_file)
    xfaas_provenance.generate_provenance_artifacts(user_wf_dir,wf_id,refactored_wf_id,wf_deployment_id,csp,region,part_id)

   

if __name__ == '__main__':

    run(USER_DIR, DAG_DEFINITION_FILE, BENCHMARK_FILE, csp,region)
    # user_pinned_nodes = get_user_pinned_nodes()
    # xfaas_user_dag = xfaas_init.init(DAG_DEFINITION_PATH)
    # # partition_config = xfaas_optimizer.optimize(xfaas_user_dag,
    # #                                             user_pinned_nodes, benchmark_path)

    # partition_config = [PartitionPoint("function_name", 2, CSP(csp), None, part_id, region)]

    # wf_id = xfaas_provenance.push_user_dag(DAG_DEFINITION_PATH)
    # refactored_wf_id = xfaas_provenance.push_refactored_workflow(DAG_DEFINITION_FILE, USER_DIR, wf_id,csp)
    # wf_deployment_id = xfaas_provenance.push_deployment_logs(DAG_DEFINITION_FILE,USER_DIR,wf_id,refactored_wf_id,csp)
    # xfaas_resource_generator.generate(USER_DIR, DAG_DEFINITION_PATH, partition_config,DAG_DEFINITION_FILE)
    # xfaas_provenance.generate_provenance_artifacts(USER_DIR,wf_id,refactored_wf_id,wf_deployment_id,csp,region,part_id)




