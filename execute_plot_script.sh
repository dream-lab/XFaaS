#!/bin/bash

# verify all parameters are correct before executing
python3 xfaas_benchmarksuite_plotgen.py \
--user-dir /Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAz \
--artifacts-filename aws-static-1-rps-medium.json \
--interleaved True \
--format pdf \
--out-dir graph-aws-static-medium-1rps