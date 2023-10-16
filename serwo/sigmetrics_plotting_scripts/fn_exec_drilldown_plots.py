from xfbench_plotter import XFBenchPlotter
import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
from datetime import datetime
import shutil
import time
import matplotlib.patches as mpatches
import numpy as np
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
    
    a,b = plotter.plot_stagewise_containers('azure',figwidth=20,yticks=[])
    global_list.append(a)
    global_list.append(b)
    # print(a,b)


run_id = 'exp1'

print('==================PLOTTING METRICS===========================')


directories = ['/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/graph_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/image_processing_wf','/Users/varad.kulkarni/xfaas/xfaas-workloads/workflows/custom_workflows/text_analytics_wf']
k = 0
for wf in range(2*len(directories[0:3])):
    dd = directories[k//2]
    wf_user_directory = dd + '/workflow-gen'
    dataa = [data[wf]]
    print(k//2,dd)
    k += 1
    for d in dataa:
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


lbls = ['RNET','RNET','ANET','ANET','PGRK','PGRK','MNET','MNET','GBFT','GBFT','GMST','GMST','FLIP','FLIP','GRAY','GRAY','SSTR','SSTR','MSRT','MSRT','TGEN','TGEN']

labels = lbls
colors = []
colors2 = []
for xd in range (0,len(lbls)):
    if xd%2==0:
        colors.append('red')
        colors2.append('red')
    else:
        colors.append('green')
        colors2.append('green')

print(labels)
mems = [9.552412645590682, 4.380243161094225, 1.9564971751412428, 2.370529801324503, 1.0410526315789475, 1.0405405405405406, 0.7703703703703705, 0.8473684210526317,0.5,0.5,0.5]


graph = global_list[0:2]
image = global_list[4:6]
text =  global_list[8:10]


graph_id_heavy = ['4']
image_id_heavy = ['6','7','8']

box_data = []






graph2 = global_list[2:4]
image2 = global_list[6:8]
text2 =  global_list[10:12]

graph_id_heavy = ['4']
image_id_heavy = ['6','7','8']

box_data2 = []



box_data2.append(image[0][0][5])
box_data2.append(image[1][0][5])

box_data2.append(image[0][0][6])
box_data2.append(image[1][0][6])


box_data2.append(graph[0][0][3])
box_data2.append(graph[1][0][3])

box_data2.append(image[0][0][7])
box_data2.append(image[1][0][7])


box_data2.append(graph[0][0][1])
box_data2.append(graph[1][0][1])

box_data2.append(graph[0][0][2])
box_data2.append(graph[1][0][2])

box_data2.append(graph[0][0][1])
box_data2.append(graph[1][0][1])

box_data2.append(image[0][0][2])
box_data2.append(image[1][0][2])


# print(len(text[0][0]))
box_data2.append(text[0][0][11])
box_data2.append(text[1][0][11])

box_data2.append(text[0][0][23])
box_data2.append(text[1][0][23])


box_data2.append(text[0][0][1])
box_data2.append(text[1][0][1])




box_data.append(image2[0][0][5])
box_data.append(image2[1][0][5])


box_data.append(image2[0][0][6])
box_data.append(image2[1][0][6])


box_data.append(graph2[0][0][3])
box_data.append(graph2[1][0][3])

box_data.append(image2[0][0][7])
box_data.append(image2[1][0][7])



box_data.append(graph2[0][0][1])
box_data.append(graph2[1][0][1])



box_data.append(graph2[0][0][2])
box_data.append(graph2[1][0][2])



box_data.append(graph2[0][0][1])
box_data.append(graph2[1][0][1])



box_data.append(image2[0][0][2])
box_data.append(image2[1][0][2])


box_data.append(text2[0][0][11])
box_data.append(text2[1][0][11])

box_data.append(text2[0][0][23])
box_data.append(text2[1][0][23])


box_data.append(text2[0][0][1])
box_data.append(text2[1][0][1])


yticks = []

### AZURE V2
fig, ax = plt.subplots(figsize=(6, 4))
fig.set_dpi(400)
ax.set_ylabel("Time (sec)")
fig.set_figwidth(7)
# labels = ['E2E w/o\nContainer Spawn', 'E2E w\nContainer Spawn']
# ax2 = ax.twinx()
# ax2.set_ylim([0,10])
# yaxis2_ticks = [0,2.5,5,7.5,10]
# ax2.set_yticks(yaxis2_ticks)
# ax2.set_yticklabels([str(x) for x in yaxis2_ticks])
# ax2.set_ylabel("Memory (%)")

# print(len(lbls))
# ax2.scatter([x+0.5 for x in range(1, len(labels),2)], mems, color='blue', marker='x', s=100)

m_list = []
q1 = []
q3 = []

labels2 =[]
for i in range(0,len(labels)):
    if i%2==0:
        labels2.append(labels[i])
    
print(labels2)

for b in box_data:
    m_list.append(np.median(b))
    q3.append(np.percentile(b,75))
    q1.append(np.percentile(b,25))



x = [i for i in range(0,len(lbls))]

print(len(x),len(m_list))

bl = ax.bar(x,m_list,color=colors)
ax.errorbar(x,m_list,yerr=[q1,q3],capsize=5,color='black',ls="none")
ax.set_yscale('log')
ax.set_ylim(ymin=0.001,ymax=100)
ax.set_xlim(xmin=-0.5)


scatter_x = [0.5,2.5,4.5,6.5,8.5,10.5,12.5,14.5,16.5,18.5,20.5]
ax.set_xticks(scatter_x)
ax.set_xticklabels(labels2,fontsize=10)
                

if not yticks == []:
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(x) for x in yticks])

# ax.set_xticks([x+1 for x in range(0, len(labels))])
# ax.set_xticklabels(labels,rotation=90)


labels2 =[]
for i in range(0,len(labels)):
    if i%2==0:
        labels2.append(labels[i])
    else:
        labels2.append("")
print(labels2)

_xloc = ax.get_xticks()
vlines_x_between = []
for idx in range(1, len(_xloc)-1,2):
    vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
ax.vlines(x=vlines_x_between, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)

ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
ax.grid(axis="y", which="major", linestyle="-", color="black")
ax.grid(axis="y", which="minor", linestyle="-", color="grey")
ax.set_axisbelow(True)

fig.savefig(f"fn_execs/fn_coldstarts_azv2_new_bar_plot.pdf", bbox_inches='tight')

    


### AZURE
# colors = colors2
# fig, ax = plt.subplots(figsize=(6, 4))
# fig.set_dpi(400)
# ax.set_ylabel("Time (sec)")
# fig.set_figwidth(7)
# # labels = ['E2E w/o\nContainer Spawn', 'E2E w\nContainer Spawn']
# ax3 = ax.twinx()
# ax3.set_ylim([0,10])
# yaxis2_ticks = [0,2.5,5,7.5,10]
# ax3.set_yticks(yaxis2_ticks)
# ax3.set_yticklabels([str(x) for x in yaxis2_ticks])
# ax3.set_ylabel("Memory (%)")

# ##legend for red and green create a patch


# p1 = mpatches.Patch(color='red', label='Coldstart')
# p2 = mpatches.Patch(color='green', label='No ColdStart')
# ##create legend for a cross marker in the same legend



# # p3 = mpatches.Patch(color='blue', label='Memory %')



# l1 = ax3.scatter([x+0.5 for x in range(1, len(labels),2)], mems, color='blue', marker='x', s=100, label='Memory %')
# bplot2 = ax.boxplot(box_data2,
#                         vert=True,
#                         widths=0.5,
#                         patch_artist=True,
#                         showfliers=False)

# # plt.xticks(rotation=90)
# ax.legend(handles=[p1,p2,l1],loc='upper right')
# # ax3.legend(loc=)
# if not yticks == []:
#     ax.set_yticks(yticks)
#     ax.set_yticklabels([str(x) for x in yticks])

# # ax.set_xticks([x+1 for x in range(0, len(labels))])
# # ax.set_xticklabels(labels,rotation=90)



# labels2 =[]
# for i in range(0,len(labels)):
#     if i%2==0:
#         labels2.append(labels[i])
#     else:
#         labels2.append("")
# print(labels2)
# ax.set_xticklabels(labels2,rotation=30)

# # Set ylim
# ax.set_ylim(ymin=0, ymax=3)
# # color='pink'
# # colors = ['lightblue', 'blue','lightgreen', 'green']

# for patch, color in zip(bplot2['boxes'], colors):
#     patch.set_facecolor(color)
# # for tick, color in zip(ax.get_xticklabels(), colors):
# #     tick.set_color(color)

# _xloc = ax.get_xticks()
# vlines_x_between = []
# for idx in range(1, len(_xloc)-1,2):
#     vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
# # ax.vlines(x=vlines_x_between, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)

# ax.vlines(x=scatter_x, ymin=0, ymax=ax.get_ylim()[1], linestyles='solid', color='darkgrey', linewidth=1.5)
# ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
# ax.grid(axis="y", which="major", linestyle="-", color="black")
# ax.grid(axis="y", which="minor", linestyle="-", color="grey")
# ax.set_axisbelow(True)

# fig.savefig(f"fn_execs/fn_coldstarts_az_new.pdf", bbox_inches='tight')


'''

do not change

graph
image
text

fd3e4e53-fc09-4c7a-a21f-ec2b16a088e8,azure,centralindia,1,300,medium,static
d5784164-9145-4caf-8fec-deca2601c02c,azure_v2,centralindia,1,300,medium,static
b4edcca9-a920-4e3b-bd5b-8d741efd0f1a,azure,centralindia,1,300,medium,static
9c4a4103-27f4-4865-95f5-c465663a984b,azure_v2,centralindia,1,300,medium,static
3c08d71f-9a0a-4258-a4e6-f6918781c868,azure,centralindia,1,300,medium,static
831da974-e232-4543-813a-8341f47ff922,azure_v2,centralindia,1,300,medium,static

'''