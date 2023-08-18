"""
NOTE - creating a serwo wrapper object from cloud events
* a different wrapper object will be constructed for different event types
* for one particular event type one object will be constructed
    - we will need to find common keys in the event object for one event type across different FaaS service providers
    - objective is to create a list of common keys, access patterns which will be used to create a common object to pass around
    - 
"""
# QUESTION - do we need a wrapper parent class around these classes ? (HttpBaseClass.HttpRequestObjec , HttpBaseClass.HttpResponseObject)


class HttpWrapperRequestObject:
    # TODO - temporary, need to use a combination of design patterns to actually populate this
    def __init__(self, body, headers) -> None:
        self._body = body
        self._headers = headers

    def get_body(self):
        return self._body

    def get_headers(self):
        return self._headers


class HttpWrapperResponseObject:
    # TODO - temporary, need to use a combination of design patterns to actually populate this
    def __init__(self, body, headers, statusCode) -> None:
        self._body = body
        self._headers = headers
        self._statusCode = statusCode

    # QUESTION - do we encode the response body ?
    def get_body(self):
        return self._body

    def get_headers(self):
        return self._headers

    def get_status_code(self):
        return self._statusCode


# TODO - temporary builder
# polymorphism in python - (how to replicate ?)
def build_serwo_http_request_object(
    _cloudEventObject, _handler_identifier
) -> HttpWrapperRequestObject:
    # add a switch case for different _handler_identifiers
    httpWrapperRequestObject = HttpWrapperRequestObject(
        _cloudEventObject["body"], _cloudEventObject["headers"]
    )
    return httpWrapperRequestObject


def build_serwo_http_response_object(
    _responseBody, _responseHeaders, _statusCode, _handler_identifier
) -> HttpWrapperResponseObject:
    # add a switch case for different _handler_identifiers
    httpWrapperResponseObject = HttpWrapperResponseObject(
        _responseBody, _responseHeaders, _statusCode
    )
    return httpWrapperResponseObject
