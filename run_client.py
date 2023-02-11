import json
import argparse
import subprocess

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')
parser.add_argument('-e', '--exp-name')
args = parser.parse_args()


# print(args)
file_name = f"serwo/examples/{args.exp_name}/build/workflow/resources/deployment-structure.json"
print(file_name)
f = open(file_name, "r")
entry_csp = json.load(f)["entry_csp"].lower()
f.close()

if entry_csp == "aws":
    file_name = "serwo/python/src/jmx-templates/aws/template.jmx"
    f = open(file_name, "r")
    template = f.read()
    f.close()
    resources_file_name = f"serwo/examples/{args.exp_name}/build/workflow/resources/aws-cloudformation-outputs.json"
    f = open(resources_file_name, "r")
    resources = json.load(f)
    f.close()
    for json_object in resources:
        if "AWSArn" in json_object["OutputKey"]:
            template = template.replace("{{statemachinearn}}", json_object["OutputValue"])
        if "ExecuteApi" in json_object["OutputKey"]:
            template = template.replace("{{execurl}}", json_object["OutputValue"]+"/execute")
    resources_file_name = f"serwo/examples/{args.exp_name}/build/workflow/resources/provenance-artifacts.json"
    f = open(resources_file_name, "r")
    resources = json.load(f)
    f.close()
    template = template.replace("{{workflowdeploymentid}}", resources["deployment_id"])
elif entry_csp == "azure":
    file_name = f"serwo/python/src/jmx-templates/azure/template.jmx"
    f = open(file_name, "r")
    template = f.read()
    f.close()
    resources_file_name = f"serwo/examples/{args.exp_name}/build/workflow/resources/provenance-artifacts.json"
    f = open(resources_file_name, "r")
    resources = json.load(f)
    f.close()
    template = template.replace("{{workflowdeploymentid}}", resources["deployment_id"])

    resources_file_name = f"serwo/examples/{args.exp_name}/build/workflow/resources/azure_resources.json"
    f = open(resources_file_name, "r")
    resources = json.load(f)
    f.close()
    template = template.replace("{{execurl}}", f'https://{resources["app_name"]}.azurewebsites.net/api/orchestrators/Orchestrate')
else:
    print("Incorrect CSP")
    exit(1)

f = open(f"serwo/examples/{args.exp_name}/build/workflow/resources/jmx_client.jmx", "w")
f.write(template)
f.close()
subprocess.run([f"jmeter -n -t serwo/examples/{args.exp_name}/build/workflow/resources/jmx_client.jmx -l smart-grid-singlecloud-azure.jtl"], shell=True)
