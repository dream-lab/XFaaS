import numpy as np
import time as t

# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

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


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = generate(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")