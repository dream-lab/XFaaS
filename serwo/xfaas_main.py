import xfaas_init as xfaas_init
import xfaas_optimizer as xfaas_optimizer
import xfaas_provenance as xfaas_provenance
import xfaas_resource_generator as xfaas_resource_generator
import xfaas_build as xfaas_build
import xfaas_deploy as xfaas_deploy
import sys

USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]
DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
BENCHMARK_FILE = sys.argv[3]
benchmark_path = f'{USER_DIR}/{BENCHMARK_FILE}'
if __name__ == '__main__':
    user_pinned_nodes = {
        # "1":"0",
        # "2":"0",
        # "3":"0",
        # "16":"0",
        # "12":"0",
        # "17":"0"
    }
    xfaas_user_dag = xfaas_init.init(DAG_DEFINITION_PATH)
    deployment_config = xfaas_optimizer.optimize(xfaas_user_dag,USER_DIR,DAG_DEFINITION_PATH,user_pinned_nodes,
                                                 benchmark_path)
    print('fin: ',deployment_config)

