import time as t
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import math


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
    
path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/Factors/inputs/input.json'
# write_req_to_file(r_int, path)
req = build_req_from_file(path)
fc = Factors(req)

print(fc.get_body())