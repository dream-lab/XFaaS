from python.src.utils.classes.commons.partition_point import PartitionPoint
from python.src.utils.classes.commons.csp import CSP

def generate(user_dir, dag_definition_path, partition_config, dag_definition_file):
    for partition in partition_config:
        csp = partition.get_left_csp()
        region = partition.get_region()
        part_id = partition.get_part_id()
        csp_temp = csp.split('_')
        csp = csp_temp[0]
        if len(csp_temp) > 1:
            is_netherite = True
        else:
            is_netherite = False
        CSP(csp).build_resources(user_dir, dag_definition_path,region,part_id,dag_definition_file,is_netherite)
        

