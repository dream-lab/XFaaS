import pathlib
import json
from jinja2 import Environment, FileSystemLoader


class JMXGenerationExeception(Exception):
    "Custom exception class raised on any error during yaml generation"

    def __init__(self, message: str):
        self._message = message
        super().__init__(self._message)


def generate_jmx_files(
    workflow_name, workflow_deployment_id, user_dir, template_root_dir, csp
):
    template_dir = pathlib.Path.joinpath(pathlib.Path(template_root_dir), csp)
    template_file = "template.jmx"

    # get the url / arn from resources
    resources_dir = pathlib.Path.joinpath(
        pathlib.Path(user_dir), "build/workflow/resources"
    )
    resources_filename = (
        "azure_resources.json" if csp == "azure" else "aws-cloudformation-outputs.json"
    )

    try:
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader)
        template = env.get_template(template_file)
        print("JMXGen::Created Jinja Environment")
    except Exception as e:
        print("[ERROR]::jmx_generator.py::", e)
        raise JMXGenerationExeception("JMXGen::Error in loading jinja environment")

    with open(pathlib.Path.joinpath(resources_dir, resources_filename), "r") as f:
        contents = json.load(f)
        output = None
        if csp == "aws":
            url = None
            arn = None
            for item in contents:
                if item["OutputKey"] == "ExecuteApi":
                    url = item["OutputValue"] + "/execute"

            for item in contents:
                if item["OutputKey"] == f"{workflow_name}Arn":
                    arn = item["OutputValue"]

            print("Here -- ")
            print("URL - ", url)
            print("ARN - ", arn)
            try:
                output = template.render(
                    workflowdeploymentid=workflow_deployment_id,
                    execurl=url,
                    statemachinearn=arn,
                )
            except Exception as e:
                print("[ERROR]::jmx_generator.py::", e)
                raise JMXGenerationExeception(
                    "JMXGen::Error in rendering Jinja Template AWS Branch"
                )

        if csp == "azure":
            app_name = contents["app_name"]
            url = f"https://{app_name}.azurewebsites.net/api/orchestrators/Orchestrate"

            try:
                output = template.render(
                    workflowdeploymentid=workflow_deployment_id, execurl=url
                )
            except Exception as e:
                print("[ERROR]::jmx_generator.py::", e)
                raise JMXGenerationExeception(
                    "JMXGen::Error in rendering Jinja Template Azure Branch"
                )

        # flush output to resources
        try:
            with open(
                pathlib.Path.joinpath(resources_dir, "jmx_client.jmx"), "w+"
            ) as out:
                out.write(output)
                print(f"JMXGen::Writing JMX to {resources_dir}")
        except Exception as e:
            print("[ERROR]::jmx_generator.py::", e)
            raise JMXGenerationExeception(
                f"JMXGen::Error in writing output to directory {resources_dir}"
            )
