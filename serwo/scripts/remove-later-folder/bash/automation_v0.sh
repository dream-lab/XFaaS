#!/bin/bash
echo "############## SETTING UP BUILD ENVIRONMENTS ############"
echo "----------------------------------------"
echo "Creating build directory for workflow.."
# create build directory
mkdir -p ../build/workflow

sleep 3

echo "----------------------------------------"
echo "Initialising workflow directory"
touch ../build/workflow/__init__.py

sleep 3

# create the functions directory
echo "----------------------------------------"
echo "Creating and Initialising functions directory.."
mkdir -p ../build/workflow/functions
touch ../build/workflow/functions/__init__.py

sleep 3

# for each function create a separate directory
echo "----------------------------------------"
echo  "Creating and initialising directory for func1"
mkdir -p ../build/workflow/functions/func1
touch ../build/workflow/functions/func1/__init__.py # init.py
cp ../../../examples/sample-dag-1/requirements.txt ../build/workflow/functions/func1/ # copy requirements.txt

sleep 3

echo "----------------------------------------"
echo  "Creating and initialising directory for func2"
mkdir -p ../build/workflow/functions/func2
touch ../build/workflow/functions/func2/__init__.py # init.py
cp ../../../examples/sample-dag-1/requirements.txt ../build/workflow/functions/func2/ # copy requirements.txt

sleep 3

echo "----------------------------------------"
echo  "Creating and initialising directory for func3"
mkdir -p ../build/workflow/functions/func3
touch ../build/workflow/functions/func3/__init__.py # init.py
cp ../../../examples/sample-dag-1/requirements.txt ../build/workflow/functions/func3/ # copy requirements.txt

sleep 3

echo "############# GENERATING RUNNERS  ############"
echo "----------------------------------------"
echo  "Generating runners for func1"
sed 's/USER_FUNCTION_PLACEHOLDER/func1/' ../runner-templates/http_runner_template.py > ../../../examples/sample-dag-1/func1_temp_runner.py # create the temp runner
stickytape ../../../examples/sample-dag-1/func1_temp_runner.py > ../build/workflow/functions/func1/standalone_func1_runner.py # generate standalone runner
rm ../../../examples/sample-dag-1/func1_temp_runner.py # remove the temp runner

sleep 3

echo  "Generating runners for func2"
sed 's/USER_FUNCTION_PLACEHOLDER/func2/' ../runner-templates/http_runner_template.py > ../../../examples/sample-dag-1/func2_temp_runner.py
stickytape ../../../examples/sample-dag-1/func2_temp_runner.py > ../build/workflow/functions/func2/standalone_func2_runner.py
rm ../../../examples/sample-dag-1/func2_temp_runner.py 

sleep 3

echo  "Generating runners for func3"
sed 's/USER_FUNCTION_PLACEHOLDER/func3/' ../runner-templates/http_runner_template.py > ../../../examples/sample-dag-1/func3_temp_runner.py
stickytape ../../../examples/sample-dag-1/func3_temp_runner.py > ../build/workflow/functions/func3/standalone_func3_runner.py
rm ../../../examples/sample-dag-1/func3_temp_runner.py

sleep 2
echo "Build Succeeded!"
echo "############# COMPLETED BUILD ENVIRONMENT CREATION!  ############"



