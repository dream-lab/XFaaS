#!/bin/bash

aws_build_dir=$1
sam_build_dir=$2
template_filename=$3
template_filepath="${aws_build_dir}/${template_filename}"

# NOTE - adding use-container in sam build temporary for ML models
sam build --build-dir "${sam_build_dir}" --template-file "${template_filepath}"