class PartitionPoint:
    # private variable
    __left_csp = None
    __right_csp = None
    __out_degree = None
    __function_name = None

    def __init__(self, function_name, out_degree, left_csp, right_csp):
        self.__function_name = function_name
        self.__left_csp = left_csp
        self.__right_csp = right_csp
        self.__out_degree = out_degree

    def get_partition_point_name(self):
        return self.__function_name

    def get_left_csp(self):
        return self.__left_csp
    
    def get_right_csp(self):
        return self.__right_csp

    def get_out_degree(self):
        return self.__out_degree
