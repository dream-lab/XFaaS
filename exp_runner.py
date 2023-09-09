import os

exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 30 --payload-size small --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key azure-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)

exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 30 --payload-size medium --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key azure-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)

exp3 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 30 --payload-size large --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key azure-1'

try:
    os.system(exp3)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp3,e)

