from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList
from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object, build_req_from_file
import os
import time

"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj

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



path = '/home/azureuser/XFaaS/serwo/examples/FileSystemRevisedAz/functions/AggregateLines/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

time.sleep(2)
ag = AggrLines(l_obj)
