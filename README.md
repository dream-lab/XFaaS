# XFaaS: Cross-platform Orchestration of FaaS Workflows on Hybrid Clouds

> Functions as a Service (FaaS) have gained popularity for programming public clouds due to their simple abstraction, ease of deployment, effortless scaling and granular billing. Cloud providers also offer basic capabilities to compose these functions into workflows. FaaS and FaaS workflow models, however, are proprietary to each cloud provider. This prevents their portability across cloud providers, and requires effort to design workflows that run on different cloud providers or data centers. Such requirements are increasingly important to meet regulatory requirements, leverage cost arbitrage and avoid vendor lock-in. Further, the FaaS execution models are also different, and the overheads of FaaS workflows due to message indirection and cold-starts need custom optimizations for different platforms.
>
> We propose XFaaS, a cross-platform deployment and orchestration engine for FaaS workflows to operate on multiple clouds. XFaaS allows “zero touch” deployment of functions and workflows across AWS and Azure clouds by automatically generating the necessary code wrappers, cloud queues, and coordinating with the native FaaS engine of the cloud providers. It also uses intelligent function fusion and placement logic to reduce the workflow execution latency in a hybrid cloud while mitigating costs, using performance and billing models specific to the providers based in detailed benchmarks. Our empirical results indicate that fusion offers up to ≈75 % benefits in latency and ≈57% reduction in cost, while placement strategies reduce the latency by ≈ 24%, compared to baselines in the best cases.
> 
> From A. Khochare, et al, IEEE/ACM CCGRID 2023.

*Note: XFaaS was earlier known as SerWO. So some of the references in the code/documentation may use these terms interchangably.*

## XFaaS Deployment processs
- First, clone the workloads repository and checkout out `workflow-integration` branch.: (https://github.com/dream-lab/xfaas-workloads/tree/workflow-integration)
- Prerequisites: A client VM to be spun up that is publicly accessible(eg: an AWS VM). 
    - Feed the client credentials in a file at: serwo/config/client_config.json, with the following schema
        {
            "<client_key>":{
                "server_ip": "<IP>",
                "server_user_id" : "<USER_NAME>",
                "server_pem_file_path":"<Path_to_pem_file>"
            }
        }
    - client_key can be anything defined by the user.
    - Apache jmeter to be installed on the VM: version: 5.6.2 (https://jmeter.apache.org/download_jmeter.cgi)
- Then Run the command: export XFAAS_WF_DIR=<absolute path to directory where you cloned above repo>
- Install all dependencies:
    pip install -r requirements.txt
- Set Azure Subscription id: 
    - Fethc Azure subscription id using: az account subscription list
    - Run export  export AZURE_SUBSCRIPTION_ID=<azure_subscription_id>
- Command to begin The Experiment:
    - python serwo/xfaas_run_benchmark.py --csp <can take values: aws, azure,azure_v2> --region <data_centre_region> --max-rps <max_rps> --duration <duration of run> --payload-size <payload_size> --dynamism <qorkload dynamism> --wf-name <wf name> --wf-user-directory <absolute path to user wf directory, wf will be contained in the workloads repo> --path-to-client-config <absolute path to client_config.json created above> --dag-file-name dag.json --teardown-flag <set to 1 if you wish to delete remote resources created, 0 recommended as remote deletion takes time> --client-key <client_key defined above>

- You can refer to example run commands from exp_runner.py script

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
