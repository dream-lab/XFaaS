from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import networkx as nx
# function specific imports
import logging
from networkx.readwrite import json_graph
import json


def MST(body):
    graph = nx.adjacency_graph(body.get("graph"))
    logging.info(graph)


    mst = nx.minimum_spanning_tree(graph)
    result = list(mst.edges)

    returnbody = {
        "function": "MST",
        "result": result,
    }
    return returnbody


def MSTHandler(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = MST(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)

path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/graphMST/input.json'
req = build_req_from_file(path)
mst_ret = MSTHandler(req)

print(mst_ret.get_body())