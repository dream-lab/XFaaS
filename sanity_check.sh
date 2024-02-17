#!/bin/bash

python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 1 \
--duration 10 \
--payload-size small \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 1 \
--duration 10 \
--payload-size small \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "Sanity check completed successfully!"

> /XFaaS/deployments.txt