import scripts.azure.azure_resource_generator as azure_resource_generator
import scripts.azure.azure_builder as azure_builder
import scripts.azure.azure_deploy as azure_deployer

from serwo.aws_create_statemachine import AWS
from serwo.openwhisk_create_statemachine import OpenWhisk

class CSP:
    __name = None

    def __init__(self, name):
        self.__name = name

    def get_name(self):
        return self.__name


    #TODO: Factory pattern for csp
    def build_resources(self, user_dir, dag_definition_path, region, part_id, dag_definition_file, is_netherite):
        if self.__name == 'azure':
            self.build_az(dag_definition_file, dag_definition_path, part_id, region, user_dir, is_netherite)
        elif self.__name == 'aws':
            if part_id == "0000":
                aws_deployer = AWS(user_dir, dag_definition_file, "REST", part_id, region)
            else:
                aws_deployer = AWS(user_dir, dag_definition_file, "SQS", part_id, region)

            aws_deployer.build_resources()
            aws_deployer.build_workflow()
            aws_deployer.deploy_workflow()

        elif self.__name.lower() == 'openwhisk':
            private_cloud_deployer = OpenWhisk(user_dir=user_dir, dag_file_name=dag_definition_file, part_id=part_id)
            
            print(":" * 80, "Generating resources for OpenWhisk Actions")
            private_cloud_deployer.build_resources()

            print(":" * 80, "Generating workflow files for OpenWhisk")
            private_cloud_deployer.build_workflow()

            print(":" * 80, "Deploying OpenWhisk")
            private_cloud_deployer.deploy_workflow()    


    def build_az(self, dag_definition_file, dag_definition_path, part_id, region, user_dir,is_netherite):
        print(':'*80, 'Azure resource generation')
        azure_resource_generator.generate(user_dir, dag_definition_path, region, part_id,is_netherite)
        print(':'*80, 'Azure Build')
        azure_builder.build(user_dir, dag_definition_file, region, part_id, is_netherite)
        print(':'*80, 'Azure Deploy')
        azure_deployer.deploy(user_dir, region, part_id,is_netherite)
        print(':'*80, 'Azure Deploy Done...')


