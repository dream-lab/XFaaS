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
    print(f'Output size Trigger : {sz}')
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
    print(f'Input size TextFileData : {sz}')
    rnd_text = generate_random_lines(n, size)
    bod = {
            "rndText": rnd_text,
            "numIters": numIters
    }
    sz = objsize.get_deep_size(bod)
    print(f'Output size TextFileData : {sz}')
    print("------------------------------------")
    return bod

def sorter(lines):
    sz = objsize.get_deep_size(lines)
    print(f'Input size sorter : {sz}')
    for line in lines:
        line = sorted(line)
    sz = objsize.get_deep_size(lines)
    print(f'Output size sorter : {sz}')
    print("------------------------------------")
    return lines

def AggLines (strings):
    sz = objsize.get_deep_size(strings)
    print(f'Input size AggLines : {sz}')
    st = []
    for text in strings:
        st.append(text)
    c = ''.join(st)
    sz = objsize.get_deep_size(c)
    print(f'Output size AggLines : {sz}')
    print("------------------------------------")
    return c

def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = arr[:mid]
    right_half = arr[mid:]

    left_half = merge_sort(left_half)
    right_half = merge_sort(right_half)

    return merge(left_half, right_half)

def merge(left, right):
    result = []
    left_index, right_index = 0, 0

    while left_index < len(left) and right_index < len(right):
        if left[left_index] < right[right_index]:
            result.append(left[left_index])
            left_index += 1
        else:
            result.append(right[right_index])
            right_index += 1

    result.extend(left[left_index:])
    result.extend(right[right_index:])

    return result

def encryptionHandler(message, numOfIterations):
    sz = objsize.get_deep_size(message)
    print(f'Input size Encryption : {sz}')
    KEY = b"\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,"
    for loops in range(numOfIterations):
        aes = AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)

    sz = objsize.get_deep_size(ciphertext)
    print(f'Output size Encryption : {sz}')
    print("------------------------------------")
    return(ciphertext)


#-----------------------------------------------------
#-----------------------------------------------------

body = {"numLines": int(sys.argv[1]),
        "numChars": int(sys.argv[2]),
        "numIters": int(sys.argv[3])}

r1 = Trigger(body)
r2 = TextFileData(r1)
r3 = sorter(r2)
lines = AggLines(r3["rndText"])
r4 = {"text": lines}
sz = objsize.get_deep_size(r4["text"])
print(f'Input size merge_sort : {sz}')
r5 = merge_sort(r4["text"])
sz = objsize.get_deep_size(r5)
print(f'Output size merge_sort : {sz}')
print("------------------------------------")
r5 = ''.join(r5)
r6 = encryptionHandler(r5, body["numIters"])
# print(r6)