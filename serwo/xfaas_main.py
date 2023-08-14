import xfaas_init as xfaas_init
import xfaas_optimizer as xfaas_optimizer
import xfaas_provenance as xfaas_provenance
import xfaas_resource_generator as xfaas_resource_generator
import xfaas_build as xfaas_build
import xfaas_deploy as xfaas_deploy
import sys
import json
import pathlib

USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]
parent_directory = pathlib.Path(__file__).parent.absolute()

DAG_DEFINITION_PATH = f"{parent_directory}/{USER_DIR}/{DAG_DEFINITION_FILE}"
BENCHMARK_FILE = sys.argv[3]
benchmark_path = f'{parent_directory}/{USER_DIR}/{BENCHMARK_FILE}'
USER_DIR = f'{parent_directory}/{USER_DIR}'

def get_user_pinned_nodes():
    config = json.loads(open('config/xfaas_user_config.json', 'r').read())
    if "user_pinned_nodes" in config:
        return config['user_pinned_nodes']
    else:
        return None

if __name__ == '__main__':
    user_pinned_nodes = get_user_pinned_nodes()
    xfaas_user_dag = xfaas_init.init(DAG_DEFINITION_PATH)
    partition_config = xfaas_optimizer.optimize(xfaas_user_dag,
                                                user_pinned_nodes, benchmark_path)

    xfaas_resource_generator.generate(USER_DIR, DAG_DEFINITION_PATH, partition_config)
    wf_id = xfaas_provenance.push_user_dag(DAG_DEFINITION_PATH)




