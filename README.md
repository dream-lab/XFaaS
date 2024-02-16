# XFBench: A Cross-Cloud Benchmark Suite for Evaluating FaaS Workflow Platforms

> Functions-as-a-Service (FaaS) is a widely used serverless computing abstraction that helps developers build
applications using event-driven, stateless functions that execute on the cloud. Commercial FaaS platforms like AWS Lambda
and Azure Functions offer elastic auto-scaling and invocation-level billing to ease operations. Applications are often composed
as a dataflow of FaaS functions that are orchestrated by FaaS workflow platforms like AWS Step Functions or Azure Durable
Functions. However, the proprietary nature of FaaS platforms on public clouds means that their internals are less understood.
While benchmarks to characterize FaaS platforms exist, none are available for a principled evaluation of FaaS workflow platforms.
Further, they are less configurable, and often limited to simple workloads and a single cloud provider. We address this by
proposing XFBench, an end-to-end automated benchmarking framework for FaaS workflows, and an accompanying function,
workflow and workload suite. The user provides a generic definition of the workflow and workload for benchmarking, and
XFBench automatically deploys the workflows across multiple cloud platforms, generates client requests, and profiles the
execution. We evaluate XFBench with realistic workflows and workloads on AWS and Azure platforms in different global
regions to understand inter-function communication, function execution time, and cold start scaling and offer unique insights.
>

> 
> From Varad Kulkarni, et al, IEEE/ACM CCGRID 2024.

*Note: the original [XFaaS paper](README-XFaaS-CCGrid23.md) was earlier known as SerWO. So some of the references in the code/documentation may use these terms interchangably.*

## XFBench Benchmarking Process

### Commands

#####Singleton Workflow

Outline of the run benchmark command 
```bash
python3 serwo/xfaas_run_benchmark.py (run benchmark code file)
    --csp <csp>                      (Cloud service provider - aws | azure)
    --region <region>                (Region of csp used to deploy e.g ap-south-1)
    --max-rps <rps>                  (request throughput) 
    --duration <duration>            (duration of the benchmark in seconds)
    --payload-size <size>            (payload size enum - small | medium | large)   
    --dynamism <dynamism>            (dynamism config enum - static | step_function | sawtooth | alibaba)  
    --wf-name <workflow name>        (workflow name)  
    --path-to-client-config <path>   (absolute path to client config file)
    --dag-file-name <filename>       (filename of the dag description file e.g dag.json)
    --teardown-flag <teardown>       (deletion of cloud resources post run - 0 (no) | 1 (yes))
    --client-key <client-id>         (client identifier from client config)     
    --is_singleton_wf <int>          (is the workflow a singleton ? 0 (no) | 1 (yes))
    --function-class <classname>     (class of the function - graph | math | multimedia | text)
    --function-name <name>           (name of the function within the class - e.g graph_bft) 
    --function-code <code>           (function alias to be used in generated plots)
    --node_name <nodename>           (function alias to be used for deployment (NOTE - use camel case if possible)) 
```
## XFBench Benchmarking Process
### Building Docker container
```shell
1. docker build -t xfbench:1.0 .
2. docker run -d --name xfbench-container xfbench:1.0
3. docker exec -it xfbench-container bash

# <--docker exec should bring you inside the docker container-->
4. az login -u <username> -p <password>
5. aws configure
6. git clone -b CCGRID2024 https://github.com/dream-lab/XFaaS.git
7. git clone -b CCGRID2024 https://github.com/dream-lab/xfaas-workloads
8. export AZURE_SUBSCRIPTION_ID=<Azure account subscription id>
```



## Cite this work as
* V. Kulkarni, N. Reddy, T. Khare, H. Mohan, J. Murali, Mohith A, Ragul B, S Balajee, Sanjjit S, Swathika, Vaishnavi S, Yashasvee, C. Babu, A. S. Prasad and Y. Simmhan, "XFaaS: Cross-platform Orchestration of FaaS Workflows on Hybrid Clouds," 2023 IEEE/ACM 23rd International Symposium on Cluster, Cloud and Internet Computing (CCGrid), Bangalore, India, 2023, pp. 498-512, 
doi: 10.1109/CCGrid57682.2023.00053.

## Acknowledgement
*This research was performed as part of the IBM IISc Hybrid Cloud Lab, an open research collaboration jointly between the DREAM:Lab at IISc and researchers at IBM India Research Lab, Bangalore.*

## License and Copyright
This code is released under Apache License, Version 2.0
https://www.apache.org/licenses/LICENSE-2.0.txt

Copyright (c) 2023 DREAM:Lab, Indian Institute of Science. All rights reserved.
