# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import networkx as nx
# function specific imports
import logging
from networkx.readwrite import json_graph
import json
def handler(event):

    size = event.get('size')
    edges = event.get('edges')
    for key in event.keys():
        if key == "startVertex":
            startVertex = event.get('startVertex')
            break
    else:
        startVertex = None

    graph = nx.barabasi_albert_graph(size, edges)

    graph_dict = json_graph.adjacency_data(graph)
    returnbody = {
            "graph": graph_dict,
            "startVertex": startVertex
    }
    
    return returnbody


def user_function(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        result = handler(body)
        print("Request has been processed")
        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)




