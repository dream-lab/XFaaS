from python.src.utils.provenance.partiql_dynamo_wrapper import PartiQLWrapper
import json
import uuid
from botocore.exceptions import ClientError


def push_user_dag(dag_definition_path):
    print(":" * 80)
    print(f"Pushing workflow configuration to Dynamo DB")
    workflow_name = ""
    try:
        wf_id = str(uuid.uuid4())
        js = open(dag_definition_path,'r').read()
        user_workflow_item = json.loads(js)
        user_workflow_item['wf_id'] = wf_id
        dynPartiQLWrapper = PartiQLWrapper('workflow_user_table')
        dynPartiQLWrapper.put(user_workflow_item)

    except Exception as e:
        print(e)

    print(":" * 80)

def push_refacored_user_dag(refactored_dag_definition_path, wf_id):

    refacored_wf_id = str(uuid.uuid4())

