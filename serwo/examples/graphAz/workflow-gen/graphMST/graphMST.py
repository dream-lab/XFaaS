# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import networkx as nx
from networkx.readwrite import json_graph
import logging

def handle(body):
    graph = nx.adjacency_graph(body.get("graph"))
    logging.info(graph)


    mst = nx.minimum_spanning_tree(graph)
    result = list(mst.edges)

    returnbody = {
        "function": "MST",
        "result": result,
    }
    return returnbody


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()
        returnbody = handle(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)

