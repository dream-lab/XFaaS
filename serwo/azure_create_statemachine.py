# TODO - wrap this script in a module and use in the master build script
# Python base imports
import os
import sys
import pathlib

# serwo imports

from . import generate_orchestrator_file as AzureOrchestratorGenerator
from  python.src.utils.classes.azure.user_dag import UserDag as AzureUserDAG


def run(user_directory,user_dag_file_name):
    # user_directory = sys.argv[1]
    # user_dag_file_name  = sys.argv[2] # pass this out as flags
    python_template_dir = pathlib.Path.joinpath(pathlib.Path(__file__).parent.absolute(), "templates/azure").resolve()
    output_dir = f"{user_directory}"
    dag_definition_path = f"{user_directory}/{user_dag_file_name}"
    orchestrator_filepath = f"{user_directory}/orchestrator.py"

    # load the dag
    user_dag = AzureUserDAG(dag_definition_path)
    orchestrator_code = user_dag.get_orchestrator_code()

    # generate the orchestration function
    try:
        AzureOrchestratorGenerator.generate(orchestrator_code, python_template_dir.absolute(), output_dir)
    except Exception as e:
        print(e)

    # indent the generated file using autopep8
    os.system(f"autopep8 --in-place {orchestrator_filepath}")