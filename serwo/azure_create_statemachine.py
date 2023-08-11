# TODO - wrap this script in a module and use in the master build script
# Python base imports
import os
import sys
import pathlib

# serwo imports
import python.src.utils.generators.azure.generate_orchestrator_file as AzureOrchestratorGenerator
from python.src.utils.classes.azure.user_dag import UserDag as AzureUserDAG

REGION = "ap-south-1"
USER_DIR = sys.argv[1]
print("Insied azure create statemachine", USER_DIR)
DAG_DEFINITION_FILE = sys.argv[2]  # pass this out as flags
TRIGGER_TYPE = sys.argv[3]  # make a separate class, azure trigger types
PYTHON_TEMPLATE_DIR = pathlib.Path.joinpath(
    pathlib.Path(__file__).parent.absolute(),
    "python/src/faas-templates/azure/python-templates",
).resolve()
OUTPUT_DIR = f"{USER_DIR}"
DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
ORCHESTRATOR_FILEPATH = f"{USER_DIR}/orchestrator.py"

# load the dag
user_dag = AzureUserDAG(DAG_DEFINITION_PATH)
orchestrator_code = user_dag.get_orchestrator_code()

# generate the orchestration function
try:
    AzureOrchestratorGenerator.generate(
        orchestrator_code, PYTHON_TEMPLATE_DIR.absolute(), OUTPUT_DIR
    )
except Exception as e:
    print(e)

# indent the generated file using autopep8
print("Autopepping the generated orchestrator..")
os.system(f"autopep8 --in-place {ORCHESTRATOR_FILEPATH}")
