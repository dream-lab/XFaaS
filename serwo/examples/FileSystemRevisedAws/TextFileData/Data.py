import random
# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

def generate_random_lines(n, size):
    lines = []
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    for _ in range(n):
        line = ''.join(random.choice(characters) for _ in range(size))
        lines.append(line)
    
    return lines

    
def handle(body):
    n = body["numLines"]
    size = body["numChars"]
    numIters = body["numIters"]
    rnd_text = generate_random_lines(n, size)
    return {
            "rndText": rnd_text,
            "numIters": numIters
    }


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = handle(body)
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
