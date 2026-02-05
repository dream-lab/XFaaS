"""
XFaaS Test Harness - Cloud Client Functions

6 client functions for AWS and Azure:
- Invocation: aws_invoke, azure_invoke
- Status polling: aws_poll_status, azure_poll_status
- Deployment checks: aws_check_deployment, azure_check_deployment
"""

import json
import time
import requests
from pathlib import Path
from typing import Optional
from .partition_parser import Partition


# ============================================================================
# AWS Client Functions
# ============================================================================

def aws_invoke(execute_url: str, state_machine_arn: str, payload: Optional[dict] = None) -> dict:
    """
    Invoke an AWS Step Functions workflow.
    
    Args:
        execute_url: API Gateway execute URL
        state_machine_arn: ARN of the state machine
        payload: Optional additional payload data
        
    Returns:
        Response JSON containing executionArn for status polling
    """
    url = f"{execute_url}/execute"
    
    input_data = {
        "workflow_instance_id": int(time.time() * 1000),
        "request_timestamp": int(time.time() * 1000),
        "deployment_id": "test",
        "session_id": "test_harness",
    }
    
    # Merge user payload at top level (not nested in "body")
    # The Lambda handler will wrap the entire input as "body" internally
    if payload:
        input_data.update(payload)
    
    body = {
        "stateMachineArn": state_machine_arn,
        "input": json.dumps(input_data)
    }
    
    response = requests.post(
        url,
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def aws_poll_status(execution_arn: str, timeout: int = 300, poll_interval: int = 5) -> str:
    """
    Poll AWS Step Functions execution until completion.
    
    Args:
        execution_arn: Execution ARN from invoke response
        timeout: Maximum seconds to wait
        poll_interval: Seconds between polls
        
    Returns:
        Final status: "SUCCEEDED", "FAILED", "TIMED_OUT", etc.
    """
    import boto3
    
    client = boto3.client("stepfunctions")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = client.describe_execution(executionArn=execution_arn)
        status = response["status"]
        
        if status in ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]:
            return status
        
        time.sleep(poll_interval)
    
    return "TIMEOUT"


def aws_check_deployment(resources_json_path: Path) -> bool:
    """
    Check if AWS deployment completed by verifying resources JSON.
    
    Args:
        resources_json_path: Path to AWS resources JSON file
        
    Returns:
        True if resources exist and contain expected keys
    """
    if not resources_json_path.exists():
        return False
    
    try:
        with open(resources_json_path) as f:
            resources = json.load(f)
        
        # Check for expected AWS resource keys
        has_execute_api = any(
            r.get("OutputKey") == "ExecuteApi" 
            for r in resources if isinstance(r, dict)
        )
        return has_execute_api or len(resources) > 0
    except (json.JSONDecodeError, KeyError):
        return False


def aws_get_resources(resources_json_path: Path) -> tuple[str, str]:
    """
    Extract execute URL and state machine ARN from AWS resources.
    
    Returns:
        (execute_url, state_machine_arn)
    """
    with open(resources_json_path) as f:
        resources = json.load(f)
    
    execute_url = ""
    state_machine_arn = ""
    
    for r in resources:
        if isinstance(r, dict):
            if r.get("OutputKey") == "ExecuteApi":
                execute_url = r.get("OutputValue", "")
            elif r.get("Description") == "Serwo CLI State machine ARN":
                state_machine_arn = r.get("OutputValue", "")
    
    return execute_url, state_machine_arn


# ============================================================================
# Azure Client Functions
# ============================================================================

def azure_invoke(app_name: str, payload: Optional[dict] = None) -> dict:
    """
    Invoke an Azure Durable Functions workflow.
    
    Args:
        app_name: Azure Function App name
        payload: Optional additional payload data
        
    Returns:
        Response JSON containing statusQueryGetUri for polling
    """
    url = f"https://{app_name}.azurewebsites.net/api/orchestrators/Orchestrate"
    
    body = {
        "workflow_instance_id": int(time.time() * 1000),
        "request_timestamp": int(time.time() * 1000),
        "deployment_id": "test",
        "session_id": "test_harness",
    }
    
    body = {
        "workflow_instance_id": int(time.time() * 1000),
        "request_timestamp": int(time.time() * 1000),
        "deployment_id": "test",
        "session_id": "test_harness",
        "body": payload if payload else {}
    }
    
    response = requests.post(
        url,
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def azure_poll_status(status_url: str, timeout: int = 300, poll_interval: int = 5) -> str:
    """
    Poll Azure Durable Functions status until completion.
    
    Args:
        status_url: statusQueryGetUri from invoke response
        timeout: Maximum seconds to wait
        poll_interval: Seconds between polls
        
    Returns:
        Final status: "Completed", "Failed", "Terminated", etc.
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(status_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        runtime_status = data.get("runtimeStatus", "")
        
        if runtime_status in ["Completed", "Failed", "Terminated", "Canceled"]:
            return runtime_status
        
        time.sleep(poll_interval)
    
    return "TIMEOUT"


def azure_check_deployment(resources_json_path: Path) -> bool:
    """
    Check if Azure deployment completed by verifying resources JSON.
    
    Args:
        resources_json_path: Path to Azure resources JSON file
        
    Returns:
        True if resources exist and contain expected keys
    """
    if not resources_json_path.exists():
        return False
    
    try:
        with open(resources_json_path) as f:
            resources = json.load(f)
        
        # Check for expected Azure resource keys
        return "app_name" in resources
    except (json.JSONDecodeError, KeyError):
        return False


def azure_get_resources(resources_json_path: Path) -> str:
    """
    Extract app name from Azure resources.
    
    Returns:
        app_name
    """
    with open(resources_json_path) as f:
        resources = json.load(f)
    
    return resources.get("app_name", "")


# ============================================================================
# Teardown/Cleanup Functions
# ============================================================================

def aws_teardown(resources_json_path: Path, wait: bool = False) -> bool:
    """
    Delete AWS CloudFormation/SAM stack.
    
    Args:
        resources_json_path: Path to AWS resources JSON file
        wait: If True, wait for deletion to complete
        
    Returns:
        True if deletion was initiated successfully
    """
    import subprocess
    
    if not resources_json_path.exists():
        print(f"[AWS Teardown] Resources file not found: {resources_json_path}")
        return False
    
    try:
        with open(resources_json_path) as f:
            resources = json.load(f)
        
        # Find the SAM stack name
        stack_name = None
        for r in resources:
            if isinstance(r, dict) and r.get("OutputKey") == "SAMStackName":
                stack_name = r.get("OutputValue")
                break
        
        if not stack_name:
            print("[AWS Teardown] Could not find SAMStackName in resources")
            return False
        
        # Extract region from the resources path (e.g., aws-ap-south-1-0000)
        # Default to ap-south-1 if cannot determine
        region = "ap-south-1"
        path_parts = resources_json_path.stem.split("-")
        if len(path_parts) >= 3:
            region = f"{path_parts[1]}-{path_parts[2]}-{path_parts[3]}"
        
        print(f"[AWS Teardown] Deleting stack: {stack_name} in {region}")
        
        # Delete the CloudFormation stack
        cmd = [
            "aws", "cloudformation", "delete-stack",
            "--stack-name", stack_name,
            "--region", region
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[AWS Teardown] Error: {result.stderr}")
            return False
        
        if wait:
            print(f"[AWS Teardown] Waiting for stack deletion...")
            wait_cmd = [
                "aws", "cloudformation", "wait", "stack-delete-complete",
                "--stack-name", stack_name,
                "--region", region
            ]
            subprocess.run(wait_cmd, capture_output=True, text=True)
        
        print(f"[AWS Teardown] Stack deletion initiated: {stack_name}")
        return True
        
    except Exception as e:
        print(f"[AWS Teardown] Error: {e}")
        return False


def azure_teardown(resources_json_path: Path, wait: bool = False) -> bool:
    """
    Delete Azure resource group.
    
    Args:
        resources_json_path: Path to Azure resources JSON file
        wait: If True, wait for deletion to complete (synchronous)
        
    Returns:
        True if deletion was initiated successfully
    """
    import subprocess
    
    if not resources_json_path.exists():
        print(f"[Azure Teardown] Resources file not found: {resources_json_path}")
        return False
    
    try:
        with open(resources_json_path) as f:
            resources = json.load(f)
        
        # Get the resource group name
        resource_group = resources.get("group")
        
        if not resource_group:
            print("[Azure Teardown] Could not find 'group' in resources")
            return False
        
        print(f"[Azure Teardown] Deleting resource group: {resource_group}")
        
        # Delete the resource group
        cmd = [
            "az", "group", "delete",
            "--name", resource_group,
            "--yes",  # Don't prompt for confirmation
        ]
        
        if not wait:
            cmd.append("--no-wait")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[Azure Teardown] Error: {result.stderr}")
            return False
        
        print(f"[Azure Teardown] Resource group deletion initiated: {resource_group}")
        return True
        
    except Exception as e:
        print(f"[Azure Teardown] Error: {e}")
        return False
