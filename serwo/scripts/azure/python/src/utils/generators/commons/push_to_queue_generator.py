from jinja2 import Environment, FileSystemLoader
from python.src.utils.classes.aws.trigger_types import TriggerType


class AWSSfnYamlGeneratorExeception(Exception):
    """Custom exception class raised on any error during yaml generation"""

    def __init__(self, message: str):
        self._message = message
        super().__init__(self._message)


def get_template_file(trigger_type):
    template_file_map = {
        TriggerType.AWS_API_GATEWAY: "apigw-awsstepfunctions.yaml",
        TriggerType.AWS_SQS: "sqs-awsstepfunctions.yaml",
    }
    return template_file_map.get(trigger_type)


def generate_sfn_yaml(
    function_params: list,
    statemachine_params: dict,
    function_object_map: dict,
    template_dir: str,
    output_dir: str,
    yaml_file: str,
    trigger_type: TriggerType,
) -> None:
    # function resource strings
    arns = []
    for function in function_params:
        try:
            arnName = function_object_map[function["name"]].get_arn()
            arnRef = function_object_map[function["name"]].get_ref()
            arn = {"name": arnName, "ref": arnRef}
            arns.append(arn)
        except:
            raise AWSSfnYamlGeneratorExeception("Invalid function params error")

    # statemachine json url (this would be coming in post build ?)
    try:
        uri = statemachine_params["uri"]
        print(f"Uri for statemachine - {uri}")
    except:
        raise AWSSfnYamlGeneratorExeception(
            "KeyError: Invalid 'uri' key in statemachine parameters"
        )

    # statemachine related template keys
    try:
        stepfunctionname = statemachine_params["name"]
        stepfunctionarn = statemachine_params["arn"]
        stefunctionarn_attribute = statemachine_params["arn_attribute"]
        stepfunctionrole = statemachine_params["role"]
        stepfunctionrolearn = statemachine_params["role_arn"]
        stepfunctionrolearn_attribute = statemachine_params["role_arn_attribute"]
        apifilename = statemachine_params["api_file"]

        print(
            f"Generated statemachine parameters.. TODO: - <print the parameters here>"
        )
    except:
        raise AWSSfnYamlGeneratorExeception(
            "KeyError: 'name' key in statemachine parameters"
        )

    # generating templates
    try:
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader)
        template = env.get_template(get_template_file(trigger_type))
        print(f"Created jinja2 environment")
    except:
        raise AWSSfnYamlGeneratorExeception(
            "Error in loading jinja template environment"
        )

    # render function
    try:
        output = template.render(
            serwouri=uri,
            functions=function_params,
            arns=arns,
            policies=function_params,
            stepfunctionname=stepfunctionname,
            stepfunctionarn=stepfunctionarn,
            stepfunctionsarnatrribute=stefunctionarn_attribute,
            stepfunctionrole=stepfunctionrole,
            stepfunctionrolearn=stepfunctionrolearn,
            stepfunctionrolearn_attribute=stepfunctionrolearn_attribute,
            apifilename=apifilename,
        )
    except:
        raise AWSSfnYamlGeneratorExeception("Error in jinja template render function")

    try:
        # flush out the generator yaml
        with open(f"{output_dir}/{yaml_file}", "w") as _sfn_yaml:
            _sfn_yaml.write(output)
            print(f"Writing YAML to directory")
    except:
        raise AWSSfnYamlGeneratorExeception("Error in writing to template file")
