import os

# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag False --client-key aws-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)

# exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

# try:
#     os.system(exp2)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp2,e)



# exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

# try:
#     os.system(exp2)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp2,e)


# exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 8 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

# try:
#     os.system(exp2)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp2,e)


# exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 8 --duration 300 --payload-size medium --dynamism step_function --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

# try:
#     os.system(exp2)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp2,e)


# exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 8 --duration 300 --payload-size medium --dynamism sawtooth --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

# try:
#     os.system(exp2)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp2,e)

# exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 17 --duration 300 --payload-size medium --dynamism alibaba --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

# try:
#     os.system(exp2)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp2,e)




exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag False --client-key aws-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)

exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 1 --duration 300 --payload-size medium --dynamism static --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)



exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)


exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 8 --duration 300 --payload-size medium --dynamism static --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)


exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 8 --duration 300 --payload-size medium --dynamism step_function --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)


exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 8 --duration 300 --payload-size medium --dynamism sawtooth --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)

exp2 = 'python3 serwo/xfaas_run_benchmark.py --csp aws --region ap-south-1 --max-rps 17 --duration 300 --payload-size medium --dynamism alibaba --wf-name imageProcessing --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf_aws --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag True --client-key aws-1'

try:
    os.system(exp2)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp2,e)