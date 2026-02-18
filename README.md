# XFaaS: Cross-platform Orchestration of FaaS Workflows on Hybrid Clouds

> Functions as a Service (FaaS) have gained popularity for programming public clouds due to their simple abstraction, ease of deployment, effortless scaling and granular billing. Cloud providers also offer basic capabilities to compose these functions into workflows. FaaS and FaaS workflow models, however, are proprietary to each cloud provider. This prevents their portability across cloud providers, and requires effort to design workflows that run on different cloud providers or data centers. Such requirements are increasingly important to meet regulatory requirements, leverage cost arbitrage and avoid vendor lock-in. Further, the FaaS execution models are also different, and the overheads of FaaS workflows due to message indirection and cold-starts need custom optimizations for different platforms.
>
> We propose XFaaS, a cross-platform deployment and orchestration engine for FaaS workflows to operate on multiple clouds. XFaaS allows “zero touch” deployment of functions and workflows across AWS and Azure clouds by automatically generating the necessary code wrappers, cloud queues, and coordinating with the native FaaS engine of the cloud providers. It also uses intelligent function fusion and placement logic to reduce the workflow execution latency in a hybrid cloud while mitigating costs, using performance and billing models specific to the providers based in detailed benchmarks. Our empirical results indicate that fusion offers up to ≈75 % benefits in latency and ≈57% reduction in cost, while placement strategies reduce the latency by ≈ 24%, compared to baselines in the best cases.
> 
> From A. Khochare, et al, IEEE/ACM CCGRID 2023.

*Note: XFaaS was earlier known as SerWO. So some of the references in the code/documentation may use these terms interchangably.*

## Features

### Original XFaaS (v1)
The original XFaaS implementation introduced cross-platform FaaS workflow orchestration with:
- Simple partitioning algorithm for workflow optimization
- Fusion strategies for latency and cost reduction
- Partitioning and fusion applied individually
- Support for AWS and Azure cloud platforms

*XFaaS v1: https://github.com/dream-lab/XFaaS/tree/XFaaSV1.0*

### Enhanced XFaaS Features

1. **DP-based Generic Partitioner**: Dynamic Programming (DP) based partitioner for workflow optimization, providing more sophisticated partitioning strategies compared to the original simple partitioning approach.
   - *To appear in proceedings*

2. **Partitioner Plus Fusion**: Combined optimization approach that integrates partitioning and fusion strategies together, enabling more effective latency and cost reduction through coordinated optimization.
   - *To appear in proceedings*

3. **Async Workflow Execution**: Support for asynchronous workflow execution patterns across hybrid clouds.
   - *V. Jha et al., "Choreography and Profiling of Quantum-Classical FaaS Workflows on Hybrid Clouds," 2025 IEEE 25th International Symposium on Cluster, Cloud and Internet Computing (CCGrid), Tromsø, Norway, 2025, pp. 01-11, doi: 10.1109/CCGRID64434.2025.00069.*

4. **Automatic Payload Handling**: Intelligent handling of cloud workflow constraints such as payload size limitations in AWS Step Functions and Azure Queues, automatically using blob stores (S3/Azure Blob) or queue stores for communication when payloads exceed platform size constraints.

5. **Conditional Looping in Workflows**: Support for conditional branching and looping constructs in workflows for both AWS and Azure platforms.
   - *To appear in proceedings*

## XFaaS Deployment processs

For detailed setup instructions, please refer to [XFaaS v1 documentation](https://github.com/dream-lab/XFaaS/tree/XFaaSV1.0).

### Quick Start

To deploy and run workflows using this branch, use `xfaas_main.py`:

```bash
python serwo/xfaas_main.py --wf-user-directory <path_to_workflow_directory> --dag-file-name dag.json --dag-benchmark dag-benchmark.json --csp <aws|azure> --region <region_name>
```

**Example:**
```bash
python serwo/xfaas_main.py --wf-user-directory serwo/examples/graphAws --dag-file-name dag.json --dag-benchmark dag-benchmark.json --csp aws --region ap-south-1
```

For benchmarking experiments with load testing, you can use `xfaas_run_benchmark.py` or refer to example run commands in the `exp_runner*.py` scripts. For more information about our benchmarking suite, refer to XFBench: [GitHub URL placeholder - to be added]

*V. Kulkarni et al., "XFBench: A Cross-Cloud Benchmark Suite for Evaluating FaaS Workflow Platforms," 2024 IEEE 24th International Symposium on Cluster, Cloud and Internet Computing (CCGrid), Philadelphia, PA, USA, 2024, pp. 543-556, doi: 10.1109/CCGrid59990.2024.00067.*

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
