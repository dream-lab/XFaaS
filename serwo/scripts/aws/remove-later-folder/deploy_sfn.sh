#!/bin/bash

sam_build_dir=$1
template_filename=$2
stack_name=$3
region=$4

sam deploy\
 --template-file "${sam_build_dir}/${template_filename}"\
 --stack-name "${stack_name}"\
 --region "${region}"\
 --capabilities CAPABILITY_IAM\
 --no-confirm-changeset\
 --resolve-image-repos\
 --disable-rollback\
 --resolve-s3

# aws_build_dir=$1
# sam_build_dir=$2
# stack_name=$3
# region=$4
# template_filename=$5
# template_filepath="${aws_build_dir}/${template_filename}"
# config_filepath=$4

# NOTE - adding use-container in sam build temporary for ML models
# sam build --build-dir "${sam_build_dir}" --template-file "${template_filepath}"
# sam deploy\
#  --template-file "${sam_build_dir}/${template_filename}"\
#  --stack-name "${stack_name}"\
#  --region "${region}"\
#  --capabilities CAPABILITY_IAM\
#  --no-confirm-changeset\
#  --resolve-image-repos\
#  --disable-rollback\
#  --resolve-s3