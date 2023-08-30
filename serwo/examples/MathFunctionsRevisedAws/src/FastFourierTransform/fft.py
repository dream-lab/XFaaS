# Python base imports
import numpy as np
import time as t


# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def handle(iters, x):
    startTime = t.time()
    for i in range(iters):
        y = np.fft.fft(x)
    endTime = t.time()

    print("\nLatency for performing fft: "+str(endTime - startTime)+" seconds")
    return y


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        x = body['list']
        iters = body['iters']
        y = handle(iters, x)
        returnbody = {
            'Resulting array on performing fft': str(y)
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")