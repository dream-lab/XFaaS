from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging
import networkx as nx
from networkx.readwrite import json_graph


def handle(body):
 
    graph = nx.adjacency_graph(body.get("graph"))
    logging.info(graph)

    startVertex = body.get("startVertex")
    if startVertex == None:
        startVertex = 0

    bfs_list = nx.bfs_successors(graph,startVertex)

    bfs = []
    i = 0
    for nd in bfs_list:
        if i == 0:
            bfs.append(nd[0])
        for e in nd[1]:
            bfs.append(e)
        i += 1

    returnbody = {
        "function": "BFS",
        "result": bfs,
    }

    return returnbody

def user_function(xfaas_object) -> SerWOObject:

    try:
        body = xfaas_object.get_body()
        returnbody = handle(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
