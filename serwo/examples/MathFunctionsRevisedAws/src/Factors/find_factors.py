# python specific imports
import math
import time as t

# xfaas specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


# find all factors of num and sort them
def handler(num: int, req: int) -> List[int]:
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
def user_function(xfaas_object: SerWOObject) -> SerWOObject:
    try:
        # body contains the input json data given in postman
        body = xfaas_object.get_body()
        list_of_factors = handler(int(body['integer']), int(body['iters']))
        returnbody = {
            f"Factors of {body['integer']}": list_of_factors
        }
        return SerWOObject(body=returnbody)

    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")