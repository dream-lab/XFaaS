import os


def run_command(cmd):
    stream = os.popen(cmd)
    res = stream.read()
    stream.close()
    return res
