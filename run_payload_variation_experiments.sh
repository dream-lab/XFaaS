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

echo "AWS SMALL PAYLOAD SIZE Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 1 \
--duration 10 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS MEDIUM PAYLOAD SIZE Done!!"
sleep 10


python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastusa \
--max-rps 1 \
--duration 10 \
--payload-size small \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE SMALL PAYLOAD SIZE Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastusa \
--max-rps 1 \
--duration 10 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE MEDIUM PAYLOAD SIZE Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastusa \
--max-rps 1 \
--duration 10 \
--payload-size large \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE LARGE PAYLOAD SIZE Done!!"
sleep 10