# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file
import networkx as nx
# function specific imports
import logging
from networkx.readwrite import json_graph
import cProfile, pstats


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


path = '/home/azureuser/XFaaS/serwo/examples/graphAz/functions/graphGen/input.json'
req = build_req_from_file(path)

# profiler = cProfile.Profile()
# profiler.enable()
ret_obj = graphGenHandler(req)
# profiler.disable()

# stats = pstats.Stats(profiler).sort_stats('tottime')
# stats.print_stats()