import sys
import networkx as nx
from networkx.readwrite import json_graph
import concurrent.futures
import objsize


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
    else:
        graph = nx.complete_graph(size)

    graph_dict = json_graph.adjacency_data(graph)
    returnbody = {
            "graph": graph_dict,
            "startVertex": startVertex
    }
    sz = objsize.get_deep_size(returnbody)
    print(f'Output size graphGen: {int(sz/1024)}')
    print("-----------------------------")
    return returnbody

def BFT(body):
    
    
    graph = nx.adjacency_graph(body.get("graph"))
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
    sz = objsize.get_deep_size(body)
    print(f'Input size BFT: {int(sz/1024)}')
    sz = objsize.get_deep_size(returnbody)
    print(f'Output size BFT: {int(sz/1024)}')
    print("-----------------------------")
    return returnbody

def MST(body):
    

    graph = nx.adjacency_graph(body.get("graph"))

    mst = nx.minimum_spanning_tree(graph)
    result = list(mst.edges)

    returnbody = {
        "function": "MST",
        "result": result,
    }
    sz = objsize.get_deep_size(body)
    print(f'Input size MST: {int(sz/1024)}')
    sz = objsize.get_deep_size(returnbody)
    print(f'Output size MST: {int(sz/1024)}')
    print("-----------------------------")
    return returnbody

def PageRank(body):
    

    graph = nx.adjacency_graph(body.get("graph"))
 
    result = nx.pagerank(graph)

    sz = objsize.get_deep_size(body)
    print(f'Input size PageRank: {int(sz/1024)}')

    sz = objsize.get_deep_size(result)

    print(f'Output size PageRank: {int(sz/1024)}')
    print("-----------------------------")
    return {
            'function': 'Pagerank',
            'result': result,
    }
    sz = objsize.get_deep_size(returnbody)
    print(f'Output size PageRank: {int(sz/1024)}')
    print("-----------------------------")
    return returnbody

def fan_out(event):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        r2_future = executor.submit(BFT, event)
        r3_future = executor.submit(MST, event)
        r4_future = executor.submit(PageRank, event)

        # Wait for all futures to complete
        r2 = r2_future.result()
        r3 = r3_future.result()
        r4 = r4_future.result()

    return r2, r3, r4

def aggregate(body, returnbody):
    returnbody["RESULT"][body["function"]]=body["result"]
    return returnbody
#==============================================================================
#==============================================================================

g_type = str(sys.argv[1])
size = int(sys.argv[2])


event = {"size":size, "graph_type":g_type}
# Node 1
r1 = graphGen(event)

returnbody = {}
returnbody["RESULT"] = {}

# Node 2,3,4 Fan-out
for idx in enumerate(fan_out(r1)):
    # Node 5 Aggregate
    aggregate(idx[1], returnbody)

o_sz = objsize.get_deep_size(returnbody)


# print(returnbody)
print(f'Output size Final : {int(o_sz/1024)}')
