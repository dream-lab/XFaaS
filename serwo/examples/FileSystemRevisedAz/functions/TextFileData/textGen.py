import random
import time
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file


def generate_random_lines(n, size):
    lines = []
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    for _ in range(n):
        line = ''.join(random.choice(characters) for _ in range(size))
        lines.append(line)
    
    return lines

    
def gen_random_handler(body):
    n = body["numLines"]
    size = body["numChars"]
    numIters = body["numIters"]
    rnd_text = generate_random_lines(n, size)
    return {
            "rndText": rnd_text,
            "numIters": numIters
    }


def TextGen(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = gen_random_handler(body)
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/TextFileData/inputs/input.json'
req = build_req_from_file(path)
time.sleep(2)
t1 = TextGen(req)
