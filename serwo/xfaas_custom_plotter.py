from xfbench_plotter import XFBenchPlotter
import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
from datetime import datetime
import shutil
import time
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")


args = parser.parse_args()
wf_user_directory = args.wf_user_directory +'/workflow-gen'


deployments_filename = 'serwo/custom_deployments.txt'

data = []
with open(deployments_filename,'r') as f:
    for line in f:
        data.append(line.strip().split(','))


global_list = []
def plot_metrics(user_wf_dir, wf_deployment_id, run_id):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot_e2e_timeline(xticks=[], yticks=[],is_overlay=True)
    plotter.plot_stagewise( yticks=[0,0.5,1,1.5,2],figwidth=6)
    # a,b = plotter.plot_e2e_invocations_wnwo_containers(csp="azure", yticks=[])
    # global_list.append(a)
    # global_list.append(b)
    plotter.plot_cumm_e2e(yticks=[])
    plotter.plot_cumm_e2e_container('azure',yticks=[0,0.2,0.4,0.6])
    # plotter.plot_stagewise_containers('azure',figwidth=20,yticks=[])
    
'''
c1d356e2-4b2f-409f-b95b-3408a1699ce2,azure,centralindia,1,300,large,static
fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
81dd3382-0546-4f5a-b5a1-282b1801dccd,azure,centralindia,1,300,small,static
'''

run_id = 'exp1'

print('==================PLOTTING METRICS===========================')

# directories = ['/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/text_analytics_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/math_processing_wf']
# k = 0
# for wf in range(2*len(directories[0:1])):
#     wf_user_directory = directories[k//2]+'/workflow-gen'

#     dataa = [data[wf]]
#     print(k//2,wf_user_directory)
#     k += 1
for d in data:
    wf_deployment_id = d[0]
    csp = d[1]
    region = d[2]
    max_rps = d[3]
    duration = d[4]
    payload_size = d[5]
    dynamism = d[6]
    print(f"Plotting for {wf_deployment_id} {csp} {region} {max_rps} {duration} {payload_size} {dynamism}")
    try:
        plot_metrics(wf_user_directory,wf_deployment_id,run_id)
    except Exception as e:
        print('==================PLOTTING METRICS FAILED===========================')
        print(e)
        pass
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    exp_conf = f"{csp}-{region}-{max_rps}-{duration}-{payload_size}-{dynamism}-{timestamp}"
    src = f"{wf_user_directory}/{wf_deployment_id}"
    dst = f"{wf_user_directory}/payload/{exp_conf}"

    if not os.path.exists(dst):

        shutil.copytree(src, dst)

# labels = ['Cold Start\n(CS) Az', 'No CS\nAz','CS\nAzV2', 'No CS\nAzV2']
# graph = global_list[0:4]
# yticks = []
# fig, ax = plt.subplots(figsize=(6, 4))
# fig.set_dpi(400)
# ax.set_ylabel("Time (sec)")
# # labels = ['E2E w/o\nContainer Spawn', 'E2E w\nContainer Spawn']

# bplot2 = ax.boxplot(graph,
#                         vert=True,
#                         widths=0.1,
#                         patch_artist=True,
#                         showfliers=False,
#                         labels=labels)


# if not yticks == []:
#     ax.set_yticks(yticks)
#     ax.set_yticklabels([str(x) for x in yticks])

# ax.set_xticks([x+1 for x in range(0, len(labels))])
# ax.set_xticklabels(labels)

# # Set ylim
# ax.set_ylim(ymin=0, ymax=max(ax.get_yticks()))
# # color='pink'
# colors = ['lightblue', 'blue','lightgreen', 'green']

# for patch, color in zip(bplot2['boxes'], colors):
#     patch.set_facecolor(color)

# _xloc = ax.get_xticks()
# vlines_x_between = []
# for idx in range(0, len(_xloc)-1):
#     vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
# ax.vlines(x=vlines_x_between, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)

# ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
# ax.grid(axis="y", which="major", linestyle="-", color="black")
# ax.grid(axis="y", which="minor", linestyle="-", color="grey")
# ax.set_axisbelow(True)
# ## plt show with tight layout 

# fig.savefig(f"{wf_user_directory}/graph_e2e_container_boxplot.pdf", bbox_inches='tight')


    