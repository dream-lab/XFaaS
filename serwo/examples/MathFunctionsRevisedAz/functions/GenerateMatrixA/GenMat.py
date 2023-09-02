import time as t
import numpy as np
import random
import json
from json import JSONEncoder
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def matGen_handlerA(body):

    StartTime = t.time()

    # Generating the size of the matrix
    np.random.seed(body['seed'])
    size = np.random.randint(72)

    #Generating a matrix by resetting the seed
    randomNo = random.randint(0,10000)
    np.random.seed(body['seed']+randomNo)
    matrix = np.random.rand(size, size)

    EndTime = t.time()
    print("\nLatency of random matrix generation: " +str(EndTime-StartTime)+" seconds")
    returnbody = {
        'matrixA': json.dumps(matrix,cls=NumpyArrayEncoder),
        'size': size,
        'iters': body['iters']
    }

    return returnbody

# User function
def GenerateMatrixA(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = matGen_handlerA(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)

path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/GenerateMatrixA/inputs/input.json'
# write_req_to_file(r1, path)
req = build_req_from_file(path)
m1 = GenerateMatrixA(req)