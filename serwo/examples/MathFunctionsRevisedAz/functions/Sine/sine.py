import time as t
from math import sin, pi
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file

def sin_handler(body):
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


def Sine(xfaas_object):
    try:
        body = xfaas_object.get_body()
        result= sin_handler(body)
        returnbody = {
            f"Sine of {body['integer']} degrees": result
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")


path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/Sine/inputs/input.json'
# write_req_to_file(r_int, path)
req = build_req_from_file(path)
s1 = Sine(req)