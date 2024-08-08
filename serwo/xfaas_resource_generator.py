from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP
import json
from jinja2 import Environment, FileSystemLoader
from botocore.exceptions import ClientError
import os

def generate(user_dir, partition_config, dag_definition_file):
    partition_config = list(reversed(partition_config))

    for i in range(len(partition_config)):
        if i==0:
            csp = partition_config[i].get_left_csp().get_name()
            region = partition_config[i].get_region()
            part_id = partition_config[i].get_part_id()
            print(f"Building resources for {csp} in {region} with part_id {part_id}")
            csp_temp = csp.split('_')
            csp = csp_temp[0]
            if len(csp_temp) > 1:
                is_netherite = True
            else:
                is_netherite = False
            updated_user_dir = f"{user_dir}/partitions/{csp}-{region}-{part_id}"
            dag_definition_path = f"{updated_user_dir}/{dag_definition_file}"
            
        else:
            downstream_csp = partition_config[i-1].get_left_csp().get_name()
            downstream_region = partition_config[i-1].get_region()
            downstream_part_id = partition_config[i-1].get_part_id()
            function_name_partition = partition_config[i].get_function_name()
            resources_dir = f"{user_dir}/partitions/{downstream_csp}-{downstream_region}-{downstream_part_id}/build/workflow/resources"
            resources_fname = f"{downstream_csp}-{downstream_region}-{downstream_part_id}.json"
            directory = f"{resources_dir}/{resources_fname}"
            dag_from_file = None
            csp = partition_config[i].get_left_csp().get_name()
            region = partition_config[i].get_region()
            part_id = partition_config[i].get_part_id()
            updated_user_dir = f"{user_dir}/partitions/{csp}-{region}-{part_id}"
            dag_path = f"{updated_user_dir}/{dag_definition_file}" 

            with open(dag_path, "r") as dag_file:
                dag_from_file = json.load(dag_file)

            if downstream_csp == "aws":
                function_id = "252"
                function_name = "PushToSQS"
                entry_point = "push_to_aws_q.py"
                src = f"{updated_user_dir}/PushToSQS"
                with open(directory, "r") as file:
                    resources = json.load(file)
                for resource in resources:
                    if resource["OutputKey"] == "SQSResource":
                        queue_url = resource["OutputValue"]
                root_dir = os.path.dirname(os.path.abspath(__file__))
                creds_file  = f"{root_dir}/config/aws_creds.json"
                with open(creds_file, "r") as file:
                    aws_credentials = json.load(file)
                aws_access_key_id = aws_credentials["access_key_id"]
                aws_secret_access_key = aws_credentials["secret_access_key"]
                resources = {
                    "queue_url": queue_url,
                    "access_key_id": aws_access_key_id,
                    "secret_access_key": aws_secret_access_key,
                }
                
                template_dir = f"{root_dir}/python/src/faas-templates/aws/push-to-sqs-template/{function_name}"
                output_path = f"{updated_user_dir}/"
                os.system(f"cp -r {template_dir} {output_path}")
                template_push_to_queue(updated_user_dir, function_name, entry_point, resources, "aws")
            
            
            if downstream_csp == "azure":
                function_id = "251"
                function_name = "PushToStorageQueue"
                entry_point = "push_to_azure_q.py"
                src = f"{updated_user_dir}/PushToStorageQueue"
                with open(directory, "r") as file:
                    resources = json.load(file)
                queue_name = resources["queue_name"]
                connection_string = resources["connection_string"]
                resources = {
                    "queue_name": queue_name,
                    "connection_string": connection_string,
                }

                template_dir = f"{root_dir}/templates/azure/push-to-storage-queue-template/{function_name}"
                output_path = f"{updated_user_dir}/"
                os.system(f"cp -r {template_dir} {output_path}")
                template_push_to_queue(updated_user_dir, function_name, entry_point, resources, "azure")
            
            egress_node = {
                "NodeId": function_id,
                "NodeName": function_name,
                "EntryPoint": entry_point,
                "Path": src,
                "CSP": "NA",
                "MemoryInMB": 256,
            }
            dag_from_file["Nodes"].append(egress_node)
            dag_from_file["Edges"].append({
                f"{function_name_partition}" : [f"{function_name}"]
            })
            
            with open(dag_path, "w") as dag_file:
                json.dump(dag_from_file, dag_file, indent=4)
        
        CSP(csp).build_resources(updated_user_dir, dag_definition_path,region,part_id,dag_definition_file,is_netherite)


def template_push_to_queue(
    user_source_dir: str,
    egress_fn_name: str,
    egress_fn_entrypoint: str,
    resources: dict,
    csp:str
):
    template_dir = f"{user_source_dir}/{egress_fn_name}"
    try:
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader)
        template = env.get_template(egress_fn_entrypoint)
        print(f"Created jinja2 environment for PushToQueue templating")
    except:
        raise Exception("Unable to load environment for PushToQueue templating")

    # templating for azure
    if csp == "azure":
        queue_name = resources["queue_name"]
        connection_string = resources["connection_string"]
        try:
            output = template.render(
                queue_name=queue_name, connection_string=connection_string
            )
        except:
            raise Exception(f"Error in rendering {egress_fn_name} template")

        # flush out the generated template
        try:
            with open(f"{template_dir}/{egress_fn_entrypoint}", "w") as out:
                out.write(output)
                print(f"Updating PushToQueue funciton for {egress_fn_name}")
        except:
            raise Exception(f"Error in flushing {egress_fn_name} template")

    # templating for AWS
    if csp == "aws":
        queue_url = resources["queue_url"]

        try:
            access_key_id = resources["access_key_id"]
            secret_access_key = resources["secret_access_key"]
            output = template.render(
                queue_url=queue_url,
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
            )
        except:
            raise Exception(f"Error in rendering {egress_fn_name} template")

        # flush out the generated template
        try:
            with open(f"{template_dir}/{egress_fn_entrypoint}", "w") as out:
                out.write(output)
                print(f"Updaing PushToQueue funciton for {egress_fn_name}")
        except:
            raise Exception(f"Error in flushing {egress_fn_name} template")
