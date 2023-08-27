# Graph

## Description of workflow
The graph workflow consisting of 5 nodes first has the graph generation before fanning out into the BFS, pagerank and MST functions. The output of these three nodes is passed to the aggregrate function.
 
### graphGen
The function generates the graph using the size and edges as parameters, startvertex as conditional parameter.
{
    "size": Number of vertices,
    "edges": Number of edges,
    "startVertex": Starting vertex for BFS (conditional parameter)
}

### graphBFS
The graphBFS function 

### pagerank
The pagerank function 

### graphMST
The graphMST function 

### aggregate
The last function aggregates the results from the previous functions to generate the result for the workflow

## Hyperlink to list of functions in the workflow


[graphBFS](https://github.com/dream-lab/xfaas-workloads/tree/a32f8af48ef9e7ebfafd08cb9ccbb07143e74ffe/functions/graphs/BFS)

[pagerank](https://github.com/dream-lab/xfaas-workloads/tree/eb5cf4de240b84e8bddd8fc8e49f35316ce0ac57/functions/graphs/pagerank)

[graphMST](https://github.com/dream-lab/xfaas-workloads/tree/553a6d7a0dd1daa92ebbc991291e2b91d6f3e102/functions/graphs/min_spanning_tree)


## Description for input params 
This function takes in the size(vertices) and edges, with the startVertex being the optional parameter.

## Description for output params
The results of each of the processes like BFS,pagerank and MST are returned in the form of a dictionary

## Sample input json
### With optional parameter (startVertex)
```json
{
    "size":10,
    "edges":5,
    "startVertex":7
}
```
### Without optional parameter (startVertex)
```json
{
    "size":10,
    "edges":5
}
```

## Sample output json
### With optional parameter (startVertex)
```json
{
    "message": "Success",
    "result": {
        "body": {
            "RESULT": {
                "BFS": [
                    7,
                    0,
                    2,
                    4,
                    5,
                    6,
                    1,
                    3,
                    8,
                    9
                ],
                "MST": [
                    0,
                    1,
                    3,
                    6,
                    10,
                    17,
                    21,
                    25,
                    30
                ],
                "Pagerank": [
                    0.11245695181814785,
                    0.10026665117402943,
                    0.12531137967636186,
                    0.0996312602915688,
                    0.1253113796763619,
                    0.09959625214814653,
                    0.11296823240539972,
                    0.07471518371394283,
                    0.0747965893099429,
                    0.07494611978609804
                ]
            }
        },
        "metadata": null,
        "statusCode": 200
    },
    "statusCode": 200
}
```

### Without optional parameter (startVertex)
```json
{
    "message": "Success",
    "result": {
        "body": {
            "RESULT": {
                "BFS": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9
                ],
                "MST": [
                    0,
                    1,
                    3,
                    6,
                    10,
                    17,
                    21,
                    25,
                    30
                ],
                "Pagerank": [
                    0.1124680234299157,
                    0.12532139604394224,
                    0.1253213960439422,
                    0.09961745893058918,
                    0.07487749460301128,
                    0.10013740580572451,
                    0.11247740708501931,
                    0.10011211798468186,
                    0.07472874271452502,
                    0.07493855735864872
                ]
            }
        },
        "metadata": null,
        "statusCode": 200
    },
    "statusCode": 200
}
```
## Dependencies
python3 3.10.12

igraph

## Workflow
[![](https://mermaid.ink/img/pako:eNqF0E0KgzAQBeCrhFnrBbIoaG1dFQq6My4GM_5QTSRNKEW8e1PJQgptZxUe37yBLNBoScChHfWj6dFYVmZCMT9JlRuce5aTIoN20KpmcXxgacjTc1H_lsfqip1P1O0PzEJ-Kcog90c2cqqSrjPU-TUKZlf_jeyLN_OJIIKJzISD9H-wvJcE2J4mEsD9U1KLbrQChFo9RWd18VQNcGscReBm6WuyAX3dBLzF8U7rC6HUbV8?type=png)](https://mermaid.live/edit#pako:eNqF0E0KgzAQBeCrhFnrBbIoaG1dFQq6My4GM_5QTSRNKEW8e1PJQgptZxUe37yBLNBoScChHfWj6dFYVmZCMT9JlRuce5aTIoN20KpmcXxgacjTc1H_lsfqip1P1O0PzEJ-Kcog90c2cqqSrjPU-TUKZlf_jeyLN_OJIIKJzISD9H-wvJcE2J4mEsD9U1KLbrQChFo9RWd18VQNcGscReBm6WuyAX3dBLzF8U7rC6HUbV8)

## Citation to external sources:

XFaaS : [@xfaas-workloads](https://github.com/dream-lab/xfaas-workloads) 


## Authors

Mohith A - [@mohithadluru](https://github.com/mohithadluru)

Sanjjit S - [@sanjjit001](https://github.com/sanjjit001)


