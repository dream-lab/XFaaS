class Function:
    def __init__(self, id, name, path, end_point, memory):
        self._name = name
        self._id = id
        self._arn = name + "Arn"
        self._ref = "!GetAtt " + name + ".Arn"
        self._path = path
        self._runner_filename = "standalone_" + end_point.split(".")[0] + "_runner"
        self._handler = self._runner_filename + ".lambda_handler"
        self._uri = "functions/" + name
        self._module_name = end_point.split(".")[0]
        self._memory = memory
        # TODO - add function id

    def get_id(self):
        return self._id

    def get_name(self):
        return self._name

    def get_arn(self):
        return self._arn

    def get_ref(self):
        return self._ref

    def get_path(self):
        return self._path

    def get_handler(self):
        return self._handler

    def get_module_name(self):
        return self._module_name

    def get_as_dict(self):
        return {
            "name": self._name,
            "uri": self._uri,
            "handler": self._handler,
            "memory": self._memory,
        }

    def get_runner_filename(self):
        return self._runner_filename

    def get_memory_in_mb(self):
        return self._memory
