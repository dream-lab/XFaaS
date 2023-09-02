import time as t
import numpy as np
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file

def fft_handler(iters, x):
    startTime = t.time()
    for i in range(iters):
        y = np.fft.fft(x)
    endTime = t.time()

    print("\nLatency for performing fft: "+str(endTime - startTime)+" seconds")
    return y


def FFT(xfaas_object):
    try:
        body = xfaas_object.get_body()
        x = body['list']
        iters = body['iters']
        y = fft_handler(iters, x)
        returnbody = {
            'Resulting array on performing fft': str(y)
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
    
path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/FFT/inputs/input.json'
# write_req_to_file(r_int, path)
req = build_req_from_file(path)
ff = FFT(req)