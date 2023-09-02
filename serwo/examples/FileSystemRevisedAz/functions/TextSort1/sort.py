from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file


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



path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/TextSort1/inputs/input.json'
req = build_req_from_file(path)
st2 = Sort(req)