from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import networkx as nx
# function specific imports
import logging
import objsize

def BFT(body):
 
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

def BFTHandler(xfaas_object) -> SerWOObject:

    try:
        body = xfaas_object.get_body()
        returnbody = BFT(body)
        return SerWOObject(body=returnbody)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)

path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/graphBFT/input.json'
req = build_req_from_file(path)

i_sz = objsize.get_deep_size(req)
bft_ret = BFTHandler(req)
o_sz = objsize.get_deep_size(bft_ret)


with open('/home/azureuser/XFaaS/serwo/examples/graphAz/functions/in_out.txt', 'a+') as file:
    file.write(f'BFT, {i_sz}, {o_sz}\n')
    file.close()