from python.src.utils.classes.commons.serwo_objects import SerWOObject

def sorter(lines):
    for line in lines:
        line = sorted(line)

    return lines

def user_function(xfaas_object):
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
