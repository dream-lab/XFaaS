from xfbench_plotter import XFBenchPlotter


def plot_metrics(user_wf_dir, wf_deployment_id, run_id, wf_name,region):
    breakpoint()
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot_e2e_timeline(xticks=[], yticks=[],is_overlay=True,region=region)
    figwidth = 7
    if wf_name == 'fileProcessing' or wf_name == 'math':
        figwidth = 20   
    plotter.plot_stagewise( yticks=[],figwidth=figwidth)
    plotter.plot_cumm_e2e(yticks=[])
    # plotter.plot_e2e_invocations_wnwo_containers(csp="azure", yticks=[])


if __name__ == "__main__":
    user_wf_dir = "/Users/vaibhavjha/Documents/IISc/xfbench_multicloud/XFaaS/serwo/examples/static-qfanout-simulator-aws/workflow-gen"
    wf_deployment_id = "random-d51-static"
    run_id = "exp_1"
    wf_name = "staticfanout"
    region = "ap-south-1"
    plot_metrics(user_wf_dir, wf_deployment_id, run_id, wf_name, region)