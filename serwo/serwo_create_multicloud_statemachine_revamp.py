import os
import os.path
import sys
import json
import pathlib
import networkx as nx
import uuid
import python.src.utils.generators.commons.jmx_generator as JMXGenerator
from distutils.dir_util import copy_tree
from python.src.utils.classes.commons.serwo_user_dag import SerWOUserDag
from python.src.utils.classes.commons.csp import CSP
from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
from aws_create_statemachine import AWS
from jinja2 import Environment, FileSystemLoader
from botocore.exceptions import ClientError
import datetime

# Dummy function for partition point


def get_partition_points():
    # filepaths for the partiiton configuraitons
    filepath1 = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/test-deploy-3/xfaas_post_op_dag_desc_p1.json"
    filepath2 = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/test-deploy-3/xfaas_post_op_dag_desc_p2.json"
    filepath3 = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/test-deploy-3/xfaas_post_op_dag_desc_p3.json"
    filepath4 = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/test-deploy-3/xfaas_post_op_dag_desc_p4.json"
    return [
        PartitionPoint("TaskB", 1, CSP.AWS, "p1", "ap-south-1", filepath1),
        PartitionPoint("TaskE", 1, CSP.AZURE, "p2", "centralindia", filepath2),
        PartitionPoint("TaskG", 1, CSP.AWS, "p3", "ap-east-1", filepath3),
        PartitionPoint("TaskI", 0, CSP.AWS, "p4", "us-west-1", filepath4)
    ]

def wire_partitions(user_dir):
    partition_points = get_partition_points()
    pp_pairs = list(zip(partition_points, partition_points[1:])).reverse()

    # Iterate over the point pairs in reverse orders
    for pair in pp_pairs:
        left_part_point = pair[0]
        right_part_point = pair[1]
        




"""
The function returns function_name, entry_point, template_path 
for a pair of CSPs in a partition point
"""
def get_egress_function_details(left_csp: CSP, right_csp: CSP, serwo_root_dir, partId):
    # here even for other clouds in addition we need all pairs
    # NOTE - this can be done only on the basis of the right CSP itself.
    # example - always wire using SQS if the right CSP is AWS

    # Placeholder comments - working code
    # if left_csp == CSP.AWS and right_csp == CSP.AZURE:
    #     function_id = "251"
    #     function_name = "PushToStorageQueue"
    #     entry_point = "push_to_azure_q.py"
    #     path = f"{serwo_root_dir}/python/src/faas-templates/azure/push-to-storage-queue-template/{function_name}"
    #     return function_id, function_name, entry_point, path
    # if left_csp == CSP.AZURE and right_csp == CSP.AWS:
    #     function_id = "252"
    #     function_name = "PushToSQS"
    #     entry_point = "push_to_aws_q.py"
    #     path = f"{serwo_root_dir}/python/src/faas-templates/aws/push-to-sqs-template/{function_name}"
    #     return function_id, function_name, entry_point, path

    # Modification (this can be done using a configuration file and applying a class based pattern as well)
    # makes the integration of a separate cloud easier as well.
    if right_csp == CSP.OPENFAAS:
        # TODO - add the egress function here for OpenFaaS
        # NOTE - add the partId in the egress function
        pass
    
    if right_csp == CSP.AZURE:
        function_id = f"251-{partId}"
        function_name = "PushToStorageQueue"
        entry_point = "push_to_azure_q.py"
        path = f"{serwo_root_dir}/python/src/faas-templates/azure/push-to-storage-queue-template/{function_name}"
        return function_id, function_name, entry_point, path
    
    if right_csp == CSP.AWS:
        function_id = f"252-{partId}"
        function_name = "PushToSQS"
        entry_point = "push_to_aws_q.py"
        path = f"{serwo_root_dir}/python/src/faas-templates/aws/push-to-sqs-template/{function_name}"
        return function_id, function_name, entry_point, path


def template_push_to_queue(
    user_source_dir: str,
    egress_fn_name: str,
    egress_fn_entrypoint: str,
    resource_dict: dict,
    aws_credentials=None,
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
    if resource_dict["filename"] == "azure_resources.json":
        with open(resource_dict["filepath"], "r") as fin:
            resources = json.load(fin)
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
    if resource_dict["filename"] == "aws-cloudformation-outputs.json":
        with open(resource_dict["filepath"], "r") as fin:
            resources = json.load(fin)
            queue_url = None
            for resource in resources:
                if resource["OutputKey"] == "SQSResource":
                    queue_url = resource["OutputValue"]

            if queue_url is None:
                raise Exception(f"Invalid File parsing for {resource_dict['filename']}")
            else:
                try:
                    access_key_id = aws_credentials["access_key_id"]
                    secret_access_key = aws_credentials["secret_access_key"]
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


def deploy_subdag(
    csp: CSP,
    user_dir: str,
    dag_definition_file: str,
    serwo_root_dir: str,
    resource_dict: dict,
    egress_fn_details: dict,
):
    user_source_dir = f"{user_dir}/src"
    credentials = None

    if csp == CSP.AWS:
        if egress_fn_details is None:
            # TODO - this should not be shell script anymore but a python function that returns a path to the output json
            aws_deployer = AWS(user_dir, dag_definition_file, "SQS")
            aws_deployer.build_resources()
            aws_deployer.build_workflow()
            aws_deployer.deploy_workflow()
            # os.system(
            #     f"python3 {serwo_root_dir}/aws_create_statemachine.py {user_dir} {dag_definition_file} SQS"
            # )
        else:
            try:
                template_push_to_queue(
                    user_source_dir=user_source_dir,
                    egress_fn_name=egress_fn_details["NodeName"],
                    egress_fn_entrypoint=egress_fn_details["EntryPoint"],
                    resource_dict=resource_dict,
                )
                # os.system(
                #     f"python3 {serwo_root_dir}/aws_create_statemachine.py {user_dir} {dag_definition_file} REST"
                # )
                aws_deployer = AWS(user_dir, dag_definition_file, "REST")
                aws_deployer.build_resources()
                aws_deployer.build_workflow()
                aws_deployer.deploy_workflow()
            except Exception as e:
                raise (e)

    if csp == CSP.AZURE:
        if egress_fn_details is not None:
            try:
                with open(f"{user_dir}/aws_credentials.json", "r") as f:
                    credentials = json.load(f)
                template_push_to_queue(
                    user_source_dir=user_source_dir,
                    egress_fn_name=egress_fn_details["NodeName"],
                    egress_fn_entrypoint=egress_fn_details["EntryPoint"],
                    resource_dict=resource_dict,
                    aws_credentials=credentials,
                )
            except Exception as e:
                raise (e)

        os.system(
            f"python3 {serwo_root_dir}/scripts/azure/azure_resource_creation.py {user_dir} {dag_definition_file}"
        )
        os.system(
            f"python3 {serwo_root_dir}/scripts/azure/azure_builder.py {user_dir} {dag_definition_file}"
        )
        os.system(
            f"python3 {serwo_root_dir}/scripts/azure/azure_deploy.py {user_dir} {dag_definition_file}"
        )


def add_forward_node_in_userdir(
    partition_point: PartitionPoint, user_dir, serwo_root_dir
):
    partId = partition_point.get_part_id()
    forward_fn_template_path = (
        f"{serwo_root_dir}/python/src/faas-templates/commons/ForwardFunction"
    )
    user_source_dir = f"{user_dir}/src"
    os.system(f"cp -r {forward_fn_template_path} {user_source_dir}")
    return dict(
        NodeId=f"250-{partId}",
        NodeName="ForwardFunction",
        EntryPoint="func.py",
        Path=f"{user_source_dir}/ForwardFunction",
    )


"""
function adds an egress function to the user directory

@returns
The function returns the details of the egress function - name, entrypoint 
TODO - fixate on the memory requirements for the egress function (minimum or default)
"""


def add_egress_node_in_userdir(
    partition_point: PartitionPoint, user_dir, serwo_root_dir,
    left_csp, right_csp
):
    left_csp = partition_point.get_left_csp()
    right_csp = partition_point.get_right_csp()
    partId = partition_point.get_part_id()
    (
        egress_fn_id,
        egress_fn_name,
        egress_fn_entrypoint,
        egress_fn_template_path,
    ) = get_egress_function_details(
        left_csp=left_csp, right_csp=right_csp, serwo_root_dir=serwo_root_dir, partId=partId
    )

    # TODO - parameterise the user source directory
    user_source_dir = f"{user_dir}/src"
    # TODO - apply try catch here later

    # add the function to the user directory
    os.system(f"cp -r {egress_fn_template_path} {user_source_dir}")
    return dict(
        NodeId=egress_fn_id,
        NodeName=egress_fn_name,
        EntryPoint=egress_fn_entrypoint,
        Path=f"{user_source_dir}/{egress_fn_name}",
    )


# TODO - change the edge structure to the node Id
def create_dag_description(
    workflow_owner: str,
    workflow_id: str,
    workflow_version: str,
    package_url: str,
    workflow_name: str,
    graph: nx.DiGraph,
    csp: CSP,
    output_dir: str,
    wf_description: str,
):
    # base skeleton of the output json
    output_dict = dict(WorkflowName=workflow_name)

    output_dict["wf_owner"] = workflow_owner
    output_dict["wf_id"] = workflow_id
    output_dict["wf_version"] = workflow_version
    output_dict["packageUrl"] = package_url
    output_dict["WorkflowDescription"] = wf_description
    output_dict["Nodes"] = []
    output_dict["Edges"] = []

    # populate the node list
    for node in graph.nodes:
        # node items
        print("Inside create DAG description")
        print("NodeName", graph.nodes[node]["NodeName"])
        csp_string = CSP.toString(csp)
        node_item = dict(
            NodeId=graph.nodes[node]["NodeId"],
            NodeName=graph.nodes[node]["NodeName"],
            Path=graph.nodes[node]["Path"],
            EntryPoint=graph.nodes[node]["EntryPoint"],
            MemoryInMB=graph.nodes[node]["MemoryInMB"],
            CSP=csp_string,
        )

        # edge items
        node_successors = list(graph.successors(node))
        edge_item_value = []

        # NOTE -  [TK] -  changed the edge item key to the nodeId than the node Name
        if node_successors:
            edge_item_key = graph.nodes[node]["NodeName"]
            # edge_item_key = graph.nodes[node]['NodeId']
            # iterate over all successors of the node and add the nodename
            for succnode in node_successors:
                edge_item_value.append(graph.nodes[succnode]["NodeName"])
                # edge_item_value.append(graph.nodes[succnode]['NodeId'])
            edge_item = {edge_item_key: edge_item_value}
            # append the edge dict
            output_dict["Edges"].append(edge_item)

        # append the node dict
        output_dict["Nodes"].append(node_item)

    # write to output file
    output_dag_description_filename = f"serwo-{csp_string}-dag-description.json"
    output_dag_description_filepath = f"{output_dir}/{output_dag_description_filename}"
    with open(output_dag_description_filepath, "w") as outfile:
        print(f"Writing json to directory {output_dag_description_filepath}")
        json.dump(output_dict, outfile, indent=4)

    return output_dag_description_filename


def get_resources_dict(csp: CSP, resources_dir: str):
    if csp == CSP.AWS:
        filename = "aws-cloudformation-outputs.json"
        return dict(filename=filename, filepath=f"{resources_dir}/{filename}")
    if csp == CSP.AZURE:
        filename = "azure_resources.json"
        return dict(filename=filename, filepath=f"{resources_dir}/{filename}")


def get_user_pinned_nodes(dag_path):
    return


def add_collect_logs_function(dag_path, G):
    out_path = "python/src/utils/CollectLogDirectories"

    node_name = "CollectLogs"
    collect_dir = out_path + "/" + node_name
    fnc_src = f"{USER_DIR}/src"

    dest = fnc_src + "/" + node_name

    copy_tree(collect_dir, dest)
    dagg = json.loads(open(f"{USER_DIR}/{dag_path}", "r").read())
    collect = dict()
    xd = list(nx.topological_sort(G))
    ind = len(xd) - 1
    max_id = int(xd[ind])
    print(max_id)
    node_name_max = ""
    for nd in dagg["Nodes"]:
        if int(nd["NodeId"]) == max_id:
            node_name_max = nd["NodeName"]

    edge = {node_name_max: [node_name]}

    collect["NodeId"] = "256"
    collect["NodeName"] = node_name
    collect["Path"] = fnc_src + "/" + node_name
    collect["EntryPoint"] = "func.py"
    collect["CSP"] = "AWS"
    collect["MemoryInMB"] = 256
    dagg["Nodes"].append(collect)
    dagg["Edges"].append(edge)
    outt = open(f"{USER_DIR}/{dag_path}", "w")
    outt.write(json.dumps(dagg))
    outt.close()
    ##copy collect logs from archive

    ##add to user dag description json and rewrite to same json


def push_user_dag_to_provenance(wf_id):
    global dynPartiQLWrapper, e
    # convert this to an api call
    print(":" * 80)
    print(f"Pushing workflow configuration to Dynamo DB")
    try:
        # print(f"{USER_DIR}/{DAG_DEFINITION_FILE}")
        f = f"{USER_DIR}/{DAG_DEFINITION_FILE}"
        js = open(f, "r").read()
        user_workflow_item = json.loads(js)

        user_workflow_item["wf_id"] = wf_id

        dynPartiQLWrapper = PartiQLWrapper("workflow_user_table")
        dynPartiQLWrapper.put(user_workflow_item)
    except ClientError as e:
        print(e)
    print(":" * 80)


def generate_refactored_workflow(left, right, user_dir, refactored_wf_id, wf_id):
    lpath = f"{user_dir}/{left}"
    rpath = f"{user_dir}/{right}"
    js_left = json.loads(open(lpath, "r").read())
    js_right = json.loads(open(rpath, "r").read())
    lp = []
    rp = []

    for nd in js_left["Nodes"]:
        lp.append(nd["NodeId"])
    for nd in js_right["Nodes"]:
        rp.append(nd["NodeId"])

    final_nodes = js_left["Nodes"] + js_right["Nodes"]
    final_edges = js_left["Edges"] + js_right["Edges"]
    js_left["Nodes"] = final_nodes
    js_left["Edges"] = final_edges
    js_left["wf_fusion_config"] = ""
    js_left["wf_id"] = wf_id
    js_left["refactored_wf_id"] = refactored_wf_id
    if "aws" in left:
        left_dc = "aws"
        right_dc = "azure"
    else:
        left_dc = "azure"
        right_dc = "aws"

    fin_parts = [
        {"partition_label": left_dc, "function_ids": lp},
        {"partition_label": right_dc, "function_ids": rp},
    ]

    js_left["wf_partitions"] = fin_parts

    js_left["refactoring_strategy"] = "Partitioning"

    try:
        # TODO - create table for refactored wf
        dynPartiQLWrapper = PartiQLWrapper("workflow_refactored_table")
        dynPartiQLWrapper.put(js_left)
    except ClientError as e:
        print(e)


def generate_deployment_logs(left, right, user_dir, wf_id, refactored_wf_id):
    workflow_deployment_id = str(uuid.uuid4())
    lpath = f"{user_dir}/{left}"
    rpath = f"{user_dir}/{right}"
    js_left = json.loads(open(lpath, "r").read())
    js_right = json.loads(open(rpath, "r").read())
    lp = []
    rp = []

    for nd in js_left["Nodes"]:
        lp.append(nd["NodeId"])
    for nd in js_right["Nodes"]:
        rp.append(nd["NodeId"])

    if "aws" in left:
        left_dc = "aws"
        right_dc = "azure"
    else:
        left_dc = "azure"
        right_dc = "aws"

    d = dict()
    d["wf_id"] = wf_id
    d["refactored_wf_id"] = refactored_wf_id
    d["wf_dc_config"] = {
        "aws": {"region": "ap-south-1", "csp": "AWS"},
        "azure": {"region": "Central India", "csp": "Azure"},
    }
    d["wf_deployment_name"] = "JPDC SMART GRID PARTITIONING"

    d["wf_deployment_id"] = workflow_deployment_id
    d["wf_deployment_time"] = str(datetime.datetime.now())

    a = dict()
    for nd in js_left["Nodes"]:
        a[nd["NodeId"]] = {"dc_config_id": left_dc, "resource_id": "", "endpoint": ""}

    for nd in js_right["Nodes"]:
        a[nd["NodeId"]] = {"dc_config_id": right_dc, "resource_id": "", "endpoint": ""}

    d["func_deployment_config"] = a

    try:
        dynPartiQLWrapper = PartiQLWrapper("workflow_deployment_table")
        dynPartiQLWrapper.put(d)
    except ClientError as e:
        print(e)

    return workflow_deployment_id


def evaluate_generic_partitioner():
    # global partition_point
    # fin_partition_points = []
    # partition_points_ = serwo_user_dag.get_best_partition(
    #     partition_points=all_valid_partition_points,
    #     num_parts=NUM_PARTS,
    #     dag_path=DAG_BENCHMARK_PATH,
    #     user_pinned_csp=user_pinned_csp,
    #     user_pinned_nodes=user_pinned_nodes,
    # )
    # for pp in partition_points_:
    #     fin_partition_points.append(get_partition_points(pp))
    # partition_point = partition_points_
    pass


if __name__ == "__main__":
    # generate_deployment_logs()
    wf_id = str(uuid.uuid4())

    USER_DIR = sys.argv[1]
    DAG_DEFINITION_FILE = sys.argv[2]
    NUM_PARTS = int(sys.argv[3])
    DAG_BENCHMARK_FILE = "dag-benchmark.json"

    PARENT_DIRECTORY = pathlib.Path(__file__).parent
    DAG_DEFINITION_PATH = f"{USER_DIR}/{DAG_DEFINITION_FILE}"

    # push_user_dag_to_provenance(wf_id)

    DAG_BENCHMARK_PATH = f"{USER_DIR}/{DAG_BENCHMARK_FILE}"
    SERWO_BUILD_DIR = f"{USER_DIR}/build/workflow"
    RESOURCES_DIR = f"{SERWO_BUILD_DIR}/resources"

    serwo_user_dag = SerWOUserDag(DAG_DEFINITION_PATH)

    all_valid_partition_points = serwo_user_dag.get_partition_points()
    user_pinned_nodes = get_user_pinned_nodes(DAG_DEFINITION_PATH)

    ## We allow only at max 2 partitions
    ##TODO: read from dag
    user_pinned_nodes = []
    user_pinned_csp = ""
    """
    NOTE - the member function in the serwo_user_dag contains the logic for generating 
    all the partition points in the main spine line of the graph
    """

    partition_points = get_partition_points()
    # get the details for the egress fn (new node) for a graph
    # QUESTION[TK] - are we supporting only a single partition point ?

    # we enumerate the partition points in reverse and start wiring and deploying 
    # the subdags and start connecting the 
    partition_point_pairs = list(zip(partition_points, partition_points[1:])).reverse()
    for idx, pp_pair in enumerate(partition_point_pairs):
        partition_point_left = pp_pair[0]
        partition_point_right = pp_pair[1]

        # Don't the addition of egress for the last partition since it ends there
        partition_xfaas_dag = SerWOUserDag(partition_point_right.get_dag_filepath()).get_dag()
        if idx > 0:
            egress_fn_details = add_egress_node_in_userdir(
                partition_point=partition_point_right,
                user_dir=USER_DIR,
                serwo_root_dir=PARENT_DIRECTORY,
                left_csp=partition_point_left.get_left_csp(),
                right_csp=partition_point_right.get_left_csp()
            )

            forward_fn_details = add_forward_node_in_userdir(
                partition_point=partition_point_right,
                user_dir=USER_DIR,
                serwo_root_dir=PARENT_DIRECTORY,
            )

            # generate the subgraphs
            subgraph = serwo_user_dag.get_partitioned_graph_v2(
                partition_point=partition_point_right,
                new_node_params=egress_fn_details,
                forward_function_params=forward_fn_details,
            )
            partition_xfaas_dag = subgraph

        # generate JSONs
        ff = json.loads((open(DAG_DEFINITION_PATH, "r").read()))
        print(ff)
        workflow_name = serwo_user_dag.get_workflow_name()
        wf_owner = "XfaasUSer"
        wf_version = "1.0"
        wf_description = "multicloud"
        print(f"Workflow Name - {workflow_name}")
        print(
            f"Generating json description for the left subgraph - CSP::{CSP.toString(partition_point.get_left_csp())}"
        )
        dag_description_filename_left = create_dag_description(
            workflow_owner=wf_owner,
            workflow_id=wf_id,
            workflow_version=wf_version,
            package_url="",
            workflow_name=workflow_name,
            graph=left_subgraph,
            csp=partition_point.get_left_csp(),
            output_dir=USER_DIR,
            wf_description=wf_description,
        )

        print(
            f"Generating json description for the right subgraph - CSP::{CSP.toString(partition_point.get_right_csp())}"
        )
        dag_description_filename_right = create_dag_description(
            workflow_owner=wf_owner,
            workflow_id=wf_id,
            workflow_version=wf_version,
            package_url="",
            workflow_name=workflow_name,
            graph=right_subgraph,
            csp=partition_point.get_right_csp(),
            output_dir=USER_DIR,
            wf_description=wf_description,
        )

        add_collect_logs_function(
            dag_description_filename_right, serwo_user_dag.get_dag()
        )
        refactored_wf_id = str(uuid.uuid4())
        generate_refactored_workflow(
            left=dag_description_filename_left,
            right=dag_description_filename_right,
            user_dir=USER_DIR,
            refactored_wf_id=refactored_wf_id,
            wf_id=wf_id,
        )

        wf_deployment_id = generate_deployment_logs(
            left=dag_description_filename_left,
            right=dag_description_filename_right,
            user_dir=USER_DIR,
            wf_id=wf_id,
            refactored_wf_id=refactored_wf_id,
        )
        """Give a partition point the deployment will first be for the right subdag and then for the left subdag"""
        print(
            f"Deploying for the right subgraph - CSP::{CSP.toString(partition_point.get_right_csp())}"
        )
        try:
            deploy_subdag(
                csp=partition_point.get_right_csp(),
                user_dir=USER_DIR,
                dag_definition_file=dag_description_filename_right,
                serwo_root_dir=PARENT_DIRECTORY,
                resource_dict=None,
                egress_fn_details=None,
            )
        except Exception as e:
            print(e)

        print(
            f"Deploying for the left subgraph - CSP::{CSP.toString(partition_point.get_left_csp())}"
        )
        try:
            deploy_subdag(
                csp=partition_point.get_left_csp(),
                user_dir=USER_DIR,
                dag_definition_file=dag_description_filename_left,
                serwo_root_dir=PARENT_DIRECTORY,
                resource_dict=get_resources_dict(
                    partition_point.get_right_csp(), resources_dir=RESOURCES_DIR
                ),
                egress_fn_details=egress_fn_details,
            )
        except Exception as e:
            print(e)

        # # generate JMX post deployment
        # try:
        #     JMXGenerator.generate_jmx_files(
        #         workflow_name=workflow_name,
        #         workflow_deployment_id=wf_deployment_id,
        #         user_dir=USER_DIR,
        #         template_root_dir="python/src/jmx-templates",
        #         csp=CSP.toString(partition_point.get_left_csp())
        #     )
        # except Exception as e:
        #     print(e)

        # resources dir
        # resources dir
        cwd = os.getcwd()
        user_dir = USER_DIR
        if "serwo" not in cwd:
            user_dir = f"serwo/{USER_DIR}"

        resources_dir = pathlib.Path.joinpath(
            pathlib.Path(user_dir), "build/workflow/resources"
        )
        # resources_dir=pathlib.Path.joinpath(pathlib.Path(USER_DIR), "build/workflow/resources")
        provenance_artifacts = {
            "workflow_id": wf_id,
            "refactored_workflow_id": refactored_wf_id,
            "deployment_id": wf_deployment_id,
        }

        print("::Provenance Artifacts::")
        print(provenance_artifacts)

        print("::Writing provenance artifacts output to JSON file::")
        json_output = json.dumps(provenance_artifacts, indent=4)
        with open(
            pathlib.Path.joinpath(resources_dir, "provenance-artifacts.json"), "w+"
        ) as out:
            out.write(json_output)

        print("::Adding deployment structure JSON::")
        deployment_structure = {
            "entry_csp": CSP.toString(partition_point.get_left_csp()).lower()
        }
        deployment_struct_json = json.dumps(deployment_structure, indent=4)
        with open(
            pathlib.Path.joinpath(resources_dir, "deployment-structure.json"), "w+"
        ) as out:
            out.write(deployment_struct_json)
