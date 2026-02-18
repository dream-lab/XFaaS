
# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging

def handler(event):
    print("EndNode Reached")
    return {
        "status": "Workflow Completed",
        "final_counter": event.get('flag_counter')
    }

def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        result = handler(body)
        print("EndNode processed")
        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
