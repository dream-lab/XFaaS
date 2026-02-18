
import pytest
from tests.harness import (
    aws_check_deployment,
    azure_check_deployment,
    aws_get_resources,
    azure_get_resources,
    aws_invoke,
    aws_poll_status,
    azure_invoke,
    azure_poll_status,
)

class TestWorkflow:
    """
    Parametrized tests for XFaaS workflows.
    Uses 'deployed_workflow' fixture from conftest.py.
    """

    def test_deployment_resources_exist(self, deployed_workflow):
        """
        Verify that deployment generated resource files for all partitions.
        """
        example_path = deployed_workflow["example_path"]
        config = deployed_workflow["config"]
        
        for partition in config.get_all_partitions():
            resources_path = partition.get_resources_path(example_path)
            
            # Check file presence
            assert resources_path.exists(), \
                f"Resources JSON not found for partition {partition.part_id} ({partition.csp})"
            
            # Check content validity
            if "aws" in partition.csp.lower():
                assert aws_check_deployment(resources_path), \
                    f"AWS resources invalid for {partition.part_id}"
            else:
                assert azure_check_deployment(resources_path), \
                    f"Azure resources invalid for {partition.part_id}"

    def test_workflow_execution(self, deployed_workflow):
        """
        Invoke the workflow and verify successful execution.
        """
        example_path = deployed_workflow["example_path"]
        config = deployed_workflow["config"]
        payload = deployed_workflow["payload"]
        
        # Determine entry point (Start Partition)
        start_partition = config.get_start_partition()
        resources_path = start_partition.get_resources_path(example_path)
        
        print(f"Invoking workflow via {start_partition.csp} ({start_partition.region})...")
        
        final_status = "UNKNOWN"
        
        if "aws" in start_partition.csp.lower():
            # Invoke AWS
            execute_url, sm_arn = aws_get_resources(resources_path)
            assert execute_url and sm_arn, "Missing AWS connection details"
            
            response = aws_invoke(execute_url, sm_arn, payload=payload)
            execution_arn = response.get("executionArn")
            assert execution_arn, "Failed to start execution"
            
            print(f"Polling execute ARN: {execution_arn}")
            final_status = aws_poll_status(execution_arn)
            
        else:
            # Invoke Azure
            app_name = azure_get_resources(resources_path)
            assert app_name, "Missing Azure app name"
            
            response = azure_invoke(app_name, payload=payload)
            status_url = response.get("statusQueryGetUri")
            assert status_url, "Failed to start orchestration"
            
            print(f"Polling status URL: {status_url}")
            final_status = azure_poll_status(status_url)
            
        print(f"Final Execution Status: {final_status}")
        
        # success states
        assert final_status in ["SUCCEEDED", "Completed"], \
            f"Workflow did not succeed. Status: {final_status}"
