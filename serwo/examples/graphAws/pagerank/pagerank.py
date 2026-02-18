# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import networkx as nx
from networkx.readwrite import json_graph

import logging
def handler(body):

    graph = nx.adjacency_graph(body.get("graph"))
    logging.info(graph)
 
    result = nx.pagerank(graph)

    return {
            'function': 'Pagerank',
            'result': result,
    }


def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        returnbody = handler(body)
        print("Request has been processed")
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)




