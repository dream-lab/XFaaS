echo "############## SETTING UP BUILD ENVIRONMENTS ############"
echo "----------------------------------------"
echo "Creating build directory for workflow.."
aws_build_dir=$1
functions_build_dir=${aws_build_dir}/functions
mkdir -p ${functions_build_dir}


echo "----------------------------------------"
echo "Initialising workflow directory"
touch ${aws_build_dir}/__init__.py

# create the functions directory
echo "----------------------------------------"
echo "Initialising functions directory.."
touch ${functions_build_dir}/__init__.py