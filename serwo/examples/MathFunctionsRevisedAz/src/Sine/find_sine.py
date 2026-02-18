# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

#function specific imports
import time as t
from math import sin, pi


def handle(body):
    """This function will calculate sine(integer) multiple times and returns the latency"""
    #estimating latency for evaluating sine for numbers in range 'integer' for 'iters' number of times.
    startTime = t.time()
    for i in range(int(body['iters'])):
        for x in range(int(body['integer'])):
            result = sin(x*pi/180)
    endTime = t.time()
    elaspedTime = str(endTime-startTime) + " seconds"
    print("\nLatency for computing sine: " + elaspedTime)
    return result


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        result= handle(body)
        returnbody = {
            f"Sine of {body['integer']} degrees": result
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")