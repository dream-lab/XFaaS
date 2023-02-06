#!/bin/sh
user_directory=$1
dag_description=$2

cd serwo/scripts/azure
python3 azure_resource_creation.py $user_directory $dag_description
python3 azure_builder.py $user_directory $dag_description
python3 azure_deploy.py $user_directory $dag_description