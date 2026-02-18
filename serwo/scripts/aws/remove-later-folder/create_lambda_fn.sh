#!/bin/bash

# command line arguments
# paths
USER_FUNCTION_PATH=$1 # user directory
SERWO_BUILD_DIR=$2 # serwo build directory for aws
RUNNER_TEMPLATE_DIR=$6 # runner template directory
SERWO_UTILS_DIR=$7
RUNNER_TEMPLATE_FILENAME=$8

# function specific data
function_name=$3 # function name
function_module_name=$4
runner_filename=$5 # handler name
function_requirements_file="requirements.txt" # requirements.txt for the function (parse from dag definition if required)


# for each function create a separate directory
echo "----------------------------------------"
echo  "Creating and initialising directory for function"
SERWO_BUILD_FUNCTION_DIR=$SERWO_BUILD_DIR/functions/$function_name
mkdir -p $SERWO_BUILD_FUNCTION_DIR
touch $SERWO_BUILD_FUNCTION_DIR/__init__.py

# place the requirements.txt for the user function in serwo function directory
cp $USER_FUNCTION_PATH/$function_requirements_file $SERWO_BUILD_FUNCTION_DIR/

# NOTE - do a conditional branch
cp -R $USER_FUNCTION_PATH/dependencies $SERWO_BUILD_FUNCTION_DIR/

# place serwo depedencies in function directory
cp -R $SERWO_UTILS_DIR $SERWO_BUILD_FUNCTION_DIR/

echo "############# GENERATING RUNNERS  ############"
echo  "Generating runners for function - ${function_name}"
sed_string="s/USER_FUNCTION_PLACEHOLDER/${function_module_name}/g"
sed ${sed_string} ${RUNNER_TEMPLATE_DIR}/${RUNNER_TEMPLATE_FILENAME} > ${USER_FUNCTION_PATH}/${function_name}_temp_runner.py
stickytape ${USER_FUNCTION_PATH}/${function_name}_temp_runner.py > ${SERWO_BUILD_FUNCTION_DIR}/${runner_filename}.py
rm $USER_FUNCTION_PATH/${function_name}_temp_runner.py
echo "############# COMPLETED BUILD ENVIRONMENT CREATION!  ############"