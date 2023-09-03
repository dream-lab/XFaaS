#!/bin/bash

# verify all parameters are correct before executing
python3 xfaas_benchmarksuite_plotgen_vk.py \
--user-dir /Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/graphAws \
--artifacts-filename aws-small-1rps-rerun.json \
--interleaved True \
--format pdf \
--out-dir aws-small-1rps-rerun
