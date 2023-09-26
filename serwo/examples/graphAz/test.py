# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import *
import networkx as nx
# function specific imports
import logging
from networkx.readwrite import json_graph
import json
import os
import objsize


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
        # req = SerWOObject.from_json(req_json)
        req = SerWOObject(body=req_json)
    return req

def write_req_to_file(req, path):
    with open(path, "w") as file:
        # Write data to the file
        print(req.get_body())
        file.write(json.dumps(req.get_body()))

##64,136,300
req_body = {"size": 300, "graph_type": "complete"}
j1 = json.dumps(req_body)
j2 = json.dumps(req_body, indent=2)
req = SerWOObject(body=req_body)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(req)
print("-----------IP GGEN-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/graph/graph_gen/samples/large/input/input.json'
write_req_to_file(req, path)
req = build_req_from_file(path)
ret_obj = graphGenHandler(req)
path = '/home/nikhil/work/xfaas-workloads/functions/graph/graph_gen/samples/large/output/output.json'
write_req_to_file(ret_obj, path)

r0 = ret_obj.get_body()
j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ret_obj)
print("-----------OP GGEN-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")



j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ret_obj)
print("-----------IP GBFT-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/graph/graph_bft/samples/large/input/input.json'
write_req_to_file(ret_obj, path)
req = build_req_from_file(path)
bft_ret = BFTHandler(ret_obj)
path = '/home/nikhil/work/xfaas-workloads/functions/graph/graph_bft/samples/large/output/output.json'
write_req_to_file(bft_ret, path)

r = bft_ret.get_body()
j1 = json.dumps(r)
j2 = json.dumps(r, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(bft_ret)
print("-----------OP GBFT-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")




j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ret_obj)
print("-----------IP GMST-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")

path = '/home/nikhil/work/xfaas-workloads/functions/graph/graph_mst/samples/large/input/input.json'
write_req_to_file(ret_obj, path)
req = build_req_from_file(path)
mst_ret = MSTHandler(req)
path = '/home/nikhil/work/xfaas-workloads/functions/graph/graph_mst/samples/large/output/output.json'
write_req_to_file(mst_ret, path)

r = mst_ret.get_body()
j1 = json.dumps(r)
j2 = json.dumps(r, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(mst_ret)
print("-----------OP GMST-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")


j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(ret_obj)
print("-----------IP PGRK-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")


path = '/home/nikhil/work/xfaas-workloads/functions/graph/pagerank/samples/large/input/input.json'
write_req_to_file(ret_obj, path)
req = build_req_from_file(path)
pg_ret = PageRankHandler(req)
path = '/home/nikhil/work/xfaas-workloads/functions/graph/pagerank/samples/large/output/output.json'
write_req_to_file(pg_ret, path)

r = pg_ret.get_body()
j1 = json.dumps(r)
j2 = json.dumps(r, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(pg_ret)
print("-----------OP PGRK-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")

fanin_list = [bft_ret, mst_ret, pg_ret]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/nikhil/work/xfaas-workloads/functions/graph/aggregate/samples/large/input/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/nikhil/work/xfaas-workloads/functions/graph/aggregate/samples/large/input/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)

obs = l_obj.get_objects()
lsz = 0
lsz_ind = 0
for ob in obs:
    bd = ob.get_body()
    osj1 = json.dumps(bd)
    osj2 = json.dumps(bd, indent=2)
    lsz = lsz + objsize.get_deep_size(osj1)
    lsz_ind = lsz + objsize.get_deep_size(osj2)

j1 = json.dumps(r0)
j2 = json.dumps(r0, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(l_obj)
print("-----------IP AGG-----------")
print(f"JSON DUMP : {lsz/1024}\nJSON DUMP INDENT : {lsz_ind/1024}\nSerWOObject : {rqs/1024}")



agg = AggHandler(l_obj)
path = '/home/nikhil/work/xfaas-workloads/functions/graph/aggregate/samples/large/output/output.json'
write_req_to_file(agg, path)


r = agg.get_body()
j1 = json.dumps(r)
j2 = json.dumps(r, indent=2)

j1s = objsize.get_deep_size(j1)
j2s = objsize.get_deep_size(j2)
rqs = objsize.get_deep_size(agg)
print("-----------OP AGG-----------")
print(f"JSON DUMP : {j1s/1024}\nJSON DUMP INDENT : {j2s/1024}\nSerWOObject : {rqs/1024}")
print("=============================\n\n")