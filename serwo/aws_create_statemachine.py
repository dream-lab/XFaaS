# TODO - wrap this script in a module and use in the master build script
# Python base imports

# TODO - make this more functional
import os
import sys
import pathlib

# Serwo imports
import python.src.utils.generators.aws.sfn_yaml_generator as AWSSfnYamlGenerator
import python.src.utils.generators.aws.sfn_asl_generator as AWSSfnAslBuilder
from python.src.utils.classes.aws.user_dag import UserDag as AWSUserDag
from python.src.utils.classes.aws.trigger_types import TriggerType
from jinja2 import Environment, FileSystemLoader

# TODO - take these user inputs as flags
REGION = "ap-south-1"
USER_DIR = sys.argv[1]
DAG_DEFINITION_FILE = sys.argv[2]  # pass this out as flags
TRIGGER_TYPE = TriggerType.get_trigger_type(sys.argv[3])


# NOTE -directores and filenames that are script generated
# TODO - check if sam-build directory creates problems with existing files (it doesn't, just adds files/folders to the specified directory)
PARENT_DIRECTORY_PATH = pathlib.Path(__file__).parent
SERWO_BUILD_DIR = f"{USER_DIR}/build/workflow"
SERWO_RESOURCES_DIR = f"{SERWO_BUILD_DIR}/resources"
RUNNER_TEMPLATE_DIR = pathlib.Path.joinpath(
    PARENT_DIRECTORY_PATH, "python/src/runner-templates/aws"
)
YAML_TEMPLATE_DIR = pathlib.Path.joinpath(
    PARENT_DIRECTORY_PATH, "python/src/faas-templates/aws/yaml-templates"
)
AWS_BUILD_DIR = f"{SERWO_BUILD_DIR}/aws"
SERWO_FUNCTION_BUILD_DIR = f"{AWS_BUILD_DIR}/functions"
SAM_BUILD_DIR = f"{AWS_BUILD_DIR}/sam-build"
YAML_FILE = "template.yaml"
JSON_FILE = "statemachine.asl.json"
DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
SERWO_UTILS_DIR = os.path.join(PARENT_DIRECTORY_PATH, "python")
OUTPUTS_FILEPATH = f"{SERWO_RESOURCES_DIR}/aws-cloudformation-outputs.json"

CREATE_ENVIRONMENT_SCRIPT = (
    pathlib.Path.joinpath(PARENT_DIRECTORY_PATH, "scripts/bash/aws/create_env.sh")
    .absolute()
    .resolve()
)
CREATE_LAMBDA_FUNCTION_SCRIPT = (
    pathlib.Path.joinpath(PARENT_DIRECTORY_PATH, "scripts/bash/aws/create_lambda_fn.sh")
    .absolute()
    .resolve()
)
DEPLOY_STEPFUNCTION_SCRIPT = (
    pathlib.Path.joinpath(PARENT_DIRECTORY_PATH, "scripts/bash/aws/deploy_sfn.sh")
    .absolute()
    .resolve()
)


def get_statemachine_params(name):
    params = {
        "name": statemachinename,
        "uri": JSON_FILE,
        "arn": statemachinename + "Arn",
        "role": statemachinename + "Role",
        "role_arn": statemachinename + "RoleArn",
        "arn_attribute": statemachinename + ".Arn",
        "api_file": "api.yaml",
    }

    role_arn_attribute = params["role"] + ".Arn"
    params["role_arn_attribute"] = role_arn_attribute
    return params


def template_function_id(runner_template_dir, function_id, function_name):
    runner_template_filename = f"runner_template_{function_id}.py"
    try:
        file_loader = FileSystemLoader(runner_template_dir)
        env = Environment(loader=file_loader)
        template = env.get_template("runner_template.py")
        print(
            f"Created jinja2 environement for templating AWS function ids for function::{function_name}"
        )
    except:
        raise Exception(
            f"Unable to load environment for AWS function id templating for function::{function_name}"
        )

    # render the template
    try:
        output = template.render(function_id_placeholder=function_id)
        with open(f"{runner_template_dir}/{runner_template_filename}", "w") as out:
            out.write(output)
            print(
                f"Rendered and flushed the runner template for AWS function for function::{function_name}"
            )
    except Exception as e:
        print(e)
        raise Exception(
            f"Unable to render the function runner template for AWS function for function::{function_name}"
        )

    return runner_template_filename


# build user dag
# TODO - filtering and subdag parsing based on CSP is required here ?
print(DAG_DEFINITION_PATH)
aws_user_dag = AWSUserDag(DAG_DEFINITION_PATH)
SAM_STACKNAME = "SerwoApp-" + aws_user_dag.get_user_dag_name()  # TODO - add nonce here

# get param list and node object map
function_metadata_list = aws_user_dag.get_node_param_list()
function_object_map = aws_user_dag.get_node_object_map()
statemachine_structure = aws_user_dag.get_statemachine_structure()

# take it from DAG file
# TODO - convention for sam-app-name and statemachine name (name + nonce - statemachine), (name + nonce - deployment)
statemachinename = aws_user_dag.get_user_dag_name()
statemachine = get_statemachine_params(statemachinename)

# create the build environment
os.system(f"{CREATE_ENVIRONMENT_SCRIPT} {AWS_BUILD_DIR}")


# create standalone runners for each function
for function_metadata in function_metadata_list:
    function_name = function_metadata["name"]
    function_runner_filename = function_object_map[
        function_metadata["name"]
    ].get_runner_filename()
    function_path = function_object_map[function_metadata["name"]].get_path()
    function_module_name = function_object_map[
        function_metadata["name"]
    ].get_module_name()
    function_id = function_object_map[function_metadata["name"]].get_id()

    # template the function runner template in the runner template directory
    runner_template_filename = template_function_id(
        runner_template_dir=RUNNER_TEMPLATE_DIR,
        function_id=function_id,
        function_name=function_name,
    )
    os.system(
        f"{CREATE_LAMBDA_FUNCTION_SCRIPT} {os.path.join(PARENT_DIRECTORY_PATH,function_path)} {AWS_BUILD_DIR} {function_name} {function_module_name} {function_runner_filename} {RUNNER_TEMPLATE_DIR} {SERWO_UTILS_DIR} {runner_template_filename}"
    )
    os.system(f"rm -r {RUNNER_TEMPLATE_DIR}/{runner_template_filename}")

# generate asl template
try:
    AWSSfnYamlGenerator.generate_sfn_yaml(
        function_metadata_list,
        statemachine,
        function_object_map,
        YAML_TEMPLATE_DIR,
        AWS_BUILD_DIR,
        YAML_FILE,
        TRIGGER_TYPE,
    )
except Exception as e:
    print(e)

# TODO [TK] - add validator for generated yaml
print("Building Statemachines JSON..")
AWSSfnAslBuilder.generate_statemachine_json(
    statemachine_structure, AWS_BUILD_DIR, JSON_FILE
)

print("Adding API specification to user directory")
os.system(
    f"cp {YAML_TEMPLATE_DIR}/execute-api-openapi.yaml {AWS_BUILD_DIR}/{statemachine['api_file']}"
)

print("Starting SAM deployment...Creating build directory")
os.system(f"mkdir -p {SAM_BUILD_DIR}")

print("Creating resource directory for AWS stack output")
os.system(f"mkdir -p {SERWO_RESOURCES_DIR}")

# print(f"{AWS_BUILD_DIR} {SAM_BUILD_DIR}  {SAM_STACKNAME} {REGION} {YAML_FILE}")
os.system(
    f"{DEPLOY_STEPFUNCTION_SCRIPT} {AWS_BUILD_DIR} {SAM_BUILD_DIR}  {SAM_STACKNAME} {REGION} {YAML_FILE}"
)

print(f"Writing SAM outputs to .. {OUTPUTS_FILEPATH}")
os.system(
    f'aws cloudformation describe-stacks --stack-name {SAM_STACKNAME} --query "Stacks[0].Outputs" --output json > {OUTPUTS_FILEPATH}'
)
