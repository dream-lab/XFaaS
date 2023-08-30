
from pyaes import AESModeOfOperationCTR


# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
def encryptionHandler(message, numOfIterations):
    KEY = b"\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,"
    for loops in range(numOfIterations):
        aes = AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)

    return(ciphertext)
def user_function(xfaas_object):
    try:
        print("Inside user function ")

        body = xfaas_object.get_body()
        text = body["text"]
        numOfIterations = body["numIters"]
        ret = encryptionHandler(text, numOfIterations)
        output=str(ret)
        returnbody = {"encrypted_string": output}

        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
