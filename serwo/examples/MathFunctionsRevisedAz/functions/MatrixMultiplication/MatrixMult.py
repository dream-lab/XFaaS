import time as t
import numpy as np
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file


def matMul_gen(matrix_A, matrix_B, iters):
    # multiply the two matrices using np.matmul

    startTime = t.time()
    for i in range(iters):
        result = np.matmul(matrix_A, matrix_B)
    endTime = t.time()

    timeElapsed = str(endTime-startTime) + " seconds"

    print('\nLatency for multiplying matrices: '+str(timeElapsed))

    return result

def MatMul(xfaas_object):
    try:
        body = xfaas_object.get_body()
        Body_A = body['matrixA']
        Body_B = body['matrixB']

        result = matMul_gen(json.loads(Body_A), json.loads(Body_B), body['iters'])
        returnbody = {
            'Resulting matrix from multiplication of two randomly generated matrices': str(result)
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/MatrixMultiplication/inputs/input.json'
# write_req_to_file(r_int, path)
req = build_req_from_file(path)
mm = MatMul(req)