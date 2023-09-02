import json
from numpy import linalg
import time as t
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file

def linpack_handler(matrix_A, matrix_B, n):
    ops = (2.0 * n) * n * n / 3.0 + (2.0 * n) * n
    start = t.time()
    x = linalg.solve(matrix_A, matrix_B)
    latency = t.time() - start
    mflops = (ops * 1e-6 / latency)

    print('\nLatency for lin_pack: ' + str(latency)+" seconds")

    return mflops

def Linpack(xfaas_object):
    try:
        body = xfaas_object.get_body()
        Body_A = body['matrixA']
        Body_B = body['matrixB']
        mflops = linpack_handler(json.loads(Body_A), json.loads(Body_B), body['size'])
        returnbody = {
            'linpack_mflops': mflops
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/Linpack/inputs/input.json'
# write_req_to_file(r_int, path)
req = build_req_from_file(path)
lp = Linpack(req)