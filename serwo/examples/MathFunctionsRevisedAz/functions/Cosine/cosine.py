from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
from math import cos, pi
import time as t


def cos_handler(body):
    startTime = t.time()
    for i in range(int(body['iters'])):
        for x in range(int(body['integer'])):
            result = cos(x*pi/180)
    endTime = t.time()
    elaspedTime = str(endTime-startTime) + " seconds"

    print("\nLatency for computing cosine: " +elaspedTime)

    return result

# User function (Add your logic here)
def Cosine(xfaas_object):
    try:
        body = xfaas_object.get_body()
        result = cos_handler(body)
        returnbody = {
            f"Cosine of {body['integer']} degrees": result
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")

path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/Cosine/inputs/input.json'
# write_req_to_file(r_int, path)
req = build_req_from_file(path)
c1 = Cosine(req)