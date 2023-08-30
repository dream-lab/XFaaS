import random
import sys
from pyaes import AESModeOfOperationCTR
import objsize

def Trigger(body):
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
    sz = objsize.get_deep_size(body)
    print(f'Output size Trigger : {int(sz/1024)}')
    return body

def generate_random_lines(n, size):
    lines = []
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    for _ in range(n):
        line = ''.join(random.choice(characters) for _ in range(size))
        lines.append(line)
    
    return lines

    
def TextFileData(body):
    n = body["numLines"]
    size = body["numChars"]
    numIters = body["numIters"]
    sz = objsize.get_deep_size(body)
    print(f'Input size TextFileData : {int(sz/1024)}')
    rnd_text = generate_random_lines(n, size)
    bod = {
            "rndText": rnd_text,
            "numIters": numIters
    }
    sz = objsize.get_deep_size(bod)
    print(f'Output size TextFileData : {int(sz/1024)}')
    print("------------------------------------")
    return bod

def sorter(lines):
    sz = objsize.get_deep_size(lines)
    print(f'Input size sorter : {int(sz/1024)}')
    # for line in lines:
    lines = sorted(lines)
    sz = objsize.get_deep_size(lines)
    print(f'Output size sorter : {int(sz/1024)}')
    print("------------------------------------")
    return lines

def AggLines (strings):
    outt = []
    for st in strings:
        sz = objsize.get_deep_size(st)
        liss = []
        for text in st['sortedText']:
            liss.append(text)
        outt.append(liss)
        
    sz = objsize.get_deep_size(outt)
    print(f'Output size AggLines : {int(sz/1024)}')
    print("------------------------------------")
    return outt


def merge_n_sorted_lists(lists):
    print('here=== ',lists)
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
    print(result)
    return result


def encryptionHandler(message, numOfIterations):
    sz = objsize.get_deep_size(message)
    print(f'Input size Encryption : {int(sz/1024)}')
    KEY = b"\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,"
    for loops in range(numOfIterations):
        aes = AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)

    sz = objsize.get_deep_size(ciphertext)
    print(f'Output size Encryption : {int(sz/1024)}')
    print("------------------------------------")
    return(ciphertext)

def single_string(list_of_string):
    sz = objsize.get_deep_size(list_of_string)
    print(f'Input size single_string : {int(sz/1024)}')
    out = ''.join(list_of_string)
    sz = objsize.get_deep_size(out)
    print(f'Output size single_string : {int(sz/1024)}')
    print("------------------------------------")
    return out


#-----------------------------------------------------
#-----------------------------------------------------


body = {"numLines": int(sys.argv[1]),
        "numChars": int(sys.argv[2]),
        "numIters": int(sys.argv[3])}

print('body: ', body)
r1 = Trigger(body)
print('r1: ', r1)

r2 = TextFileData(r1)
print('r2: ', r2)
r3 = sorter(r2['rndText'])
body = {
            "sortedText":r3,
            "numIters": r2["numIters"]
        }
print('r3: ', body)
lines = AggLines([body, body, body])
r4 = {"text":lines,
            "numIters": r2["numIters"]}
print('r4: ', r4)

# sz = objsize.get_deep_size(r4["text"])
r5 = merge_n_sorted_lists(r4["text"])
print('r5: ', r5)
r5 = {"text":r5,
    "numIters": r2["numIters"]}

r6 = single_string(r5["text"])
print('r6: ', r6)
r6 = {"text":r6,
    "numIters": r2["numIters"]}

r7 = encryptionHandler(r6["text"], r6["numIters"])
print('r7: ', r7)
# sz = objsize.get_deep_size(r5)
# r5 = ''.join(r5)
# r6 = encryptionHandler(r5, body["numIters"])
