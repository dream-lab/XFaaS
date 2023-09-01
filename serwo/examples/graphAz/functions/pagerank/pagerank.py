# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import networkx as nx
# function specific imports
import logging


def PageRank(body):

    graph = nx.adjacency_graph(body.get("graph"))
    logging.info(graph)
 
    result = nx.pagerank(graph)

    return {
            'function': 'Pagerank',
            'result': result,
    }


def PageRankHandler(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        returnbody = PageRank(body)
        print("Request has been processed")
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/pagerank/input.json'
req = build_req_from_file(path)
pg_ret = PageRankHandler(req)

print(pg_ret.get_body())