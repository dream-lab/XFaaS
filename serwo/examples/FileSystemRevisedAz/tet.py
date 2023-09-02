from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import *
import random
from pyaes import AESModeOfOperationCTR
import os


#/////////////////////////////////////////////////
#                   Trigger
#/////////////////////////////////////////////////
def Trigger(xfaas_object):
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
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////

#/////////////////////////////////////////////////
#               Text Generation
#/////////////////////////////////////////////////
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

#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////



#/////////////////////////////////////////////////
#                   Sorter
#/////////////////////////////////////////////////

def Sort(xfaas_object):
    try:
        print("Inside user function ")
        body = xfaas_object.get_body()
        lines = body["rndText"]
        numIters = body["numIters"]

        # Call the function to decode and save the content
        res = sorted(lines)
        body = {
            "sortedText":res,
            "numIters":numIters
        }
        return SerWOObject(body = body)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////


#/////////////////////////////////////////////////
#                   Aggregate Lines
#/////////////////////////////////////////////////
def AggrLines(serwo_list_object):
    try:
        objects= serwo_list_object.get_objects()
        strings = []
        numIters = 0
        for obj in objects:
            body = obj.get_body()
            strings = body["sortedText"]
            numIters = body["numIters"]
            st = []
            for text in strings:
                st.append(text)
            strings.append(st)
            
        returnbody = {"text":strings,
                      "numIters":numIters}
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////

#/////////////////////////////////////////////////
#                   Merge Lines
#/////////////////////////////////////////////////

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
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////



#/////////////////////////////////////////////////
#                   Single String
#/////////////////////////////////////////////////
def SingelString(xfaas_object):
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
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////

#/////////////////////////////////////////////////
#                   Encryption
#/////////////////////////////////////////////////
def encryptionHandler(message, numOfIterations):
    KEY = b"\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,"
    for loops in range(numOfIterations):
        aes = AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)

    return(ciphertext)
def Encrypt(xfaas_object):
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
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
#/////////////////////////////////////////////////
"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj

def build_req_from_file(path):
    with open(path, "r") as file:
        # Write data to the file
        req_txt = file.read()
        req_json = json.loads(req_txt)
        req = SerWOObject.from_json(req_json)
    return req

def write_req_to_file(req, path):
    with open(path, "w") as file:
        # Write data to the file
        file.write(req.to_json())

body = {"numIters":1,
        "numLines":150,
        "numChars":100}

req = SerWOObject(body=body)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/Trigger/inputs/input.json'
write_req_to_file(req, path)
req = build_req_from_file(path)
r1 = Trigger(req)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/TextFileData/inputs/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
t1 = TextGen(req)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/TextSort/inputs/input.json'
write_req_to_file(t1, path)
req = build_req_from_file(path)
st1 = Sort(req)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/TextFileData1/inputs/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
t2 = TextGen(req)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/TextSort1/inputs/input.json'
write_req_to_file(t2, path)
req = build_req_from_file(path)
st2 = Sort(req)

fanin_list = [st1, st2]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/AggregateLines/inputs/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/AggregateLines/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)
ag = AggrLines(l_obj)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/MergeAggregate/inputs/input.json'
write_req_to_file(ag, path)
req = build_req_from_file(path)
mg = Merge(req)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/SingleString/inputs/input.json'
write_req_to_file(mg, path)
req = build_req_from_file(path)
ss = SingelString(req)

path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/Encrypt/inputs/input.json'
write_req_to_file(ss, path)
req = build_req_from_file(path)
en = Encrypt(req)

print(en.get_body())
