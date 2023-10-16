from xfbench_plotter import XFBenchPlotter

if __name__ == "__main__":
    dir = "/Users/tuhinkhare/Work/IISc/DREAM-Lab/XFaaS-Dev/sigmetrics-ad-hoc/microbenchmarks/datasize-variation-1kb-1mb/azure-centralindia-1-600-1KB-static-14-09-2023-21-55-41/exp1"
    plotter = XFBenchPlotter(dir, format="pdf")
    plotter.plot_comms_time_payload_varition(yticks=[])

