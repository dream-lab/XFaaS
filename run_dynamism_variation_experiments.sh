#!/bin/bash

python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 8 \
--duration 840 \
--payload-size medium \
--dynamism step_function \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS Step function Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 8 \
--duration 840 \
--payload-size medium \
--dynamism step_function \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE Step function Done!!"
sleep 10


python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 8 \
--duration 300 \
--payload-size medium \
--dynamism sawtooth \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS SAWTOOTH Done!!"
sleep 10


python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 8 \
--duration 300 \
--payload-size medium \
--dynamism sawtooth \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE SAWTOOTH Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp aws \
--region us-east-1 \
--max-rps 17 \
--duration 300 \
--payload-size medium \
--dynamism alibaba \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AWS ALIBABA Done!!"
sleep 10

python3 serwo/xfaas_run_benchmark.py \
--csp azure \
--region eastus \
--max-rps 17 \
--duration 300 \
--payload-size medium \
--dynamism alibaba \
--wf-name graph \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf \
--dag-file-name dag.json \
--teardown-flag 0 \
--client-key localhost

echo "AZURE ALIBABA Done!!"
sleep 10


python3 ccgrid2024_artifact_plotting_scripts/plot_dynamism_variation.py \
--wf-user-directory /XFBench/workflows/custom_workflows/graph_processing_wf

echo "Plotting Done!!"