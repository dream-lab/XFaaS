# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject

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


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        lines = body["text"]
        # Perform merge sort on the lines


        sorted_lines = merge_sort(lines)

        numIters = body["numIters"]

        returnbody = { "text" : sorted_lines, "numIters":numIters }


        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
    
