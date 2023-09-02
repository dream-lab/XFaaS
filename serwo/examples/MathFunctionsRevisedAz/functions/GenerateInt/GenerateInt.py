import numpy as np
import time as t
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file

def generate(body):

    # Generating a random integer
    start = t.time()
    np.random.seed(body['seed'])
    param = np.random.randint(10000)
    end = t.time()

    print("\nLatency for random number generation: " +str(end-start)+" seconds")

    returnbody = {
        'integer': param,
        'iters': body['iters']
    }

    return returnbody


def GenerateInt(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = generate(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")


path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/GenerateInt/inputs/input.json'
# write_req_to_file(r_list, path)
req = build_req_from_file(path)
r_int = GenerateInt(req)