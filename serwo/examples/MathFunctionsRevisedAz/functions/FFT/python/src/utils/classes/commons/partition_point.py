class PartitionPoint:
    # private variable
    __left_csp = None
    __right_csp = None
    __out_degree = None
    __function_name = None
    __part_id = None
    __region = None

    def __init__(self, function_name, out_degree, left_csp, right_csp,part_id,region):
        self.__function_name = function_name
        self.__left_csp = left_csp
        self.__right_csp = right_csp
        self.__out_degree = out_degree
        self.__part_id = part_id
        self.__region = region

    def get_partition_point_name(self):
        return self.__function_name

    def get_left_csp(self):
        return self.__left_csp

    def get_right_csp(self):
        return self.__right_csp

    def get_out_degree(self):
        return self.__out_degree

    def get_part_id(self):
        return self.__part_id

    def get_region(self):
        return self.__region
