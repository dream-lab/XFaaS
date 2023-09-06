#!/bin/bash
# verify all parameters are correct before executing
python3 xfaas_benchmarksuite_plotgen.py \
--user-dir /Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/FileSystemRevisedAws \
--artifacts-filename aws-static-1-rps-small.json \
--interleaved True \
--format pdf \
--out-dir filesystem-aws-static-small-1rps
