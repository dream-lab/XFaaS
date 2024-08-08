import os
import glob
import json
import shutil
import zipfile
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from python.src.utils.classes.openwhisk.user_dag import UserDag
from python.src.utils.classes.commons.logger import LoggerFactory

logger = LoggerFactory.get_logger(__file__, log_level="INFO")


class OpenWhisk:
    def __init__(self, user_dir, dag_file_name, part_id):
        self.__user_dir = Path(user_dir)
        self.__dag_file_name = dag_file_name
        self.__part_id = part_id

        self.__parent_directory_path = Path(__file__).parent

        # xfaas specfic directories
        self.__serwo_build_dir = self.__user_dir / "build" / "workflow"
        self.__serwo_resources_dir = self.__serwo_build_dir / "resources"
        
        # This holds utility scripts and templates
        self.__serwo_utils_dir = self.__parent_directory_path / "python"
        self.__runner_template_dir = self.__serwo_utils_dir / "src" / "runner-templates" / "openwhisk"

        self.__dag_definition_path = self.__user_dir / self.__dag_file_name

        # openwhisk specific directories
        self.__openwhisk_build_dir = self.__serwo_build_dir / "openwhisk"
        self.__openwhisk_functions_dir = self.__openwhisk_build_dir / "functions"
        # This holds the zip files to be deployed
        self.__openwhisk_artifacts_dir = self.__openwhisk_build_dir / "artifacts"
        # This holds the bash script to setup local nodejs for openwhisk composer
        self.__openwhisk_helpers_dir = self.__openwhisk_build_dir / "helpers"
        self.__openwhisk_helpers_nodejs_dir = self.__openwhisk_helpers_dir / "local_nodejs"

        # OpenWhisk configuration parameters with sensible defaults suggested in OW documentation
        self.__action_namespace = os.environ.get("XFAAS_OW_ACTION_NS", "guest")
        self.__action_concurrency = int(os.environ.get("XFAAS_OW_ACTION_CONCURRENCY", 1))
        self.__action_timeout = int(os.environ.get("XFAAS_OW_ACTION_TIMEOUT", 300000))
        self.__action_memory = int(os.environ.get("XFAAS_OW_ACTION_MEMORY", 256)) # This is only used for orchestrator action for now
        self.__redis_url = os.environ.get("XFAAS_OW_REDIS_URL", "redis://owdev-redis.openwhisk.svc.cluster.local:6379")
        self.__ignore_certs = bool(os.environ.get("XFAAS_OW_REDIS_IGNORE_CERTS", 1)) # 1/0 for True or False

        # DAG related parameters
        self.__user_dag = UserDag(self.__dag_definition_path)
        self.__openwhisk_workflow_orchestrator_action_name = f"/{self.__action_namespace}/{self.__user_dag.get_user_dag_name()}/orchestrator"
        self.__openwhisk_composer_input_path = self.__openwhisk_build_dir / f"{self.__user_dag.get_user_dag_name()}_workflow_composition.js"
        self.__openwhisk_composer_output_path = self.__openwhisk_build_dir / f"{self.__user_dag.get_user_dag_name()}_workflow_composition.json"


    def __create_environment(self):
        """
        Create the directories to put functions into.
        * /functions/ directory holds the converted functions
        * /artifacts/ directory contains the zip files to be deployed to OpenWhisk
        """
        # TODO: Check me removing and shizz
        if os.path.exists(self.__openwhisk_functions_dir):
            shutil.rmtree(self.__openwhisk_functions_dir)
        
        if os.path.exists(self.__openwhisk_artifacts_dir):
            shutil.rmtree(self.__openwhisk_artifacts_dir)

        # Not deleting this to save the time spent on downloading nodejs
        # if os.path.exists(self.__openwhisk_helpers_dir):
        #     shutil.rmtree(self.__openwhisk_helpers_dir)

        self.__openwhisk_functions_dir.mkdir(parents=True, exist_ok=True)
        self.__openwhisk_artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.__openwhisk_helpers_dir.mkdir(parents=True, exist_ok=True)
        self.__openwhisk_helpers_nodejs_dir.mkdir(parents=True, exist_ok=True)
        self.__serwo_resources_dir.mkdir(parents=True, exist_ok=True)
        
        # Copying the bash script to install a local nodejs copy (used by openwhisk-composer)
        shutil.copyfile(src=self.__runner_template_dir/"local_nodejs_installer.sh", dst=self.__openwhisk_helpers_dir/"local_nodejs_installer.sh")
    

    def __render_runner_template(self, runner_template_dir, function_id, function_name, function_runner_filename):
        """
        """
        runner_template_filename = function_runner_filename
        
        try:
            file_loader = FileSystemLoader(runner_template_dir)
            env = Environment(loader=file_loader)
            template = env.get_template("runner_template.py")
            logger.info(
                f"Created jinja2 environement for templating Openwhisk function ids for function::{function_name}"
            )
        except:
            raise Exception(
                f"Unable to load environment for Openwhisk function id templating for function::{function_name}"
            )
        
        # render the template
        try:
            output = template.render(function_id_placeholder=function_id)
            with open(f"{runner_template_dir}/{runner_template_filename}", "w") as out:
                out.write(output)
                logger.info(
                    f"Rendered and flushed the runner template for Openwhisk function for function::{function_name}"
                )
        except Exception as e:
            logger.error(e)
            raise Exception(
                f"Unable to render the function runner template for Openwhisk function for function::{function_name}"
            )

        return runner_template_filename
    

    def __append_xfaas_default_requirements(self, filepath):
        """
        Appends XFaaS dependencies to the function requirements
        """
        with open(filepath, "r") as file:
            lines = file.readlines()
            lines.append("psutil\n")
            lines.append("objsize\n")
            unqiue_dependencies = set(lines)
            file.flush()
            
        with open(filepath, "w") as file:
            for line in [x.strip("\n") for x in sorted(unqiue_dependencies)]:
                file.write(f"{line}\n")
    

    def __create_openwhisk_actions(
        self, 
        user_fn_path,
        fn_name,
        fn_module_name,
        runner_template_filename,
        runner_template_dir,
    ):
        """
        user_fn_path: Workflow code is taken from hardcoded XFaaS samples from this path 
        """
        fn_requirements_filename = "requirements.txt"
        src_fn_dir = user_fn_path / fn_requirements_filename
        dst_fn_dir = self.__openwhisk_functions_dir / fn_name

        dst_requirements_path = dst_fn_dir / fn_requirements_filename
        
        logger.info(f"Creating function directory for {fn_name}")
        if not os.path.exists(dst_fn_dir):
            os.makedirs(dst_fn_dir)

        logger.info(f"Moving requirements file for {fn_name} for user at to {dst_fn_dir}")
        shutil.copyfile(src=src_fn_dir, dst=dst_requirements_path)

        logger.info(f"Adding default requirements {fn_name}")
        self.__append_xfaas_default_requirements(dst_requirements_path)

        # place the dependencies folder from the user function path if it exists
        if os.path.exists(user_fn_path / "dependencies"):
            shutil.copytree(
                user_fn_path / "dependencies", 
                dst_fn_dir / "dependencies", 
                dirs_exist_ok=True
            )

        logger.info(f"Moving xfaas boilerplate for {fn_name}")
        shutil.copytree(src=self.__serwo_utils_dir, dst=dst_fn_dir / "python", dirs_exist_ok=True)

        logger.info(f"Generating Runners for function {fn_name}")

        fnr_string = f"USER_FUNCTION_PLACEHOLDER"
        temp_runner_path = user_fn_path / f"{fn_name}_temp_runner.py"
        runner_template_path = runner_template_dir / runner_template_filename
        
        print("Here", runner_template_path)
        with open(runner_template_path, "r") as file:
            contents = file.read()
            contents = contents.replace(fnr_string, fn_module_name)

        with open(temp_runner_path, "w") as file:
            file.write(contents)

        # XFaaS code provided by the user comes as the module name due to
        # import USER_FUNCTION_PLACEHOLDER being replaced by the module name
        final_import_file_src_path = user_fn_path / f"{fn_module_name}.py"
        final_import_file_dst_path = dst_fn_dir / f"{fn_module_name}.py"
        final_runner_file_path = dst_fn_dir / "__main__.py"

        os.system(f"cp {final_import_file_src_path} {final_import_file_dst_path}")

        # Standalone runner from other clouds is replaced by __main__.py file for OpenWhisk
        os.system(f"cp {temp_runner_path} {final_runner_file_path}")
       
        logger.info(f"Deleting temporary runner")
        os.remove(temp_runner_path)

        logger.info(f"Successfully created build directory for function {fn_name}")


    def __create_standalone_runners(self):
        """
        The function entrypoint is __main__.py due to OpenWhisk deployment
        requirements for large library imports
        """
        function_metadata_list = self.__user_dag.get_node_param_list()
        function_object_map = self.__user_dag.get_node_object_map()
        
        for function_metadata in function_metadata_list:
            function_name = function_metadata["name"]        
            function_runner_filename = "__main__" # OpenWhisk requires the main file name to be __main__.py

            function_runner_filename = function_object_map[
                function_metadata["name"]
            ].get_runner_filename()
            
            function_path = function_object_map[function_name].get_path()
            function_module_name = function_object_map[function_name].get_module_name()
            function_id = function_object_map[function_name].get_id()

            runner_template_filename = self.__render_runner_template(
                runner_template_dir=self.__runner_template_dir,
                function_id=function_id,
                function_name=function_name,
                function_runner_filename=function_runner_filename
            )

            logger.info(f"Starting Standalone Runner Creation for function {function_name}")

            self.__create_openwhisk_actions(
                self.__parent_directory_path / function_path,
                function_name,
                function_module_name,
                function_runner_filename,
                self.__runner_template_dir,
            )

            runner_template_filepath = self.__runner_template_dir / runner_template_filename
            logger.info(f"Deleting Temporary Runner Template at {runner_template_filepath}")
            os.remove(f"{runner_template_filepath}")


    def __create_workflow_orchestrator(self, file_name_prefix):
        """
        Generates a js file to send as an input to openwhisk composer.
        See: https://github.com/apache/openwhisk-composer
        """
        composer_file_path = self.__openwhisk_build_dir / f"{file_name_prefix}_workflow_composition.js"

        generated_code = self.__user_dag.get_orchestrator_code()
        with open(composer_file_path, "w") as f:
            f.write(generated_code)
    

    def build_resources(self):
        """
        First of the 3 main functions for the workflow.

        1. Creates OpenWhisk's action compatible source code function files
        2. TODO: Creates openwhisk composer js files
        """
        logger.info("*" * 30)
        logger.info("Build Resources: Started")
        logger.info("*" * 30)

        logger.info(f"Creating environment for {self.__user_dag.get_user_dag_name()}")
        self.__create_environment()

        logger.info(f"Initating standalone runner creation for {self.__user_dag.get_user_dag_name()}")
        self.__create_standalone_runners()
        
        logger.info(f"Initating openwhisk composer js orchestrator for {self.__user_dag.get_user_dag_name()}")
        self.__create_workflow_orchestrator(self.__user_dag.get_user_dag_name())

        logger.info("*" * 30)
        logger.info("Build Resources: Success")
        logger.info("*" * 30)


    def build_workflow(self):
        """
        Second of the 3 main functions for the workflow.
        - Creates zip artifacts for all the functions
        - Downloads a local nodejs copy using "n"
        - Converts the openwhisk-composer js file into json

        ------------
        Assumptions:
        ------------
        - wsk tool is setup -> User's responsibility
        """
        # Create a zip artifact from each function
        for func_name in self.__user_dag.get_node_object_map():
            output_artifact_path = self.__openwhisk_build_dir/"artifacts"/f"{func_name}.zip"
            
            files_to_zip = []
            for file in os.listdir(self.__openwhisk_functions_dir/func_name):
                if file.endswith(".py"):
                    curr_file_path = self.__openwhisk_functions_dir/func_name/file
                    # basename thing is required to unzip correctly
                    files_to_zip.append([curr_file_path, os.path.basename(curr_file_path)])
            
            with zipfile.ZipFile(output_artifact_path, "w") as archive:
                for fz in files_to_zip:
                    archive.write(filename=fz[0], arcname=os.path.basename(fz[1]))

                req_file_path = self.__openwhisk_functions_dir/func_name/"requirements.txt"
                archive.write(filename=req_file_path, arcname=os.path.basename(req_file_path))

                xfaas_folder_path = str(self.__openwhisk_functions_dir/func_name/"python"/"**"/"*")
                for file in glob.glob(xfaas_folder_path, recursive=True):
                    path = file.split("python/")[1]
                    archive.write(filename=file, arcname=os.path.join("python", path))

                dependencies_folder_path = str(self.__openwhisk_functions_dir/func_name/"dependencies"/"**"/"*")
                for file in glob.glob(dependencies_folder_path, recursive=True):
                    path = file.split("dependencies/")[1]
                    archive.write(filename=file, arcname=os.path.join("dependencies", path))

        logger.info(":" * 30)
        logger.info("Installing nodejs and openwhisk-composer")
        logger.info(":" * 30)

        builder_dir = str(self.__openwhisk_helpers_dir.resolve())
        builder_path = os.path.join(builder_dir, "local_nodejs_installer.sh")
        nodejs_local_dir = str(self.__openwhisk_helpers_nodejs_dir.resolve())

        # Only downloading a local NodeJS copy if one doesn't exist already with required libraries installed
        ow_composer_binary_path = os.path.join(nodejs_local_dir, "node_modules", "openwhisk-composer", "bin", "compose.js")
        if not os.path.exists(ow_composer_binary_path):
            logger.info("Installing NodeJS using 'https://raw.githubusercontent.com/tj/n/master/bin/n'")
            nodejs_installation_status = subprocess.run(["sh", builder_path, nodejs_local_dir])
            
            if nodejs_installation_status.returncode == 0:
                logger.info("NodeJS installation success")
            else:
                # TODO: Handle me gracefully
                logger.info("NodeJS installation failure")
                raise Exception("NodeJS installation failed")
            
            # ------------------------------------------------------------------------------------------
            # Doing a "$ npm install openwhisk-composer" from the local npm binary
            logger.info("Starting to install openwhisk-composer using npm: See 'https://github.com/apache/openwhisk-composer'")
            
            local_nodejs_binary_path = self.__openwhisk_helpers_nodejs_dir/"bin"/"node"
            local_npm_binary_path = self.__openwhisk_helpers_nodejs_dir/"bin"/"npm"
            ow_composer_installation_status = subprocess.run([str(local_nodejs_binary_path.resolve()), str(local_npm_binary_path.resolve()), "install", "--prefix", nodejs_local_dir, "openwhisk-composer"])
            if ow_composer_installation_status.returncode == 0:
                logger.info("Successfully installed openwhisk-composer")
            else:
                # TODO: Handle me gracefully
                logger.info("openwhisk-composer installation failure")
                raise Exception("openwhisk-composer installation failed")
            # ------------------------------------------------------------------------------------------
        else:
            logger.info(":" * 30)
            logger.info("Required local NodeJS already exists in the build directory")
            logger.info(":" * 30)

        logger.info(":" * 30)
        logger.info("Installing nodejs and openwhisk-composer: SUCCESS")
        logger.info(":" * 30)

        logger.info(":" * 30)
        logger.info("Creating workflow composition files using openwhisk-composer")
        logger.info(":" * 30)

        local_nodejs_binary_path = self.__openwhisk_helpers_nodejs_dir/"bin"/"node"
        ow_composer_binary_path = os.path.join(nodejs_local_dir, "node_modules", "openwhisk-composer", "bin", "compose.js")
        orchestrator_creation_status = subprocess.run([
            local_nodejs_binary_path, ow_composer_binary_path, 
            str(self.__openwhisk_composer_input_path.resolve()), 
            "-o", str(self.__openwhisk_composer_output_path.resolve()),
        ])

        if orchestrator_creation_status.returncode != 0:
            logger.info("Orchestrator file creation failed")
            raise Exception("Orchestrator file creation failed")
        
        logger.info(":" * 30)
        logger.info("Creating openwhisk-composer files: SUCCESS")
        logger.info(":" * 30)


    def deploy_workflow(self):
        """
        Third of the 3 main functions for the workflow.
        1. Removes existing actions with the current workflow's name
        2. Deploys all the actions
        3. Creates openwhisk-compatible orchestrator json file using third-party tool
        4. Deploys the orchestrator action

        -----
        TODO:
        1. Figure out web api mode, web hooks and related stuff
        2. Handle the input.json somehow to allow parallel workflow actions - "wsk -i action invoke /guest/graph-workflow -P input.json"
        3. Throw Exception if wsk command is not working -> Or find a better way to connect to the cluster
        -----
        """
        logger.info(":" * 30)
        logger.info("Deleting any existing OpenWhisk components")
        logger.info(":" * 30)

        # ----------------- Existing OpenWhisk components deletion -----------------
        for node_name in self.__user_dag.get_node_object_map():
            curr_action_name = f"/{self.__action_namespace}/{self.__user_dag.get_user_dag_name()}/{node_name}"
            try:
                os.system(f"wsk -i action delete {curr_action_name}")
            except Exception as e:
                # TODO: Handle me gracefully
                print("Either the openwhisk action does not exist or some error happened")
                print(e)
            
        try:
            os.system(f"wsk -i action delete {self.__openwhisk_workflow_orchestrator_action_name}")
        except Exception as e:
            # TODO: Handle me gracefully
            print("Either the openwhisk workflow orchestrator does not exist or some error happened")
            print(e)

        try:
            # TODO: This creates the package in the "/guest/" namespace, need to figure out how to change that
            # Hints: Helm changes are required
            os.system(f"wsk -i package delete {self.__user_dag.get_user_dag_name()}")
            os.system(f"wsk -i package create {self.__user_dag.get_user_dag_name()}")
        except Exception as e:
            # TODO: Handle me gracefully
            print("Either the openwhisk package does not exist or some error happened")
            print(e)
        # -------------------------------------------------------------------------

        # ----------------- New OpenWhisk components creation -----------------
        # Creating the actions manually using the wsk tool
        logger.info(":" * 30)
        logger.info("Deploying OpenWhisk action for each function")
        logger.info(":" * 30)

        for func_name in self.__user_dag.get_node_object_map():
            action_name = f"/{self.__action_namespace}/{self.__user_dag.get_user_dag_name()}/{func_name}"
            action_zip_path = self.__openwhisk_artifacts_dir / f"{func_name}.zip"

            # This overrides the default configuration set from the environment at an action level from the provided DAG.
            memory_in_mb = self.__user_dag.get_node_object_map()[func_name].get_memory()

            try:
                os.system(f"wsk -i action create {action_name} --kind python:3 {action_zip_path} --timeout {self.__action_timeout} --concurrency {self.__action_concurrency} --memory {memory_in_mb}")
            except Exception as e:
                print("X" * 20)
                print(f"Action creation command failed for {action_name}")
                print(e)
                print("X" * 20)

        logger.info(":" * 30)
        logger.info("Deploying OpenWhisk action for each function: SUCCESS")
        logger.info(":" * 30)

        logger.info(":" * 30)
        logger.info("Deploying OpenWhisk orchestrator action")
        logger.info(":" * 30)
        
        nodejs_local_dir = str(self.__openwhisk_helpers_nodejs_dir.resolve())
        local_nodejs_binary_path = self.__openwhisk_helpers_nodejs_dir/"bin"/"node"
        ow_deployer_binary_path = os.path.join(nodejs_local_dir, "node_modules", "openwhisk-composer", "bin", "deploy.js")
        os.system(f"{local_nodejs_binary_path} {ow_deployer_binary_path} {self.__openwhisk_workflow_orchestrator_action_name} {self.__openwhisk_composer_output_path} -w -i")
        
        ignore_certs = "false"
        if self.__ignore_certs:
            ignore_certs = "true"

        # Hackish way to create this complex string input for orchestrator function
        workflow_update_cmd = f"wsk -i action update {self.__openwhisk_workflow_orchestrator_action_name} --timeout {self.__action_timeout} --concurrency {self.__action_concurrency} --memory {self.__action_memory}"
        workflow_update_cmd += " --param '$composer' '{"
        workflow_update_cmd += '"redis":{"uri":"'
        workflow_update_cmd += self.__redis_url
        workflow_update_cmd += '"},"openwhisk":{"ignore_certs":'
        workflow_update_cmd += ignore_certs
        workflow_update_cmd += '}'
        workflow_update_cmd += "}'"

        try:
            os.system(workflow_update_cmd)
        except Exception as e:
            print("Workflow action updation command failed")
            print(e)
        
        logger.info(":" * 30)
        logger.info("Deploying OpenWhisk orchestrator action: SUCCESS")
        logger.info(":" * 30)

        logger.info(":" * 30)
        logger.info("Writing output json resource file")
        logger.info(":" * 30)
        
        wsk_host_output = subprocess.run(["wsk", "property", "get", "--apihost"], capture_output=True)
        wsk_auth_output = subprocess.run(["wsk", "property", "get", "--auth"], capture_output=True)

        if wsk_host_output.returncode != 0 or wsk_auth_output.returncode != 0:
            print(" X " * 30)
            print("Failed to get host and auth from 'wsk' client for the resources")
            print(" X " * 30)
        
        wsk_host = wsk_host_output.stdout.decode("utf-8").strip().split()[-1].strip()
        execution_auth = wsk_auth_output.stdout.decode("utf-8").strip().split()[-1].strip()
        execution_url = f"https://{wsk_host}/api/v1/namespaces/{self.__action_namespace}/actions/{self.__user_dag.get_user_dag_name()}/orchestrator?blocking=false"

        output_resource_file_path = self.__serwo_resources_dir / f"openwhisk-{self.__region}-{self.__part_id}.json"
        with open(output_resource_file_path, "w") as f:
            output = {
                "WorkflowEntrypoint": self.__openwhisk_workflow_orchestrator_action_name,
                "Decription": f"Run 'wsk -i action invoke {self.__openwhisk_workflow_orchestrator_action_name}' to start the workflow",
                "ExecutionUrl": execution_url,
                "ExecutionAuth": execution_auth,
            }
            
            f.write(json.dumps(output, indent=4))

        logger.info(":" * 30)
        logger.info("Writing output json resource file: SUCCESS")
        logger.info(":" * 30)
        # -------------------------------------------------------------------------
