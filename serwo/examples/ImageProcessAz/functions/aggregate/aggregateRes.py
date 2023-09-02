from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
from python.src.utils.classes.commons.serwo_objects import build_serwo_list_object
import os

"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj

def Aggregate(xfaas_object):
    try:
        print("Inside user function : Aggregator")
        results = []

        for idx, item in enumerate(xfaas_object.get_objects()):
            body = item.get_body()
            results.append(body)
        predictions = {"Predictions": results}
        return SerWOObject(body=predictions)

    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")


path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/aggregate/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)
res = Aggregate(l_obj)