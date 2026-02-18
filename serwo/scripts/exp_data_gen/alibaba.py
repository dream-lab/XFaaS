import argparse
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
parser.add_argument("--file-path", type=str, required=True,dest="file_path", help="Path to raw data file")
parser.add_argument("--out-put-file-path", type=str, required=True,dest="op_file_path", help="Path to output data file")
args = parser.parse_args()
file_path = args.file_path

## read csv file in a list append pairs of (timestamp, value)
with open(file_path, 'r') as f:
    data = f.readlines()
    data = [x.strip() for x in data]
    data = [x.split(',') for x in data]
    data = [(int(x[0]), int(x[1])) for x in data]
print(data)
## from element 2, take the difference between the timestamp and the previous one and insert it in a list
## along with the value


ans = []
ans.append((data[0][0], data[0][1]))

diff = [(data[i][0] - data[i-1][0],data[i][1]) for i in range(1, len(data))]
ans.extend(diff)
print(ans)

## write the list in a csv file
with open(args.op_file_path, 'w') as f:
    for item in ans:
        f.write("%s,%s\n" % item)
