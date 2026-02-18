
# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging

def handler(event):
    # Initialize flag_counter
    counter = event.get('flag_counter', 0)
    counter += 1
    
    poll_status = True
    if counter >= 3:
        poll_status = False
        
    return {
        "flag_counter": counter,
        "Poll": poll_status
    }

def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        result = handler(body)
        print(f"PollerNode processed. Counter: {result['flag_counter']}, Poll: {result['Poll']}")
        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
