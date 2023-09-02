import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import pathlib
import argparse
import numpy as np

from collections import defaultdict
from serwo.python.src.utils.classes.commons.logger import LoggerFactory

logger = LoggerFactory.get_logger(__file__, log_level="INFO")

def get_timings(loglines):
    timings = defaultdict(list)
    for line in loglines:
        split_lines = line.split(",")
        nodename = split_lines[1].strip()
        mem_val = float(split_lines[2].strip())
        timings[nodename].append(mem_val)
    return timings

def plot_mem_usage_boxplot(timings):
        fig, ax = plt.subplots()
        fig.set_dpi(400)
        fontdict = {'size': 12}

        ax.set_xlabel("Task Name", fontdict=fontdict)
        ax.set_ylabel("Memory Consumed (in MB)", fontdict=fontdict)
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
        
        # TODO - plot edge later
        wf_labels = list([key for key in timings.keys()])
        logger.info(f"Workflow Labels - {wf_labels}")
        mem_usage = [np.array(timings[label]) for label in wf_labels]
        
        # rectangular box plot
        bplot1 = ax.boxplot(mem_usage,
                            vert=True,  # vertical box alignment
                            patch_artist=True,
                            showfliers=False)  # fill with color
                            # labels=interfunction_labels)
        
        ax.set_xticklabels(wf_labels, 
                           rotation=90,
                           fontdict=fontdict)
        
        ax.set_yticklabels([str(x) for x in range(0, 70, 10)], fontdict=fontdict)

        ax.yaxis.set_tick_params(which='major', labelsize=fontdict['size'])

        color_node = 'yellow'
        for patch in bplot1['boxes']:
            patch.set_facecolor(color_node)

        vlines = []
        _xloc = np.arange(len(wf_labels))
        for idx in range(0, len(_xloc)-1):
            vlines.append(_xloc[idx]/2 + _xloc[idx+1]/2)
        
        
        ax.set_ylim(ymin=0, ymax=60)
        ax.vlines(vlines, ymin=0, ymax=60, linestyles='solid', color='darkgrey')
        ax.grid(axis="y", which="major", linestyle="-", color="black")
        ax.grid(axis="y", which="minor", linestyle="--", color="grey")
        ax.set_axisbelow(True)

        fig.savefig(mem_logfile.parent / f"{output_filename}.{format}", bbox_inches='tight')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="What the program does",
        epilog="Text at the bottom of help",
    )

    parser.add_argument("--logfile",dest='mem_logfile',type=str,help="Path to memory usage logfile")
    parser.add_argument("--output-filename",dest='output_filename',type=str,help="Output Filename")
    parser.add_argument("--format",dest="format",type=str,help="Plot format (svg | pdf)")
    parser.add_argument("--plottype",dest="plot_type",type=str,help="Plot format (cpu | mem)")
    args = parser.parse_args()

    mem_logfile = pathlib.Path(args.mem_logfile)
    output_filename = args.output_filename
    format = args.format

    with open(mem_logfile, "r") as file:
        lines = file.readlines()
    
    timings = get_timings(lines)
    plot_mem_usage_boxplot(timings=timings)