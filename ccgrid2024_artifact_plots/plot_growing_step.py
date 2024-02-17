import argparse
from collections import defaultdict
import os
import json
import statistics
import numpy as np


from matplotlib import pyplot as plt
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
parser.add_argument("--wf-user-directory", help="Path to the user directory")


def copy_pdf_file(src,dest):
    os.system(f"cp {src} {dest}")


if __name__ == "__main__":
    wf_user_directory = parser.parse_args().wf_user_directory + '/workflow-gen'

    xfaas_dir = os.getenv('XFAAS_DIR')
    deployments_file_path = f"{xfaas_dir}/deployments.txt"

    deployments = []
    with open(deployments_file_path, 'r') as f:
        deployments = f.readlines()
        deployments = [x.strip() for x in deployments]
    i = 0
    os.makedirs(f"{xfaas_dir}/ccgrid2024_artifact_plots/growing_step_timelines", exist_ok=True)
    timeline_dir = f"{xfaas_dir}/ccgrid2024_artifact_plots/growing_step_timelines"
    for deployment in deployments:
        log_file_dir = f"{wf_user_directory}/{deployment}/exp1/logs/"
        files = os.listdir(log_file_dir)
        log_file_path = f"{log_file_dir}/{files[0]}"
        plots_dir = f"{wf_user_directory}/{deployment}/exp1/plots/"
        plots = os.listdir(plots_dir)
        for p in plots:
            print(p)
            if 'timeline' in p:
                full_path = f"{plots_dir}/{p}"
                copy_pdf_file(full_path,timeline_dir)
        print(log_file_path)
        i += 1





