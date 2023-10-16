import os


exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/text/text_sort --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

try:
    os.system(exp1)
except Exception as e:
    print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/resnet --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/mobilenet --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/flip --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/grayscale --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# # exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/alexnet --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# # try:
# #     os.system(exp1)
# # except Exception as e:
# #     print('Excep in experiment 1: cmd: ',exp1,e)


# # exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/resnet --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# # try:
# #     os.system(exp1)
# # except Exception as e:
# #     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/mobilenet --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/flip --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/singleton_workflows/multimedia/grayscale --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)




# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 840 --payload-size medium --dynamism step_function --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)




# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_part32 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_part32 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism sawtooth --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_part32 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 17 --duration 300 --payload-size medium --dynamism alibaba --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_part32 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 17 --duration 300 --payload-size medium --dynamism alibaba --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)




# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_part32 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size large --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf_part32 --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)







# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 8 --duration 840 --payload-size medium --dynamism step_function --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)






# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size large --dynamism static --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 840 --payload-size medium --dynamism step_function --wf-name image --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 840 --payload-size medium --dynamism step_function --wf-name text --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/text_analytics_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 840 --payload-size medium --dynamism step_function --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name graph --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)


# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 720 --payload-size small --dynamism static --wf-name comm_stress --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/microbenchmarks/communication_stress --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 1 --duration 300 --payload-size large --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism step_function --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism sawtooth --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)




# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure --region centralindia --max-rps 17 --duration 300 --payload-size medium --dynamism alibaba --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)





# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size small --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 1 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2_v2 --region centralindia --max-rps 1 --duration 300 --payload-size large --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 4 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism static --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism step_function --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)



# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 8 --duration 300 --payload-size medium --dynamism sawtooth --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)




# exp1 = 'python3 serwo/xfaas_run_benchmark.py --csp azure_v2 --region centralindia --max-rps 17 --duration 300 --payload-size medium --dynamism alibaba --wf-name math --wf-user-directory /Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf_new --path-to-client-config /Users/varad.kulkarni/xfaas/XFaaS/serwo/config/client_config.json --dag-file-name dag.json --teardown-flag 0 --client-key azure-1'

# try:
#     os.system(exp1)
# except Exception as e:
#     print('Excep in experiment 1: cmd: ',exp1,e)