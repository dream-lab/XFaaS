#!/bin/bash

python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 1 \
--duration 300 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS 1 rps Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 1 \
--duration 300 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE 1rps Done!!"
sleep 10


python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 4 \
--duration 300 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS 4 rps Done!!"
sleep 10


python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 4 \
--duration 300 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE 4 rps Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 8 \
--duration 300 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS 4 rps Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 8 \
--duration 300 \
--payload-size medium \
--dynamism static \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE 8 RPS  SIZE Done!!"
sleep 10

python3 ccgrid2024_artifact_plots/plot_rps_variation.py \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf

echo "Plotting Done!!"

> /XFaaS/deployments.txt