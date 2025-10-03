import boto3
import re
import time
from botocore.exceptions import ClientError

# Set your pattern here
PATTERN = r'^Serwo-Execute-API' 
# PATTERN = r'UserWf.*'
# PATTERN = r'Serwo-.*'
# Initialize clients
apigateway_client = boto3.client('apigateway')
stepfunctions_client = boto3.client('stepfunctions')


def delete_with_retry(client, operation, **kwargs):
    """Delete with exponential backoff retry for rate limiting"""
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return client.delete_rest_api(**kwargs)
        except ClientError as e:
            if e.response['Error']['Code'] == 'TooManyRequestsException':
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
            else:
                print(f"Error deleting: {e}")
                break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    print(f"Failed to delete after {max_retries} attempts")
    return None

def delete_api_gateways(pattern):
    print("Checking API Gateways...")
    apis = apigateway_client.get_rest_apis()['items']
    for api in apis:
        name = api['name']
        
        if re.match(pattern, name):
            print(f'name === {name}, vkrules')
            print(f"Deleting API Gateway: {name} (ID: {api['id']})")
            delete_with_retry(apigateway_client, 'delete_rest_api', restApiId=api['id'])
            time.sleep(0.5)  # Small delay between deletions


def delete_step_functions_with_retry(client, **kwargs):
    """Delete Step Function with exponential backoff retry for rate limiting"""
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return client.delete_state_machine(**kwargs)
        except ClientError as e:
            if e.response['Error']['Code'] == 'TooManyRequestsException':
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
            else:
                print(f"Error deleting: {e}")
                break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    print(f"Failed to delete after {max_retries} attempts")
    return None

def delete_step_functions(pattern):
    print("Checking Step Functions...")
    response = stepfunctions_client.list_state_machines()
    
    for sm in response['stateMachines']:
        name = sm['name']
        print(f'name === {name}, vkrules')
        if re.match(pattern, name):
            print(f"Deleting Step Function: {name} (ARN: {sm['stateMachineArn']})")
            delete_step_functions_with_retry(stepfunctions_client, stateMachineArn=sm['stateMachineArn'])
            time.sleep(0.5)  # Small delay between deletions


if __name__ == '__main__':
    print("Starting AWS cleanup with rate limiting...")
    delete_api_gateways(PATTERN)
    # delete_step_functions(PATTERN)
    print("Cleanup completed!")
