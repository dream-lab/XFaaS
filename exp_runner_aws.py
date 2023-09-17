import os 



exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name parallel_stress_2 --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/microbenchmarks/parallelism_stress_2 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key aws-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)

exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name parallel_stress_5 --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/microbenchmarks/parallelism_stress_5 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key aws-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)


exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name parallel_stress_10 --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/microbenchmarks/parallelism_stress_10 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key aws-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)




exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name parallel_stress_25 --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/microbenchmarks/parallelism_stress_25 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key aws-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)

exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name parallel_stress_50 --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/microbenchmarks/parallelism_stress_50 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key aws-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)