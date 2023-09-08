import scripts.azure.azure_resource_generator as azure_resource_generator
import scripts.azure.azure_builder as azure_builder
import scripts.azure.azure_deploy as azure_deployer


from serwo.aws_create_statemachine import AWS
class CSP:
    __name = None

    def __init__(self, name):
        self.__name = name

    def get_name(self):
        return self.__name


    #TODO: Factory pattern for csp
    def build_resources(self,user_dir, dag_definition_path, region, part_id, dag_definition_file, is_netherite):
        if self.__name == 'azure':
            self.build_az(dag_definition_file, dag_definition_path, part_id, region, user_dir, is_netherite)
        if self.__name == 'aws':
            aws_deployer = AWS(user_dir, dag_definition_file, "REST", part_id, region)
            aws_deployer.build_resources()
            aws_deployer.build_workflow()
            aws_deployer.deploy_workflow()
            pass


    def build_az(self, dag_definition_file, dag_definition_path, part_id, region, user_dir,is_netherite):
        print(':'*80, 'Azure resource generation')
        azure_resource_generator.generate(user_dir, dag_definition_path, region, part_id,is_netherite)
        print(':'*80, 'Azure Build')
        azure_builder.build(user_dir, dag_definition_file, region, part_id, is_netherite)
        print(':'*80, 'Azure Deploy')
        azure_deployer.deploy(user_dir, region, part_id,is_netherite)
        print(':'*80, 'Azure Deploy Done...')


