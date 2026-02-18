class Function:
    def __init__(self, id, name, path, end_point, memory, model_name=None):
        self._name = name
        self._id = id
        self._arn = name + "Arn"
        self._ref = "!GetAtt " + name + ".Arn"
        self._path = path
        self._runner_filename = "standalone_app_runner"
        self._handler = self._runner_filename + ".lambda_handler"
        self._uri = "functions/" + name
        self._module_name = end_point.split(".")[0]
        self._memory = memory
        self._model_name = model_name or "openai:gpt-4o-mini"  # Default model
        # TODO - add function id
        self._isasync = False
        self._iscontainerised=False

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

    def get_model_name(self):
        return self._model_name

    def get_as_dict(self):
        return {
            "name": self._name,
            "uri": self._uri,
            "handler": self._handler,
            "memory": self._memory,
            "iscontainer": self._iscontainerised,
        }

    def get_runner_filename(self):
        return self._runner_filename

    def get_memory_in_mb(self):
        return self._memory

    def set_isasync(self):
        self._isasync = True
    
    def get_isasync(self):
        return self._isasync
    
    def set_iscontainerised(self):
        self._iscontainerised =True
    def get_iscontainerised(self):
        return self._iscontainerised 