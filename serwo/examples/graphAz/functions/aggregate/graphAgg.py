from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object
import os
import logging
import time

"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj


def aggregate(body, returnbody):
    returnbody["RESULT"][body["function"]]=body["result"]
    return returnbody

def AggHandler(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_objects()
        returnbody = {}
        returnbody["RESULT"] = {}
        for idx , body in enumerate(xfaas_object.get_objects()):
            body = body.get_body()
            aggregate(body, returnbody)
        return SerWOObject(body=returnbody)

    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/aggregate/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)
time.sleep(2)
print("Starting")
res = AggHandler(l_obj)
