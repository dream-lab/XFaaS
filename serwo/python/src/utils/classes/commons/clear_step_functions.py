import boto3
import re

# Set your pattern here
PATTERN = r'^Serwo-Execute-API' 
# PATTERN = r'UserWf.*'
# PATTERN = r'Serwo-.*'
# Initialize clients
apigateway_client = boto3.client('apigateway')
stepfunctions_client = boto3.client('stepfunctions')


def delete_api_gateways(pattern):
    print("Checking API Gateways...")
    apis = apigateway_client.get_rest_apis()['items']
    for api in apis:
        name = api['name']
        
        if re.match(pattern, name):
            print(f'name === {name}, vkrules')
            print(f"Deleting API Gateway: {name} (ID: {api['id']})")
            apigateway_client.delete_rest_api(restApiId=api['id'])


def delete_step_functions(pattern):
    print("Checking Step Functions...")
    response = stepfunctions_client.list_state_machines()
    
    for sm in response['stateMachines']:
        name = sm['name']
        print(f'name === {name}, vkrules')
        if re.match(pattern, name):
            print(f"Deleting Step Function: {name} (ARN: {sm['stateMachineArn']})")
            stepfunctions_client.delete_state_machine(stateMachineArn=sm['stateMachineArn'])


if __name__ == '__main__':
    delete_api_gateways(PATTERN)
    # delete_step_functions(PATTERN)
