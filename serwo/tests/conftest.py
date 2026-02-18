
import pytest
import shutil
import time
from pathlib import Path
from tests.harness import (
    get_example_dir,
    deploy_example,
    parse_partition_config,
    get_example,
    aws_teardown,
    azure_teardown,
    list_examples,
    create_user_pinned_nodes
)

def pytest_addoption(parser):
    """Add command line options."""
    parser.addoption(
        "--example", 
        action="store", 
        default="all", 
        help="Name of the example to test, or 'all' to test all in registry"
    )
    parser.addoption(
        "--skip-deploy", 
        action="store_true", 
        default=False, 
        help="Skip deployment if resources already exist"
    )
    parser.addoption(
        "--keep-resources", 
        action="store_true", 
        default=False, 
        help="Do not tear down resources after test (default: cleanup after test)"
    )

def pytest_generate_tests(metafunc):
    """Parametrize 'example_name' based on registry or CLI option."""
    if "example_name" in metafunc.fixturenames:
        example_opt = metafunc.config.getoption("--example")
        if example_opt == "all":
            examples = list_examples()
        else:
            examples = [example_opt]
        metafunc.parametrize("example_name", examples, scope="class")

@pytest.fixture(scope="class")
def deployed_workflow(request, example_name):
    """
    Fixture that deploys the workflow and yields configuration.
    Parametrized by example_name.
    """
    skip_deploy = request.config.getoption("--skip-deploy")
    keep_resources = request.config.getoption("--keep-resources")
    
    example_config = get_example(example_name)
    if not example_config:
        pytest.fail(f"Example '{example_name}' not found in registry")
        
    example_dir = get_example_dir(example_name)
    
    # 1. Deployment
    if not skip_deploy:
        print(f"\n[Fixture] Deploying {example_name}...")
        
        # Deploy to all defined CSPs
        for run_config in example_config.get("runs", []):
            csp = run_config["csp"]
            region = run_config["region"]
            pin = run_config.get("pin", -1)
            if pin != -1:
                user_pinned_nodes = create_user_pinned_nodes(example_name, pin)
                print(str(user_pinned_nodes))
                success, error = deploy_example(example_name, csp, region, user_pinned_nodes)
            else:
                success, error = deploy_example(example_name, csp, region)
            if not success:
                pytest.fail(f"Deployment failed for {csp} in {region}: {error}")
    else:
        print(f"\n[Fixture] Skipping deployment for {example_name}...")
    
    # 2. Parse Partition Config
    # We wait a moment to ensure file writes are flushed if we just deployed
    if not skip_deploy:
        time.sleep(2)
        
    config = parse_partition_config(example_dir)
    if not config:
        pytest.fail(f"Could not find valid partition config in {example_dir}")
        
    # Yield both the config and the example directory path
    yield {
        "example_path": example_dir,
        "config": config,
        "payload": example_config.get("payload")
    }
    
    # 3. Teardown - Default is to cleanup
    if keep_resources:
        print(f"\n[Fixture] Keeping resources (--keep-resources flag set)")
        return
        
    print(f"\n[Fixture] Teardown: Cleaning up cloud resources and partition files...")
    
    for partition in config.get_all_partitions():
        resources_path = partition.get_resources_path(example_dir)
        partition_dir = example_dir / "partitions" / f"{partition.csp}-{partition.region}-{partition.part_id}"
        
        # Delete cloud resources
        if "aws" in partition.csp.lower():
            print(f"[Teardown] Deleting AWS resources for partition {partition.part_id}...")
            aws_teardown(resources_path, wait=False)
        else:
            print(f"[Teardown] Deleting Azure resources for partition {partition.part_id}...")
            azure_teardown(resources_path, wait=False)
        
        # Delete local partition directory
        if partition_dir.exists():
            print(f"[Teardown] Removing partition directory: {partition_dir}")
            try:
                shutil.rmtree(partition_dir)
            except Exception as e:
                print(f"[Teardown] Warning: Could not remove directory: {e}")
    
    # Also remove part-details.json
    part_details_path = example_dir / "partitions" / "part-details.json"
    if part_details_path.exists():
        print(f"[Teardown] Removing part-details.json")
        try:
            part_details_path.unlink()
        except Exception as e:
            print(f"[Teardown] Warning: Could not remove part-details.json: {e}")
    
    print(f"[Teardown] Cleanup complete for {example_name}")
