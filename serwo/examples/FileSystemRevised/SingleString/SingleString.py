# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
def user_function(xfaas_object):
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
