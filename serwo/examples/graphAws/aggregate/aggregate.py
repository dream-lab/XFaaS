# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging
def aggregate(body, returnbody):
    returnbody["RESULT"][body["function"]]=body["result"]
    return returnbody

def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_objects()
        returnbody = {}
        returnbody["RESULT"] = {}
        for idx , body in enumerate(xfaas_object.get_objects()):
            body = body.get_body()
            aggregate(body, returnbody)
        return SerWOObject(body=returnbody)

    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
