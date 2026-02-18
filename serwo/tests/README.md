# XFaaS Test Harness

Automated testing framework for XFaaS multi-cloud workflows (AWS & Azure).

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests in the registry (parallelized)
pytest serwo/tests/test_workflow.py -n {<number of examples>} -v # Setting this manually works the best for now

# Run tests for a specific example (skip deployment if already exists)
pytest serwo/tests/test_workflow.py --example=graphAws --skip-deploy -v

# Run and keep cloud resources for inspection
pytest serwo/tests/test_workflow.py --example=asyncTester --keep-resources -v
```

## Command Line Options

| Flag | Default | Description |
|------|---------|-------------|
| `--example=NAME` | `asyncTester` | Name of the example to test (must exist in `registry.yaml`) |
| `--skip-deploy` | `False` | Skip deployment if resources already exist |
| `--keep-resources` | `False` | Do not tear down resources after test (default: cleanup) |

## Directory Structure

```
tests/
├── registry.yaml           # Central registry for test workflows
├── test_workflow.py        # Main test file (parametrized)
├── conftest.py             # Pytest fixtures (deployment, teardown)
└── harness/                # Core utility library
    ├── loader.py           # Handles example deployment logic
    ├── partition_parser.py # Parses part-details.json
    └── clients.py          # Cloud provider interaction logic
```

## Core Components

### 1. Loader (`harness/loader.py`)
- Reads `serwo/tests/registry.yaml` for workflow configurations.
- Resolves example paths relative to the project root.
- Executes `xfaas_main.py` via subprocess to deploy workflows.

### 2. Registry (`registry.yaml`)
Define your test cases here. The `path` should be relative to the `serwo/` root.

```yaml
examples:
  - name: asyncTester
    path: examples/asyncTester
    runs:
      - csp: aws
        region: ap-south-1
      - csp: azure
        region: centralindia

  - name: graphAws
    path: examples/graphAws
    payload:
      size: 10
      edges: 5
    runs:
      - csp: aws
        region: ap-south-1
```

### 3. Fixtures (`conftest.py`)
The `deployed_workflow` fixture manages the complete test lifecycle:
1. **Setup**: Deploys the workflow to all specified regions.
2. **Execution**: Pass control to the test function.
3. **Teardown**: Cleans up cloud resources (CFN stacks, Azure Resource Groups) and local partition files.

## Performance Tuning (Local Runs)

Since cloud deployments can be slow (~8-10 mins for a full cycle), it is recommended to run tests in parallel using `pytest-xdist`.

```bash
# Run with 4 parallel workers
pytest serwo/tests/test_workflow.py -n 4 -v
```

**Note:** Always use `-n` (parallel workers) when testing multiple different examples to significantly reduce the total execution time.


Examples:
1. text workflow -aws, azure, default ( multi cloud ) - benchmark file do not touch
2. asynctester -aws, azure, default ( multi cloud ) - modify benchmark
Add the output expected v/s actual in the test file
3. Looping feature XFaaS- add later 