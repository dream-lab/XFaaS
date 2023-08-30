import numpy as np
import time as t

# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject



def generate(body):
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


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = generate(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")