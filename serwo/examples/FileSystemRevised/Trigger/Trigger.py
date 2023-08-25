import random

# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        if body is not None:
            if "numLines" in body:
                n = int((body["numLines"]))
            else:
                n = 10000

            if "numChars" in body:
                size = int((body["numChars"]))
            else:
                size = 10240

            if "numIters" in body:
                iters = int((body["numChars"]))
            else:
                iters = random.randint(10,100)


        body = {"numIters":iters,
                "numLines":n,
                "numChars":size}
    
        return SerWOObject(body)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
