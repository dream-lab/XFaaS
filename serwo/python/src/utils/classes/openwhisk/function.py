"""
A Function object refers to an Action in Openwhisk
"""

class Function:
    def __init__(self, id, name, path, entry_point, memory):
        self._id = id
        self._name = name
        self._path = path
        self._memory = memory
        self._uri = "functions/" + name
        self._module_name = entry_point.split(".")[0]
        
        self._runner_filename = "standalone_" + entry_point.split(".")[0] + "_runner"
        self._handler = self._runner_filename + ".main"

    def get_runner_filename(self):
        return self._runner_filename

    def get_path(self):
        return self._path

    def get_module_name(self):
        return self._module_name
    
    def get_memory(self):
        return self._memory

    def get_id(self):
        return self._id
    
    def get_as_dict(self):
        return {
            "name": self._name,
            "uri": self._uri,
            "handler": self._handler,
            "memory": self._memory,
        }
