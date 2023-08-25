# XFaaS specific imports
from .python.src.utils.classes.commons.serwo_objects import SerWOObject
import json
#function specific imports
import time as t
import numpy as np
import random
from json import JSONEncoder
np.random.seed(1)

import logging
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def handle(body):

    StartTime = t.time()

    # Generating the size of the matrix
    np.random.seed(body['seed'])
    size = np.random.randint(100)

    #Generating a matrix by resetting the seed
    randomNo = random.randint(0,10000)
    np.random.seed(body['seed']+randomNo)
    matrix = np.random.rand(size, size)

    EndTime = t.time()
    print("\nLatency of random matrix generation: " +str(EndTime-StartTime)+" seconds")
    returnbody = {
        'matrixB': json.dumps(matrix,cls=NumpyArrayEncoder),
        'size': size,
        'iters': body['iters']
    }

    return returnbody

# User function
def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = handle(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)