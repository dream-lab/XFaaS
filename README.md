# XFaaS: Cross-platform Orchestration of FaaS Workflows on Hybrid Clouds

> Functions as a Service (FaaS) have gained popularity for programming public clouds due to their simple abstraction, ease of deployment, effortless scaling and granular billing. Cloud providers also offer basic capabilities to compose these functions into workflows. FaaS and FaaS workflow models, however, are proprietary to each cloud provider. This prevents their portability across cloud providers, and requires effort to design workflows that run on different cloud providers or data centers. Such requirements are increasingly important to meet regulatory requirements, leverage cost arbitrage and avoid vendor lock-in. Further, the FaaS execution models are also different, and the overheads of FaaS workflows due to message indirection and cold-starts need custom optimizations for different platforms.
>
> We propose XFaaS, a cross-platform deployment and orchestration engine for FaaS workflows to operate on multiple clouds. XFaaS allows “zero touch” deployment of functions and workflows across AWS and Azure clouds by automatically generating the necessary code wrappers, cloud queues, and coordinating with the native FaaS engine of the cloud providers. It also uses intelligent function fusion and placement logic to reduce the workflow execution latency in a hybrid cloud while mitigating costs, using performance and billing models specific to the providers based in detailed benchmarks. Our empirical results indicate that fusion offers up to ≈75 % benefits in latency and ≈57% reduction in cost, while placement strategies reduce the latency by ≈ 24%, compared to baselines in the best cases.
> 
> From A. Khochare, et al, IEEE/ACM CCGRID 2023.

*Note: XFaaS was earlier known as SerWO. So some of the references in the code/documentation may use these terms interchangably.*

## XFaaS Deployment processs

### **User directory structure**
The user directory should look like (see serwo/examples for reference)
```
folder/src - directory containing function code

```


### *AWS Step functions*


#### **Deployment commands**

```
Command
    python3 <path..>/aws_create_statemachine.py <path-to-user-dir> <workflow-description-filename> <trigger-type>

NOTE
    trigger types - REST | SQS
```

### *Azure Durable functions*
#### **Deployment commands**

```
Command
    python3 <path..>/azure_create_statemachine.py <path-to-user-dir> <workflow-description-filename> <trigger-type>

NOTE
    trigger types - !To be integrated!
```

## Cite this work as
* A. Khochare, T. Khare, V. Kulkarni and Y. Simmhan, "XFaaS: Cross-platform Orchestration of FaaS Workflows on Hybrid Clouds," 2023 IEEE/ACM 23rd International Symposium on Cluster, Cloud and Internet Computing (CCGrid), Bangalore, India, 2023, pp. 498-512, doi: 10.1109/CCGrid57682.2023.00053.
  * Awarded with Open Research Objects (ORO) and Research Objects Reviewed (ROR) Badges

* A. Khochare, Y. Simmhan, S. Mehta and A. Agarwal, "Toward Scientific Workflows in a Serverless World," 2022 IEEE 18th International Conference on e-Science (e-Science), Salt Lake City, UT, USA, 2022, pp. 399-400, doi: 10.1109/eScience55777.2022.00057.

## Acknowledgement
*This research was performed as part of the IBM IISc Hybrid Cloud Lab, an open research collaboration jointly between the DREAM:Lab at IISc and researchers at IBM India Research Lab, Bangalore.*

## License and Copyright
This code is released under Apache License, Version 2.0
https://www.apache.org/licenses/LICENSE-2.0.txt

Copyright (c) 2023 DREAM:Lab, Indian Institute of Science. All rights reserved.
