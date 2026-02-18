"""
XFaaS Test Harness - Example Loader

Loads test examples from registry.yaml and deploys via xfaas_main.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional
import json

# Add serwo to path for xfaas imports
SERWO_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SERWO_DIR))


def get_registry() -> dict:
    """Load registry.yaml from tests directory."""
    # tests/registry.yaml
    registry_path = Path(__file__).parent.parent / "registry.yaml"
    with open(registry_path) as f:
        return yaml.safe_load(f)


def get_example(name: str) -> Optional[dict]:
    """
    Get a specific example by name.
    
    Returns:
        {name, path, runs: [{csp, region}]} or None if not found
    """
    registry = get_registry()
    for example in registry.get("examples", []):
        if example["name"] == name:
            return example
    return None


def get_example_dir(name: str) -> Path:
    """
    Get absolute path to example directory.
    
    Resolves path relative to SERWO_DIR.
    """
    example = get_example(name)
    if not example:
        raise ValueError(f"Example '{name}' not found in registry")
        
    # registry path is relative to serwo root (e.g. examples/asyncTester)
    # SERWO_DIR is .../serwo
    return SERWO_DIR / example["path"]


def list_examples() -> list[str]:
    """List all registered example names."""
    registry = get_registry()
    return [ex["name"] for ex in registry.get("examples", [])]

def create_user_pinned_nodes(name: str, pin: int):
    """Create the user pinned nodes dict for the example"""
    example_dir = get_example_dir(name)
    dag_file = "dag.json"
    dag_file_path = example_dir / dag_file
    with open(dag_file_path) as f:
        dag = json.load(f)
    
    node_ids = [node["NodeId"] for node in dag["Nodes"]]
    user_pinned_nodes = {node_id: str(pin) for node_id in node_ids}
    return user_pinned_nodes


def deploy_example(name: str, csp: str, region: str, user_pinned_nodes: dict = None, pin: int = -1) -> bool:
    """
    Deploy an example workflow using XFaaS via subprocess.
    
    Uses subprocess to avoid conflicts with xfaas_main's module-level
    argument parsing when running under pytest.
    
    Args:
        name: Example name (folder in tests/examples/)
        csp: Cloud provider (aws, azure)
        region: Cloud region
        
    Returns:
        True if deployment succeeded, False otherwise
    """
    import subprocess
    
    example_dir = get_example_dir(name)
    dag_file = "dag.json"
    benchmark_file = "dag-benchmark.json"
    
    print(f"Deploying {name} to {csp} ({region})...")
    
    cmd = [
        sys.executable,
        str(SERWO_DIR / "xfaas_main.py"),
        "--wf-user-directory", str(example_dir),
        "--dag-file-name", dag_file,
        "--dag-benchmark", benchmark_file,
        "--csp", csp,
        "--region", region,
    ]

    if user_pinned_nodes is not None:
        cmd.append("--user-pinned-nodes")
        cmd.append(json.dumps(user_pinned_nodes))
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SERWO_DIR),
            capture_output=True,
            text=True,
            timeout=1200  # Increased to 20 minute timeout for deployment
        )
        
        if result.returncode != 0:
            print(f"Deployment failed with exit code {result.returncode}")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            return False, f"Exit code {result.returncode}"
            
        print(f"Deployment output:\n{result.stdout}")
        if result.stderr:
            print(f"Deployment warnings:\n{result.stderr}")
        print(f"Deployment complete for {name}")
        return True, "Success"
        
    except subprocess.TimeoutExpired as e:
        print(f"Deployment timed out after 1200 seconds")
        if e.stdout:
            print(f"STDOUT so far:\n{e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout}")
        if e.stderr:
            print(f"STDERR so far:\n{e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
        return False, "Timeout"
    except Exception as e:
        print(f"Deployment failed: {e}")
        return False, str(e)


def get_partition_details_path(name: str) -> Path:
    """Get path to part-details.json for an example."""
    return get_example_dir(name) / "partitions" / "part-details.json"
