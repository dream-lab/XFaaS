import json
class SerWOObject:
    def __init__(self, body=None, error=None, metadata=None) -> None:
        self._body = body
        self._err = error  # Either body might be set or error might be set
        self._metadata = metadata

    def get_body(self):
        return self._body

    def get_metadata(self):
        return self._metadata

    def get_error(self, key):
        return self._err

    def has_error(self):
        if self._err is not None:
            return True
        else:
            return False

    def to_json(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_dct):
        return SerWOObject(json_dct['_body'],
                           json_dct['_err'],
                           json_dct['_metadata'])


class SerWOObjectsList:
    def __init__(self, body=None) -> None:
        self._object_list = []
        if body:
            self._object_list.append(SerWOObject(body))

    def get_objects(self):
        return self._object_list

    def add_object(self, body):
        self._object_list.append(SerWOObject(body))


def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(SerWOObject(body=record["body"]))


def build_serwo_object(event):
    return SerWOObject(body=event["body"],metadata=event['metadata'])
