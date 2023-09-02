from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList
from python.src.utils.classes.commons.serwo_objects import build_req_from_file, build_serwo_list_object
import os

"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj

def Aggregate(serwo_list_object) -> SerWOObject:
    try:
        objects = serwo_list_object.get_objects()
        print(objects)
        returnbody = {}
        for obj in objects:
            body = obj.get_body()
            for key in body:
                returnbody[key] = body[key]
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")

path = '/home/azureuser/XFaaS/serwo/examples/MathFunctionsRevisedAz/functions/Aggregator1/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

ag1 = Aggregate(l_obj)

