import scripts.azure.azure_resource_generator as azure_resource_generator

class CSP:
    __name = None

    def __init__(self, name):
        self.__name = name

    def get_name(self):
        return self.__name


    #TODO: Factory pattern for csp
    def build_resources(self,user_dir, dag_definition_path, region, part_id):
        if self.__name == 'azure':
            azure_resource_generator.generate(user_dir, dag_definition_path,region,part_id)
        else:
            # NOTE - this does not do anything since there is no resource creation for AWS
            pass


