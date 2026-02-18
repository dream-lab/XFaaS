
# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging

def handler(event):
    # Initialize flag_counter
    return {
        "flag_counter": 0
    }

def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        result = handler(body)
        print("StartNode processed")
        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
