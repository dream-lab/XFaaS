from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import *
import random
from pyaes import AESModeOfOperationCTR
import os
import objsize


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
        # print("Inside user function ")
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
    # print('pointers: ', pointers)
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
def SingleString(xfaas_object):
    try:
        # print("Inside user function ")

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
        # print("Inside user function ")

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
        # req = SerWOObject.from_json(req_json)
        req = SerWOObject(body=req_json)
    return req

def write_req_to_file(req, path):
    with open(path, "w") as file:
        # Write data to the file
        # file.write(req.to_json())
        body = req.get_body()
        file.write(json.dumps(body))

body = {"numIters":1,
        "numLines":50,
        "numChars":100}

# body = {"numIters":1,
#         "numLines":200,
#         "numChars":100}

# body = {"numIters":1,
#         "numLines":1100,
#         "numChars":100}

req = SerWOObject(body=body)

j1 = json.dumps(body)
j2 = json.dumps(body, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(req)
print("-----------IP TRIG-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/text/trigger/samples/small/input/input.json'
write_req_to_file(req, path)
req = build_req_from_file(path)
r1 = Trigger(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/trigger/samples/small/output/output.json'
write_req_to_file(r1, path)

r0 = r1.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(r1)
print("-----------OP TRIG-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")

body = r1.get_body()
j1 = json.dumps(body)
j2 = json.dumps(body, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(r1)
print("-----------IP TGEN-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/text/text_data_gen/samples/small/input/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
t1 = TextGen(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/trigger/samples/small/output/output.json'
write_req_to_file(t1, path)

r0 = t1.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(t1)
print("-----------OP TGEN-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")



body = t1.get_body()
j1 = json.dumps(body)
j2 = json.dumps(body, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(t1)
print("-----------IP TSRT-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/text/text_sort/samples/small/input/input.json'
write_req_to_file(t1, path)
req = build_req_from_file(path)
st1 = Sort(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/text_sort/samples/small/output/output.json'
write_req_to_file(st1, path)

r0 = st1.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(st1)
print("-----------OP TSRT-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")


path = '/home/nikhil/work/xfaas-workloads/functions/text/TextFileData1/samples/small/input/input.json'
write_req_to_file(r1, path)
req = build_req_from_file(path)
t2 = TextGen(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/text_sort/samples/small/output/output.json'
write_req_to_file(t2, path)



path = '/home/nikhil/work/xfaas-workloads/functions/text/TextSort1/samples/small/input/input.json'
write_req_to_file(t2, path)
req = build_req_from_file(path)
st2 = Sort(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/TextSort1/samples/small/output/output.json'
write_req_to_file(st2, path)


fanin_list = [st1, st2]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/nikhil/work/xfaas-workloads/functions/text/aggregate_lines/samples/small/input/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/nikhil/work/xfaas-workloads/functions/text/aggregate_lines/samples/small/input/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)


obs = l_obj.get_objects()
lsz = 0
lsz_ind = 0
for ob in obs:
    bd = ob.get_body()
    osj1 = json.dumps(bd)
    osj2 = json.dumps(bd, indent=2)
    lsz = lsz + objsize.get_deep_size(osj1)
    lsz_ind = lsz + objsize.get_deep_size(osj2)

j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(l_obj)
print("-----------IP AGGR-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
ag = AggrLines(l_obj)
path = '/home/nikhil/work/xfaas-workloads/functions/text/aggregate_lines/samples/small/output/output.json'
write_req_to_file(ag, path)


r0 = ag.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ag)
print("-----------OP AGGR-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")



body = ag.get_body()
j1 = json.dumps(body)
j2 = json.dumps(body, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ag)
print("-----------IP MSRT-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/text/merge_aggregate/samples/small/input/input.json'
write_req_to_file(ag, path)
req = build_req_from_file(path)
mg = Merge(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/merge_aggregate/samples/small/output/output.json'
write_req_to_file(mg, path)

r0 = mg.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(mg)
print("-----------OP MSRT-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")


body = mg.get_body()
j1 = json.dumps(body)
j2 = json.dumps(body, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(mg)
print("-----------IP SSTR-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/text/single_string/samples/small/input/input.json'
write_req_to_file(mg, path)
req = build_req_from_file(path)
ss = SingleString(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/single_string/samples/small/output/output.json'
write_req_to_file(ss, path)

r0 = ss.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ss)
print("-----------OP SSTR-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")


body = ss.get_body()
j1 = json.dumps(body)
j2 = json.dumps(body, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ss)
print("-----------IP ENCR-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/text/encrypt/samples/small/input/input.json'
write_req_to_file(ss, path)
req = build_req_from_file(path)
en = Encrypt(req)
path = '/home/nikhil/work/xfaas-workloads/functions/text/encrypt/samples/small/output/output.json'
write_req_to_file(en, path)
# print(en.get_body())

r0 = en.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(en)
print("-----------OP ENCR-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")