from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import time


def SingleString(xfaas_object):
    try:
        print("Inside user function ")

        body = xfaas_object.get_body()
        # Name of the input text file
        sorted_strings = body["text"]
        numIters = body["numIters"]
        sorted_strings = ''.join(sorted_strings)

        
        returnbody = {"text":sorted_strings,
                      "numIters":numIters}
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/SingleString/inputs/input.json'
# write_req_to_file(mg, path)
req = build_req_from_file(path)
time.sleep(2)
ss = SingleString(req)
