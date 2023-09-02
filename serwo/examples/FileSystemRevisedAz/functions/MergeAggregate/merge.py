from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file


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


def Merge(xfaas_object):
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


path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/MergeAggregate/inputs/input.json'
req = build_req_from_file(path)
mg = Merge(req)
