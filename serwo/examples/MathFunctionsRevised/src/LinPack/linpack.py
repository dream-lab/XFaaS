from numpy import linalg
from time import time
from .python.src.utils.classes.commons.serwo_objects import SerWOObject
import json

def handle(matrix_A, matrix_B, n):
    ops = (2.0 * n) * n * n / 3.0 + (2.0 * n) * n
    start = time()
    x = linalg.solve(matrix_A, matrix_B)
    latency = time() - start
    mflops = (ops * 1e-6 / latency)

    print('\nLatency for lin_pack: ' + str(latency)+" seconds")

    return mflops

def user_function(serwo_list_object):
    try:
        objects = serwo_list_object.get_objects()
        Body_A = objects[0].get_body()
        Body_B = objects[1].get_body()
        mflops = handle(json.loads(Body_A['matrix']), json.loads(Body_B['matrix']), Body_A['size'])
        returnbody = {
            'linpack_mflops': mflops
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)