import time as t
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import numpy as np

def gen_list(body):
    start = t.time()
    np.random.seed(body['seed'])
    param = np.random.rand(10000)
    param = param.tolist()
    end = t.time()

    print("\nLatency for random list generation: "+str(end-start)+" seconds")

    returnbody = {
        'list': param,
        'iters': body['iters']
    }

    return returnbody


def GenerateList(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = gen_list(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")

path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/GenerateList/inputs/input.json'
# write_req_to_file(r1, path)
req = build_req_from_file(path)
r_list = GenerateList(req)
