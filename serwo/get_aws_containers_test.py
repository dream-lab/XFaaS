from get_aws_containers import get_max_concurrent_execs

def get_quick(wf_name):
    print(get_max_concurrent_execs(wf_name))


if __name__ == '__main__':
    xfaas_app = 'XFaaSApp-graph163'
    get_quick(xfaas_app)
