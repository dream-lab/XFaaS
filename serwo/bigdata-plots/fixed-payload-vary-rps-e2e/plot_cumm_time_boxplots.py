import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import json
import numpy as np
import sys
from matplotlib.patches import Patch
from matplotlib.lines import Line2D




if __name__ == "__main__":
        # filepaths for thespecific cloud 
        
        csp_flag = sys.argv[1]
        ## Graph (Start) ##
        # AWS - 
        if csp_flag == "aws":
            csp = "AWS"
            filepath_1rps = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAws/build/workflow/resources/graph-aws-static-medium-1rps/cumm_time_dir/cumm_time_dict.json"
            filepath_4rps = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAws/build/workflow/resources/graph-aws-static-medium-4rps/cumm_time_dir/cumm_time_dict.json"
            filepath_8rps = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAws/build/workflow/resources/graph-aws-static-medium-8rps/cumm_time_dir/cumm_time_dict.json"

        # Azure - 
        if csp_flag == "azure":
            csp = "Azure"
            filepath_1rps = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAz/build/workflow/resources/graph-azure-static-medium-1rps/cumm_time_dir/cumm_time_dict.json"
            filepath_4rps = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAz/build/workflow/resources/graph-azure-static-medium-4rps/cumm_time_dir/cumm_time_dict.json"
            filepath_8rps = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/CCGrid-Artifact/XFaaS/serwo/examples/graphAz/build/workflow/resources/graph-azure-static-medium-8rps/cumm_time_dir/cumm_time_dict.json"
        ## Graph (End) ##

        files = [filepath_1rps, filepath_4rps, filepath_8rps]

        # create a list to be plotted
        data = []
        for filepath in files:
              with open(filepath, "r") as file:
                cumm_time_dict = json.load(file)
                data.append(np.array(cumm_time_dict["cumm_func_time"]))
                data.append(np.array(cumm_time_dict["cumm_comms_time"]))
                data.append(np.array(cumm_time_dict["cumm_e2e_time"]))

        fig, ax = plt.subplots()
        # Change plot aesthetics
        fontdict = {'size': 14}
        ymin = 0
        ymax = 2
        yticklabels = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.50, 1.75, 2]
        xticklabels = [" ", "1RPS", " ", " ", "4RPS", " ", " ", "8RPS", " "]

        ax.set_ylabel("Time (sec)", fontdict=fontdict)
        bplot = ax.boxplot(data,
                           vert=True,
                           widths=0.3,
                           patch_artist=True,
                           showfliers=False)
        
        
        # color='pink'
        colors = ['blue', 'green', 'brown']*3
        for patch, color in zip(bplot['boxes'], colors):
            patch.set_facecolor(color)

        ax.set_ylim(ymin=ymin, ymax=ymax)
        yticks = ax.get_yticks()
        
        # ax.minorticks_on()
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
        ax.xaxis.set_minor_locator(tck.NullLocator())
        ax.grid(axis="y", which="major", linestyle="-", color="black")
        ax.grid(axis="y", which="minor", linestyle="-", color="grey")
        ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])
        ax.set_yticklabels([str(y) for y in yticklabels])
        ax.set_xticklabels(xticklabels, fontdict=fontdict)

        _xloc = ax.get_xticks()
        vlines_x_between = []
        for idx in range(0, len(_xloc)-1):
            vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
        ax.vlines(x=vlines_x_between, ymin=0, ymax=ymax, linestyles='solid', color='darkgrey')
        ax.vlines(x=[vlines_x_between[2], vlines_x_between[5]], ymin=ymin, ymax=ymax, linestyles='solid', color='black')

        cumm_labels = [r'$\sum Exec$', r'$\sum Comms$', r'$\sum E2E$']
        legend_elements = [
                            Patch(facecolor='blue', edgecolor='black', label=cumm_labels[0]),
                            Patch(facecolor='green', edgecolor='black', label=cumm_labels[1]),
                            Patch(facecolor='red', edgecolor='black', label=cumm_labels[2])
                        ]
        legend = ax.legend(handles=legend_elements, loc='upper left')
        legend.get_frame().set_alpha(None)
        plt.savefig(f"{csp}-medium-rps-1-4-8-correction.pdf", bbox_inches='tight')