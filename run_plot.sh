#!/bin/bash

# verify all parameters are correct before executing
python3 xfaas_benchmarksuite_plotgen_vk.py \
--user-dir /Users/varad.kulkarni/xfaas/XFaaS/serwo/examples/graphAws \
--artifacts-file aws-static-small-1rps.json \
--interleaved True \
--format pdf \
--out-dir aws-static-1-rps-small \
