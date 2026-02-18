# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

def merge(lists):
    n_pointers = len(lists)
    pointers = [0] * n_pointers
    print('pointers: ', pointers)
    result = []
    while True:
        min_val = None
        min_val_idx = None
        for i in range(n_pointers):
            if pointers[i] < len(lists[i]):
                if min_val is None or lists[i][pointers[i]] < min_val:
                    min_val = lists[i][pointers[i]]
                    min_val_idx = i
        if min_val_idx is None:
            break
        result.append(min_val)
        pointers[min_val_idx] += 1
    return result


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        lines = body["text"]
        sorted_lines = merge(lines)
        numIters = body["numIters"]
        returnbody = { "text" : sorted_lines, "numIters":numIters }
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
    
