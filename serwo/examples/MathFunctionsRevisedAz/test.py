import random
import time as t
import numpy as np
from math import sin, cos, pi
import math
import json
import objsize
from json import JSONEncoder
from numpy import linalg
# XFaaS specific imports
import os
from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList
from python.src.utils.classes.commons.serwo_objects import build_req_from_file, write_req_to_file, build_serwo_list_object
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


#/////////////////////////////////////
#               Source
#/////////////////////////////////////
def Source(xfaas_object):
    try:
        print("\n\n\n\n",xfaas_object)
        body = xfaas_object.get_body()
        if 'seed' in body and 'iters' in body:
            ub = body['upper_bound']
            returnbody = body
        else:
            seed = random.randrange(10000)
            iters = random.randrange(10000)
            ub = body['upper_bound']
            returnbody = {
                'seed': seed,
                'iters': iters,
                'upper_bound': ub
            }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#            Generate Int
#/////////////////////////////////////
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


def GenerateInt(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = generate(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#               Sine
#/////////////////////////////////////
def sin_handler(body):
    """This function will calculate sine(integer) multiple times and returns the latency"""
    #estimating latency for evaluating sine for numbers in range 'integer' for 'iters' number of times.
    startTime = t.time()
    for i in range(int(body['iters'])):
        for x in range(int(body['integer'])):
            result = sin(x*pi/180)
    endTime = t.time()
    elaspedTime = str(endTime-startTime) + " seconds"
    print("\nLatency for computing sine: " + elaspedTime)
    return result


def Sine(xfaas_object):
    try:
        body = xfaas_object.get_body()
        result= sin_handler(body)
        returnbody = {
            f"Sine of {body['integer']} degrees": result
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#               Cosine
#/////////////////////////////////////
def cos_handler(body):
    startTime = t.time()
    for i in range(int(body['iters'])):
        for x in range(int(body['integer'])):
            result = cos(x*pi/180)
    endTime = t.time()
    elaspedTime = str(endTime-startTime) + " seconds"

    print("\nLatency for computing cosine: " +elaspedTime)

    return result

# User function (Add your logic here)
def Cosine(xfaas_object):
    try:
        body = xfaas_object.get_body()
        result = cos_handler(body)
        returnbody = {
            f"Cosine of {body['integer']} degrees": result
        }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#               Factors
#/////////////////////////////////////
# find all factors of num and sort them
def fact_handler(num: int, req: int):
    start_time = t.time()
    n_factors = []
    for i in range(req):
        n_factors = []
        for i in range(1, math.floor(math.sqrt(num)) + 1):
            if num % i == 0:
                n_factors.append(i)
                if num / i != i:
                    n_factors.append(int(num / i))

    n_factors.sort()
    end_time = t.time()

    print("\nLatency for finding factors: " +str(end_time-start_time)+" seconds")

    return n_factors


# main function to implement XFAAS framework
def Factors(xfaas_object: SerWOObject) -> SerWOObject:
    try:
        # body contains the input json data given in postman
        body = xfaas_object.get_body()
        list_of_factors = fact_handler(int(body['integer']), int(body['iters']))
        returnbody = {
            f"Factors of {body['integer']}": list_of_factors
        }
        return SerWOObject(body=returnbody)

    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#               Aggregate
#/////////////////////////////////////
def Aggregate(serwo_list_object) -> SerWOObject:
    try:
        objects = serwo_list_object.get_objects()
        print(objects)
        returnbody = {}
        for obj in objects:
            body = obj.get_body()
            for key in body:
                returnbody[key] = body[key]
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#            Generate List
#/////////////////////////////////////
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
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#               FFT
#/////////////////////////////////////
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
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#        Matrix Generation
#/////////////////////////////////////

def matGen_handlerA(body):

    StartTime = t.time()

    # Generating the size of the matrix
    np.random.seed(body['seed'])
    ub = body['upper_bound']
    # size = np.random.randint(ub)
    size = 72

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
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#/////////////////////////////////////
#        Matrix Multiplication B
#/////////////////////////////////////

def matGen_handlerB(body):

    StartTime = t.time()

    # Generating the size of the matrix
    np.random.seed(body['seed'])
    ub = body['upper_bound']
    # size = np.random.randint(ub)
    size = 72

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
def GenerateMatrixB(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = matGen_handlerB(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////


#////////////////////////////////////
#              Linpack
#////////////////////////////////////
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
#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////

#////////////////////////////////////
#              Matrix Mult
#////////////////////////////////////
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


#/////////////////////////////////////
#/////////////////////////////////////
#/////////////////////////////////////
"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj


body = {"seed":10, "iters": 1, "upper_bound": 170}

req = SerWOObject(body=body)

path = '/home/nikhil/work/xfaas-workloads/functions/math/source/samples/large/input/input.json'
write_req_to_file(req, path)
req = build_req_from_file(path)
r1 = Source(req)
path = '/home/nikhil/work/xfaas-workloads/functions/math/source/samples/large/output/output.json'
write_req_to_file(r1, path)


path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_list/samples/large/input/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
r_list = GenerateList(r1)
path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_list/samples/large/output/output.json'
write_req_to_file(r_list, path)

# r0 = r_list.get_body()
# j1 = json.dumps(r0)
# j2 = json.dumps(r0, indent=2)

# j1s = objsize.get_deep_size(j1)
# j2s = objsize.get_deep_size(j2)
# rqs = objsize.get_deep_size(r_list)
# print("-----------OP GLST-----------")
# print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
# print("=============================\n\n")


path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_int/samples/large/input/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
r_int = GenerateInt(r1)
path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_int/samples/large/output/output.json'
write_req_to_file(r_int, path)


path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_matrix_a/samples/large/input/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
m1 = GenerateMatrixA(r1)
path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_matrix_a/samples/large/output/output.json'
write_req_to_file(m1, path)


path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_matrix_b/samples/large/input/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
m2 = GenerateMatrixB(r1)
path = '/home/nikhil/work/xfaas-workloads/functions/math/gen_matrix_b/samples/large/output/output.json'
write_req_to_file(m2, path)

r0 = m2.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(m2)
print("-----------OP GGEN-----------")
print(f"JSON DUMP : {j1s/1024*2}\nJSON DUMP INDENT : {j2s/1024*2}\nSerWOObject : {rqs/1024*2}")
print("=============================\n\n")

path = '/home/nikhil/work/xfaas-workloads/functions/math/sine/samples/large/input/input.json'
write_req_to_file(r_int, path)
req = build_req_from_file(path)
s1 = Sine(r_int)
path = '/home/nikhil/work/xfaas-workloads/functions/math/sine/samples/large/output/output.json'
write_req_to_file(s1, path)


path = '/home/nikhil/work/xfaas-workloads/functions/math/cosine/samples/large/input/input.json'
write_req_to_file(r_int, path)
req = build_req_from_file(path)
c1 = Cosine(r_int)
path = '/home/nikhil/work/xfaas-workloads/functions/math/cosine/samples/large/input/input.json'
write_req_to_file(c1, path)


path = '/home/nikhil/work/xfaas-workloads/functions/math/factors/samples/large/input/input.json'
write_req_to_file(r_int, path)
req = build_req_from_file(path)
fc = Factors(r_int)
path = '/home/nikhil/work/xfaas-workloads/functions/math/factors/samples/large/output/output.json'
write_req_to_file(fc, path)


fanin_list = [s1, c1, fc]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/nikhil/work/xfaas-workloads/functions/math/Aggregator1/samples/large/input/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/nikhil/work/xfaas-workloads/functions/math/Aggregator1/samples/large/input/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

ag1 = Aggregate(l_obj)


path = '/home/nikhil/work/xfaas-workloads/functions/math/fast_fourier_transform/samples/large/input/input.json'
write_req_to_file(r_list, path)
req = build_req_from_file(path)
ff = FFT(r_list)
path = '/home/nikhil/work/xfaas-workloads/functions/math/fast_fourier_transform/samples/large/output/output.json'
write_req_to_file(ff, path)


fanin_list = [m1, m2]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/nikhil/work/xfaas-workloads/functions/math/Aggregator2/samples/large/input/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/nikhil/work/xfaas-workloads/functions/math/Aggregator2/samples/large/input/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

ag2 = Aggregate(l_obj)

path = '/home/nikhil/work/xfaas-workloads/functions/math/matrix_multiplication/samples/large/input/input.json'
write_req_to_file(ag2, path)
req = build_req_from_file(path)
mm = MatMul(ag2)
path = '/home/nikhil/work/xfaas-workloads/functions/math/matrix_multiplication/samples/large/output/output.json'
write_req_to_file(mm, path)



path = '/home/nikhil/work/xfaas-workloads/functions/math/linpack/samples/large/input/input.json'
write_req_to_file(ag2, path)
req = build_req_from_file(path)
lp = Linpack(ag2)
path = '/home/nikhil/work/xfaas-workloads/functions/math/linpack/samples/large/output/output.json'
write_req_to_file(lp, path)


fanin_list = [mm, lp]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/nikhil/work/xfaas-workloads/functions/math/Aggregator3/samples/large/input/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/nikhil/work/xfaas-workloads/functions/math/Aggregator3/samples/large/input/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

ag3 = Aggregate(l_obj)


fanin_list = [ag1, ag3, ff]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/nikhil/work/xfaas-workloads/functions/math/aggregator/samples/large/input/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/nikhil/work/xfaas-workloads/functions/math/aggregator/samples/large/input/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        print("NOWWWWWWWWWWWWWWWWWW")
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

# path = '/home/nikhil/work/xfaas-workloads/functions/math/aggregator/samples/large/input/input.json'
# write_req_to_file(l_obj, path)
ag4 = Aggregate(l_obj)
path = '/home/nikhil/work/xfaas-workloads/functions/math/aggregator/samples/large/output/output.json'
write_req_to_file(ag4, path)