# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

#function specific imports
import time as t
from math import cos, pi


def handle(body):
    startTime = t.time()
    for i in range(int(body['iters'])):
        for x in range(int(body['integer'])):
            result = cos(x*pi/180)
    endTime = t.time()
    elaspedTime = str(endTime-startTime) + " seconds"

    print("\nLatency for computing cosine: " +elaspedTime)

    return result

# User function (Add your logic here)
def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        result = handle(body)
        returnbody = {
            f"Cosine of {body['integer']} degrees": result
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")