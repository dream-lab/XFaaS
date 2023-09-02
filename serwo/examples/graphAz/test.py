# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import *
import networkx as nx
# function specific imports
import logging
from networkx.readwrite import json_graph
import json
import os


#///////////////////////////////////////////////////////////////
#/////////////////////////GRAPH GEN/////////////////////////////
#///////////////////////////////////////////////////////////////
def graphGen(event):

    size = event.get('size')
    for key in event.keys():
        if key == "startVertex":
            startVertex = event.get('startVertex')
            break
    else:
        startVertex = None

    if "graph_type" in event:
        graph_type = event.get("graph_type")
    else:
        graph_type = "complete"

    if graph_type.lower() == "barabasi":
        edges = event.get('edges')
        graph = nx.barabasi_albert_graph(size,edges)
    elif graph_type.lower() == "binomial_tree":
        graph = nx.binomial_tree(size)
    elif graph_type.lower() == "power_law":
        edges = event.get('edges')
        graph = nx.powerlaw_cluster_graph(size,edges,p=0.5)
    else:
        graph = nx.complete_graph(size)

    graph_dict = json_graph.adjacency_data(graph)
    returnbody = {
            "graph": graph_dict,
            "startVertex": startVertex
    }
    
    return returnbody


def graphGenHandler(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_body()
        result = graphGen(body)
        print("Request has been processed")
        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)

#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////

#///////////////////////////////////////////////////////////////
#/////////////////////////BFT///////////////////////////////////
#///////////////////////////////////////////////////////////////
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

#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////

#///////////////////////////////////////////////////////////////
#/////////////////////////MST///////////////////////////////////
#///////////////////////////////////////////////////////////////
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
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////


#///////////////////////////////////////////////////////////////
#/////////////////////////MST///////////////////////////////////
#///////////////////////////////////////////////////////////////
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
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////

#///////////////////////////////////////////////////////////////
#/////////////////////////AGGREGATE/////////////////////////////
#///////////////////////////////////////////////////////////////
def aggregate(body, returnbody):
    returnbody["RESULT"][body["function"]]=body["result"]
    return returnbody

def AggHandler(xfaas_object) -> SerWOObject:
    try:
        body = xfaas_object.get_objects()
        returnbody = {}
        returnbody["RESULT"] = {}
        for idx , body in enumerate(xfaas_object.get_objects()):
            body = body.get_body()
            aggregate(body, returnbody)
        return SerWOObject(body=returnbody)

    except Exception as e:
        print(e)
        logging.info(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////
"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj

def build_req_from_file(path):
    with open(path, "r") as file:
        # Write data to the file
        req_txt = file.read()
        req_json = json.loads(req_txt)
        req = SerWOObject.from_json(req_json)
    return req

def write_req_to_file(req, path):
    with open(path, "w") as file:
        # Write data to the file
        file.write(req.to_json())


req_body = {"size": 32, "graph_type": "complete"}
req = SerWOObject(body=req_body)

path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/graphGen/input.json'
write_req_to_file(req, path)
req = build_req_from_file(path)
ret_obj = graphGenHandler(req)

path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/graphBFT/input.json'
write_req_to_file(ret_obj, path)
req = build_req_from_file(path)
bft_ret = BFTHandler(ret_obj)

path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/graphMST/input.json'
write_req_to_file(ret_obj, path)
req = build_req_from_file(path)
mst_ret = MSTHandler(req)

path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/pagerank/input.json'
write_req_to_file(ret_obj, path)
req = build_req_from_file(path)
pg_ret = PageRankHandler(req)

fanin_list = [bft_ret, mst_ret, pg_ret]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/azureuser/XFaaS/serwo/examples/graphAz/functions/aggregate/inputs/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/aggregate/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

agg = AggHandler(l_obj)
