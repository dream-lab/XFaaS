import json


class SerWOObject:
    def __init__(self, body=None, error=None, metadata=None) -> None:
        self._body = body
        self._err = error  # Either body might be set or error might be set
        self._metadata = metadata
        self._basepath = None

    def get_body(self):
        return self._body

    def get_metadata(self):
        return self._metadata

    def get_error(self, key):
        return self._err

    def get_basepath(self):
        return self._basepath

    def set_basepath(self, basepath):
        self._basepath = basepath

    def has_error(self):
        if self._err is not None:
            return True
        else:
            return False

    def to_json(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_dct):
        return SerWOObject(json_dct["_body"], json_dct["_err"], json_dct["_metadata"])


class SerWOObjectsList:
    def __init__(self, body=None, metadata=None) -> None:
        self._object_list = []
        self._metadata = dict()
        if body:
            self._object_list.append(SerWOObject(body))
        if metadata:
            self._metadata = metadata
        self._basepath = None

    def get_objects(self):
        return self._object_list

    def get_metadata(self):
        return self._metadata

    def add_metadata(self, metadata):
        self._metadata = metadata

    # NOTE - will create issues if metadata is exposed to the user
    def add_object(self, body):
        self._object_list.append(SerWOObject(body))

    def get_basepath(self):
        return self._basepath

    def set_basepath(self, basepath):
        self._basepath = basepath


def build_serwo_list_object(event):
    """
    perform a union of all the metadata from incoming branches and
    collate into a metadata dictionary to remove duplicate data
    from a fan out at some point in the DAG
    """
    collated_metadata = dict()
    list_obj = SerWOObjectsList()
    functions_metadata_dict = dict()
    collated_functions_metadata_list = []
    for record in event:
        incoming_metadata = record.get("metadata")
        collated_metadata.update(
            dict(
                workflow_instance_id=incoming_metadata.get("workflow_instance_id"),
                workflow_start_time=incoming_metadata.get("workflow_start_time"),
                overheads=incoming_metadata.get("overheads"),
                request_timestamp=incoming_metadata.get("request_timestamp"),
                session_id=incoming_metadata.get("session_id"),
                deployment_id = incoming_metadata.get("deployment_id")
            )
        )
        # get the functions list for each record and add it to a dict to remove duplicates
        functions_metadata_list = incoming_metadata.get("functions")
        for data in functions_metadata_list:
            for fid, fdata in data.items():
                functions_metadata_dict[fid] = fdata
        list_obj.add_object(body=record.get("body"))
    # convert the function metadata dict to a list to be added to collated metadata
    for fid, fdata in functions_metadata_dict.items():
        collated_functions_metadata_list.append({fid: fdata})
    collated_metadata.update(functions=collated_functions_metadata_list)
    # NOTE - remove the unnecesary serialisation
    list_obj.add_metadata(collated_metadata)
    return list_obj


def build_serwo_object(event):
    return SerWOObject(body=event["body"], metadata=event["metadata"])
